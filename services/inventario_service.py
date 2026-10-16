#from json import load
from mysql.connector import Error

from db import get_connection

def fetch_inventory():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT CODIGO, PRODUCTO, UBICACION, PRECIO, CANTIDAD, TOTAL FROM inventario")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

def add_product(cod, prod, ubic, precio, cantidad):
    conn = get_connection()
    cursor = conn.cursor()
    total = precio * cantidad

    query = """
    INSERT INTO inventario (CODIGO, PRODUCTO, UBICACION, PRECIO, CANTIDAD, TOTAL)
    VALUES (%s, %s, %s, %s, %s, %s)
    """

    cursor.execute(query, (cod.upper(), prod.upper(), ubic.upper(), precio, cantidad, total))
    conn.commit()

    cursor.close()
    conn.close()

def update_product(cod, prod, ubic, precio, cantidad):
    conn = get_connection()
    cursor = conn.cursor()

    total = precio * cantidad

    query = """
    UPDATE inventario
    SET PRODUCTO=%s, UBICACION=%s, PRECIO=%s, CANTIDAD=%s, TOTAL=%s
    WHERE CODIGO=%s
    """

    cursor.execute(query, (prod, ubic, precio, cantidad, total, cod))
    conn.commit()

    cursor.close()
    conn.close()

"""
def delete_product(cod):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM inventario WHERE CODIGO=%s", (cod,))
        conn.commit()
    except Error as e:
        return False
    finally:
        cursor.close()
        conn.close()   
"""
def delete_product_db(cod):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Usamos .strip() por si acaso hay espacios invisibles
        cursor.execute("DELETE FROM inventario WHERE CODIGO=%s", (str(cod).strip(),))
        conn.commit()
        return True # <-- IMPORTANTE: Confirmamos que se hizo el commit
    except Exception as e:
        print(f"Error en DB: {e}") # Esto te ayudará a depurar en la terminal
        return False
    finally:
        cursor.close()
        conn.close()    

def search_inventory(term):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT CODIGO, PRODUCTO, UBICACION, PRECIO, CANTIDAD, TOTAL
    FROM inventario
    WHERE CODIGO LIKE %s OR PRODUCTO LIKE %s
    """

    term = f"%{term}%"
    cursor.execute(query, (term, term))

    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return data