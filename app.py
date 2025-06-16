# app.py - Main Flask Application with Enhanced Features
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from datetime import datetime, timedelta
import secrets
from functools import wraps
import logging
import re

# Importar tus módulos existentes (Blueprints)
from user_auth import (
    user_bp, user_required, add_notification, load_payment_methods, 
    get_cart, add_to_cart, remove_from_cart, update_cart_quantity, 
    clear_user_persistent_cart, load_user_carts, load_users # IMPORTAR load_users
) 
from admin_products import admin_products_bp, admin_required

# Configurar el logging para ver mensajes informativos y errores
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar la aplicación Flask
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Configuración de archivos de datos
ADMIN_FILE = 'admin_users.json'
PRODUCTS_FILE = 'products.json'
REPORTS_FILE = 'reports.json' 
ORDERS_FILE = 'user_orders.json' 
CART_SESSION_KEY = 'cart' 

app.permanent_session_lifetime = timedelta(days=31)

def init_admin_users():
    """Inicializa el archivo de usuarios administradores con un administrador por defecto si no existe."""
    if not os.path.exists(ADMIN_FILE):
        default_admin = {
            'admin': {
                'username': 'admin',
                'password': generate_password_hash('admin123'), 
                'email': 'admin@marketplace.com',
                'role': 'admin',
                'created_at': datetime.now().isoformat()
            }
        }
        try:
            with open(ADMIN_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_admin, f, indent=2, ensure_ascii=False)
            logger.info("Archivo de usuarios administradores inicializado con admin por defecto.")
        except Exception as e:
            logger.error(f"Error al inicializar el archivo de usuarios administradores: {e}")

def load_admin_users():
    """Carga los usuarios administradores desde el archivo JSON."""
    try:
        with open(ADMIN_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        init_admin_users()
        return load_admin_users()
    except Exception as e:
        logger.error(f"Error al cargar usuarios administradores: {e}")
        return {}

def load_products():
    """Carga los productos desde el archivo JSON. Si no existe, crea algunos productos de ejemplo."""
    if not os.path.exists(PRODUCTS_FILE):
        sample_products = [
            {
                "id": 1,
                "name": "Laptop Gaming",
                "description": "Potente laptop para gaming con GPU dedicada y pantalla de 144Hz.",
                "price": 1299.99,
                "stock": 15,
                "image_url": "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=400&h=300&fit=crop",
                "category": "Electrónicos"
            },
            {
                "id": 2,
                "name": "Smartphone Pro",
                "description": "Teléfono inteligente de última generación con cámara profesional y batería de larga duración.",
                "price": 899.99,
                "stock": 25,
                "image_url": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400&h=300&fit=crop",
                "category": "Electrónicos"
            },
            {
                "id": 3,
                "name": "Auriculares Bluetooth",
                "description": "Auriculares inalámbricos con cancelación de ruido activa y sonido de alta fidelidad.",
                "price": 199.99,
                "stock": 50,
                "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=300&fit=crop",
                "category": "Audio"
            },
            {
                "id": 4,
                "name": "Smartwatch Deportivo",
                "description": "Reloj inteligente con monitor de frecuencia cardíaca, GPS y seguimiento de actividad.",
                "price": 249.00,
                "stock": 30,
                "image_url": "https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=400&h=300&fit=crop",
                "category": "Wearables"
            },
            {
                "id": 5,
                "name": "Tableta Gráfica",
                "description": "Tableta profesional para diseño gráfico y dibujo digital, con alta precisión.",
                "price": 349.50,
                "stock": 10,
                "image_url": "https://images.unsplash.com/photo-1588019777085-f55a109a25b2?w=400&h=300&fit=crop",
                "category": "Creatividad"
            }
        ]
        try:
            with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(sample_products, f, indent=2, ensure_ascii=False)
            logger.info("Archivo de productos inicializado con productos de ejemplo.")
            return sample_products
        except Exception as e:
            logger.error(f"Error al guardar productos de ejemplo: {e}")
            return []
    try:
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error al cargar productos desde el archivo: {e}")
        return []

def load_reports():
    """Carga los reportes desde el archivo JSON. Si no existe, crea algunos reportes de ejemplo."""
    if not os.path.exists(REPORTS_FILE):
        sample_reports = [
            {"id": 1, "type": "Bug", "user": "usuario1", "date": "2024-05-10", "status": "Abierto", "description": "El botón de agregar al carrito no funciona en la página de productos.", "admin_response": ""},
            {"id": 2, "type": "Sugerencia", "user": "usuario2", "date": "2024-05-08", "status": "Cerrado", "description": "Me gustaría ver más opciones de filtrado en la sección de productos.", "admin_response": "Gracias por tu sugerencia. Hemos tomado nota para futuras actualizaciones."},
            {"id": 3, "type": "Problema de Pago", "user": "usuario3", "date": "2024-05-05", "status": "En Progreso", "description": "Mi pago fue rechazado pero el dinero se descontó de mi cuenta.", "admin_response": "Estamos investigando tu problema de pago y te contactaremos pronto con una solución."},
            {"id": 4, "type": "Consulta", "user": "usuario1", "date": "2024-05-03", "status": "Abierto", "description": "¿Hay una forma de guardar productos en una lista de deseos?", "admin_response": ""},
        ]
        try:
            with open(REPORTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(sample_reports, f, indent=2, ensure_ascii=False)
            logger.info("Archivo de reportes inicializado con reportes de ejemplo.")
            return sample_reports
        except Exception as e:
            logger.error(f"Error al guardar reportes de ejemplo: {e}")
            return []
    try:
        with open(REPORTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error al cargar reportes desde el archivo: {e}")
        return []

def save_reports(reports):
    """Guarda los reportes en el archivo JSON."""
    try:
        with open(REPORTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(reports, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error al guardar reportes: {e}")
        return False

def load_orders():
    """Carga los pedidos desde el archivo JSON. Si no existe, crea un archivo vacío."""
    if not os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2, ensure_ascii=False)
        return []
    try:
        with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error al cargar pedidos: {e}")
        return []

def save_orders(orders):
    """Guarda los pedidos en el archivo JSON."""
    try:
        with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(orders, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error al guardar pedidos: {e}")
        return False

def get_cart_total():
    """Calcula el valor total del carrito."""
    cart = get_cart() 
    return sum(item['price'] * item['quantity'] for item in cart.values())

def clear_cart_session():
    """Limpia el carrito de compras de la sesión (usado internamente por Flask)."""
    if CART_SESSION_KEY in session:
        session.pop(CART_SESSION_KEY)
        session.permanent = True 


# --- Rutas Principales de la Aplicación ---

@app.route('/')
def home():
    """Página de inicio con productos destacados."""
    products = load_products()
    import random
    featured_products = random.sample(products, min(len(products), 3))
    
    return render_template('home.html', products=featured_products)

@app.route('/products')
def products():
    """Página del catálogo de productos con búsqueda y filtrado."""
    products_list = load_products()
    search_query = request.args.get('search', '').lower()
    category_filter = request.args.get('category', '')
    
    if search_query:
        products_list = [p for p in products_list if search_query in p['name'].lower() or search_query in p['description'].lower()]
    
    if category_filter:
        products_list = [p for p in products_list if p.get('category', '') == category_filter]
    
    categories = sorted(list(set(p.get('category', 'Sin categoría') for p in load_products())))
    
    return render_template('products.html', products=products_list, categories=categories)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Página de detalle de producto."""
    products = load_products()
    product = next((p for p in products if p['id'] == product_id), None)
    
    if not product:
        flash('Producto no encontrado.', 'error')
        return redirect(url_for('products'))
    
    return render_template('product_detail.html', product=product)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@user_required
def add_to_cart_route(product_id):
    """Ruta para agregar un producto al carrito (maneja la lógica de stock y persistencia)."""
    quantity = int(request.form.get('quantity', 1))
    add_to_cart(product_id, quantity) 
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
@user_required
def remove_from_cart_route(product_id):
    """Ruta para eliminar un producto del carrito (maneja la lógica de persistencia)."""
    remove_from_cart(product_id) 
    return redirect(url_for('cart'))

@app.route('/update_cart/<int:product_id>', methods=['POST'])
@user_required
def update_cart_route(product_id):
    """Ruta para actualizar la cantidad de un producto en el carrito (maneja la lógica de persistencia)."""
    new_quantity = int(request.form.get('quantity', 1))
    update_cart_quantity(product_id, new_quantity) 
    return redirect(url_for('cart'))

@app.route('/cart')
@user_required
def cart():
    """Página del carrito de compras."""
    cart_items = get_cart() 
    total = get_cart_total()
    
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/checkout', methods=['GET', 'POST']) 
@user_required
def checkout():
    """
    Página de checkout para revisar el pedido y seleccionar el método de pago.
    También maneja la simulación del procesamiento de pago.
    """
    cart_items = get_cart()
    total = get_cart_total()
    username = session['user_username']

    if not cart_items:
        flash('Tu carrito está vacío. No puedes proceder al pago.', 'error')
        return redirect(url_for('cart'))

    # Cargar datos del usuario para obtener la dirección de entrega
    users = load_users() # Ahora load_users() está importada de user_auth.py
    user_data = users.get(username, {})
    
    # Obtener la dirección de entrega del usuario, o un valor por defecto
    delivery_address = user_data.get('delivery_address', '').strip()

    # Cargar métodos de pago del usuario actual
    all_payment_methods = load_payment_methods() 
    user_payment_methods = [
        method for method in all_payment_methods if method['user_username'] == username
    ]

    if request.method == 'POST':
        selected_method_id = request.form.get('payment_method')
        # Obtener la dirección de entrega del formulario
        provided_delivery_address = request.form.get('delivery_address_input', '').strip()

        if not selected_method_id:
            flash('Por favor, selecciona un método de pago.', 'error')
            return redirect(url_for('checkout'))
        
        if not provided_delivery_address:
            flash('Por favor, ingresa una dirección de entrega.', 'error')
            return redirect(url_for('checkout'))

        try:
            products_in_db = load_products()
            for item_id_str, item_details in cart_items.items():
                item_id = int(item_id_str)
                for p in products_in_db:
                    if p['id'] == item_id:
                        if p['stock'] >= item_details['quantity']: 
                            p['stock'] -= item_details['quantity']
                        else:
                            flash(f'No hay suficiente stock para {item_details["name"]}. La compra no se pudo completar.', 'error')
                            return redirect(url_for('checkout')) 
                        break
            with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(products_in_db, f, indent=2, ensure_ascii=False)
            
            orders = load_orders()
            new_order_id = 1
            if orders:
                new_order_id = max(o.get('id', 0) for o in orders) + 1 

            order_items = []
            for product_id_str, item_details in cart_items.items():
                order_items.append({
                    "product_id": int(product_id_str),
                    "name": item_details['name'],
                    "price": item_details['price'],
                    "quantity": item_details['quantity'],
                    "image_url": item_details.get('image_url', '') 
                })

            new_order = {
                "id": new_order_id,
                "user_username": username,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "total": total,
                "items": order_items,
                "status": "Completado",
                "delivery_address": provided_delivery_address # GUARDAR DIRECCIÓN EN EL PEDIDO
            }
            orders.append(new_order)
            save_orders(orders)

            clear_cart_session() 
            clear_user_persistent_cart(username) 
            
            flash('¡Pago procesado con éxito! Tu pedido ha sido confirmado.', 'success')
            add_notification(username, "compra", "¡Tu compra ha sido confirmada!", f"Gracias por tu compra por un total de ${total:.2f}. Tu pedido está en procesamiento y será enviado a: {provided_delivery_address}.")
            
            return redirect(url_for('home')) 
        except Exception as e:
            flash(f'Hubo un error al procesar tu pago: {e}. Por favor, inténtalo de nuevo.', 'error')
            logger.error(f"Error al procesar el pago: {e}")
            return redirect(url_for('checkout'))

    return render_template('checkout.html', cart_items=cart_items, total=total, 
                           payment_methods=user_payment_methods, 
                           delivery_address=delivery_address) # Pasar la dirección a la plantilla

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Página de inicio de sesión del administrador."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin_users = load_admin_users()
        
        if username in admin_users and check_password_hash(admin_users[username]['password'], password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Inicio de sesión de administrador exitoso.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Credenciales de administrador incorrectas.', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Panel de control del administrador."""
    products = load_products()
    
    total_stock = sum(p.get('stock', 0) for p in products)
    total_price = sum(p.get('price', 0) for p in products)
    avg_price = total_price / len(products) if products else 0
    low_stock_products = len([p for p in products if p.get('stock', 0) < 10])

    stats = {
        'total_products': len(products),
        'total_stock': total_stock,
        'avg_price': avg_price,
        'low_stock_products': low_stock_products
    }
    
    return render_template('admin_dashboard.html', stats=stats, products=products)

@app.route('/admin/reports')
@admin_required
def admin_reports():
    """Página para ver los reportes de los usuarios."""
    reports = load_reports() 
    sorted_reports = sorted(
        reports,
        key=lambda x: (0 if x['status'] == 'Abierto' else 1 if x['status'] == 'En Progreso' else 2, x['date']),
        reverse=False 
    )
    return render_template('admin_reports.html', reports=sorted_reports)

@app.route('/admin/reports/respond/<int:report_id>', methods=['POST'])
@admin_required
def admin_respond_report(report_id):
    """
    Maneja la respuesta y actualización del estado de un reporte.
    Recibe los datos del modal en admin_reports.html via AJAX.
    """
    response_text = request.form.get('admin_response_text', '').strip()
    new_status = request.form.get('report_status', '').strip()

    reports = load_reports()
    report_found = False
    for report in reports:
        if report['id'] == report_id:
            report_found = True
            report['admin_response'] = response_text
            report['status'] = new_status
            
            add_notification(report.get('user', 'Usuario Desconocido'), "reporte_respuesta", f"Respuesta a tu reporte #{report_id} ({report.get('type', 'General')})", f"Tu reporte: \"{report.get('description', '')[:50]}...\" ha sido actualizado a '{new_status}'. Respuesta: \"{response_text[:100]}...\"")

            if 'status_history' not in report:
                report['status_history'] = []
            report['status_history'].append({
                'timestamp': datetime.now().isoformat(),
                'status': new_status,
                'response': response_text,
                'admin': session.get('admin_username', 'Desconocido')
            })
            break
    
    if report_found and save_reports(reports):
        flash('Reporte actualizado exitosamente.', 'success')
        return jsonify(success=True, message='Reporte actualizado.')
    else:
        flash('Error al actualizar el reporte.', 'error')
        return jsonify(success=False, message='Error al actualizar el reporte.'), 400

@app.route('/admin/logout')
def admin_logout():
    """Cierra la sesión del administrador."""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Sesión de administrador cerrada.', 'success')
    return redirect(url_for('home'))

@app.errorhandler(404)
def not_found_error(error):
    """Maneja errores 404 (Página no encontrada)."""
    return render_template('error_404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Maneja errores 500 (Error interno del servidor)."""
    logger.exception("Ha ocurrido un error 500:")
    return render_template('error_500.html'), 500

def init_app():
    """Inicializa la aplicación Flask, incluyendo la configuración de usuarios y el registro de Blueprints."""
    init_admin_users() 
    load_products()    
    load_reports()     
    load_user_carts()  
    load_orders()      
    
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(admin_products_bp, url_prefix='/admin')
    logger.info("Blueprints de usuario y administrador registrados.")

if __name__ == '__main__':
    init_app()
    app.run(debug=True, host='0.0.0.0', port=5000)

