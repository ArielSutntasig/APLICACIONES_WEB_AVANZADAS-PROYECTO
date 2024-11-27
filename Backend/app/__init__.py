from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO
from .config import Config

db = SQLAlchemy()
socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializa CORS con configuración específica
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # Inicializa SQLAlchemy
    db.init_app(app)

    # Inicializa SocketIO con configuración adicional
    socketio.init_app(app, 
                     cors_allowed_origins="*",
                     logger=True,
                     engineio_logger=True)

    # Importa y registra las rutas
    from .routes import main
    app.register_blueprint(main)

    # Importa y registra los eventos de socket
    from .chat_routes import register_socket_events
    register_socket_events(socketio)

    # Crear todas las tablas de la base de datos
    with app.app_context():
        db.create_all()

    return app