
def predecir_reservas(reservas_historicas, semanas_futuras=2):
    """
    Estima reservas futuras mediante una tendencia lineal simple.
    Los resultados son orientativos.
    """

    if len(reservas_historicas) < 3:
        return []

    valores = [float(valor) for valor in reservas_historicas]
    cantidad = len(valores)

    promedio_x = (cantidad - 1) / 2
    promedio_y = sum(valores) / cantidad

    numerador = sum(
        (i - promedio_x) * (valor - promedio_y)
        for i, valor in enumerate(valores)
    )

    denominador = sum(
        (i - promedio_x) ** 2
        for i in range(cantidad)
    )

    pendiente = numerador / denominador if denominador else 0
    intercepto = promedio_y - pendiente * promedio_x

    predicciones = []

    for semana in range(cantidad, cantidad + semanas_futuras):
        estimacion = pendiente * semana + intercepto
        predicciones.append(max(0, round(estimacion)))

    return predicciones


if __name__ == "__main__":
    datos_prueba = [22, 27, 32, 39]
    print("Reservas históricas:", datos_prueba)
    print("Predicción próximas 2 semanas:",
          predecir_reservas(datos_prueba))
