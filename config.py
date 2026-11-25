import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.engine import URL

# ==========================================
# UBICACIÓN PRINCIPAL DEL PROYECTO
# ==========================================

BASE_DIR = Path(__file__).resolve().parent


# ==========================================
# CARGAR VARIABLES DE ENTORNO
# ==========================================

# En el computador utiliza .env.local.
# En Render utiliza las variables configuradas
# directamente en el panel de Environment.

load_dotenv(BASE_DIR / ".env.local")


# ==========================================
# CONEXIÓN A POSTGRESQL - SUPABASE
# ==========================================

def obtener_database_url():

    variables = [
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD"
    ]

    # Comprobar que existan las variables
    faltantes = [
        variable for variable in variables
        if not os.getenv(variable)
    ]

    if faltantes:
        raise RuntimeError(
            "Faltan variables de PostgreSQL: "
            + ", ".join(faltantes)
        )

    # Crear conexión segura a PostgreSQL
    return URL.create(
        drivername="postgresql+psycopg",

        username=os.getenv("POSTGRES_USER"),

        password=os.getenv("POSTGRES_PASSWORD"),

        host=os.getenv("POSTGRES_HOST"),

        port=int(os.getenv("POSTGRES_PORT")),

        database=os.getenv("POSTGRES_DB"),

        query={
            "sslmode": os.getenv(
                "POSTGRES_SSLMODE", "require"
            )
        }
    )


# ==========================================
# CLAVE DE SEGURIDAD DEL SISTEMA
# ==========================================

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "Falta configurar SECRET_KEY en las variables de entorno."
    )