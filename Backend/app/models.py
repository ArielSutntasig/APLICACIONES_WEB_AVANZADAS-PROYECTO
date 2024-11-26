from . import db

# Modelo de Usuario
class Usuario(db.Model):
    __tablename__ = 'Usuarios'
    id = db.Column('Id', db.Integer, primary_key=True)
    nombre_completo = db.Column('NombreCompleto', db.String(100), nullable=False)
    email = db.Column('Email', db.String(100), unique=True, nullable=False)
    contraseña = db.Column('Contraseña', db.String(255), nullable=False)  # Encriptada
    fecha_registro = db.Column('FechaRegistro', db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<Usuario {self.email}>"

# Modelo de Producto
class Producto(db.Model):
    __tablename__ = 'Productos'
    id = db.Column('Id', db.Integer, primary_key=True)
    nombre = db.Column('Nombre', db.String(100), nullable=False)
    precio = db.Column('Precio', db.Float, nullable=False)
    imagen_url = db.Column('ImagenURL', db.String(255), nullable=True)
    en_oferta = db.Column('EnOferta', db.Boolean, default=False)
    stock = db.Column('Stock', db.Integer, default=0)
    fecha_creacion = db.Column('FechaCreacion', db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<Producto {self.nombre}>"

# Modelo de Carrito
class Carrito(db.Model):
    __tablename__ = 'Carrito'
    id = db.Column('Id', db.Integer, primary_key=True)
    usuario_id = db.Column('UsuarioId', db.Integer, db.ForeignKey('Usuarios.Id'), nullable=False)
    producto_id = db.Column('ProductoId', db.Integer, db.ForeignKey('Productos.Id'), nullable=False)
    cantidad = db.Column('Cantidad', db.Integer, nullable=False)
    precio_unitario = db.Column('PrecioUnitario', db.Float, nullable=False)
    estado = db.Column('Estado', db.String(50), nullable=False, default='Pendiente')
    fecha = db.Column('Fecha', db.DateTime, default=db.func.current_timestamp())

    usuario = db.relationship('Usuario', backref='carrito')
    producto = db.relationship('Producto', backref='carrito')

    def __repr__(self):
        return f"<Carrito Usuario: {self.usuario_id} Producto: {self.producto_id}>"
