from flask import Blueprint, jsonify
from .models import Product
from app import db

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return jsonify({"message": "¡Bienvenido a TechShop!"})


@main.route('/products', methods=['GET'])
def get_products():
    try:
        # Obtiene todos los productos de la base de datos
        products = Product.query.all()

        # Convierte los productos a un formato de lista de diccionarios
        products_list = []
        for product in products:
            product_data = {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'stock': product.stock
            }
            products_list.append(product_data)

        return jsonify(products_list), 200

    except Exception as e:
        return jsonify({"error": f"Error al obtener productos: {e}"}), 500
