import os
from dotenv import load_dotenv
from google import genai

load_dotenv()


def analizar_estadisticas(datos):
    """Analiza estadísticas de Pilates Studio con Gemini API."""

    clave = os.getenv("GEMINI_API_KEY")

    if not clave:
        raise RuntimeError(
            "No se encontró GEMINI_API_KEY en el archivo .env"
        )

    cliente = genai.Client(api_key=clave)

    prompt = f"""
Eres un asistente de análisis administrativo para Pilates Studio.

Analiza las siguientes estadísticas:
{datos}

Instrucciones:
- Responde en español.
- No inventes información ni resultados.
- Si hay pocos registros, indica que los datos son insuficientes.
- Genera hasta tres recomendaciones prácticas.
- No realices diagnósticos de salud.
- Responde de forma clara y profesional.
"""

    respuesta = cliente.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    return respuesta.text or "Gemini no devolvió recomendaciones."


if __name__ == "__main__":

    datos_prueba = {
        "alumnos": 12,
        "reservas": 35,
        "asistencias": 28,
        "horarios": 8,
        "reservas_semanales": [5, 7, 9, 14],
        "prediccion": [16, 18]
    }

    try:
        print("=== ANÁLISIS CON GEMINI API ===")
        print(analizar_estadisticas(datos_prueba))

    except Exception as error:
        print("\n=== DIAGNÓSTICO DE GEMINI ===")
        print("Tipo de error:", type(error).__name__)
        print("Código HTTP:", getattr(error, "code", "No disponible"))

        codigo = getattr(error, "code", None)

        if codigo == 400:
            print("La solicitud no es válida.")
        elif codigo == 401:
            print("La clave API no fue aceptada.")
        elif codigo == 403:
            print("La clave o el proyecto no tiene permisos.")
        elif codigo == 404:
            print("El modelo solicitado no está disponible.")
        elif codigo == 429:
            print("Se alcanzó un límite de uso o cuota.")
        else:
            print("Es necesario revisar la configuración de Gemini.")
