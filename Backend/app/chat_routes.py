from flask import request, jsonify
from flask_socketio import SocketIO, emit
from . import db
from .models import Usuario, Mensaje
from datetime import datetime

socketio = SocketIO(cors_allowed_origins="*")

ASESOR_EMAIL = 'asesor@techshop.com'
usuarios_conectados = {}

@socketio.on('connect')
def handle_connect():
    print('Cliente conectado:', request.sid)

@socketio.on('login')
def handle_login(data):
    print('Login data:', data)
    usuario_id = data['usuario_id']
    email = data['email']
    
    usuarios_conectados[usuario_id] = {
        'id': usuario_id,
        'email': email,
        'sid': request.sid
    }
    
    if email == ASESOR_EMAIL:
        # Cargar mensajes no leídos para el asesor
        mensajes_pendientes = Mensaje.query.filter_by(
            receptor_id=usuario_id,
            leido=False
        ).order_by(Mensaje.fecha).all()
        
        for mensaje in mensajes_pendientes:
            emit('mensaje_nuevo', {
                'emisor_id': mensaje.emisor_id,
                'contenido': mensaje.contenido,
                'fecha': mensaje.fecha.isoformat()
            })
            mensaje.leido = True
        db.session.commit()

@socketio.on('enviar_mensaje')
def handle_mensaje(data):
    print('Mensaje recibido:', data)
    emisor_id = data['emisor_id']
    contenido = data['contenido']
    
    # Obtener al asesor
    asesor = Usuario.query.filter_by(email=ASESOR_EMAIL).first()
    
    # Determinar el receptor
    receptor_id = asesor.id if int(emisor_id) != asesor.id else data.get('receptor_id')
    
    mensaje = Mensaje(
        emisor_id=emisor_id,
        receptor_id=receptor_id,
        contenido=contenido,
        leido=False
    )
    db.session.add(mensaje)
    db.session.commit()

    mensaje_data = {
        'id': mensaje.id,
        'emisor_id': emisor_id,
        'contenido': contenido,
        'fecha': mensaje.fecha.isoformat()
    }
    
    # Emitir el mensaje al receptor si está conectado
    if str(receptor_id) in usuarios_conectados:
        receptor_sid = usuarios_conectados[str(receptor_id)]['sid']
        emit('mensaje_nuevo', mensaje_data, room=receptor_sid)
        mensaje.leido = True
        db.session.commit()

@socketio.on('disconnect')
def handle_disconnect():
    print('Cliente desconectado:', request.sid)
    for usuario_id, datos in list(usuarios_conectados.items()):
        if datos['sid'] == request.sid:
            del usuarios_conectados[usuario_id]
            break