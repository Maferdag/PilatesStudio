
from conexion_estadisticas import obtener_conexion_estadisticas


def consultar_demanda_horarios():
    conexion = None

    try:
        conexion = obtener_conexion_estadisticas()

        consulta = """
            SELECT
                h.id AS id_horario,
                c.nombre_clase,
                h.fecha,
                h.hora,
                h.cupo_maximo,
                COUNT(r.id) FILTER (
                    WHERE LOWER(r.estado) = 'confirmada'
                ) AS reservas_confirmadas
            FROM horarios h
            JOIN clases c ON c.id = h.id_clase
            LEFT JOIN reservas r ON r.id_horario = h.id
            GROUP BY
                h.id,
                c.nombre_clase,
                h.fecha,
                h.hora,
                h.cupo_maximo
            ORDER BY
                reservas_confirmadas DESC,
                h.fecha,
                h.hora
        """

        with conexion.cursor() as cursor:
            cursor.execute(consulta)
            resultados = cursor.fetchall()

        print("\n=== HORARIOS CON MAYOR DEMANDA ===")

        if not resultados:
            print("No existen horarios registrados.")
            return

        for horario in resultados:
            reservas = horario["reservas_confirmadas"]
            cupos = horario["cupo_maximo"]

            ocupacion = (
                round(reservas / cupos * 100, 1)
                if cupos and cupos > 0 else 0
            )

            print("-----------------------------")
            print("Clase:", horario["nombre_clase"])
            print("Fecha:", horario["fecha"])
            print("Hora:", horario["hora"])
            print("Cupos máximos:", cupos)
            print("Reservas confirmadas:", reservas)
            print("Ocupación:", f"{ocupacion}%")

    except Exception as error:
        print("Error al consultar horarios.")
        print("Tipo de error:", type(error).__name__)

    finally:
        if conexion is not None:
            conexion.close()


if __name__ == "__main__":
    consultar_demanda_horarios()
