
from conexion_estadisticas import obtener_conexion_estadisticas


def consultar_alumnos_inactivos():
    try:
        with obtener_conexion_estadisticas() as conexion:
            with conexion.cursor() as cursor:

                consulta = """
                    SELECT
                        al.id,
                        al.nombre_completo,

                        MAX(
                            CASE
                                WHEN LOWER(a.estado) = 'presente'
                                THEN h.fecha
                                ELSE NULL
                            END
                        ) AS ultima_asistencia

                    FROM alumnos al

                    LEFT JOIN reservas r
                        ON r.id_alumno = al.id

                    LEFT JOIN asistencias a
                        ON a.id_reserva = r.id

                    LEFT JOIN horarios h
                        ON h.id = r.id_horario

                    GROUP BY
                        al.id,
                        al.nombre_completo

                    HAVING
                        MAX(
                            CASE
                                WHEN LOWER(a.estado) = 'presente'
                                THEN h.fecha
                                ELSE NULL
                            END
                        ) < CURRENT_DATE - INTERVAL '30 days'

                        OR MAX(
                            CASE
                                WHEN LOWER(a.estado) = 'presente'
                                THEN h.fecha
                                ELSE NULL
                            END
                        ) IS NULL

                    ORDER BY ultima_asistencia ASC NULLS FIRST
                """

                cursor.execute(consulta)
                resultados = cursor.fetchall()

                print("\n=== ALUMNOS SIN ASISTENCIA RECIENTE ===")

                if not resultados:
                    print("No se encontraron alumnos inactivos.")
                    return

                for alumno in resultados:
                    print("-----------------------------")
                    print("Alumno:", alumno["nombre_completo"])
                    print("Última asistencia:",
                          alumno["ultima_asistencia"] or
                          "Sin asistencia registrada")

    except Exception as error:
        print("Error al consultar alumnos inactivos:")
        print(type(error).__name__, str(error))


if __name__ == "__main__":
    consultar_alumnos_inactivos()
