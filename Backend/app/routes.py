import datetime
from flask import Blueprint, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from .models import Usuario, Producto, Carrito, Orden, DetalleOrden, Mensaje
from app import db
from werkzeug.utils import secure_filename
import os


main = Blueprint('main', __name__)
CORS(main)

ASESOR_EMAIL = 'asesor.comercial@gmail.com'

# Crear un nuevo usuario
@main.route('/usuarios', methods=['POST'])
def crear_usuario():
    data = request.json
    nombre = data.get('nombre_completo')
    email = data.get('email')
    contraseña = data.get('contraseña')

    if not nombre or not email or not contraseña:
        return jsonify({"error": "Todos los campos son obligatorios"}), 400

    contraseña_hash = generate_password_hash(contraseña)

    nuevo_usuario = Usuario(nombre_completo=nombre, email=email, contraseña=contraseña_hash)

    try:
        db.session.add(nuevo_usuario)
        db.session.commit()
        return jsonify({"message": "Usuario creado exitosamente"}), 201
    except Exception as e:
        db.session.rollback()
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

# Obtener todos los productos
@main.route('/productos', methods=['GET'])
def obtener_productos():
    try:
        productos = Producto.query.all()
        productos_list = []
        
        for producto in productos:
            try:
                productos_list.append({
                    "id": producto.id,
                    "nombre": producto.nombre,
                    "precio": float(producto.precio),
                    "imagen_url": producto.imagen_url or "/static/images/default-product.jpg",
                    "en_oferta": bool(producto.en_oferta),
                    "stock": int(producto.stock),
                    "fecha_creacion": producto.fecha_creacion.isoformat() if producto.fecha_creacion else None
                })
            except Exception as e:
                print(f"Error procesando producto {producto.id}: {str(e)}")
                continue
                
        return jsonify(productos_list), 200
        
    except Exception as e:
        print(f"Error al obtener productos: {str(e)}")
        return jsonify({"error": "Error al obtener productos"}), 500

# Obtener productos del carrito de un usuario
@main.route('/carrito/<int:usuario_id>', methods=['GET'])
def obtener_carrito(usuario_id):
    try:
        print(f"Obteniendo carrito para usuario {usuario_id}")
        
        items = db.session.query(
            Carrito, Producto
        ).join(
            Producto, Carrito.producto_id == Producto.id
        ).filter(
            Carrito.usuario_id == usuario_id,
            Carrito.estado == 'Pendiente'
        ).all()

        print(f"Items encontrados: {len(items)}")

        carrito = [{
            "id": item.Carrito.id,
            "producto_id": item.Carrito.producto_id,
            "producto": item.Producto.nombre,
            "cantidad": item.Carrito.cantidad,
            "precio_unitario": float(item.Carrito.precio_unitario),
            "imagen": item.Producto.imagen_url,
            "subtotal": float(item.Carrito.precio_unitario * item.Carrito.cantidad)
        } for item in items]
        
        print("Carrito a devolver:", carrito)
        return jsonify(carrito), 200
        
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": f"No se pudo obtener el carrito: {e}"}), 500

@main.route('/carrito', methods=['POST'])
def agregar_al_carrito():
    try:
        data = request.json
        print("Datos recibidos:", data)  # Debug log

        # Validar datos requeridos
        if not all(key in data for key in ['usuario_id', 'producto_id', 'cantidad', 'precio_unitario']):
            return jsonify({"error": "Faltan datos requeridos"}), 400

        # Validar existencia del usuario y producto
        usuario = Usuario.query.get(data['usuario_id'])
        producto = Producto.query.get(data['producto_id'])
        
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404
        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 404

        # Verificar stock
        if producto.stock < data['cantidad']:
            return jsonify({"error": "Stock insuficiente"}), 400

        # Verificar si el producto ya existe en el carrito
        carrito_existente = Carrito.query.filter_by(
            usuario_id=data['usuario_id'],
            producto_id=data['producto_id'],
            estado='Pendiente'
        ).first()

        if carrito_existente:
            carrito_existente.cantidad += data['cantidad']
            print(f"Actualizando cantidad en carrito existente: {carrito_existente.cantidad}")
        else:
            carrito_item = Carrito(
                usuario_id=data['usuario_id'],
                producto_id=data['producto_id'],
                cantidad=data['cantidad'],
                precio_unitario=data['precio_unitario'],
                estado='Pendiente'
            )
            db.session.add(carrito_item)
            print("Agregando nuevo item al carrito")

        db.session.commit()
        return jsonify({"message": "Producto agregado al carrito"}), 201

    except Exception as e:
        print(f"Error en agregar_al_carrito: {str(e)}")  # Debug log
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Actualizar cantidad en el carrito
@main.route('/carrito/actualizar', methods=['POST'])
def actualizar_carrito():
    try:
        data = request.json
        item = Carrito.query.get(data['item_id'])
        if item:
            item.cantidad = data['cantidad']
            db.session.commit()
            return jsonify({"message": "Cantidad actualizada"}), 200
        return jsonify({"error": "Item no encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Eliminar item del carrito
@main.route('/carrito/eliminar/<int:item_id>', methods=['DELETE'])
def eliminar_del_carrito(item_id):
    try:
        item = Carrito.query.get(item_id)
        if item:
            db.session.delete(item)
            db.session.commit()
            return jsonify({"message": "Item eliminado"}), 200
        return jsonify({"error": "Item no encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Manejar el inicio de sesión
@main.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    try:
        usuario = Usuario.query.filter_by(email=email).first()

        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404

        if not check_password_hash(usuario.contraseña, password):
            return jsonify({"error": "Contraseña incorrecta"}), 401

        return jsonify({
            "message": "Inicio de sesión exitoso",
            "nombre_completo": usuario.nombre_completo,
            "usuario_id": usuario.id
        }), 200
    except Exception as e:
        return jsonify({"error": f"Error en el servidor: {e}"}), 500

# Manejar el restablecimiento de contraseña
@main.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    email = data.get('email')
    new_password = data.get('new_password')

    try:
        usuario = Usuario.query.filter_by(email=email).first()
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404

        usuario.contraseña = generate_password_hash(new_password)
        db.session.commit()
        
        return jsonify({"message": "Contraseña actualizada exitosamente"}), 200
    except Exception as e:
        return jsonify({"error": f"Error al actualizar la contraseña: {e}"}), 500

# Confirmar compra
@main.route('/confirmar-compra', methods=['POST'])
def confirmar_compra():
    try:
        data = request.json
        
        # Crear nueva orden
        nueva_orden = Orden(
            usuario_id=data['usuario_id'],
            subtotal=data['subtotal'],
            iva=data['iva'],
            envio=data['envio'],
            total=data['total']
        )
        db.session.add(nueva_orden)
        db.session.flush()

        # Procesar cada producto
        for producto in data['productos']:
            # Crear detalle de orden
            detalle = DetalleOrden(
                orden_id=nueva_orden.id,
                producto_id=producto['id'],
                cantidad=producto['cantidad'],
                precio_unitario=producto['precio_unitario']
            )
            db.session.add(detalle)

            # Actualizar stock
            producto_db = Producto.query.get(producto['id'])
            if producto_db:
                if producto_db.stock >= producto['cantidad']:
                    producto_db.stock -= producto['cantidad']
                else:
                    raise Exception(f"Stock insuficiente para el producto {producto_db.nombre}")

        # Actualizar estado del carrito
        items_carrito = Carrito.query.filter_by(
            usuario_id=data['usuario_id'],
            estado='Pendiente'
        ).all()
        for item in items_carrito:
            item.estado = 'Finalizado'

        db.session.commit()
        return jsonify({
            "message": "Compra realizada con éxito",
            "orden_id": nueva_orden.id
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Ruta para obtener el historial de órdenes
@main.route('/ordenes/<int:usuario_id>', methods=['GET'])
def obtener_ordenes(usuario_id):
    try:
        ordenes = Orden.query.filter_by(usuario_id=usuario_id).order_by(Orden.fecha.desc()).all()
        return jsonify([{
            "id": orden.id,
            "fecha": orden.fecha.isoformat(),
            "total": float(orden.total),
            "estado": orden.estado
        } for orden in ordenes]), 200
    except Exception as e:
        return jsonify({"error": f"Error al obtener órdenes: {e}"}), 500

# Ruta para obtener detalles de una orden específica
@main.route('/orden/<int:orden_id>', methods=['GET'])
def obtener_detalle_orden(orden_id):
    try:
        detalles = DetalleOrden.query.filter_by(orden_id=orden_id).all()
        return jsonify([{
            "producto_id": detalle.producto_id,
            "cantidad": detalle.cantidad,
            "precio_unitario": float(detalle.precio_unitario)
        } for detalle in detalles]), 200
    except Exception as e:
        return jsonify({"error": f"Error al obtener detalles de la orden: {e}"}), 500
    
# Configurar la ruta de subida
UPLOAD_FOLDER = os.path.join('app', 'static', 'images', 'productos')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/upload-image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Generar nombre único
        unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        file.save(os.path.join(UPLOAD_FOLDER, unique_filename))
        
        # Devolver la URL de la imagen
        image_url = f'/static/images/productos/{unique_filename}'
        return jsonify({'url': image_url}), 200


# Obtener el nombre completo de un usuario
@main.route('/usuario/<int:usuario_id>', methods=['GET'])
def obtener_nombre_usuario(usuario_id):
    try:
        # Buscar al usuario por su ID
        usuario = Usuario.query.get(usuario_id)

        # Si el usuario no existe, devolver un error
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404

        # Devolver el nombre completo del usuario
        return jsonify({"nombre_completo": usuario.nombre_completo}), 200
    except Exception as e:
        return jsonify({"error": f"Error al obtener el nombre del usuario: {e}"}), 500

    
# Obtener mensajes entre un usuario y el asesor
@main.route('/mensajes/<int:usuario_id>', methods=['GET'])
def obtener_mensajes(usuario_id):
    try:
        # Obtener el asesor
        asesor = Usuario.query.filter_by(email=ASESOR_EMAIL).first()
        if not asesor:
            return jsonify({"error": "Asesor no encontrado"}), 404

        # Obtener mensajes
        mensajes = Mensaje.query.filter(
            db.or_(
                db.and_(Mensaje.emisor_id == usuario_id, Mensaje.receptor_id == asesor.id),
                db.and_(Mensaje.emisor_id == asesor.id, Mensaje.receptor_id == usuario_id)
            )
        ).order_by(Mensaje.fecha).all()

        # Agregar logging para debug
        print(f"Mensajes encontrados: {len(mensajes)}")
        for mensaje in mensajes:
            print(f"Mensaje: {mensaje.contenido} - De: {mensaje.emisor_id} Para: {mensaje.receptor_id}")

        return jsonify([{
            "id": mensaje.id,
            "emisor_id": mensaje.emisor_id,
            "receptor_id": mensaje.receptor_id,
            "contenido": mensaje.contenido,
            "fecha": mensaje.fecha.isoformat()
        } for mensaje in mensajes]), 200
    except Exception as e:
        print(f"Error al obtener mensajes: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Agregar un nuevo mensaje
@main.route('/mensajes', methods=['POST'])
def agregar_mensaje():
    data = request.json
    emisor_id = data.get('emisor_id')
    receptor_id = data.get('receptor_id')
    contenido = data.get('contenido')

    if not emisor_id or not receptor_id or not contenido:
        return jsonify({"error": "Todos los campos son obligatorios"}), 400

    try:
        # Validar existencia de usuarios
        emisor = Usuario.query.get(emisor_id)
        receptor = Usuario.query.get(receptor_id)

        if not emisor or not receptor:
            return jsonify({"error": "Emisor o receptor no encontrado"}), 404

        # Crear mensaje
        nuevo_mensaje = Mensaje(
            emisor_id=emisor_id,
            receptor_id=receptor_id,
            contenido=contenido
        )
        db.session.add(nuevo_mensaje)
        db.session.commit()

        return jsonify({
            "message": "Mensaje enviado exitosamente",
            "mensaje": {
                "id": nuevo_mensaje.id,
                "emisor_id": nuevo_mensaje.emisor_id,
                "receptor_id": nuevo_mensaje.receptor_id,
                "contenido": nuevo_mensaje.contenido,
                "fecha": nuevo_mensaje.fecha.isoformat(),
                "leido": nuevo_mensaje.leido
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        print("Error al agregar mensaje:", str(e))
        return jsonify({"error": f"No se pudo enviar el mensaje: {e}"}), 500

# Obtener chats activos (solo para el asesor)
# In routes.py - Update obtener_chats_activos route
# app/routes.py
@main.route('/obtener-chats-activos')
def obtener_chats_activos():
    try:
        asesor = Usuario.query.filter_by(email=ASESOR_EMAIL).first()
        if not asesor:
            return jsonify({"error": "Asesor no encontrado"}), 404

        # Get users with unread message counts
        usuarios = db.session.query(
            Usuario.id,
            Usuario.nombre_completo,
            db.func.count(Mensaje.id).label('mensajes_no_leidos')
        ).outerjoin(
            Mensaje,
            db.and_(
                Mensaje.emisor_id == Usuario.id,
                Mensaje.receptor_id == asesor.id,
                Mensaje.leido == False
            )
        ).filter(
            Usuario.email != ASESOR_EMAIL
        ).group_by(
            Usuario.id,
            Usuario.nombre_completo
        ).all()

        result = [{
            "usuario_id": usuario[0],
            "nombre": usuario[1],
            "mensajes_no_leidos": usuario[2]
        } for usuario in usuarios]

        return jsonify(result)
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

    
@main.route('/obtener-asesor', methods=['GET'])
def obtener_asesor():
    try:
        asesor = Usuario.query.filter_by(email=ASESOR_EMAIL).first()
        if not asesor:
            return jsonify({"error": "Asesor no encontrado"}), 404
        return jsonify({"asesor_id": asesor.id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Actualizar producto
@main.route('/productos/<int:producto_id>', methods=['PUT'])
def actualizar_producto(producto_id):
    try:
        data = request.json
        producto = Producto.query.get(producto_id)
        if producto:
            producto.nombre = data.get('nombre', producto.nombre)
            producto.precio = data.get('precio', producto.precio)
            producto.imagen_url = data.get('imagen_url', producto.imagen_url)
            producto.en_oferta = data.get('en_oferta', producto.en_oferta)
            producto.stock = data.get('stock', producto.stock)
            db.session.commit()
            return jsonify({"message": "Producto actualizado"}), 200
        return jsonify({"error": "Producto no encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Eliminar producto
@main.route('/productos/<int:producto_id>', methods=['DELETE'])
def eliminar_producto(producto_id):
    try:
        producto = Producto.query.get(producto_id)
        if producto:
            db.session.delete(producto)
            db.session.commit()
            return jsonify({"message": "Producto eliminado"}), 200
        return jsonify({"error": "Producto no encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@main.route('/marcar-mensajes-leidos/<int:emisor_id>', methods=['POST'])
def marcar_mensajes_leidos(emisor_id):
    try:
        asesor = Usuario.query.filter_by(email=ASESOR_EMAIL).first()
        if not asesor:
            return jsonify({"error": "Asesor no encontrado"}), 404

        # Update unread messages from this user to read
        Mensaje.query.filter_by(
            emisor_id=emisor_id,
            receptor_id=asesor.id,
            leido=False
        ).update({"leido": True})
        
        db.session.commit()
        return jsonify({"message": "Mensajes marcados como leídos"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500