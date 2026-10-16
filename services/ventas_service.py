from db import get_connection
from datetime import datetime

def search_product(term):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT CODIGO, PRODUCTO, PRECIO, CANTIDAD
    FROM inventario
    WHERE PRODUCTO LIKE %s OR CODIGO LIKE %s
    """

    term = f"%{term}%"
    cursor.execute(query, (term, term))

    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return data

def get_next_invoice():
    conn = get_connection()
    if conn is None:
        return "MN000000000"
    
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(CAST(SUBSTR(num_factura, 3) AS UNSIGNED)) + 1 FROM MotoNorte.ventas")
    result = cursor.fetchone()[0]
    if not result:
            result = 1

    next_invoice = result

    cursor.close()
    conn.close()

    return f"MN{str(next_invoice).zfill(10)}"

def register_sale(invoice, cart, payment_type, sale_date):
    conn = get_connection()
    if conn is None:
        return False, "Could not connect to the database."
    
    cursor = conn.cursor()
    try:
        for item in cart:
            # item: (code, product, quantity, price, total)
            code, product, quantity, price, total = item

            # The query requires 8 values to match the 8 columns listed
            query = """
            INSERT INTO ventas (codigo_producto, num_factura, producto, cantidad, precio_unitario, total, tipo_pago, fecha_venta)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                code,         # codigo_producto
                invoice,      # num_factura
                product,      # producto
                quantity,     # cantidad
                price,        # precio_unitario
                total,        # total
                payment_type, # tipo_pago
                sale_date     # fecha_venta
            ))

            # Update inventory
            cursor.execute("""
                UPDATE inventario
                SET cantidad = cantidad - %s
                WHERE codigo = %s;
            """, (quantity, code))

        conn.commit()
        return True, "Venta registrada exitosamente."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

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

