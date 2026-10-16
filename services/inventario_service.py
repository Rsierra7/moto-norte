from contextlib import contextmanager

from db import get_connection


@contextmanager
def _cursor(write=False):
    """Cierra los recursos y revierte las escrituras que fallen."""
    conn = get_connection()
    cursor = None
    try:
        cursor = conn.cursor()
        yield cursor
        if write:
            conn.commit()
    except Exception:
        if write:
            try:
                conn.rollback()
            except Exception:
                pass  # Conservar el error original si se perdió la conexión.
        raise
    finally:
        try:
            if cursor is not None:
                cursor.close()
        finally:
            conn.close()


def fetch_inventory():
    with _cursor() as cursor:
        cursor.execute(
            "SELECT CODIGO, PRODUCTO, UBICACION, PRECIO, CANTIDAD, TOTAL FROM inventario"
        )
        return cursor.fetchall()


def add_product(cod, prod, ubic, precio, cantidad):
    with _cursor(write=True) as cursor:
        cursor.execute(
            """INSERT INTO inventario
            (CODIGO, PRODUCTO, UBICACION, PRECIO, CANTIDAD, TOTAL)
            VALUES (%s, %s, %s, %s, %s, %s)""",
            (cod.upper(), prod.upper(), ubic.upper(), precio, cantidad, precio * cantidad),
        )


def update_product(cod, prod, ubic, precio, cantidad):
    with _cursor(write=True) as cursor:
        cursor.execute(
            """UPDATE inventario
            SET PRODUCTO=%s, UBICACION=%s, PRECIO=%s, CANTIDAD=%s, TOTAL=%s
            WHERE CODIGO=%s""",
            (prod, ubic, precio, cantidad, precio * cantidad, cod),
        )


def delete_product_db(cod):
    with _cursor(write=True) as cursor:
        cursor.execute("DELETE FROM inventario WHERE CODIGO=%s", (str(cod).strip(),))
        return cursor.rowcount > 0


def search_inventory(term):
    with _cursor() as cursor:
        term = f"%{term}%"
        cursor.execute(
            """SELECT CODIGO, PRODUCTO, UBICACION, PRECIO, CANTIDAD, TOTAL
            FROM inventario WHERE CODIGO LIKE %s OR PRODUCTO LIKE %s""",
            (term, term),
        )
        return cursor.fetchall()
