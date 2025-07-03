# app.py - Main Flask Application with Enhanced Features
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import json
import os
from datetime import datetime, timedelta
import secrets
from functools import wraps
import logging
import re

# --- Importar funciones de carga/guardado desde data_manager.py ---
# ¡IMPORTANTE! Asegúrate de que tengas un archivo data_manager.py
# en la misma carpeta, con todas las funciones de carga/guardado.
from data_manager import (
    load_products, save_products, load_orders, save_orders,
    load_reports, save_reports, load_users, save_users,
    load_notifications, save_notifications, load_user_carts, save_user_carts,
    load_user_purchases, save_user_purchases,  # <-- Agregado aquí
    # ADMIN_FILE eliminado porque no existe en data_manager.py
    # Estas funciones se importan ahora DIRECTAMENTE desde data_manager.py
    add_notification, get_cart, add_to_cart, remove_from_cart, update_cart_quantity,
    clear_user_persistent_cart
)
from data_manager_chat import add_chat_message, get_user_chat, get_all_user_chats

# --- Importar tus módulos existentes (Blueprints) ---
# Aquí, solo importas el Blueprint de user_auth, no sus funciones internas
from user_auth import user_bp, login_required
from admin_products import admin_products_bp
from admin_users import admin_users_bp
from admin_forms import AdminLoginForm

# Configuración básica del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Generar una clave secreta fuerte para las sesiones
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Configuración para hacer las sesiones permanentes (recordar al usuario)
# NOTA: 30 minutos es un tiempo relativamente corto para una sesión "permanente".
# Considera aumentar esto (ej. a días o semanas) si el usuario espera más persistencia.
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7) # Cambiado a 7 días como ejemplo

# Configuración para carga de imágenes
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Registrar Blueprints
app.register_blueprint(user_bp)
app.register_blueprint(admin_products_bp)
app.register_blueprint(admin_users_bp)


# --- Funciones de utilidad ---

def init_admin_users():
    """Inicializa o actualiza el usuario administrador con la contraseña por defecto."""
    users = load_users()
    # Siempre actualiza la contraseña del admin
    ADMIN_PASSWORD_HASH = generate_password_hash("ADMIN1234@")
    users['admin'] = {
        'username': 'admin',
        'email': 'admin@marketplace.com',
        'password': ADMIN_PASSWORD_HASH,
        'role': 'admin',
        'registration_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'last_login': None,
        'is_active': True
    }
    save_users(users)
    logger.info("Usuario administrador 'admin' creado o actualizado con contraseña por defecto.")

# Decorador para requerir autenticación de administrador
# (Este decorador puede estar en admin_users.py o aquí si es global)
# Asegúrate de que solo los usuarios con 'role': 'admin' puedan acceder
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Acceso denegado. Se requiere iniciar sesión como administrador.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --- Rutas principales ---

@app.route('/')
def home():
    """Página de inicio que muestra los productos disponibles."""
    products_dict = load_products()
    products = list(products_dict.values())  # Convertir a lista para la plantilla
    return render_template('index.html', products=products)

@app.route('/cart')
@login_required # Asegúrate de que el usuario esté logueado para ver el carrito
def cart():
    """Muestra el contenido del carrito de compras del usuario."""
    # user_cart es el carrito persistente del usuario (si está logueado)
    user_cart = get_cart(session.get('user_username'))
    
    products = load_products() # Para obtener detalles de los productos en el carrito
    
    cart_items_details = []
    total_price = 0
    
    if user_cart:
        for product_id, quantity in user_cart.items():
            product = products.get(product_id)
            if product:
                item_total = product['price'] * quantity
                total_price += item_total
                cart_items_details.append({
                    'id': product_id,
                    'name': product['name'],
                    'price': product['price'],
                    'quantity': quantity,
                    'image': product.get('image', '/static/images/default_product.png'), # Imagen por defecto
                    'total': item_total
                })
            else:
                flash(f'Producto con ID {product_id} no encontrado.', 'warning')
    
    return render_template('cart.html', cart_items=cart_items_details, total_price=total_price)


@app.route('/add_to_cart/<product_id>', methods=['POST'])
@login_required
def add_to_cart_route(product_id):
    """Añade un producto al carrito del usuario."""
    quantity = int(request.form.get('quantity', 1))
    username = session.get('user_username')
    
    if add_to_cart(product_id, quantity, username):
        flash(f'Producto añadido al carrito. Cantidad: {quantity}', 'success')
    else:
        flash('Error al añadir producto al carrito o producto no encontrado.', 'error')
    
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<product_id>', methods=['POST'])
@login_required
def remove_from_cart_route(product_id):
    """Elimina un producto del carrito del usuario."""
    username = session.get('user_username')
    
    if remove_from_cart(username, product_id):
        flash('Producto eliminado del carrito.', 'success')
    else:
        flash('Error al eliminar producto del carrito.', 'error')
    
    return redirect(url_for('cart'))

@app.route('/update_cart_quantity/<product_id>', methods=['POST'])
@login_required
def update_cart_quantity_route(product_id):
    """Actualiza la cantidad de un producto en el carrito del usuario."""
    new_quantity = int(request.form.get('quantity'))
    username = session.get('user_username')

    if new_quantity <= 0:
        return redirect(url_for('remove_from_cart_route', product_id=product_id, _method='POST'))

    if update_cart_quantity(username, product_id, new_quantity):
        flash('Cantidad del producto actualizada.', 'success')
    else:
        flash('Error al actualizar la cantidad del producto.', 'error')

    return redirect(url_for('cart'))


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Procesa el pago y crea una orden."""
    username = session.get('user_username')
    user_cart = get_cart(username)
    
    if not user_cart:
        flash('Tu carrito está vacío.', 'error')
        return redirect(url_for('cart'))

    products = load_products()
    orders = load_orders()
    users = load_users()
    current_user = users.get(username)

    cart_items_details = []
    total_price = 0

    for product_id, quantity in user_cart.items():
        product = products.get(product_id)
        if product and product['stock'] >= quantity: # Verificar stock antes de checkout
            item_total = product['price'] * quantity
            total_price += item_total
            cart_items_details.append({
                'id': product_id,
                'name': product['name'],
                'price': product['price'],
                'quantity': quantity,
                'image': product.get('image', '/static/images/default_product.png'),
                'total': item_total
            })
        else:
            flash(f'Stock insuficiente para {product.get("name", "un producto")}. Por favor, ajusta tu carrito.', 'error')
            return redirect(url_for('cart'))

    if request.method == 'POST':
        # Eliminar referencia a delivery_address
        # Proceso de pago simulado (sin métodos de pago)
        payment_successful = True # Simulación de pago exitoso

        if payment_successful:
            order_id = secrets.token_hex(8)
            new_order = {
                'order_id': order_id,
                'username': username,
                'items': [{
                    'product_id': item['id'],
                    'name': item['name'],
                    'quantity': item['quantity'],
                    'price': item['price']
                } for item in cart_items_details],
                'total_price': total_price,
                'payment_method_id': 'default', # Valor fijo o eliminar si lo deseas
                'order_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'pending'
            }
            orders[order_id] = new_order
            save_orders(orders)

            # --- Registrar la compra en user_purchases.json ---
            user_purchases = load_user_purchases()
            user_purchases.append({
                'order_id': order_id,
                'username': username,
                'items': new_order['items'],
                'total_price': total_price,
                'payment_method_id': 'default',
                'order_date': new_order['order_date'],
                'status': new_order['status']
            })
            save_user_purchases(user_purchases)
            # --- Fin registro compra ---

            # Actualizar stock de productos
            for item in cart_items_details:
                product_id = item['id']
                quantity_bought = item['quantity']
                products[product_id]['stock'] -= quantity_bought
            save_products(products) # Guardar los productos con el stock actualizado

            # Limpiar el carrito del usuario después de la compra
            clear_user_persistent_cart(username)

            flash('¡Tu pedido ha sido realizado con éxito!', 'success')
            add_notification(username, f'Tu pedido #{order_id} ha sido confirmado. Total: ${total_price:.2f}', 'order_confirmation')
            
            # --- Mensaje de compra en el chat ---
            for item in cart_items_details:
                product_name = item['name']
                product_image = item.get('image', '/static/images/default_product.png')
                chat_text = f"¡Has comprado: {product_name}!"
                # El mensaje tendrá tanto texto como imagen
                add_chat_message(username, 'system', chat_text, image_url=product_image, order_id=order_id)
            # --- Fin mensaje de compra en el chat ---

            return redirect(url_for('user_auth.user_orders'))
        else:
            flash('Error en el procesamiento del pago. Por favor, inténtalo de nuevo.', 'error')

    # Si es GET, o POST con error, renderiza la página de checkout
    user_address = current_user.get('delivery_address', '') if current_user else ''

    return render_template('checkout.html', 
                           cart_items=cart_items_details, 
                           total_price=total_price,
                           user_address=user_address)

@app.route('/products')
def products():
    """Página del catálogo de productos con búsqueda y filtrado."""
    products_dict = load_products()
    # Convertir a lista para iterar en la plantilla
    products = list(products_dict.values())
    # Obtener categorías únicas
    categories = sorted(set(p.get('category', 'Sin categoría') for p in products))
    # Filtros
    search = request.args.get('search', '').lower()
    category = request.args.get('category', '')
    if search:
        products = [p for p in products if search in p.get('name', '').lower() or search in p.get('description', '').lower()]
    if category:
        products = [p for p in products if p.get('category', 'Sin categoría') == category]
    return render_template('products.html', products=products, categories=categories)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    products = load_products()
    product = products.get(str(product_id))
    if not product:
        return render_template('error_404.html'), 404
    return render_template('product_detail.html', product=product)


# --- Rutas de administración ---

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Página principal del panel de administración."""
    users = load_users()
    products = load_products()
    orders = load_orders()
    reports = load_reports()

    # Contar usuarios y administradores
    total_users = len(users)
    total_admins = sum(1 for u in users.values() if u.get('role') == 'admin')

    # Contar productos (activos/inactivos)
    total_products = len(products)
    active_products = sum(1 for p in products.values() if p.get('is_active', False))

    # Estadísticas de órdenes
    total_orders = len(orders)
    pending_orders = sum(1 for o in orders.values() if o.get('status') == 'pending')
    completed_orders = sum(1 for o in orders.values() if o.get('status') == 'completed')

    # Suma total de ingresos de órdenes completadas
    total_revenue = sum(o.get('total_price', 0) for o in orders.values() if o.get('status') == 'completed')

    # Calcular precio promedio de productos
    if products:
        avg_price = sum(p.get('price', 0) for p in products.values()) / len(products)
    else:
        avg_price = 0

    # Notificaciones recientes (ejemplo: las últimas 5)
    all_notifications = load_notifications()
    recent_notifications = []
    for user_notifs in all_notifications.values():
        recent_notifications.extend(user_notifs)
    recent_notifications = sorted(recent_notifications, key=lambda x: x.get('timestamp', '0'), reverse=True)[:5]

    # Agrupar estadísticas en un diccionario
    stats = {
        'total_usuarios': total_users,
        'total_administradores': total_admins,
        'total_productos': total_products,
        'productos_activos': active_products,
        'total_ordenes': total_orders,
        'ordenes_pendientes': pending_orders,
        'ordenes_completadas': completed_orders,
        'ingresos_totales': total_revenue,
        'avg_price': avg_price
    }

    return render_template('admin_dashboard.html',
                           stats=stats,
                           recent_notifications=recent_notifications)

@app.route('/admin/reports')
@admin_required
def admin_reports():
    """Genera y muestra informes de la tienda."""
    reports = load_reports()

    # Ordenar por fecha de generación si lo deseas
    reports_sorted = dict(sorted(reports.items(), key=lambda item: item[1].get('generated_at', ''), reverse=True))

    return render_template('admin_reports.html', reports=reports_sorted)

@app.route('/admin/logout')
def admin_logout():
    """Cierra la sesión del administrador."""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Sesión de administrador cerrada.', 'success')
    return redirect(url_for('home'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Página de inicio de sesión para administradores."""
    form = AdminLoginForm()
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        users = load_users()
        admin = users.get('admin')
        if admin and username == 'admin' and check_password_hash(admin['password'], password):
            session['admin_logged_in'] = True
            session['admin_username'] = 'admin'
            flash('Bienvenido, administrador.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Credenciales incorrectas.', 'error')
    return render_template('admin_login.html', form=form)


@app.route('/admin/user_purchases')
@admin_required
def admin_user_purchases():
    """Muestra el historial de compras de todos los usuarios para el administrador."""
    purchases = load_user_purchases()
    # Ordenar por fecha descendente
    purchases_sorted = sorted(purchases, key=lambda x: x.get('order_date', ''), reverse=True)
    return render_template('admin_user_purchases.html', purchases=purchases_sorted)

@app.route('/admin/user_chats')
@admin_required
def admin_user_chats():
    """Muestra la lista de usuarios con los que hay chat."""
    # Obtener todos los chats agrupados por usuario
    user_chats = get_all_user_chats()
    # user_chats es un dict: {username: [mensajes]}
    return render_template('admin_user_chats.html', user_chats=user_chats)

@app.route('/admin/user_chats_overview')
@admin_required
def admin_user_chats_overview():
    """Muestra una lista de usuarios que han escrito en el chat (sin mostrar mensajes)."""
    user_chats = get_all_user_chats()
    user_list = sorted(user_chats.keys())
    return render_template('admin_user_chats_overview.html', user_list=user_list)

@app.route('/admin/user_chat/<username>', methods=['GET', 'POST'])
@admin_required
def admin_user_chat(username):
    chat_history = get_user_chat(username)
    user_chats = get_all_user_chats()
    user_list = sorted(user_chats.keys())
    if request.method == 'POST':
        message = request.form.get('message')
        image_url = None
        if 'admin_image' in request.files:
            file = request.files['admin_image']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"admin_{username}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                image_url = f"/static/uploads/{filename}"
        if message or image_url:
            add_chat_message(username, 'admin', message, image_url=image_url)
            flash('Mensaje enviado al usuario.', 'success')
        return redirect(url_for('admin_user_chat', username=username))
    return render_template('admin_user_chat.html', username=username, chat_history=chat_history, user_list=user_list)

@app.route('/contact_admin', methods=['GET', 'POST'])
@login_required
def contact_admin():
    username = session.get('user_username')
    user_cart = get_cart(username)
    products = load_products()
    users = load_users()
    current_user = users.get(username)

    cart_items_details = []
    total_price = 0

    if user_cart:
        for product_id, quantity in user_cart.items():
            product = products.get(product_id)
            if product:
                item_total = product['price'] * quantity
                total_price += item_total
                cart_items_details.append({
                    'id': product_id,
                    'name': product['name'],
                    'price': product['price'],
                    'quantity': quantity,
                    'image': product.get('image', '/static/images/default_product.png'),
                    'total': item_total
                })

    chat_history = get_user_chat(username)

    if request.method == 'POST':
        message = request.form.get('message')
        ancho = request.form.get('ancho')
        ancho_unidad = request.form.get('ancho_unidad')
        largo = request.form.get('largo')
        largo_unidad = request.form.get('largo_unidad')
        image_url = None
        if 'admin_image' in request.files:
            file = request.files['admin_image']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{username}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                image_url = f"/static/uploads/{filename}"
        # Registrar la compra como pendiente (flujo original)
        orders = load_orders()
        order_id = secrets.token_hex(8)
        new_order = {
            'order_id': order_id,
            'username': username,
            'items': [
                {
                    'product_id': item['id'],
                    'name': item['name'],
                    'quantity': item['quantity'],
                    'price': item['price']
                } for item in cart_items_details
            ],
            'total_price': total_price,
            'payment_method_id': 'contact_admin',
            'order_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'pending',
            'admin_message': message
        }
        orders[order_id] = new_order
        save_orders(orders)
        # Guardar mensaje en el chat (ahora con order_id)
        msg_text = f"{message}\nTamaño solicitado: {ancho} {ancho_unidad} x {largo} {largo_unidad}"
        # --- FILTRO DE MENSAJES: No guardar tokens ni cadenas sospechosas ---
        def is_suspicious_message(msg):
            if not msg:
                return False
            # Si es muy largo y sin espacios, probablemente es un token
            if len(msg) > 40 and ' ' not in msg:
                return True
            # Si parece un JWT o CSRF (muchos caracteres base64 y puntos)
            if re.match(r'^[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+$', msg):
                return True
            # Si contiene la palabra 'csrf' o 'token'
            if 'csrf' in msg.lower() or 'token' in msg.lower():
                return True
            return False
        if (message and not is_suspicious_message(message)) or image_url:
            add_chat_message(username, 'user', msg_text, image_url=image_url, order_id=order_id)
        # Registrar en user_purchases.json
        user_purchases = load_user_purchases()
        user_purchases.append({
            'order_id': order_id,
            'username': username,
            'items': new_order['items'],
            'total_price': total_price,
            'payment_method_id': 'contact_admin',
            'order_date': new_order['order_date'],
            'status': 'pending',
            'admin_message': message
        })
        save_user_purchases(user_purchases)
        clear_user_persistent_cart(username)
        flash('Tu solicitud ha sido enviada al administrador. Pronto te contactarán para finalizar la compra.', 'success')
        return redirect(url_for('user_auth.user_orders'))

    return render_template('contact_admin.html', cart_items=cart_items_details, total_price=total_price, chat_history=chat_history)

@app.route('/user/chat', methods=['GET', 'POST'])
@login_required
def user_chat():
    username = session.get('user_username')
    chat_history = get_user_chat(username)
    if request.method == 'POST':
        message = request.form.get('message')
        image_url = None
        if 'user_image' in request.files:
            file = request.files['user_image']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{username}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                image_url = f"/static/uploads/{filename}"
        # --- FILTRO DE MENSAJES: No guardar tokens ni cadenas sospechosas ---
        def is_suspicious_message(msg):
            if not msg:
                return False
            # Si es muy largo y sin espacios, probablemente es un token
            if len(msg) > 40 and ' ' not in msg:
                return True
            # Si parece un JWT o CSRF (muchos caracteres base64 y puntos)
            if re.match(r'^[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+$', msg):
                return True
            # Si contiene la palabra 'csrf' o 'token'
            if 'csrf' in msg.lower() or 'token' in msg.lower():
                return True
            return False
        if (message and not is_suspicious_message(message)) or image_url:
            add_chat_message(username, 'user', message, image_url=image_url)
            flash('Mensaje enviado al administrador.', 'success')
        else:
            flash('Mensaje inválido o sospechoso, no se ha enviado.', 'error')
        return redirect(url_for('user_chat'))
    return render_template('user_chat.html', chat_history=chat_history)

@app.route('/user/notifications')
@login_required
def user_notifications():
    username = session.get('user_username')
    notifications = load_notifications().get(username, [])
    return render_template('user_notifications.html', notifications=notifications)

@app.route('/user/notification_settings', methods=['GET', 'POST'])
@login_required
def notification_settings():
    username = session.get('user_username')
    users = load_users()
    user = users.get(username)
    if not user:
        flash('Usuario no encontrado.', 'error')
        return redirect(url_for('user_auth.user_dashboard'))
    if request.method == 'POST':
        notifications_enabled = request.form.get('notifications_enabled') == 'on'
        user['notifications_enabled'] = notifications_enabled
        users[username] = user
        save_users(users)
        flash('Preferencia de notificaciones actualizada.', 'success')
        return redirect(url_for('notification_settings'))
    notifications_enabled = user.get('notifications_enabled', True)
    return render_template('notification_settings.html', notifications_enabled=notifications_enabled)

@app.route('/admin/create_notification', methods=['GET', 'POST'])
@admin_required
def admin_create_notification():
    users = load_users()
    usernames = [u for u in users if users[u].get('role') != 'admin']
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        message = request.form.get('message', '').strip()
        notif_type = request.form.get('notif_type', 'info')
        target = request.form.get('target', 'all')
        if not title or not message:
            flash('Título y mensaje son obligatorios.', 'error')
            return redirect(url_for('admin_create_notification'))
        # Enviar a todos o a un usuario
        if target == 'all':
            for username in usernames:
                user = users[username]
                if user.get('notifications_enabled', True):
                    add_notification(username, message, notif_type, title=title)
            flash('Notificación enviada a todos los usuarios que aceptan notificaciones.', 'success')
        else:
            user = users.get(target)
            if user and user.get('notifications_enabled', True):
                add_notification(target, message, notif_type, title=title)
                flash(f'Notificación enviada a {target}.', 'success')
            else:
                flash('El usuario no existe o no acepta notificaciones.', 'error')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_create_notification.html', usernames=usernames)

def init_app():
    """Inicializa la aplicación Flask, incluyendo la configuración de usuarios y el registro de Blueprints."""
    init_admin_users()
    # Asegúrate de que los archivos de datos existan para evitar errores al cargarlos
    # Las funciones load_x() en data_manager.py deben manejar la creación de listas/diccionarios vacías
    # si los archivos no existen.

if __name__ == '__main__':
    init_app()
    app.run(debug=True)