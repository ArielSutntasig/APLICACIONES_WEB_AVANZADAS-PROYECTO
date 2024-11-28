from flask import request
from flask_socketio import emit
from . import db
from .models import Usuario, Mensaje
from datetime import datetime

ASESOR_EMAIL = 'asesor.comercial@gmail.com'
usuarios_conectados = {}

def register_socket_events(socketio):
    @socketio.on('connect')
    def handle_connect():
        print(f"Usuario conectado: {request.sid}")
        emit('connected', {'status': 'success'})

    @socketio.on('login')
    def handle_login(data):
        try:
            print(f"Intento de login con datos: {data}")  # Debug
            usuario_id = data.get('usuario_id')
            email = data.get('email')

            if not usuario_id or not email:
                emit('error', {'error': 'Datos incompletos para el login.'})
                return

            # Verificar que el usuario existe en la base de datos
            usuario = Usuario.query.get(usuario_id)
            if not usuario:
                emit('error', {'error': 'Usuario no encontrado.'})
                return

            usuarios_conectados[str(usuario_id)] = {
                'id': usuario_id,
                'email': email,
                'sid': request.sid
            }

            print(f"Usuario {email} conectado con sid: {request.sid}")  # Debug

            # Verificar si el usuario es el asesor
            if email == ASESOR_EMAIL:
                print("Cargando mensajes pendientes para el asesor.")
                mensajes_pendientes = Mensaje.query.filter_by(
                    receptor_id=usuario_id,
                    leido=False
                ).order_by(Mensaje.fecha.asc()).all()

                print(f"Mensajes pendientes encontrados: {len(mensajes_pendientes)}")  # Debug

                for mensaje in mensajes_pendientes:
                    emisor = Usuario.query.get(mensaje.emisor_id)
                    mensaje_data = {
                        'id': mensaje.id,
                        'emisor_id': mensaje.emisor_id,
                        'emisor_nombre': emisor.nombre_completo if emisor else 'Desconocido',
                        'contenido': mensaje.contenido,
                        'fecha': mensaje.fecha.isoformat()
                    }
                    print(f"Enviando mensaje pendiente: {mensaje_data}")  # Debug
                    emit('mensaje_nuevo', mensaje_data)
                    mensaje.leido = True

                db.session.commit()

            # Emitir confirmación de login exitoso
            emit('login_success', {
                'usuario_id': usuario_id,
                'email': email
            })

        except Exception as e:
            print(f"Error en login: {e}")
            emit('error', {'error': f'Error en el servidor: {str(e)}'})


    @socketio.on('enviar_mensaje')
    def handle_enviar_mensaje(data):
        try:
            emisor_id = data['emisor_id']
            receptor_id = data.get('receptor_id')
            contenido = data['contenido']

            # Create message in database
            mensaje = Mensaje(
                emisor_id=emisor_id,
                receptor_id=receptor_id,
                contenido=contenido,
                leido=False,
                fecha=datetime.utcnow()
            )
            db.session.add(mensaje)
            db.session.commit()

            mensaje_data = {
                "id": mensaje.id,
                "emisor_id": emisor_id,
                "receptor_id": receptor_id,
                "contenido": contenido,
                "fecha": mensaje.fecha.isoformat(),
                "leido": False
            }

            # Emit to receiver if connected
            if str(receptor_id) in usuarios_conectados:
                emit('mensaje_nuevo', mensaje_data, room=usuarios_conectados[str(receptor_id)]['sid'])
            
            # Update notification badge for asesor
            if receptor_id == Usuario.query.filter_by(email=ASESOR_EMAIL).first().id:
                emit('actualizar_notificacion', {
                    'cliente_id': emisor_id,
                    'increment': True
                }, broadcast=True)

        except Exception as e:
            print(f"Error al enviar mensaje: {e}")
            emit('error', {'error': str(e)})

            
    @socketio.on('disconnect')
    def handle_disconnect():
        try:
            for usuario_id, datos in list(usuarios_conectados.items()):
                if datos['sid'] == request.sid:
                    print(f"Usuario {datos['email']} desconectado")  # Debug
                    del usuarios_conectados[usuario_id]
                    break
        except Exception as e:
            print(f"Error en disconnect: {e}")

    @socketio.on_error()
    def error_handler(e):
        print(f"Error en WebSocket: {e}")
        emit('error', {'error': 'Error interno del servidor'})

    return socketio

