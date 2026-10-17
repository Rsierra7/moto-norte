from contextlib import contextmanager
from mysql.connector import Error
from db import get_connection, DatabaseConnectionError


class SaleCommitUnknown(Error):
    """Se perdió la confirmación del commit; no es seguro repetir la venta."""


def database_message(exc):
    if isinstance(exc, (DatabaseConnectionError, SaleCommitUnknown)):
        return str(exc)
    if exc.errno in (2006, 2013, 2055):
        return "Se perdió la conexión con MySQL. Comprueba el servidor y vuelve a consultar."
    if exc.errno in (1451, 1452):
        return "No se pudo guardar: hay un producto inexistente o registros relacionados."
    if exc.errno == 1062:
        return "No se pudo guardar porque existe un registro con la misma clave."
    return "No se pudo completar la operación en MySQL. Revisa la conexión y la estructura de la base."


def close_resources(conn, cursor):
    # No ocultar el resultado de un commit por un fallo posterior de limpieza.
    for resource in (cursor, conn):
        if resource is not None:
            try:
                resource.close()
            except Error:
                pass


@contextmanager
def read_cursor():
    conn = get_connection()
    cursor = None
    try:
        cursor = conn.cursor()
        yield cursor
    finally:
        close_resources(conn, cursor)
