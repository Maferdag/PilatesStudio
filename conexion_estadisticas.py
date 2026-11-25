import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env.local", override=True)

load_dotenv()


def obtener_conexion_estadisticas():
    variables = [
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
    ]

    faltantes = [
        variable for variable in variables
        if not os.getenv(variable)
    ]

    if faltantes:
        raise RuntimeError(
            "Faltan variables de Supabase: "
            + ", ".join(faltantes)
        )

    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        sslmode="disable",
        row_factory=dict_row,
        connect_timeout=10,
    )
