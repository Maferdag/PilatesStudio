from datetime import date
from flask import render_template, redirect, url_for, flash, session, Response

ESTILOS = """
:root {
  --lila: #b39ddb;
  --lila-oscuro: #7b5fb5;
  --lila-claro: #ece6f7;
  --menta: #a8e0c8;
  --menta-oscuro: #2f8a69;
  --menta-claro: #e3f6ee;
  --fondo: #f7f4fb;
  --crema: #ffffff;
  --texto: #2e2a3a;
  --borde: #e2daf0;
}

body {
  background-color: var(--fondo);
  color: var(--texto);
  font-family: "Segoe UI", system-ui, sans-serif;
}

h1 {
  font-weight: 600;
  color: var(--lila-oscuro);
  margin: 1.5rem 0 1rem;
}

.barra-superior {
  background-color: var(--lila-oscuro);
  padding: 0.8rem 0;
}
.barra-superior .navbar-brand,
.barra-superior .nav-link {
  color: #fff;
}
.barra-superior .nav-link:hover {
  color: var(--menta);
}

.tarjeta {
  background-color: var(--crema);
  border: 1px solid var(--borde);
  border-radius: 16px;
  box-shadow: 0 2px 10px rgba(123, 95, 181, 0.12);
  overflow: hidden;
}
.tarjeta .table {
  margin-bottom: 0;
  --bs-table-bg: transparent;
  --bs-table-hover-bg: var(--lila-claro);
}
.tarjeta thead th {
  background-color: var(--lila);
  color: #fff;
  border: none;
  padding: 14px 16px;
}
.tarjeta tbody td {
  padding: 14px 16px;
  vertical-align: middle;
  border-color: var(--borde);
}

.btn-salvia {
  background-color: var(--menta-oscuro);
  border-color: var(--menta-oscuro);
  color: #fff;
  border-radius: 20px;
  padding: 6px 18px;
}
.btn-salvia:hover {
  background-color: #247055;
  border-color: #247055;
  color: #fff;
}
.btn-espera {
  background-color: transparent;
  border: 1px solid var(--lila-oscuro);
  color: var(--lila-oscuro);
  border-radius: 20px;
  padding: 6px 18px;
}
.btn-espera:hover {
  background-color: var(--lila-oscuro);
  color: #fff;
}
.btn-cancelar {
  background-color: transparent;
  border: 1px solid #c0707f;
  color: #c0707f;
  border-radius: 20px;
  padding: 6px 18px;
}
.btn-cancelar:hover {
  background-color: #c0707f;
  color: #fff;
}

.insignia {
  display: inline-block;
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
}
.insignia-libre,
.insignia-confirmada {
  background-color: var(--menta-claro);
  color: var(--menta-oscuro);
}
.insignia-llena,
.insignia-cancelada {
  background-color: var(--lila-claro);
  color: var(--lila-oscuro);
}

.alerta-salvia {
  background-color: var(--menta-claro);
  border: 1px solid var(--menta);
  color: var(--texto);
  border-radius: 12px;
}
"""


def registrar_rutas_reservas(app, db, Usuario, Horario, Reserva, ListaEspera):
    """Agrega a la app las rutas de reservas del lado cliente."""

    if 'cliente_horarios' in app.view_functions:
        return

    def alumno_actual():
        if 'usuario_id' not in session:
            return None
        usuario = db.session.get(Usuario, session['usuario_id'])
        if usuario is None:
            return None
        return usuario.alumno

    
    def cupos_ocupados(horario_id):
        return Reserva.query.filter_by(
            id_horario=horario_id,
            estado='confirmada'
        ).count()


    @app.route('/reservas/estilos.css')
    def cliente_estilos():
        return Response(ESTILOS, mimetype='text/css')

    @app.route('/reservas/horarios')
    def cliente_horarios():
        alumno = alumno_actual()
        if alumno is None:
            flash('Debes iniciar sesión como alumno para reservar.')
            return redirect(url_for('login'))

        horarios = (
            Horario.query.filter(Horario.fecha >= date.today())
            .order_by(Horario.fecha, Horario.hora)
            .all()
        )
        datos = []
        for h in horarios:
            libres = h.cupo_maximo - cupos_ocupados(h.id)
            datos.append({'horario': h, 'libres': libres})
        return render_template('cliente_horarios.html', datos=datos)

    @app.route('/reservas/reservar/<int:horario_id>', methods=['POST'])
    def cliente_reservar(horario_id):
        alumno = alumno_actual()
        if alumno is None:
            flash('Debes iniciar sesión como alumno para reservar.')
            return redirect(url_for('login'))

        horario = Horario.query.get_or_404(horario_id)

        ya_reservo = Reserva.query.filter_by(
            id_alumno=alumno.id, id_horario=horario_id, estado='confirmada'
        ).first()
        if ya_reservo:
            flash('Ya tienes una reserva en esta clase.')
            return redirect(url_for('cliente_horarios'))

        if cupos_ocupados(horario_id) >= horario.cupo_maximo:
            flash('La clase está llena. Puedes unirte a la lista de espera.')
            return redirect(url_for('cliente_horarios'))

        db.session.add(Reserva(id_alumno=alumno.id, id_horario=horario_id))
        db.session.commit()
        flash('¡Reserva confirmada!')
        return redirect(url_for('cliente_mis_reservas'))

    @app.route('/reservas/cancelar/<int:reserva_id>', methods=['POST'])
    def cliente_cancelar(reserva_id):
        alumno = alumno_actual()
        if alumno is None:
            flash('Debes iniciar sesión como alumno.')
            return redirect(url_for('login'))

        reserva = Reserva.query.get_or_404(reserva_id)
        if reserva.id_alumno != alumno.id:
            flash('No puedes cancelar la reserva de otra persona.')
            return redirect(url_for('cliente_mis_reservas'))

        reserva.estado = 'cancelada'
        db.session.commit()

        siguiente = (
            ListaEspera.query.filter_by(id_horario=reserva.id_horario)
            .order_by(ListaEspera.id)
            .first()
        )
        if siguiente:
            db.session.add(
                Reserva(id_alumno=siguiente.id_alumno, id_horario=reserva.id_horario)
            )
            db.session.delete(siguiente)
            db.session.commit()

        flash('Reserva cancelada.')
        return redirect(url_for('cliente_mis_reservas'))

    @app.route('/reservas/lista-espera/<int:horario_id>', methods=['POST'])
    def cliente_lista_espera(horario_id):
        alumno = alumno_actual()
        if alumno is None:
            flash('Debes iniciar sesión como alumno.')
            return redirect(url_for('login'))

        Horario.query.get_or_404(horario_id)

        ya_reservo = Reserva.query.filter_by(
            id_alumno=alumno.id, id_horario=horario_id, estado='confirmada'
        ).first()
        ya_esta = ListaEspera.query.filter_by(
            id_alumno=alumno.id, id_horario=horario_id
        ).first()

        if ya_reservo:
            flash('Ya tienes una reserva en esta clase.')
        elif ya_esta:
            flash('Ya estás en la lista de espera de esta clase.')
        else:
            db.session.add(ListaEspera(id_alumno=alumno.id, id_horario=horario_id))
            db.session.commit()
            flash('Quedaste en la lista de espera.')
        return redirect(url_for('cliente_horarios'))

    @app.route('/reservas/mis-reservas')
    def cliente_mis_reservas():
        alumno = alumno_actual()
        if alumno is None:
            flash('Debes iniciar sesión como alumno.')
            return redirect(url_for('login'))

        reservas = (
            Reserva.query.filter_by(id_alumno=alumno.id)
            .order_by(Reserva.id.desc())
            .all()
        )
        return render_template('cliente_mis_reservas.html', reservas=reservas)