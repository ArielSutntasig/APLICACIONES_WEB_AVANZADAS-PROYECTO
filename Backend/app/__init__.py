from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO  # Importa SocketIO
from .config import Config

db = SQLAlchemy()
socketio = SocketIO(cors_allowed_origins="*")  # Inicializa SocketIO con CORS habilitado

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializa CORS
    CORS(app)

    # Inicializa SQLAlchemy
    db.init_app(app)

    # Inicializa SocketIO
    socketio.init_app(app, cors_allowed_origins="*")

    # Importa y registra las rutas
    from .routes import main
    app.register_blueprint(main)

    return app
