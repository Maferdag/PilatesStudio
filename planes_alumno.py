"""
Planes y pagos del lado del alumno.

Rutas que agrega:
  /alumno/planes                    -> catálogo de planes (tarjetas)
  /alumno/planes/<id>/pagar         -> resumen y confirmación del pago
  /alumno/mis-pagos                 -> historial de pagos del alumno

Se conecta igual que reservas.py:
    registrar_rutas_planes(app, db, Usuario, Plan, Pago)
"""

from datetime import date

from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    session,
    request
)
from sqlalchemy import func


# ------------------------------------------------------------------
# MODO DEMOSTRACIÓN
# ------------------------------------------------------------------
# Mientras sea True, el pago se registra en la base de datos pero NO se
# cobra dinero de verdad. Para cobrar de verdad hay que conectar una
# pasarela (Webpay, Flow, Mercado Pago...) dentro de procesar_cobro()
# y dejar esta variable en False.
MODO_DEMOSTRACION = True


def procesar_cobro(alumno, plan):
    """Cobra el plan al alumno. Devuelve True si el cobro fue aprobado.

    Aquí va la llamada a la pasarela de pago. En modo demostración
    aprueba siempre, sin cobrar nada.
    """
    return True


# ------------------------------------------------------------------
# Formatos para las plantillas
# ------------------------------------------------------------------

def formatear_clp(valor):
    """49990 -> $49.990 (formato chileno)."""
    try:
        return "$" + f"{int(round(valor)):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "$0"


def descripcion_plan(cantidad_clases):
    """4 -> '4 clases · 1 vez por semana'."""
    if not cantidad_clases:
        return ""

    if cantidad_clases == 1:
        return "1 clase"

    if cantidad_clases % 4 == 0:
        por_semana = cantidad_clases // 4
        veces = "1 vez" if por_semana == 1 else f"{por_semana} veces"
        return f"{cantidad_clases} clases · {veces} por semana"

    return f"{cantidad_clases} clases"


def registrar_rutas_planes(app, db, Usuario, Plan, Pago):
    """Agrega a la app las rutas de planes y pagos del alumno."""

    if 'cliente_planes' in app.view_functions:
        return

    app.add_template_filter(formatear_clp, 'clp')
    app.add_template_filter(descripcion_plan, 'descripcion_plan')

    def alumno_actual():
        if 'usuario_id' not in session:
            return None
        usuario = db.session.get(Usuario, session['usuario_id'])
        if usuario is None:
            return None
        return usuario.alumno

    # --------------------------------------------------------------
    # CATÁLOGO DE PLANES
    # --------------------------------------------------------------
    @app.route('/alumno/planes')
    def cliente_planes():
        alumno = alumno_actual()
        if alumno is None:
            flash('Debes iniciar sesión como alumno para ver los planes.')
            return redirect(url_for('login'))

        planes = Plan.query.order_by(Plan.precio).all()

        # "Más elegido": el plan con más pagos registrados.
        # Solo se muestra si hay al menos dos planes para comparar.
        mas_elegido = None
        if len(planes) > 1:
            fila = (
                db.session.query(Pago.id_plan, func.count(Pago.id))
                .group_by(Pago.id_plan)
                .order_by(func.count(Pago.id).desc())
                .first()
            )
            if fila:
                mas_elegido = fila[0]

        return render_template(
            'cliente_planes.html',
            planes=planes,
            mas_elegido=mas_elegido
        )

    # --------------------------------------------------------------
    # RESUMEN Y CONFIRMACIÓN DEL PAGO
    # --------------------------------------------------------------
    @app.route('/alumno/planes/<int:plan_id>/pagar', methods=['GET', 'POST'])
    def cliente_pagar_plan(plan_id):
        alumno = alumno_actual()
        if alumno is None:
            flash('Debes iniciar sesión como alumno para contratar un plan.')
            return redirect(url_for('login'))

        plan = db.session.get(Plan, plan_id)
        if plan is None:
            flash('El plan seleccionado no existe.')
            return redirect(url_for('cliente_planes'))

        if request.method == 'POST':
            try:
                if not procesar_cobro(alumno, plan):
                    flash('No se pudo procesar el pago. Inténtalo nuevamente.')
                    return redirect(
                        url_for('cliente_pagar_plan', plan_id=plan.id)
                    )

                # El monto sale siempre del plan guardado en la base de
                # datos, nunca de lo que envíe el navegador.
                db.session.add(
                    Pago(
                        id_alumno=alumno.id,
                        id_plan=plan.id,
                        fecha_pago=date.today(),
                        monto=plan.precio
                    )
                )
                db.session.commit()

            except Exception:
                db.session.rollback()
                app.logger.exception('Error al registrar el pago del alumno')
                flash('No se pudo registrar el pago. Inténtalo nuevamente.')
                return redirect(
                    url_for('cliente_pagar_plan', plan_id=plan.id)
                )

            flash(f'¡Pago registrado! Contrataste el plan {plan.nombre_plan}.')
            return redirect(url_for('cliente_mis_pagos'))

        return render_template(
            'cliente_pagar_plan.html',
            plan=plan,
            modo_demostracion=MODO_DEMOSTRACION
        )

    # --------------------------------------------------------------
    # HISTORIAL DE PAGOS
    # --------------------------------------------------------------
    @app.route('/alumno/mis-pagos')
    def cliente_mis_pagos():
        alumno = alumno_actual()
        if alumno is None:
            flash('Debes iniciar sesión como alumno para ver tus pagos.')
            return redirect(url_for('login'))

        pagos = (
            Pago.query.filter_by(id_alumno=alumno.id)
            .order_by(Pago.fecha_pago.desc(), Pago.id.desc())
            .all()
        )

        return render_template('cliente_mis_pagos.html', pagos=pagos)
