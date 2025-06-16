# user_auth.py
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from functools import wraps
from datetime import datetime
import hashlib
import json
import os
import re
import secrets

# Archivos simulados de base de datos
USERS_FILE = 'usuarios_register.json'
NOTIFICATIONS_FILE = 'notifications.json'
PAYMENT_METHODS_FILE = 'payment_methods.json'
USER_CARTS_FILE = 'user_carts.json' 

# Define CART_SESSION_KEY aquí también, ya que las funciones de carrito lo necesitan.
CART_SESSION_KEY = 'cart'

# Blueprint para la autenticación de usuarios
user_bp = Blueprint('user_auth', __name__)

# Importar funciones necesarias desde app.py para evitar duplicación de lógica de carga de datos
try:
    from app import load_products 
except ImportError:
    # Fallback si load_products no puede ser importado
    def load_products():
        if not os.path.exists('products.json'):
            return []
        try:
            with open('products.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error al cargar productos en user_auth.py (fallback): {e}")
            return []

try:
    from app import load_orders 
except ImportError:
    # Fallback si load_orders no puede ser importado
    def load_orders():
        if not os.path.exists('user_orders.json'):
            return []
        try:
            with open('user_orders.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error al cargar pedidos en user_auth.py (fallback): {e}")
            return []


def load_users():
    """Carga los usuarios desde el archivo JSON."""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar usuarios: {e}")
            return {} 
    return {}

def save_users(users):
    """Guarda los usuarios en el archivo JSON."""
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error al guardar usuarios: {e}")
        return False

def hash_password(password):
    """Hashea una contraseña con un salt aleatorio."""
    salt = secrets.token_hex(32)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
    return f"{salt}:{password_hash}"

def verify_password(stored_password, provided_password):
    """Verifica una contraseña proporcionada contra una contraseña hasheada almacenada."""
    try:
        salt, stored_hash = stored_password.split(':')
        provided_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
        return provided_hash == stored_hash
    except ValueError: 
        return False

def user_required(f):
    """
    Decorador para asegurar que el usuario está logueado.
    Redirige al inicio de sesión de usuario si no está autenticado.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_logged_in' not in session:
            flash('Debes iniciar sesión para ver esta página.', 'error')
            return redirect(url_for('user_auth.user_login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Funciones para manejar Notificaciones ---
def load_notifications():
    """Carga las notificaciones desde el archivo JSON."""
    if not os.path.exists(NOTIFICATIONS_FILE):
        initial_notifications = [
            {"id": 1, "user_username": "usuario1", "type": "oferta", "title": "¡Oferta Semanal!", "message": "25% de descuento en todos los auriculares gaming.", "timestamp": "2024-06-14 10:00:00", "read": False},
            {"id": 2, "user_username": "usuario2", "type": "actualizacion", "title": "Mejoras en la App", "message": "Hemos actualizado la interfaz de usuario para una mejor experiencia.", "timestamp": "2024-06-15 09:30:00", "read": False},
            {"id": 3, "user_username": "usuario1", "type": "compra", "title": "Tu pedido #1234 ha sido enviado", "message": "Tu laptop gaming está en camino. ¡Revisa el seguimiento!", "timestamp": "2024-06-15 14:00:00", "read": False}
        ]
        try:
            with open(NOTIFICATIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(initial_notifications, f, indent=2, ensure_ascii=False)
            print("Archivo de notificaciones inicializado con datos de ejemplo.")
            return initial_notifications
        except Exception as e:
            print(f"Error al inicializar el archivo de notificaciones: {e}")
            return []
    try:
        with open(NOTIFICATIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error al cargar notificaciones: {e}")
        return []

def save_notifications(notifications):
    """Guarda las notificaciones en el archivo JSON."""
    try:
        with open(NOTIFICATIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(notifications, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error al guardar notificaciones: {e}")
        return False

def add_notification(user_username, notification_type, title, message, related_id=None):
    """Añade una nueva notificación para un usuario específico."""
    notifications = load_notifications()
    new_id = 1
    if notifications:
        new_id = max(n['id'] for n in notifications) + 1
    
    new_notification = {
        "id": new_id,
        "user_username": user_username,
        "type": notification_type,
        "title": title,
        "message": message,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "read": False
    }
    if related_id:
        new_notification['related_id'] = related_id 
    
    notifications.append(new_notification)
    return save_notifications(notifications)

# --- Funciones para manejar Métodos de Pago ---
def load_payment_methods():
    """Carga los métodos de pago desde el archivo JSON."""
    if not os.path.exists(PAYMENT_METHODS_FILE):
        with open(PAYMENT_METHODS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2, ensure_ascii=False)
        return []
    try:
        with open(PAYMENT_METHODS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error al cargar métodos de pago: {e}")
        return []

def save_payment_methods(methods):
    """Guarda los métodos de pago en el archivo JSON."""
    try:
        with open(PAYMENT_METHODS_FILE, 'w', encoding='utf-8') as f:
            json.dump(methods, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error al guardar métodos de pago: {e}")
        return False

# --- Funciones para manejar Carritos Persistentes ---
def load_user_carts():
    """Carga todos los carritos de usuario desde el archivo JSON."""
    if not os.path.exists(USER_CARTS_FILE):
        with open(USER_CARTS_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=2, ensure_ascii=False) 
        return {}
    try:
        with open(USER_CARTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error al cargar carritos de usuario: {e}")
        return {}

def save_user_carts(all_carts):
    """Guarda todos los carritos de usuario en el archivo JSON."""
    try:
        with open(USER_CARTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_carts, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error al guardar carritos de usuario: {e}")
        return False

def get_cart():
    """Obtiene el carrito actual del usuario desde la sesión, o desde el archivo persistente si no está en sesión."""
    if 'user_logged_in' in session and session.get('user_username'):
        username = session['user_username']
        if CART_SESSION_KEY not in session: 
            all_carts = load_user_carts()
            session[CART_SESSION_KEY] = all_carts.get(username, {})
        return session.get(CART_SESSION_KEY, {})
    else:
        return session.get(CART_SESSION_KEY, {})

def add_to_cart(product_id, quantity=1):
    """Agrega un producto al carrito y lo guarda de forma persistente si el usuario está logueado."""
    cart = get_cart() 
    product_id_str = str(product_id)

    products = load_products() 
    product = next((p for p in products if p['id'] == int(product_id_str)), None)

    if not product:
        flash('Producto no encontrado.', 'error')
        return

    if product['stock'] < quantity:
        flash(f'No hay suficiente stock para {product["name"]}. Stock disponible: {product["stock"]}.', 'error')
        return
    
    if product_id_str in cart:
        if cart[product_id_str]['quantity'] + quantity > product['stock']:
            flash(f'No se puede agregar más de {product["stock"]} unidades de {product["name"]} al carrito.', 'error')
            return
        cart[product_id_str]['quantity'] += quantity
    else:
        cart[product_id_str] = {
            'name': product['name'],
            'price': product['price'],
            'quantity': quantity,
            'image_url': product['image_url']
        }
    
    session[CART_SESSION_KEY] = cart 
    session.permanent = True 
    
    if 'user_logged_in' in session and session.get('user_username'):
        username = session['user_username']
        all_carts = load_user_carts()
        all_carts[username] = cart 
        save_user_carts(all_carts) 
    
    flash(f'"{product["name"]}" se ha agregado al carrito.', 'success')

def remove_from_cart(product_id):
    """Elimina un producto del carrito y lo guarda de forma persistente si el usuario está logueado."""
    cart = get_cart()
    product_id_str = str(product_id)
    if product_id_str in cart:
        del cart[product_id_str]
        session[CART_SESSION_KEY] = cart
        
        if 'user_logged_in' in session and session.get('user_username'):
            username = session['user_username']
            all_carts = load_user_carts()
            all_carts[username] = cart
            save_user_carts(all_carts)
        
        flash('Producto eliminado del carrito.', 'info')
    else:
        flash('El producto no se encontró en el carrito.', 'error')

def update_cart_quantity(product_id, new_quantity):
    """Actualiza la cantidad de un producto en el carrito y lo guarda de forma persistente si el usuario está logueado."""
    cart = get_cart()
    product_id_str = str(product_id)
    
    products = load_products() 
    product_in_db = next((p for p in products if p['id'] == int(product_id_str)), None)

    if product_id_str in cart and product_in_db:
        if new_quantity <= 0:
            remove_from_cart(product_id) 
            return

        if new_quantity > product_in_db['stock']:
            flash(f'Solo hay {product_in_db["name"]} disponibles en stock: {product_in_db["stock"]}.', 'error')
            cart[product_id_str]['quantity'] = product_in_db['stock']
        else:
            cart[product_id_str]['quantity'] = new_quantity
        
        session[CART_SESSION_KEY] = cart
        
        if 'user_logged_in' in session and session.get('user_username'):
            username = session['user_username']
            all_carts = load_user_carts()
            all_carts[username] = cart
            save_user_carts(all_carts)
        
        flash(f'Cantidad de "{product_in_db["name"]}" actualizada a {new_quantity}.', 'success')
    else:
        flash('Producto no encontrado en el carrito.', 'error')

def clear_user_persistent_cart(username):
    """Limpia el carrito persistente de un usuario específico."""
    all_carts = load_user_carts()
    if username in all_carts:
        all_carts[username] = {} 
        save_user_carts(all_carts)

# --- Rutas para el Blueprint de Usuario ---

@user_bp.route('/user/register', methods=['GET', 'POST'])
def user_register():
    """
    Maneja el registro de nuevos usuarios.
    Incluye validación de entrada para usuario, email y contraseña.
    """
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']
        email = request.form['email']
        # NUEVO: Campo de dirección de entrega al registrarse
        delivery_address = request.form.get('delivery_address', '').strip()

        users = load_users()

        if not (6 <= len(username) <= 20 and username.isalnum()):
            flash('El nombre de usuario debe tener entre 6 y 20 caracteres alfanuméricos.', 'error')
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash('Formato de email inválido.', 'error')
        elif not (8 <= len(password) <= 20 and
                  re.search(r'[a-z]', password) and
                  re.search(r'[A-Z]', password) and
                  re.search(r'[0-9]', password) and
                  re.search(r'[!@#$%^&*(),.?":{}|<>]', password)):
            flash('La contraseña debe tener entre 8 y 20 caracteres, e incluir mayúsculas, minúsculas, números y símbolos.', 'error')
        elif username in users:
            flash('El nombre de usuario ya existe. Por favor, elige otro.', 'error')
        elif any(u['email'] == email for u in users.values()):
            flash('El email ya está registrado. Por favor, utiliza otro.', 'error')
        else:
            hashed_password = hash_password(password)
            users[username] = {
                'username': username,
                'password': hashed_password,
                'email': email,
                'registration_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'delivery_address': delivery_address # Guardar la dirección
            }
            if save_users(users):
                flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
                return redirect(url_for('user_auth.user_login'))
            else:
                flash('Error al guardar el usuario. Inténtalo de nuevo.', 'error')
    
    return render_template('user_register.html')

@user_bp.route('/user/login', methods=['GET', 'POST'])
def user_login():
    """
    Maneja el inicio de sesión de usuario.
    Verifica las credenciales y establece la sesión.
    Después del login exitoso, carga el carrito persistente del usuario en la sesión.
    """
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']
        users = load_users()

        if username in users and verify_password(users[username]['password'], password):
            session['user_logged_in'] = True
            session['user_username'] = username
            
            all_carts = load_user_carts()
            session[CART_SESSION_KEY] = all_carts.get(username, {}) 
            
            flash('¡Inicio de sesión exitoso!', 'success')
            return redirect(url_for('user_auth.user_dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
            
    return render_template('user_login.html')

@user_bp.route('/user/dashboard')
@user_required
def user_dashboard():
    """
    Muestra el panel de usuario.
    Requiere que el usuario esté logueado.
    """
    username = session['user_username']
    users = load_users()
    user = users.get(username)
    if user:
        return render_template('user_dashboard.html', user=user)
    flash('No se encontró la información del usuario.', 'error')
    return redirect(url_for('user_auth.user_login'))

@user_bp.route('/user/logout')
@user_required
def user_logout():
    """
    Cierra la sesión del usuario.
    Antes de cerrar, guarda el carrito de la sesión en el almacenamiento persistente.
    """
    if 'user_username' in session and CART_SESSION_KEY in session: 
        username = session['user_username']
        all_carts = load_user_carts()
        all_carts[username] = session[CART_SESSION_KEY] 
        save_user_carts(all_carts)

    session.pop('user_logged_in', None)
    session.pop('user_username', None)
    session.pop(CART_SESSION_KEY, None) 
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('home'))

@user_bp.route('/user/profile')
@user_required
def user_profile():
    """
    Muestra la página de perfil del usuario.
    """
    username = session['user_username']
    users = load_users()
    user = users.get(username)
    if not user:
        flash('No se pudo cargar el perfil del usuario.', 'error')
        return redirect(url_for('user_auth.user_dashboard'))

    # Ahora renderiza el archivo user_profile.html
    return render_template('user_profile.html', user=user)

@user_bp.route('/user/profile/edit', methods=['GET', 'POST']) # NUEVA RUTA PARA EDITAR PERFIL
@user_required
def user_edit_profile():
    """
    Permite al usuario editar su información de perfil, incluyendo la dirección de entrega.
    """
    username = session['user_username']
    users = load_users()
    user = users.get(username)

    if not user:
        flash('Error: No se encontró tu perfil de usuario.', 'error')
        return redirect(url_for('user_auth.user_dashboard'))

    if request.method == 'POST':
        new_email = request.form.get('email', '').strip()
        new_delivery_address = request.form.get('delivery_address', '').strip()

        # Validaciones para el email (si se cambia)
        if new_email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', new_email):
            flash('Formato de email inválido.', 'error')
            return redirect(url_for('user_auth.user_edit_profile'))
        
        # Verificar si el nuevo email ya está en uso por otro usuario
        if new_email and new_email != user['email']:
            if any(u['email'] == new_email for u_username, u in users.items() if u_username != username):
                flash('El email ya está registrado por otro usuario.', 'error')
                return redirect(url_for('user_auth.user_edit_profile'))

        user['email'] = new_email if new_email else user['email'] # Actualizar solo si se proporciona
        user['delivery_address'] = new_delivery_address # Siempre actualizar la dirección (puede ser vacía)

        if save_users(users):
            flash('¡Perfil actualizado exitosamente!', 'success')
            return redirect(url_for('user_auth.user_profile'))
        else:
            flash('Error al actualizar el perfil. Inténtalo de nuevo.', 'error')

    return render_template('user_edit_profile.html', user=user)


@user_bp.route('/user/settings')
@user_required
def user_settings():
    """
    Muestra la página de configuración de la cuenta del usuario.
    """
    return render_template('user_settings.html')

@user_bp.route('/user/change_password', methods=['GET', 'POST'])
@user_required
def user_change_password():
    """
    Permite al usuario cambiar su contraseña.
    """
    username = session['user_username']
    users = load_users()
    user = users.get(username)

    if not user:
        flash('Error: No se encontró tu perfil de usuario.', 'error')
        return redirect(url_for('user_auth.user_settings'))

    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_new_password = request.form['confirm_new_password']

        if not verify_password(user['password'], current_password):
            flash('La contraseña actual es incorrecta.', 'error')
        elif not (8 <= len(new_password) <= 20 and
                  re.search(r'[a-z]', new_password) and
                  re.search(r'[A-Z]', new_password) and
                  re.search(r'[0-9]', new_password) and
                  re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password)):
            flash('La nueva contraseña debe tener entre 8 y 20 caracteres, e incluir mayúsculas, minúsculas, números y símbolos.', 'error')
        elif new_password != confirm_new_password:
            flash('La nueva contraseña y la confirmación no coinciden.', 'error')
        else:
            user['password'] = hash_password(new_password)
            if save_users(users):
                flash('¡Contraseña actualizada exitosamente!', 'success')
                return redirect(url_for('user_auth.user_settings'))
            else:
                flash('Error al guardar la nueva contraseña. Inténtalo de nuevo.', 'error')

    return render_template('user_change_password.html')

@user_bp.route('/user/notifications') 
@user_required
def user_notifications():
    """
    Muestra la página de notificaciones del usuario.
    """
    username = session['user_username']
    all_notifications = load_notifications()
    user_notifications = sorted(
        [n for n in all_notifications if n['user_username'] == username],
        key=lambda x: x['timestamp'],
        reverse=True
    )
    return render_template('user_notifications.html', notifications=user_notifications)

@user_bp.route('/user/notifications/mark_read/<int:notification_id>', methods=['POST']) 
@user_required
def mark_notification_read(notification_id):
    """
    Marca una notificación específica como leída.
    """
    notifications = load_notifications()
    for notification in notifications:
        if notification['id'] == notification_id and notification['user_username'] == session['user_username']:
            notification['read'] = True
            save_notifications(notifications)
            return jsonify(success=True)
    return jsonify(success=False, message="Notificación no encontrada o no autorizada"), 404

@user_bp.route('/user/notifications/delete/<int:notification_id>', methods=['POST']) 
@user_required
def delete_notification(notification_id):
    """
    Elimina una notificación específica.
    """
    notifications = load_notifications()
    initial_count = len(notifications)
    notifications = [n for n in notifications if not (n['id'] == notification_id and n['user_username'] == session['user_username'])]
    
    if len(notifications) < initial_count:
        save_notifications(notifications)
        return jsonify(success=True)
    return jsonify(success=False, message="Notificación no encontrada o no autorizada"), 404

@user_bp.route('/user/payment_methods')
@user_required
def user_payment_methods():
    """
    Muestra la página de métodos de pago del usuario.
    """
    username = session['user_username']
    all_payment_methods = load_payment_methods()
    user_payment_methods = [
        method for method in all_payment_methods if method['user_username'] == username
    ]
    return render_template('user_payment_methods.html', payment_methods=user_payment_methods)

@user_bp.route('/user/payment_methods/add', methods=['GET', 'POST'])
@user_required
def user_add_payment_method():
    """
    Maneja la adición de un nuevo método de pago (Nequi o Bancolombia).
    """
    if request.method == 'POST':
        username = session['user_username']
        method_type = request.form.get('method_type')
        account_number = request.form.get('account_number')
        account_holder = request.form.get('account_holder')

        if not all([method_type, account_number, account_holder]):
            flash('Por favor, completa todos los campos.', 'error')
        elif method_type not in ['nequi', 'bancolombia']:
            flash('Tipo de método de pago no válido.', 'error')
        else:
            all_payment_methods = load_payment_methods()
            new_id = 1
            if all_payment_methods:
                new_id = max(m['id'] for m in all_payment_methods) + 1
            
            new_method = {
                "id": new_id,
                "user_username": username,
                "type": method_type,
                "account_number": account_number,
                "account_holder": account_holder,
                "added_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            all_payment_methods.append(new_method)
            
            if save_payment_methods(all_payment_methods):
                flash(f'¡Cuenta de {method_type.capitalize()} agregada exitosamente!', 'success')
                return redirect(url_for('user_auth.user_payment_methods'))
            else:
                flash('Error al agregar el método de pago. Inténtalo de nuevo.', 'error')

    return render_template('user_add_payment_method.html')

@user_bp.route('/user/payment_methods/delete/<int:method_id>', methods=['POST']) 
@user_required
def user_delete_payment_method(method_id):
    """
    Elimina un método de pago.
    """
    username = session['user_username']
    all_payment_methods = load_payment_methods()
    
    initial_count = len(all_payment_methods)
    all_payment_methods = [
        m for m in all_payment_methods if not (m['id'] == method_id and m['user_username'] == username)
    ]

    if len(all_payment_methods) < initial_count: 
        if save_payment_methods(all_payment_methods):
            flash('Método de pago eliminado exitosamente.', 'info')
            return jsonify(success=True)
        else:
            flash('Error al eliminar el método de pago.', 'error')
            return jsonify(success=False), 500
    else:
        flash('Método de pago no encontrado o no autorizado.', 'error')
        return jsonify(success=False), 404

@user_bp.route('/user/orders') 
@user_required
def user_orders():
    """
    Muestra la página de pedidos del usuario.
    """
    username = session['user_username']
    all_orders = load_orders() 
    user_orders_list = sorted(
        [order for order in all_orders if order.get('user_username') == username],
        key=lambda x: x.get('timestamp', ''), 
        reverse=True
    )
    return render_template('user_orders.html', orders=user_orders_list)

@user_bp.route('/user/privacy')
@user_required
def user_privacy():
    """
    Muestra la página de privacidad del usuario.
    """
    return render_template('user_privacy.html')
