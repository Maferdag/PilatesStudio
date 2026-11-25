import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()
def obtener_conexion():
    servidor = os.getenv("DB_SERVER")

    if not servidor:
        raise RuntimeError(
            "Falta configurar DB_SERVER en el equipo."
        )

    conexion = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={servidor};"
        "DATABASE=PilatesStudio;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )

    return conexion
