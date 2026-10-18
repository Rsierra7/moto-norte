from datetime import datetime
from decimal import Decimal, InvalidOperation

from mysql.connector import Error

from db import get_connection
from services.database_support import (
    SaleCommitUnknown,
    close_resources,
    database_message,
    read_cursor,
)


LABOUR_CODE = "MO01"


class SaleValidationError(ValueError):
    """Los datos o las existencias no permiten registrar la venta."""


def search_product(term):
    with read_cursor() as cursor:
        term = f"%{term}%"

        cursor.execute(
            """
            SELECT CODIGO, PRODUCTO, PRECIO, CANTIDAD
            FROM inventario
            WHERE PRODUCTO LIKE %s OR CODIGO LIKE %s
            """,
            (term, term),
        )

        return cursor.fetchall()


def _validated_cart(cart):
    if not cart:
        raise SaleValidationError("El carrito está vacío.")

    validated = []

    for code, product, quantity, price, total in cart:
        code = str(code).strip()

        if not code:
            raise SaleValidationError(
                "Hay un producto sin código."
            )

        try:
            if isinstance(quantity, bool):
                raise ValueError()

            number = Decimal(str(quantity))

            if (
                not number.is_finite()
                or number <= 0
                or number != number.to_integral_value()
            ):
                raise ValueError()

            quantity = int(number)

        except (InvalidOperation, ValueError, OverflowError):
            raise SaleValidationError(
                f"La cantidad de {product} ({code}) debe ser "
                "un entero mayor que cero."
            ) from None

        if code.upper() == LABOUR_CODE:
            code = LABOUR_CODE

        validated.append(
            (code, product, quantity, price, total)
        )

    return validated


def _allocate_invoice(cursor):
    """
    Reserva el siguiente número dentro de la transacción.

    El bloqueo permanece hasta confirmar o revertir toda la venta.
    """
    cursor.execute(
        """
        SELECT ultimo_numero
        FROM numeracion_facturas
        WHERE prefijo = %s
        FOR UPDATE
        """,
        ("MN",),
    )

    row = cursor.fetchone()

    if row is None:
        raise SaleValidationError(
            "Falta inicializar la numeración de facturas. "
            "Ejecuta la actualización de la base de datos."
        )

    number = int(row[0]) + 1

    if number > 9999999999:
        raise SaleValidationError(
            "Se agotó la numeración disponible para el prefijo MN."
        )

    cursor.execute(
        """
        UPDATE numeracion_facturas
        SET ultimo_numero = %s
        WHERE prefijo = %s
        """,
        (number, "MN"),
    )

    return f"MN{number:010d}"


def register_sale(cart, payment_type, sale_date):
    """
    Devuelve:
        (éxito, mensaje, número de factura)

    La factura solo se devuelve cuando el commit fue confirmado.
    """
    try:
        cart = _validated_cart(cart)
    except SaleValidationError as exc:
        return False, str(exc), None

    conn = None
    cursor = None
    committing = False
    invoice = None

    try:
        conn = get_connection()
        conn.start_transaction()

        cursor = conn.cursor()

        # Reservar el número antes de guardar los productos.
        invoice = _allocate_invoice(cursor)

        for code, product, quantity, price, total in cart:
            if code == LABOUR_CODE:
                # Crear la referencia requerida por la clave foránea.
                # Si ya existe, conservar sus datos y existencias.
                cursor.execute(
                    """
                    INSERT INTO inventario (
                        CODIGO,
                        PRODUCTO,
                        UBICACION,
                        PRECIO,
                        CANTIDAD,
                        TOTAL
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE CODIGO = CODIGO
                    """,
                    (
                        LABOUR_CODE,
                        "MANO DE OBRA",
                        "SERVICIO",
                        0,
                        0,
                        0,
                    ),
                )

            else:
                # Comprobar y descontar en una sola operación.
                cursor.execute(
                    """
                    UPDATE inventario
                    SET CANTIDAD = CANTIDAD - %s
                    WHERE CODIGO = %s
                      AND CANTIDAD >= %s
                    """,
                    (quantity, code, quantity),
                )

                if cursor.rowcount != 1:
                    raise SaleValidationError(
                        "Existencias insuficientes o producto "
                        f"inexistente: {product} ({code}). "
                        f"Cantidad solicitada: {quantity}. "
                        "No se registró la venta. "
                        "Actualiza la búsqueda y revisa el carrito."
                    )

            cursor.execute(
                """
                INSERT INTO ventas (
                    codigo_producto,
                    num_factura,
                    producto,
                    cantidad,
                    precio_unitario,
                    total,
                    tipo_pago,
                    fecha_venta
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    code,
                    invoice,
                    product,
                    quantity,
                    price,
                    total,
                    payment_type,
                    sale_date,
                ),
            )

        committing = True
        conn.commit()

        return (
            True,
            f"Venta registrada exitosamente. Factura: {invoice}.",
            invoice,
        )

    except (Error, SaleValidationError) as exc:
        if conn is not None:
            try:
                conn.rollback()
            except Error:
                pass

        if committing:
            raise SaleCommitUnknown(
                "No se pudo confirmar el resultado de la factura "
                f"{invoice}. No repitas la venta. "
                "Revisa el reporte de ventas y el inventario "
                "antes de volver a registrarla."
            ) from exc

        if isinstance(exc, SaleValidationError):
            message = str(exc)

        elif getattr(exc, "errno", None) == 1146:
            message = (
                "Falta una tabla necesaria. "
                "Revisa la estructura de la base de datos "
                "y ejecuta la actualización de numeración."
            )

        else:
            message = database_message(exc)

        return False, message, None

    finally:
        close_resources(conn, cursor)

def build_invoice_text(invoice, cart):

    # invoice = get_next_invoice()
    total = sum(item[4] for item in cart)
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    # 1. Configuración de ancho para POS-58 (32 caracteres es el estándar)
    # Si ves que sobra mucho espacio, puedes probar con 40, pero 32 es lo seguro.
    ANCHO = 32 

    def format_line(text_left, text_right, width=ANCHO):
        # Aseguramos que el texto no exceda el ancho para evitar saltos de línea
        espacios = width - len(str(text_left)) - len(str(text_right))
        if espacios < 0: espacios = 1
        return f"{text_left}{' ' * espacios}{text_right}"
    # 2. Construcción del cuerpo de la factura
    # Nota: He quitado los emojis porque muchas POS-58 no los procesan en modo texto
    # y causan que la impresora salte de línea erróneamente.
    lines = []
    lines.append("=" * ANCHO)
    lines.append("MOTO NORTE".center(ANCHO))
    lines.append("NIT: 52899596-5".center(ANCHO))
    lines.append("Dir: KR 118 # 138 - 14".center(ANCHO))
    lines.append("Tel: +57 3102217917".center(ANCHO))
    lines.append("=" * ANCHO)
    lines.append(f"Factura: {invoice}")
    lines.append(f"Fecha:   {fecha}")
    lines.append("=" * ANCHO)
    lines.append(format_line("Producto", "Total"))
    lines.append("-" * ANCHO)

    for code, product, qty, price, subtotal in cart:
        # Cortamos el nombre si es muy largo para que no rompa el formato
        name = product[:ANCHO] 
        qty_price = f"{qty} x {price:.0f}"
        total_str = f"{subtotal:.0f}"
        
        lines.append(name)
        lines.append(format_line(qty_price, total_str))

    lines.append("-" * ANCHO)
    lines.append(format_line("TOTAL:", f"${total:.0f}"))
    lines.append("=" * ANCHO)
    lines.append("¡Gracias por su compra!".center(ANCHO))
    lines.append("-" * ANCHO)
    lines.append("\nY todo lo que hagáis, hacedlo".center(ANCHO))
    lines.append("de corazón, como para el Señor".center(ANCHO))
    lines.append("y no para los hombres".center(ANCHO))
    lines.append("Colosenses 3:23\n".center(ANCHO))
    lines.append("=" * ANCHO)
    lines.append("\n\n\n") # Espacio para poder cortar el papel
    
    cuerpo_factura="\n".join(lines)
    
    return cuerpo_factura

