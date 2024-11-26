from app import create_app, socketio  # Importa socketio desde tu __init__.py

app = create_app()

if __name__ == "__main__":
    # Cambia app.run por socketio.run para manejar SocketIO
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
