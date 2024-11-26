from app import create_app, db
from sqlalchemy import text  # Importa la función text

app = create_app()

with app.app_context():
    try:
        # Utiliza text() para envolver la consulta SQL
        db.session.execute(text('SELECT 1'))  # Prueba la conexión
        print("¡Conexión exitosa a la base de datos!")
    except Exception as e:
        print(f"Error al conectarse a la base de datos: {e}")