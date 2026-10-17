from datetime import datetime
from mysql.connector import Error
from db import get_connection
from services.database_support import (
    read_cursor, close_resources, database_message, SaleCommitUnknown,
)


def search_product(term):
    with read_cursor() as cursor:
        term = f"%{term}%"
        cursor.execute(
            """SELECT CODIGO, PRODUCTO, PRECIO, CANTIDAD FROM inventario
            WHERE PRODUCTO LIKE %s OR CODIGO LIKE %s""", (term, term)
        )
        return cursor.fetchall()


def get_next_invoice():
    with read_cursor() as cursor:
        cursor.execute(
            "SELECT MAX(CAST(SUBSTR(num_factura, 3) AS UNSIGNED)) + 1 FROM ventas"
        )
        result = cursor.fetchone()[0] or 1
        return f"MN{result:010d}"


def register_sale(invoice, cart, payment_type, sale_date):
    conn = None
    cursor = None
    committing = False
    try:
        conn = get_connection()
        cursor = conn.cursor()
        for code, product, quantity, price, total in cart:
            cursor.execute(
                """INSERT INTO ventas
                (codigo_producto, num_factura, producto, cantidad, precio_unitario,
                 total, tipo_pago, fecha_venta)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (code, invoice, product, quantity, price, total, payment_type, sale_date),
            )
            cursor.execute(
                "UPDATE inventario SET cantidad = cantidad - %s WHERE codigo = %s",
                (quantity, code),
            )
        committing = True
        conn.commit()
        return True, "Venta registrada exitosamente."
    except Error as exc:
        if conn is not None:
            try:
                conn.rollback()
            except Error:
                pass
        if committing:
            raise SaleCommitUnknown(
                f"No se pudo confirmar el resultado de la factura {invoice}. "
                "No repitas la venta. Revisa el reporte de ventas y el inventario "
                "antes de volver a registrarla."
            ) from exc
        return False, database_message(exc)
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

