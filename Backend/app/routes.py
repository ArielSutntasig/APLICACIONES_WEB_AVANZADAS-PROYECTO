from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash
from .models import Usuario, Producto, Carrito
from app import db

main = Blueprint('main', __name__)

# Crear un nuevo usuario
@main.route('/usuarios', methods=['POST'])
def crear_usuario():
    data = request.json
    nombre = data.get('nombre_completo')
    email = data.get('email')
    contraseña = generate_password_hash(data.get('contraseña'))

    nuevo_usuario = Usuario(nombre_completo=nombre, email=email, contraseña=contraseña)

    try:
        db.session.add(nuevo_usuario)
        db.session.commit()
        return jsonify({"message": "Usuario creado exitosamente"}), 201
    except Exception as e:
        return jsonify({"error": f"No se pudo crear el usuario: {e}"}), 500

# Agregar un producto
@main.route('/productos', methods=['POST'])
def agregar_producto():
    data = request.json
    producto = Producto(
        nombre=data.get('nombre'),
        precio=data.get('precio'),
        imagen_url=data.get('imagen_url'),
        en_oferta=data.get('en_oferta', False),
        stock=data.get('stock')
    )

    try:
        db.session.add(producto)
        db.session.commit()
        return jsonify({"message": "Producto agregado correctamente"}), 201
    except Exception as e:
        return jsonify({"error": f"No se pudo agregar el producto: {e}"}), 500

# Obtener productos del carrito de un usuario
@main.route('/carrito/<int:usuario_id>', methods=['GET'])
def obtener_carrito(usuario_id):
    try:
        items = Carrito.query.filter_by(usuario_id=usuario_id, estado='Pendiente').all()
        carrito = [
            {
                "id": item.id,
                "producto": item.producto.nombre,
                "cantidad": item.cantidad,
                "precio_unitario": item.precio_unitario,
                "imagen": item.producto.imagen_url
            }
            for item in items
        ]
        return jsonify(carrito), 200
    except Exception as e:
        return jsonify({"error": f"No se pudo obtener el carrito: {e}"}), 500

# Agregar un producto al carrito
@main.route('/carrito', methods=['POST'])
def agregar_al_carrito():
    data = request
