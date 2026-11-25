
from conexion_estadisticas import obtener_conexion_estadisticas


def consultar_baja_asistencia():
    conexion = None

    try:
        conexion = obtener_conexion_estadisticas()

        consulta = """
            SELECT
                c.nombre_clase,
                h.fecha,
                h.hora,
                h.cupo_maximo,

                COUNT(r.id) FILTER (
                    WHERE LOWER(r.estado) = 'confirmada'
                ) AS reservas_confirmadas,

                COUNT(a.id) FILTER (
                    WHERE LOWER(a.estado) = 'presente'
                ) AS alumnos_presentes

            FROM horarios h

            INNER JOIN clases c
                ON c.id = h.id_clase

            LEFT JOIN reservas r
                ON r.id_horario = h.id

            LEFT JOIN asistencias a
                ON a.id_reserva = r.id

            WHERE h.fecha <= CURRENT_DATE

            GROUP BY
                h.id,
                c.nombre_clase,
                h.fecha,
                h.hora,
                h.cupo_maximo

            ORDER BY
                alumnos_presentes ASC,
                h.fecha DESC,
                h.hora
        """

        with conexion.cursor() as cursor:
            cursor.execute(consulta)
            resultados = cursor.fetchall()

        print("\n=== CLASES CON BAJA ASISTENCIA ===")

        if not resultados:
            print("No existen clases programadas hasta hoy.")
            return

        for clase in resultados:
            presentes = clase["alumnos_presentes"]
            cupos = clase["cupo_maximo"]

            porcentaje = (
                round(presentes / cupos * 100, 1)
                if cupos and cupos > 0
                else 0
            )

            print("------------------------------")
            print("Clase:", clase["nombre_clase"])
            print("Fecha:", clase["fecha"])
            print("Hora:", clase["hora"])
            print("Cupos:", cupos)
            print(
                "Reservas confirmadas:",
                clase["reservas_confirmadas"]
            )
            print("Alumnos presentes:", presentes)
            print("Ocupación por asistencia:", f"{porcentaje}%")

    except Exception as error:
        print("No se pudo consultar la asistencia.")
        print("Tipo de error:", type(error).__name__)

    finally:
        if conexion is not None:
            conexion.close()


if __name__ == "__main__":
    consultar_baja_asistencia()
