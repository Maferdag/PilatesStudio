
import os
import uuid
import psycopg

from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from sqlalchemy.engine import URL

from config import (
    obtener_database_url,
    SECRET_KEY
)

from predicciones import predecir_reservas
from conexion_estadisticas import obtener_conexion_estadisticas
from reservas import registrar_rutas_reservas
from planes_alumno import registrar_rutas_planes
# ==========================================
# CONFIGURACIÓN DE LA APLICACIÓN
# ==========================================

app = Flask(__name__)

app.config["SECRET_KEY"] = SECRET_KEY

app.config["SQLALCHEMY_DATABASE_URI"] = obtener_database_url()

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True
}


# ==========================================
# CONEXIÓN ÚNICA A POSTGRESQL
# ==========================================

db = SQLAlchemy(app)


# ==========================================
# MIGRACIONES DE BASE DE DATOS
# ==========================================

migrate = Migrate(app, db)


# ==========================================
# DEFINICIÓN DE LAS 11 TABLAS (MODELOS)
# ==========================================

class Alumno(db.Model):
    __tablename__ = 'alumnos'
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), unique=True, nullable=False)
    nombre_completo = db.Column(db.String(150), nullable=False)
    telefono = db.Column(db.String(20))
    reservas = db.relationship('Reserva', backref='alumno', lazy=True)
    pagos = db.relationship('Pago', backref='alumno', lazy=True)
    lista_espera = db.relationship('ListaEspera', backref='alumno', lazy=True)


class Instructor(db.Model):
    __tablename__ = 'instructores'

    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id'),
        unique=True,
        nullable=True
    )
    nombre_completo = db.Column(db.String(150), nullable=False)
    especialidad = db.Column(db.String(100))

    horarios = db.relationship(
        'Horario',
        backref='instructor',
        lazy=True
    )


class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    contrasena_hash = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='alumno')

    estado_aprobacion = db.Column(
        db.String(20),
        nullable=False,
        default='aprobado'
    )

    alumno = db.relationship(
        'Alumno',
        backref='usuario',
        uselist=False
    )

    instructor = db.relationship(
        'Instructor',
        backref='usuario',
        uselist=False
    )

    notificaciones = db.relationship(
        'Notificacion',
        backref='usuario',
        lazy=True
    )


class Clase(db.Model):
    __tablename__ = 'clases'
    id = db.Column(db.Integer, primary_key=True)
    nombre_clase = db.Column(db.String(100), nullable=False)
    duracion_minutos = db.Column(db.Integer, nullable=False)
    horarios = db.relationship('Horario', backref='clase', lazy=True)

class Horario(db.Model):
    __tablename__ = 'horarios'
    id = db.Column(db.Integer, primary_key=True)
    id_clase = db.Column(db.Integer, db.ForeignKey('clases.id'), nullable=False)
    id_instructor = db.Column(db.Integer, db.ForeignKey('instructores.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, nullable=False)
    cupo_maximo = db.Column(db.Integer, nullable=False)
    reservas = db.relationship('Reserva', backref='horario', lazy=True)
    lista_espera = db.relationship('ListaEspera', backref='horario', lazy=True)

class Reserva(db.Model):
    __tablename__ = 'reservas'
    id = db.Column(db.Integer, primary_key=True)
    id_alumno = db.Column(db.Integer, db.ForeignKey('alumnos.id'), nullable=False)
    id_horario = db.Column(db.Integer, db.ForeignKey('horarios.id'), nullable=False)
    estado = db.Column(db.String(20), default='confirmada')
    fecha_reserva = db.Column(db.DateTime, default=datetime.utcnow)
    asistencia = db.relationship('Asistencia', backref='reserva', uselist=False)

class Asistencia(db.Model):
    __tablename__ = 'asistencias'
    id = db.Column(db.Integer, primary_key=True)
    id_reserva = db.Column(db.Integer, db.ForeignKey('reservas.id'), unique=True, nullable=False)
    estado = db.Column(db.String(20), nullable=False)

class Plan(db.Model):
    __tablename__ = 'planes'
    id = db.Column(db.Integer, primary_key=True)
    nombre_plan = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    cantidad_clases = db.Column(db.Integer)
    pagos = db.relationship('Pago', backref='plan', lazy=True)

class Pago(db.Model):
    __tablename__ = 'pagos'
    id = db.Column(db.Integer, primary_key=True)
    id_alumno = db.Column(db.Integer, db.ForeignKey('alumnos.id'), nullable=False)
    id_plan = db.Column(db.Integer, db.ForeignKey('planes.id'), nullable=False)
    fecha_pago = db.Column(db.Date, nullable=False)
    monto = db.Column(db.Float, nullable=False)

class ListaEspera(db.Model):
    __tablename__ = 'lista_espera'
    id = db.Column(db.Integer, primary_key=True)
    id_alumno = db.Column(db.Integer, db.ForeignKey('alumnos.id'), nullable=False)
    id_horario = db.Column(db.Integer, db.ForeignKey('horarios.id'), nullable=False)

class Notificacion(db.Model):
    __tablename__ = 'notificaciones'
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    mensaje = db.Column(db.String(255), nullable=False)

class RecuperacionPassword(db.Model):
    __tablename__ = 'recuperacion_password'
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)

# ==========================================
# RUTA PRINCIPAL UNIFICADA
# ==========================================


# ==========================================
# PÁGINA PRINCIPAL
# ==========================================

@app.route('/')
def inicio():
    return render_template('inicio.html')

# RUTAS DE SEGURIDAD (TUS RUTAS)
# ==========================================

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':

        correo = request.form.get('correo', '').strip().lower()
        contrasena = request.form.get('contrasena', '')
        rol = request.form.get('rol', 'alumno')

        # Solo se permiten alumnos e instructores.
        if rol not in ('alumno', 'instructor'):
            return "Tipo de usuario no permitido."

        if not correo or not contrasena:
            return "Debes completar el correo y la contraseña."

        if len(contrasena) < 8:
            return "La contraseña debe tener al menos 8 caracteres."

        hash_seguro = generate_password_hash(contrasena)

        try:
            with obtener_conexion_estadisticas() as conexion:
                with conexion.cursor() as cursor:

                    # Los alumnos quedan aprobados.
                    # Los instructores necesitan autorización.
                    estado = (
                        'pendiente'
                        if rol == 'instructor'
                        else 'aprobado'
                    )

                    cursor.execute(
                        """
                        INSERT INTO usuarios
                            (correo, contrasena_hash, rol, estado_aprobacion)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                        """,
                        (correo, hash_seguro, rol, estado)
                    )

                    usuario = cursor.fetchone()
                    usuario_id = usuario["id"]

                    if rol == 'alumno':

                        nombre = correo.split('@')[0]

                        cursor.execute(
                            """
                            INSERT INTO alumnos
                                (id_usuario, nombre_completo)
                            VALUES (%s, %s)
                            """,
                            (usuario_id, nombre)
                        )

                    elif rol == 'instructor':

                        nombre_completo = request.form.get(
                            'nombre_completo', ''
                        ).strip()

                        especialidad = request.form.get(
                            'especialidad', ''
                        ).strip()

                        if not nombre_completo:
                            raise ValueError(
                                "Debes ingresar el nombre completo."
                            )

                        cursor.execute(
                            """
                            INSERT INTO instructores
                                (id_usuario, nombre_completo, especialidad)
                            VALUES (%s, %s, %s)
                            """,
                            (
                                usuario_id,
                                nombre_completo,
                                especialidad or None
                            )
                        )

            if rol == 'instructor':
                flash(
                    'Tu solicitud fue enviada. '
                    'El administrador debe aprobarla antes de que puedas iniciar sesión.'
                )
            else:
                flash('¡Registro exitoso! Ya puedes iniciar sesión.')

            return redirect(url_for('login'))

        except ValueError as error:
            return str(error)

        except Exception:
            app.logger.exception(
                "Error al registrar usuario en PostgreSQL"
            )
            return (
                "No se pudo completar el registro. "
                "Comprueba que el correo no esté registrado."
            )

    return render_template('registro.html')




@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        correo = request.form.get('correo', '').strip().lower()
        contrasena = request.form.get('contrasena', '')

        if not correo or not contrasena:
            flash('Debes ingresar tu correo y contraseña.')
            return redirect(url_for('login'))

        try:
            with obtener_conexion_estadisticas() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT
                            id,
                            correo,
                            contrasena_hash,
                            rol,
                            estado_aprobacion
                        FROM usuarios
                        WHERE correo = %s
                        LIMIT 1
                        """,
                        (correo,)
                    )

                    usuario = cursor.fetchone()

        except Exception:
            app.logger.exception(
                "Error al consultar usuario en PostgreSQL"
            )
            flash('No se pudo verificar tu cuenta. Inténtalo nuevamente.')
            return redirect(url_for('login'))

        if not usuario or not check_password_hash(
            usuario["contrasena_hash"],
            contrasena
        ):
            flash('Correo o contraseña incorrectos.')
            return redirect(url_for('login'))

        if usuario["estado_aprobacion"] != 'aprobado':

            if usuario["rol"] == 'instructor':
                flash(
                    'Tu solicitud de instructor está pendiente de aprobación. '
                    'Podrás ingresar cuando el administrador la autorice.'
                )
            else:
                flash('Tu cuenta todavía no está habilitada.')

            return redirect(url_for('login'))

        # Limpiar mensajes anteriores.
        session.pop('_flashes', None)

        # Iniciar sesión.
        session['usuario_id'] = usuario["id"]
        session['rol'] = usuario["rol"]

        flash('¡Bienvenido/a! Has iniciado sesión correctamente.')

        if usuario["rol"] == "instructor":
            return redirect(url_for("panel_instructor"))

        return redirect(url_for("inicio"))

    return render_template('login.html')




@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente.')
    return redirect(url_for('login'))

@app.route('/recuperar', methods=['GET', 'POST'])
def recuperar():
    mensaje = None
    if request.method == 'POST':
        correo = request.form['correo']

        try:
            with obtener_conexion_estadisticas() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id, correo
                        FROM usuarios
                        WHERE correo = %s
                        LIMIT 1
                        """,
                        (correo,),
                    )
                    usuario = cursor.fetchone()

                    if usuario:
                        token_unico = str(uuid.uuid4())
                        cursor.execute(
                            """
                            INSERT INTO recuperacion_password (id_usuario, token)
                            VALUES (%s, %s)
                            """,
                            (usuario["id"], token_unico),
                        )
                        enlace = url_for('restablecer', token=token_unico, _external=True)
                        print("\n" + "="*50)
                        print(f"📧 SIMULACIÓN DE EMAIL ENVIADO A: {correo}")
                        print(f"Para cambiar tu contraseña, haz clic aquí: {enlace}")
                        print("="*50 + "\n")
        except Exception:
            app.logger.exception("Error al consultar/crear recuperación en PostgreSQL")

        mensaje = "Si el correo está registrado en nuestro sistema, recibirás un enlace de recuperación."

    return render_template('recuperar.html', mensaje=mensaje)

@app.route('/restablecer/<token>', methods=['GET', 'POST'])
def restablecer(token):
    try:
        with obtener_conexion_estadisticas() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, id_usuario, token
                    FROM recuperacion_password
                    WHERE token = %s
                    LIMIT 1
                    """,
                    (token,),
                )
                registro_token = cursor.fetchone()
    except Exception:
        app.logger.exception("Error al consultar el token de recuperación en PostgreSQL")
        return "El enlace es inválido o ya ha expirado."

    if not registro_token:
        return "El enlace es inválido o ya ha expirado."

    if request.method == 'POST':
        nueva_contrasena = request.form['contrasena']
        repetir_contrasena = request.form['repetir_contrasena']

        if nueva_contrasena != repetir_contrasena:
            return render_template('restablecer.html', error="Las contraseñas no coinciden. Inténtalo de nuevo.")

        try:
            with obtener_conexion_estadisticas() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE usuarios
                        SET contrasena_hash = %s
                        WHERE id = %s
                        """,
                        (generate_password_hash(nueva_contrasena), registro_token["id_usuario"]),
                    )
                    cursor.execute(
                        """
                        DELETE FROM recuperacion_password
                        WHERE id = %s
                        """,
                        (registro_token["id"],),
                    )
        except Exception:
            app.logger.exception("Error al restablecer contraseña en PostgreSQL")
            return "No se pudo actualizar la contraseña. Inténtalo más tarde."

        return "¡Contraseña actualizada con éxito! <a href='/login'>Ir al Login</a>"

    return render_template('restablecer.html')

# ==========================================
# RUTAS DE TU COMPAÑERA (PostgreSQL/ ALUMNOS) 
# ==========================================


@app.route("/alumnos/agregar", methods=["POST"])
def agregar_alumno():

    # Solo el administrador puede agregar alumnos.
    if session.get('rol') != 'admin':
        flash('No tienes permiso para realizar esta acción.')
        return redirect(url_for('login'))

    nombre = request.form.get("nombre", "").strip()
    apellido = request.form.get("apellido", "").strip()
    correo = request.form.get("correo", "").strip() or None
    telefono = request.form.get("telefono", "").strip()

    if not nombre or not apellido:
        return "El nombre y apellido son obligatorios", 400

    try:
        nuevo_alumno = Alumno(
            nombre=nombre,
            apellido=apellido,
            correo=correo,
            telefono=telefono
        )

        db.session.add(nuevo_alumno)
        db.session.commit()

    except Exception:
        db.session.rollback()
        return "No se pudo registrar el alumno. Verifica los datos.", 400

    return redirect(url_for("alumnos"))

@app.route("/alumnos/editar/<int:id_alumno>", methods=["POST"])
def editar_alumno(id_alumno):

    # Solo el administrador puede editar alumnos.
    if session.get('rol') != 'admin':
        flash('No tienes permiso para realizar esta acción.')
        return redirect(url_for('login'))

    alumno = db.session.get(Alumno, id_alumno)

    if alumno is None:
        return "Alumno no encontrado", 404

    nombre = request.form.get("nombre", "").strip()
    apellido = request.form.get("apellido", "").strip()
    correo = request.form.get("correo", "").strip() or None
    telefono = request.form.get("telefono", "").strip()

    if not nombre or not apellido:
        return "El nombre y apellido son obligatorios", 400

    try:
        alumno.nombre = nombre
        alumno.apellido = apellido
        alumno.correo = correo
        alumno.telefono = telefono

        db.session.commit()

    except Exception:
        db.session.rollback()
        return "No se pudo actualizar el alumno. Verifica los datos.", 400

    return redirect(url_for("alumnos"))
@app.route("/alumnos/desactivar/<int:id_alumno>", methods=["POST"])
def desactivar_alumno(id_alumno):

    # Solo el administrador puede desactivar alumnos.
    if session.get('rol') != 'admin':
        flash('No tienes permiso para realizar esta acción.')
        return redirect(url_for('login'))

    alumno = db.session.get(Alumno, id_alumno)

    if alumno is None:
        return "Alumno no encontrado", 404

    try:
        alumno.activo = False
        db.session.commit()

    except Exception:
        db.session.rollback()
        return "No se pudo desactivar el alumno.", 400

    return redirect(url_for("alumnos"))


@app.route("/instructores")
def instructores():

    # Solo el administrador puede acceder.
    if session.get('rol') != 'admin':
        flash('No tienes permiso para acceder a esta sección.')
        return redirect(url_for('login'))

    lista = Instructor.query.order_by(
        Instructor.id.desc()
    ).all()

    return render_template(
        "instructores.html",
        instructores=lista
    )


registrar_rutas_reservas(
    app, db, Usuario, Horario, Reserva, ListaEspera
)

registrar_rutas_planes(
    app, db, Usuario, Plan, Pago
)
# ==========================================
# VER ALUMNOS DE CADA INSTRUCTOR
# ==========================================

# ==========================================
# VER ALUMNOS Y HORARIOS DE CADA INSTRUCTOR
# ==========================================

@app.route("/instructores/<int:id_instructor>/alumnos")
def alumnos_instructor(id_instructor):

    # Solo administradores
    if session.get("rol") != "admin":
        flash("No tienes permiso para acceder.")
        return redirect(url_for("login"))

    # Buscar instructor
    instructor = db.session.get(Instructor, id_instructor)

    if not instructor:
        return "Instructor no encontrado", 404

    # Obtener reservas de las clases del instructor
    reservas = (
        db.session.query(
            Alumno,
            Clase,
            Horario,
            Reserva
        )
        .join(
            Reserva,
            Reserva.id_alumno == Alumno.id
        )
        .join(
            Horario,
            Reserva.id_horario == Horario.id
        )
        .join(
            Clase,
            Horario.id_clase == Clase.id
        )
        .filter(
            Horario.id_instructor == id_instructor
        )
        .filter(
            db.func.lower(
                db.func.coalesce(Reserva.estado, "")
            ).notin_(["cancelada", "cancelado"])
        )
        .order_by(
            Horario.fecha.asc(),
            Horario.hora.asc(),
            Alumno.nombre_completo.asc()
        )
        .all()
    )

    return render_template(
        "instructores/alumnos.html",
        instructor=instructor,
        reservas=reservas
    )
def alumnos_instructor(id_instructor):

    # Solo administradores
    if session.get("rol") != "admin":
        flash("No tienes permiso para acceder.")
        return redirect(url_for("login"))

    # Buscar al instructor
    instructor = db.session.get(Instructor, id_instructor)

    if not instructor:
        return "Instructor no encontrado", 404

    # Buscar los alumnos con reservas en sus clases
    alumnos = (
        db.session.query(Alumno)
        .join(Reserva, Reserva.id_alumno == Alumno.id)
        .join(Horario, Reserva.id_horario == Horario.id)
        .filter(Horario.id_instructor == id_instructor)
        .distinct()
        .order_by(Alumno.nombre_completo)
        .all()
    )

    return render_template(
        "instructores/alumnos.html",
        instructor=instructor,
        alumnos=alumnos
    )

@app.route('/instructor/panel')
def panel_instructor():

    # Solo pueden entrar instructores.
    if session.get('rol') != 'instructor':
        flash('No tienes permiso para acceder a esta sección.')
        return redirect(url_for('login'))

    try:
        # Buscar la cuenta del instructor que inició sesión.
        usuario = db.session.get(
            Usuario,
            session.get('usuario_id')
        )

        if usuario is None or usuario.estado_aprobacion != 'aprobado':
            session.clear()
            flash('Tu cuenta no está autorizada para ingresar.')
            return redirect(url_for('login'))

        # Buscar su perfil de instructor.
        instructor = Instructor.query.filter_by(
            id_usuario=usuario.id
        ).first()

        if instructor is None:
            flash('No se encontró tu perfil de instructor.')
            return redirect(url_for('inicio'))

        # Obtener solamente sus horarios.
        horarios = Horario.query.filter_by(
            id_instructor=instructor.id
        ).order_by(
            Horario.fecha,
            Horario.hora
        ).all()

        clases = Clase.query.order_by(Clase.nombre_clase).all()

        return render_template(
          'panel_instructor.html',
          instructor=instructor,
          horarios=horarios,
          clases=clases
)

    except Exception:
        db.session.rollback()
        app.logger.exception('Error al cargar el panel del instructor')
        flash('No se pudo cargar tu panel.')
        return redirect(url_for('inicio'))
    
    
@app.route('/instructor/horarios/crear', methods=['POST'])
def crear_horario_instructor():
    from datetime import datetime, timedelta

    if session.get('rol') != 'instructor':
        flash('No tienes permiso para realizar esta acción.')
        return redirect(url_for('login'))

    try:
        usuario = db.session.get(Usuario, session.get('usuario_id'))

        if usuario is None or usuario.estado_aprobacion != 'aprobado':
            session.clear()
            flash('Tu cuenta no está autorizada para realizar esta acción.')
            return redirect(url_for('login'))

        instructor = Instructor.query.filter_by(
            id_usuario=usuario.id
        ).first()

        if instructor is None:
            flash('No se encontró tu perfil de instructor.')
            return redirect(url_for('inicio'))

        id_clase = request.form.get('id_clase', type=int)
        fecha_texto = request.form.get('fecha', '').strip()
        hora_texto = request.form.get('hora', '').strip()
        cupo_maximo = request.form.get('cupo_maximo', type=int)

        if not id_clase or not fecha_texto or not hora_texto or not cupo_maximo:
            flash('Debes completar todos los campos.')
            return redirect(url_for('panel_instructor'))

        if cupo_maximo < 1:
            flash('El cupo debe ser mayor que cero.')
            return redirect(url_for('panel_instructor'))

        clase = db.session.get(Clase, id_clase)

        if clase is None:
            flash('La clase seleccionada no existe.')
            return redirect(url_for('panel_instructor'))

        if not clase.duracion_minutos or clase.duracion_minutos <= 0:
            flash('La duración de la clase no es válida.')
            return redirect(url_for('panel_instructor'))

        fecha = datetime.strptime(fecha_texto, '%Y-%m-%d').date()
        hora = datetime.strptime(hora_texto, '%H:%M').time()

        inicio_nuevo = datetime.combine(fecha, hora)
        fin_nuevo = inicio_nuevo + timedelta(
            minutes=clase.duracion_minutos
        )

        if inicio_nuevo <= datetime.now():
            flash('Debes seleccionar una fecha y hora futuras.')
            return redirect(url_for('panel_instructor'))

        horarios_existentes = Horario.query.filter_by(
            id_instructor=instructor.id,
            fecha=fecha
        ).all()

        for horario in horarios_existentes:
            inicio_existente = datetime.combine(
                horario.fecha,
                horario.hora
            )

            fin_existente = inicio_existente + timedelta(
                minutes=horario.clase.duracion_minutos
            )

            if inicio_nuevo < fin_existente and inicio_existente < fin_nuevo:
                flash('Ya tienes otra clase programada en ese horario.')
                return redirect(url_for('panel_instructor'))

        nuevo_horario = Horario(
            id_clase=clase.id,
            id_instructor=instructor.id,
            fecha=fecha,
            hora=hora,
            cupo_maximo=cupo_maximo
        )

        db.session.add(nuevo_horario)
        db.session.commit()

        flash('¡Tu horario se publicó correctamente!')
        return redirect(url_for('panel_instructor'))

    except ValueError:
        db.session.rollback()
        flash('La fecha o la hora ingresada no tiene un formato válido.')
        return redirect(url_for('panel_instructor'))

    except Exception:
        db.session.rollback()
        app.logger.exception('Error al crear horario del instructor')
        flash('No se pudo publicar el horario. Inténtalo nuevamente.')
        return redirect(url_for('panel_instructor'))


@app.route('/admin/solicitudes-instructores')
def solicitudes_instructores_admin():

    # Solo puede entrar el administrador.
    if session.get('rol') != 'admin':
        flash('No tienes permiso para acceder a esta sección.')
        return redirect(url_for('login'))

    try:
        with obtener_conexion_estadisticas() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        u.id AS usuario_id,
                        u.correo,
                        u.estado_aprobacion,
                        i.nombre_completo,
                        i.especialidad
                    FROM usuarios u
                    INNER JOIN instructores i
                        ON i.id_usuario = u.id
                    WHERE u.rol = 'instructor'
                      AND u.estado_aprobacion = 'pendiente'
                    ORDER BY u.id DESC
                    """
                )

                solicitudes = cursor.fetchall()

    except Exception:
        app.logger.exception(
            "Error al consultar solicitudes de instructores"
        )
        flash('No se pudieron cargar las solicitudes.')
        return redirect(url_for('inicio'))

    return render_template(
        'solicitudes_instructores.html',
        solicitudes=solicitudes
    )


@app.route('/admin/usuarios/nuevo', methods=['GET', 'POST'])
def crear_usuario_administrativo():
    if session.get('rol') != 'admin':
        flash('No tienes permiso para realizar esta acción.')
        return redirect(url_for('login'))

    correo = ''
    rol = 'instructor'
    nombre_completo = ''
    especialidad = ''
    error = None

    if request.method == 'POST':
        correo = request.form.get('correo', '').strip().lower()
        contrasena = request.form.get('contrasena', '')
        rol = request.form.get('rol', '')
        nombre_completo = request.form.get('nombre_completo', '').strip()
        especialidad = request.form.get('especialidad', '').strip()

        if not correo or not contrasena:
            error = 'Debes ingresar el correo y la contraseña.'
        elif len(correo) > 100:
            error = 'El correo no puede superar los 100 caracteres.'
        elif len(contrasena) < 8:
            error = 'La contraseña debe tener al menos 8 caracteres.'
        elif rol not in ('instructor', 'admin'):
            error = 'Selecciona un tipo de cuenta válido.'
        elif rol == 'instructor' and not nombre_completo:
            error = 'Debes ingresar el nombre completo del instructor.'
        elif len(nombre_completo) > 150:
            error = 'El nombre no puede superar los 150 caracteres.'
        elif len(especialidad) > 100:
            error = 'La especialidad no puede superar los 100 caracteres.'

        if error:
            return render_template(
                'crear_usuario_admin.html',
                correo=correo,
                rol=rol,
                nombre_completo=nombre_completo,
                especialidad=especialidad,
                error=error
            )

        try:
            with obtener_conexion_estadisticas() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO usuarios
                            (correo, contrasena_hash, rol, estado_aprobacion)
                        VALUES (%s, %s, %s, 'aprobado')
                        RETURNING id
                        """,
                        (correo, generate_password_hash(contrasena), rol)
                    )
                    usuario_id = cursor.fetchone()['id']

                    if rol == 'instructor':
                        cursor.execute(
                            """
                            INSERT INTO instructores
                                (id_usuario, nombre_completo, especialidad)
                            VALUES (%s, %s, %s)
                            """,
                            (
                                usuario_id,
                                nombre_completo,
                                especialidad or None
                            )
                        )

            flash(
                'La cuenta de instructor fue creada y aprobada.'
                if rol == 'instructor'
                else 'La cuenta de administrador fue creada.'
            )
            return redirect(url_for('crear_usuario_administrativo'))

        except psycopg.errors.UniqueViolation:
            error = 'Ya existe una cuenta registrada con ese correo.'
        except Exception:
            app.logger.exception('Error al crear cuenta administrativa')
            error = 'No se pudo crear la cuenta. Inténtalo nuevamente.'

    return render_template(
        'crear_usuario_admin.html',
        correo=correo,
        rol=rol,
        nombre_completo=nombre_completo,
        especialidad=especialidad,
        error=error
    )


@app.route(
    '/admin/instructores/<int:usuario_id>/aprobar',
    methods=['POST']
)

@app.route('/admin/instructores/<int:usuario_id>/aprobar', methods=['POST'])
def aprobar_instructor(usuario_id):

    if session.get('rol') != 'admin':
        flash('No tienes permiso para realizar esta acción.')
        return redirect(url_for('login'))

    try:
        with obtener_conexion_estadisticas() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE usuarios
                    SET estado_aprobacion = 'aprobado'
                    WHERE id = %s
                      AND rol = 'instructor'
                      AND estado_aprobacion = 'pendiente'
                    """,
                    (usuario_id,)
                )

                actualizado = cursor.rowcount

                if actualizado:
                    cursor.execute(
                        """
                        INSERT INTO notificaciones (id_usuario, mensaje)
                        VALUES (%s, %s)
                        """,
                        (
                            usuario_id,
                            '¡Felicitaciones! Tu solicitud para formar parte de Pilates Studio ha sido aprobada. Ya puedes iniciar sesión y acceder a tu panel de instructor.'
                        )
                    )

        if actualizado:
            flash('¡Instructor aprobado y notificación creada correctamente!')
        else:
            flash('No se encontró una solicitud pendiente para aprobar.')

    except Exception:
        app.logger.exception("Error al aprobar instructor")
        flash('No se pudo aprobar la solicitud.')

    return redirect(url_for('solicitudes_instructores_admin'))


@app.route(
    '/admin/instructores/<int:usuario_id>/rechazar',
    methods=['POST']
)
def rechazar_instructor(usuario_id):

    if session.get('rol') != 'admin':
        flash('No tienes permiso para realizar esta acción.')
        return redirect(url_for('login'))

    try:
        with obtener_conexion_estadisticas() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE usuarios
                    SET estado_aprobacion = 'rechazado'
                    WHERE id = %s
                      AND rol = 'instructor'
                      AND estado_aprobacion = 'pendiente'
                    """,
                    (usuario_id,)
                )

                actualizado = cursor.rowcount

        if actualizado:
            flash('La solicitud fue rechazada.')
        else:
            flash('No se encontró una solicitud pendiente para rechazar.')

    except Exception:
        app.logger.exception("Error al rechazar instructor")
        flash('No se pudo rechazar la solicitud.')

    return redirect(url_for('solicitudes_instructores_admin'))


# =====================================================
# MÓDULO DE ESTADÍSTICAS Y PREDICCIONES CON IA
# =====================================================
@app.route('/estadisticas', methods=['GET', 'POST'])
def estadisticas():
    """Consulta datos agregados de Supabase y genera análisis a solicitud."""
    

    # Solo administradores pueden solicitar análisis a Gemini.
    if request.method == "POST" and (
        'usuario_id' not in session or session.get('rol') != 'admin'
    ):
        return "Acceso reservado a administradores.", 403

    analisis_ia = None
    datos = {
        "total_alumnos": 0,
        "total_reservas": 0,
        "total_asistencias": 0,
        "total_horarios": 0,
        "semanas": [],
        "reservas_por_semana": [],
        "predicciones": [],
        "demanda_horarios": [],
        "baja_asistencia": [],
        "alumnos_inactivos": {"total": 0},
    }

    try:
        with obtener_conexion_estadisticas() as conexion:
            with conexion.cursor() as cursor:
                
                # ALUMNOS SIN ASISTENCIA EN LOS ÚLTIMOS 30 DÍAS
                cursor.execute("""
                    SELECT COUNT(*) AS total
                    FROM alumnos al
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM reservas r
                        INNER JOIN asistencias a
                            ON a.id_reserva = r.id
                        INNER JOIN horarios h
                            ON h.id = r.id_horario
                        WHERE r.id_alumno = al.id
                          AND LOWER(a.estado) = 'presente'
                          AND h.fecha >= CURRENT_DATE - INTERVAL '30 days'
                          AND h.fecha <= CURRENT_DATE
                    )
                """)

                resultado_inactivos = cursor.fetchone()

                datos["alumnos_inactivos"] = {
                    "total": int(resultado_inactivos["total"])
                }

                conteos = {
                    "total_alumnos": "SELECT COUNT(*) AS total FROM alumnos",
                    "total_reservas": "SELECT COUNT(*) AS total FROM reservas",
                    "total_asistencias": "SELECT COUNT(*) AS total FROM asistencias",
                    "total_horarios": "SELECT COUNT(*) AS total FROM horarios",
                }
                for nombre, consulta in conteos.items():
                    cursor.execute(consulta)
                    datos[nombre] = int(cursor.fetchone()["total"])

                # Seis semanas completas y la semana actual (incluye semanas sin reservas).
                cursor.execute("""
                    SELECT semanas.semana::date AS semana,
                           COUNT(r.id) AS total
                    FROM generate_series(
                        DATE_TRUNC('week', CURRENT_DATE) - INTERVAL '6 weeks',
                        DATE_TRUNC('week', CURRENT_DATE),
                        INTERVAL '1 week'
                    ) AS semanas(semana)
                    LEFT JOIN reservas r
                        ON r.fecha_reserva >= semanas.semana
                       AND r.fecha_reserva < semanas.semana + INTERVAL '1 week'
                       AND r.fecha_reserva <= CURRENT_TIMESTAMP
                    GROUP BY semanas.semana
                    ORDER BY semanas.semana
                """)
                resultados = cursor.fetchall()
                datos["semanas"] = [
                    fila["semana"].strftime("%d/%m") for fila in resultados
                ]
                datos["reservas_por_semana"] = [
                    int(fila["total"]) for fila in resultados
                ]

                # Ocupación de cada sesión; no revela datos personales de alumnos.
                cursor.execute("""
                    SELECT h.id AS id_horario,
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
                    GROUP BY h.id, c.nombre_clase, h.fecha,
                             h.hora, h.cupo_maximo
                    ORDER BY reservas_confirmadas DESC, h.fecha, h.hora
                    LIMIT 10
                """)
                filas_demanda = cursor.fetchall()
                datos["demanda_horarios"] = [
                    {
                        "clase": fila["nombre_clase"],
                        "fecha": fila["fecha"].strftime("%d/%m/%Y"),
                        "hora": fila["hora"].strftime("%H:%M"),
                        "cupos": int(fila["cupo_maximo"]),
                        "reservas": int(fila["reservas_confirmadas"]),
                        "ocupacion": round(
                            int(fila["reservas_confirmadas"]) /
                            int(fila["cupo_maximo"]) * 100, 1
                        ) if fila["cupo_maximo"] and fila["cupo_maximo"] > 0 else 0,
                    }
                    for fila in filas_demanda
                ]

                # CLASES CON BAJA ASISTENCIA
                cursor.execute("""
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

                    JOIN clases c
                        ON c.id = h.id_clase

                    LEFT JOIN reservas r
                        ON r.id_horario = h.id

                    LEFT JOIN asistencias a
                        ON a.id_reserva = r.id

                    WHERE
                        h.fecha + h.hora +
                        (c.duracion_minutos * INTERVAL '1 minute')
                        < CURRENT_TIMESTAMP

                    GROUP BY
                        h.id,
                        c.nombre_clase,
                        h.fecha,
                        h.hora,
                        h.cupo_maximo

                    ORDER BY
                        alumnos_presentes ASC,
                        h.fecha DESC

                    LIMIT 10
                """)

                filas_asistencia = cursor.fetchall()

                datos["baja_asistencia"] = [
                    {
                        "clase": fila["nombre_clase"],
                        "fecha": fila["fecha"].strftime("%d/%m/%Y"),
                        "hora": fila["hora"].strftime("%H:%M"),
                        "cupos": int(fila["cupo_maximo"]),
                        "reservas": int(fila["reservas_confirmadas"]),
                        "presentes": int(fila["alumnos_presentes"]),
                        "porcentaje": round(
                            int(fila["alumnos_presentes"])
                            / int(fila["cupo_maximo"]) * 100, 1
                        ) if fila["cupo_maximo"] > 0 else 0
                    }
                    for fila in filas_asistencia
                
                ]
        historico_completo = datos["reservas_por_semana"][:-1]
        semanas_con_reservas = sum(v > 0 for v in historico_completo)
        if semanas_con_reservas >= 3 and sum(historico_completo) >= 3:
            # Se descarta la proyección para la semana actual.
            proyeccion = predecir_reservas(historico_completo, semanas_futuras=3)
            datos["predicciones"] = proyeccion[1:3]

        print("=== ESTADÍSTICAS PILATES STUDIO ===")
        print("Semanas (última es la actual):", datos["semanas"])
        print("Reservas reales por semana:", datos["reservas_por_semana"])
        print("Predicciones próximas 2 semanas:", datos["predicciones"])

    except Exception:
        app.logger.exception("Error al consultar estadísticas en Supabase")
        return "No se pudieron cargar las estadísticas.", 503

    if request.method == "POST":
        from gemini_analisis import analizar_estadisticas
        resumen = {
            "total_alumnos": datos["total_alumnos"],
            "total_reservas": datos["total_reservas"],
            "total_asistencias": datos["total_asistencias"],
            "total_horarios": datos["total_horarios"],
            "semanas": datos["semanas"],
            "reservas_por_semana": datos["reservas_por_semana"],
            "predicciones": datos["predicciones"],
            "demanda_horarios": datos["demanda_horarios"],
            "baja_asistencia": datos["baja_asistencia"],
            "alumnos_inactivos": datos["alumnos_inactivos"]
        }
        try:
            analisis_ia = analizar_estadisticas(resumen)
        except Exception:
            app.logger.exception("Error al consultar Gemini API")
            analisis_ia = (
                "No fue posible generar el análisis en este momento. "
                "Comprueba la conexión y los límites de Gemini."
            )

    return render_template("estadisticas.html", analisis_ia=analisis_ia, **datos)


# ==========================================
# INICIAR SERVIDOR (SIEMPRE AL FINAL)
# ==========================================
if __name__ == '__main__':
    app.run(debug=True)
    
    
    
