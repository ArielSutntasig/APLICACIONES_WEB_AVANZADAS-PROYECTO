from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializa SQLAlchemy
    db.init_app(app)

    # Importa y registra las rutas
    from .routes import main
    app.register_blueprint(main)

    return app
