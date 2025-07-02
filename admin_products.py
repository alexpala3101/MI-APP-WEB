# admin_products.py
from flask import Blueprint, render_template_string, request, redirect, url_for, flash, session, render_template
import json
import os
from functools import wraps
from datetime import datetime

# Importar load_orders desde app.py (asumiendo que app.py la define y la carga)
try:
    from app import load_orders, load_products # Necesitamos load_products para el detalle del producto en la lista de órdenes
except ImportError:
    # Fallback si se ejecuta admin_products.py de forma independiente, o si app.py no las tiene
    # En una aplicación real, esto indicaría un problema de arquitectura.
    print("WARNING: Could not import load_orders or load_products from app.py. Using local mock.")
    def load_orders():
        if os.path.exists('user_orders.json'):
            try:
                with open('user_orders.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error al cargar pedidos (fallback): {e}")
                return []
        return []
    def load_products():
        if os.path.exists('products.json'):
            try:
                with open('products.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error al cargar productos (fallback): {e}")
                return []
        return []


# Blueprint para la gestión de productos de administrador
admin_products_bp = Blueprint('admin_products', __name__)

# Archivo simulado de base de datos de productos
PRODUCTS_FILE = 'products.json' # Definido aquí para que las funciones locales puedan usarlo, si no se importa de app.py

def admin_required(f):
    """
    Decorador para asegurar que el usuario es un administrador logueado.
    Redirige al login de administrador si no está autenticado.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Debes iniciar sesión como administrador para ver esta página.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def load_products_local(): # Renombrada para evitar conflicto si se importa de app
    """Carga los productos desde el archivo JSON."""
    if not os.path.exists(PRODUCTS_FILE):
        return []
    try:
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error al cargar los productos: {e}")
        return []

def save_products(products):
    """Guarda los productos en el archivo JSON."""
    try:
        with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error al guardar productos: {e}")
        return False

# Plantillas HTML (se han movido a archivos separados en una estructura real)
PRODUCT_FORM_TEMPLATE = """
{% extends "base.html" %}
{% block title %}{{ title }}{% endblock %}
{% block content %}
<div class="max-w-md mx-auto bg-white p-8 rounded-lg shadow-lg mt-8">
    <h1 class="text-2xl font-bold mb-6 text-center text-gray-800">{{ title }}</h1>
    <form method="POST">
        <div class="mb-4">
            <label for="name" class="block text-gray-700 text-sm font-bold mb-2">Nombre del Producto:</label>
            <input type="text" id="name" name="name" value="{{ product.name | default('') }}" required
                   class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline">
        </div>
        <div class="mb-4">
            <label for="description" class="block text-gray-700 text-sm font-bold mb-2">Descripción:</label>
            <textarea id="description" name="description" rows="4" required
                      class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline">{{ product.description | default('') }}</textarea>
        </div>
        <div class="mb-4">
            <label for="price" class="block text-gray-700 text-sm font-bold mb-2">Precio:</label>
            <input type="number" id="price" name="price" value="{{ product.price | default(0) }}" step="0.01" required
                   class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline">
        </div>
        <div class="mb-4">
            <label for="stock" class="block text-gray-700 text-sm font-bold mb-2">Stock:</label>
            <input type="number" id="stock" name="stock" value="{{ product.stock | default(0) }}" required
                   class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline">
        </div>
        <div class="mb-6">
            <label for="image_url" class="block text-gray-700 text-sm font-bold mb-2">URL de la Imagen:</label>
            <input type="url" id="image_url" name="image_url" value="{{ product.image_url | default('') }}"
                   class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline">
        </div>
        <div class="flex items-center justify-between">
            <button type="submit" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline">
                Guardar Producto
            </button>
            <a href="{{ url_for('admin_products.manage_products') }}" class="inline-block align-baseline font-bold text-sm text-blue-500 hover:text-blue-800">
                Cancelar
            </a>
        </div>
    </form>
</div>
{% endblock %}
"""

# Rutas de administración de productos
@admin_products_bp.route('/admin/products')
@admin_required
def manage_products():
    """
    Muestra una lista de todos los productos y permite acciones de gestión.
    """
    products = load_products_local() # Usa la función local o importada
    return render_template_string("""
{% extends "base.html" %}
{% block title %}Gestión de Productos{% endblock %}
{% block content %}
<div class="max-w-4xl mx-auto px-4 py-8">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-bold text-gray-800">📦 Gestión de Productos</h1>
        <a href="{{ url_for('admin_products.add_product') }}" class="bg-green-600 text-white px-5 py-2 rounded-lg hover:bg-green-700 transition shadow font-semibold">
            <i class="fas fa-plus-circle mr-2"></i>Añadir Nuevo Producto
        </a>
    </div>

    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class="bg-{{ category }}-100 border-l-4 border-{{ category }}-500 text-{{ category }}-700 p-4 mb-4" role="alert">
                    <p class="font-bold">{{ category.capitalize() }}:</p>
                    <p>{{ message }}</p>
                </div>
            {% endfor %}
        {% endif %}
    {% endwith %}

    {% if products %}
    <div class="bg-white shadow-md rounded-lg overflow-hidden">
        <table class="min-w-full leading-normal">
            <thead>
                <tr class="bg-gray-100 border-b border-gray-200">
                    <th class="px-5 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">ID</th>
                    <th class="px-5 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Imagen</th>
                    <th class="px-5 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Nombre</th>
                    <th class="px-5 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Precio</th>
                    <th class="px-5 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Stock</th>
                    <th class="px-5 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">Acciones</th>
                </tr>
            </thead>
            <tbody>
                {% for product in products %}
                <tr class="hover:bg-gray-50 border-b border-gray-200">
                    <td class="px-5 py-5 text-sm text-gray-900">{{ product.id }}</td>
                    <td class="px-5 py-5 text-sm text-gray-900">
                        <img src="{{ product.image_url | default('https://placehold.co/50x50/e2e8f0/64748b?text=No+Img') }}" onerror="this.onerror=null;this.src='https://placehold.co/50x50/e2e8f0/64748b?text=No+Img';" alt="{{ product.name }}" class="w-12 h-12 object-cover rounded-md">
                    </td>
                    <td class="px-5 py-5 text-sm text-gray-900">{{ product.name }}</td>
                    <td class="px-5 py-5 text-sm text-gray-900">${{ "%.2f"|format(product.price) }}</td>
                    <td class="px-5 py-5 text-sm text-gray-900">{{ product.stock }}</td>
                    <td class="px-5 py-5 text-sm text-gray-900 text-center">
                        <a href="{{ url_for('admin_products.edit_product', product_id=product.id) }}" class="text-blue-600 hover:text-blue-900 mr-3" title="Editar">
                            <i class="fas fa-edit"></i>
                        </a>
                        <form action="{{ url_for('admin_products.delete_product', product_id=product.id) }}" method="POST" class="inline-block" onsubmit="return confirm('¿Estás seguro de que quieres eliminar este producto?');">
                            <button type="submit" class="text-red-600 hover:text-red-900" title="Eliminar">
                                <i class="fas fa-trash-alt"></i>
                            </button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
    <div class="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
        <i class="fas fa-box-open text-gray-400 text-6xl mb-4"></i>
        <h2 class="text-2xl font-semibold text-gray-600 mb-4">No hay productos disponibles.</h2>
        <p class="text-gray-500 mb-6">¡Añade tu primer producto para empezar!</p>
        <a href="{{ url_for('admin_products.add_product') }}" class="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition shadow">
            <i class="fas fa-plus-circle mr-2"></i>Añadir Producto
        </a>
    </div>
    {% endif %}
    
    <div class="text-center mt-8">
        <a href="{{ url_for('admin_dashboard') }}" class="bg-blue-600 text-white px-6 py-3 rounded-lg text-lg font-medium hover:bg-blue-700 transition shadow-md">
            <i class="fas fa-arrow-left mr-2"></i>Volver al Dashboard
        </a>
    </div>
</div>
{% endblock %}
    """, products=products)


@admin_products_bp.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    """
    Maneja la adición de nuevos productos.
    """
    if request.method == 'POST':
        products = load_products_local()
        new_id = 1
        if products:
            new_id = max(p['id'] for p in products) + 1

        try:
            name = request.form['name']
            description = request.form['description']
            price = float(request.form['price'])
            stock = int(request.form['stock'])
            image_url = request.form.get('image_url', '') # Permitir URL vacía, usar default en template

            if not name or not description or price <= 0 or stock < 0:
                flash('Todos los campos son requeridos y los valores deben ser válidos.', 'error')
            else:
                new_product = {
                    'id': new_id,
                    'name': name,
                    'description': description,
                    'price': price,
                    'stock': stock,
                    'image_url': image_url
                }
                products.append(new_product)
                if save_products(products):
                    flash('¡Producto añadido exitosamente!', 'success')
                    return redirect(url_for('admin_products.manage_products'))
                else:
                    flash('Error al guardar el producto.', 'error')
        except ValueError:
            flash('Por favor, introduce valores numéricos válidos para precio y stock.', 'error')
        
    return render_template_string(PRODUCT_FORM_TEMPLATE, title="Añadir Nuevo Producto", product={})

@admin_products_bp.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    """
    Maneja la edición de un producto existente.
    """
    products = load_products_local()
    product = next((p for p in products if p['id'] == product_id), None)

    if not product:
        flash('Producto no encontrado.', 'error')
        return redirect(url_for('admin_products.manage_products'))

    if request.method == 'POST':
        try:
            product['name'] = request.form['name']
            product['description'] = request.form['description']
            product['price'] = float(request.form['price'])
            product['stock'] = int(request.form['stock'])
            product['image_url'] = request.form.get('image_url', '')

            if not product['name'] or not product['description'] or product['price'] <= 0 or product['stock'] < 0:
                flash('Todos los campos son requeridos y los valores deben ser válidos.', 'error')
            else:
                if save_products(products):
                    flash('¡Producto actualizado exitosamente!', 'success')
                    return redirect(url_for('admin_products.manage_products'))
                else:
                    flash('Error al actualizar el producto.', 'error')
        except ValueError:
            flash('Por favor, introduce valores numéricos válidos para precio y stock.', 'error')
            
    return render_template_string(PRODUCT_FORM_TEMPLATE, title="Editar Producto", product=product)

@admin_products_bp.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    """
    Maneja la eliminación de un producto.
    """
    products = load_products_local()
    initial_count = len(products)
    products = [p for p in products if p['id'] != product_id]
    
    if len(products) < initial_count:
        if save_products(products):
            flash('¡Producto eliminado exitosamente!', 'success')
        else:
            flash('Error al eliminar el producto.', 'error')
    else:
        flash('No se pudo eliminar el producto porque no fue encontrado.', 'error')

    return redirect(url_for('admin_products.manage_products'))

@admin_products_bp.route('/admin/orders') # NUEVA RUTA
@admin_required
def admin_orders():
    """
    Muestra la página de gestión de pedidos del administrador.
    """
    all_orders = load_orders() # Carga todos los pedidos
    all_products = load_products() # Carga todos los productos para buscar detalles

    # Enriquecer los elementos de cada pedido con detalles del producto (nombre, imagen)
    # Esto es útil si los datos del pedido solo guardan el ID del producto
    enriched_orders = []
    for order in all_orders:
        enriched_items = []
        for item in order.get('items', []):
            product_detail = next((p for p in all_products if p['id'] == item['product_id']), None)
            if product_detail:
                item['name'] = product_detail.get('name', item.get('name', 'Producto Desconocido'))
                item['image_url'] = product_detail.get('image_url', item.get('image_url', ''))
            enriched_items.append(item)
        order['items'] = enriched_items
        enriched_orders.append(order)

    # Opcional: Ordenar los pedidos, por ejemplo, por fecha descendente
    sorted_orders = sorted(
        enriched_orders,
        key=lambda x: x.get('timestamp', ''),
        reverse=True
    )
    
    return render_template('admin_orders.html', orders=sorted_orders)

@admin_products_bp.route('/admin/orders/delete/<int:order_id>', methods=['POST'])
@admin_required
def delete_order(order_id):
    """
    Elimina un pedido por su ID (solo admins).
    """
    orders = load_orders()
    initial_count = len(orders)
    orders = [o for o in orders if o.get('id') != order_id]
    if len(orders) < initial_count:
        # Guardar los pedidos actualizados
        try:
            with open('user_orders.json', 'w', encoding='utf-8') as f:
                json.dump(orders, f, indent=2, ensure_ascii=False)
            flash('¡Pedido eliminado exitosamente!', 'success')
        except Exception as e:
            flash(f'Error al eliminar el pedido: {e}', 'error')
    else:
        flash('No se encontró el pedido a eliminar.', 'error')
    return redirect(url_for('admin_orders'))

def create_admin_products_routes(app):
    """
    Registra el Blueprint de administración de productos en la aplicación principal.
    Esta función se llama desde app.py.
    """
    app.register_blueprint(admin_products_bp, url_prefix='/admin')

