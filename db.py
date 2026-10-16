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
}


def get_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"Error DB: {e}")
        return None