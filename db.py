import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", ""),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", ""),
    "connection_timeout": 5,
}


class DatabaseConnectionError(Error):
    """No fue posible establecer una conexión con MySQL."""


def get_connection():
    if not DB_CONFIG["user"] or not DB_CONFIG["database"]:
        raise DatabaseConnectionError(
            "Falta configurar DB_USER o DB_NAME en el archivo .env."
        )
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as exc:
        if exc.errno == 1045:
            message = "MySQL rechazó las credenciales. Revisa DB_USER y DB_PASSWORD en .env."
        elif exc.errno == 1049:
            message = "La base de datos no existe. Revisa DB_NAME en .env."
        else:
            message = "No se pudo conectar a MySQL. Revisa el servidor, DB_HOST y la conexión."
        raise DatabaseConnectionError(message) from exc
