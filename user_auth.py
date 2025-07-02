# user_auth.py

from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from functools import wraps
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import re
import secrets

# --- IMPORTACIONES DESDE data_manager.py ---
# Todas las funciones de carga y guardado de datos deben venir de aquí.
from data_manager import (
    load_users, save_users, load_products, save_products, load_orders, save_orders,
    load_notifications, save_notifications, load_payment_methods, save_payment_methods,
    load_user_carts, save_user_carts,
    USERS_FILE, NOTIFICATIONS_FILE, PAYMENT_METHODS_FILE, USER_CARTS_FILE
)
# Aquí también, importas estas funciones directamente desde data_manager
from data_manager import add_notification, get_cart, add_to_cart, remove_from_cart, update_cart_quantity, clear_user_persistent_cart
from data_manager_chat import get_user_chats_by_order


# Define CART_SESSION_KEY aquí también si es necesario para funciones de carrito internas
CART_SESSION_KEY = 'cart'

# Blueprint para la autenticación de usuarios
user_bp = Blueprint('user_auth', __name__)

# Decorador para requerir autenticación de usuario
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_logged_in'):
            flash('Necesitas iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('user_auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Funciones de utilidad para validación (pueden estar en un archivo de utilidades separado)
def is_valid_email(email):
    """Valida si la cadena es un email con un formato básico."""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def is_valid_password(password):
    """
    Valida la fortaleza de la contraseña:
    - Mínimo 8 caracteres, máximo 20.
    - Al menos una letra mayúscula, una minúscula, un número y un símbolo.
    """
    if not (8 <= len(password) <= 20):
        return False
    if not re.search(r"[a-z]", password): return False
    if not re.search(r"[A-Z]", password): return False
    if not re.search(r"\d", password): return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password): return False
    return True

@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Ruta para el registro de nuevos usuarios."""
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']

        users = load_users()

        # Validaciones
        if not username or not email or not password:
            flash('Todos los campos son obligatorios.', 'error')
            return render_template('user_register.html')
        
        if not (6 <= len(username) <= 20) or not username.isalnum():
            flash('El nombre de usuario debe tener entre 6 y 20 caracteres alfanuméricos.', 'error')
            return render_template('user_register.html', username=username, email=email)

        if any(u_data['username'] == username for u_data in users.values()):
            flash('Nombre de usuario ya existe.', 'error')
            return render_template('user_register.html', email=email) # Mantener email para comodidad

        if not is_valid_email(email):
            flash('Formato de email inválido.', 'error')
            return render_template('user_register.html', username=username) # Mantener username

        if any(u_data['email'] == email for u_data in users.values()):
            flash('Este email ya está registrado.', 'error')
            return render_template('user_register.html', username=username)

        if not is_valid_password(password):
            flash('La contraseña debe tener entre 8 y 20 caracteres, e incluir al menos una mayúscula, una minúscula, un número y un símbolo.', 'error')
            return render_template('user_register.html', username=username, email=email)

        # Hashear la contraseña antes de guardar
        hashed_password = generate_password_hash(password)

        # Guardar el usuario usando el username como clave
        users[username] = {
            'username': username,
            'email': email,
            'password': hashed_password, # Guardar el hash
            'role': 'user', # Rol por defecto
            'registration_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'last_login': None,
            'is_active': True,
            'delivery_address': '', # Dirección de entrega por defecto
            'payment_methods': [] # Métodos de pago vacíos por defecto
        }
        save_users(users)
        flash('Registro exitoso. ¡Ahora puedes iniciar sesión!', 'success')
        return redirect(url_for('user_auth.login'))
    return render_template('user_register.html')


@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Ruta para el inicio de sesión de usuarios."""
    if request.method == 'POST':
        username_or_email = request.form['username'].strip() # Aceptar usuario o email
        password = request.form['password']

        users = load_users()
        user = None

        # Intenta encontrar usuario por username o email
        for u_data in users.values():
            if u_data['username'] == username_or_email or u_data['email'] == username_or_email:
                user = u_data
                break

        if user:
            # Usar check_password_hash para verificar la contraseña
            # Compara la contraseña ingresada con el hash almacenado de forma segura
            if check_password_hash(user['password'], password):
                session.permanent = True # Hacer la sesión permanente
                session['user_logged_in'] = True
                session['user_username'] = user['username']
                session['user_email'] = user['email']
                user['last_login'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                save_users(users)
                flash(f'¡Bienvenido de nuevo, {user["username"]}!', 'success')
                return redirect(url_for('user_auth.user_dashboard'))
            else:
                flash('Contraseña incorrecta.', 'error')
        else:
            flash('Usuario o email no encontrado.', 'error')

    return render_template('user_login.html')

@user_bp.route('/dashboard')
@login_required
def user_dashboard():
    """Muestra el panel de control del usuario."""
    username = session.get('user_username')
    users = load_users()
    user = users.get(username) # Obtener todos los datos del usuario

    if not user:
        flash('Error al cargar los datos del usuario.', 'error')
        return redirect(url_for('user_auth.login'))

    return render_template('user_dashboard.html', username=username, user=user)

@user_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def user_edit_profile():
    """Permite al usuario editar su perfil."""
    username = session.get('user_username')
    users = load_users()
    user = users.get(username)

    if not user:
        flash('Error: Usuario no encontrado.', 'error')
        return redirect(url_for('user_auth.user_dashboard'))

    if request.method == 'POST':
        # Los campos de username y email no deben ser editables aquí si son usados para login
        # Si se permiten cambios, deben validarse cuidadosamente (ej. unicidad)
        new_email = request.form.get('email', '').strip()
        new_delivery_address = request.form.get('delivery_address', '').strip()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')

        # Validación de email
        if new_email and new_email != user['email']:
            if not is_valid_email(new_email):
                flash('Formato de email inválido.', 'error')
                return render_template('user_edit_profile.html', user=user)
            if any(u_data['email'] == new_email for u_data in users.values() if u_data['username'] != username):
                flash('Este email ya está en uso por otra cuenta.', 'error')
                return render_template('user_edit_profile.html', user=user)
            user['email'] = new_email

        user['delivery_address'] = new_delivery_address

        # Cambio de contraseña
        if new_password:
            if not current_password or not check_password_hash(user['password'], current_password):
                flash('Contraseña actual incorrecta.', 'error')
                return render_template('user_edit_profile.html', user=user)
            
            if not is_valid_password(new_password):
                flash('La nueva contraseña no cumple con los requisitos de seguridad.', 'error')
                return render_template('user_edit_profile.html', user=user)
            
            user['password'] = generate_password_hash(new_password)
            flash('Contraseña actualizada con éxito.', 'success')
        
        save_users(users)
        flash('Perfil actualizado con éxito.', 'success')
        # Actualizar email en sesión si ha cambiado
        if 'user_email' in session and session['user_email'] != user['email']:
            session['user_email'] = user['email']
            
        return redirect(url_for('user_auth.user_dashboard'))

    return render_template('user_edit_profile.html', user=user)

@user_bp.route('/orders')
@login_required
def user_orders():
    """Muestra el historial de pedidos del usuario."""
    username = session.get('user_username')
    all_orders = load_orders()
    # Filtrar órdenes para el usuario actual y ordenar por fecha descendente
    user_orders = [
        order for order in all_orders.values() 
        if order.get('username') == username
    ]
    user_orders_sorted = sorted(user_orders, key=lambda x: x.get('order_date', '0'), reverse=True)
    # Obtener los chats agrupados por order_id
    chats_por_pedido = get_user_chats_by_order(username)
    return render_template('user_orders.html', orders=user_orders_sorted, chats_por_pedido=chats_por_pedido)

@user_bp.route('/notifications')
@login_required
def user_notifications():
    """Muestra las notificaciones del usuario."""
    username = session.get('user_username')
    all_notifications = load_notifications()
    
    user_notifications_list = all_notifications.get(username, [])
    
    # Marcar todas las notificaciones como leídas cuando el usuario las ve
    if username in all_notifications:
        for notif in all_notifications[username]:
            notif['read'] = True
        save_notifications(all_notifications) # Guardar los cambios
    
    # Ordenar por fecha, las no leídas primero si se desea
    sorted_notifications = sorted(user_notifications_list, 
                                  key=lambda x: (x.get('read', False), x.get('timestamp', '0')), 
                                  reverse=True) # Las no leídas (False) irán primero si se invierte
                                                # Y luego por fecha descendente
    
    return render_template('user_notifications.html', notifications=sorted_notifications)

@user_bp.route('/notifications/mark_read/<int:index>', methods=['POST'])
@login_required
def mark_notification_read(index):
    username = session.get('user_username')
    all_notifications = load_notifications()
    
    if username in all_notifications and 0 <= index < len(all_notifications[username]):
        all_notifications[username][index]['read'] = True
        save_notifications(all_notifications)
        flash('Notificación marcada como leída.', 'success')
    else:
        flash('Notificación no encontrada.', 'error')
        
    return redirect(url_for('user_auth.user_notifications'))


@user_bp.route('/privacy')
@login_required
def user_privacy():
    """Muestra la página de política de privacidad y control de datos."""
    username = session.get('user_username')
    users = load_users()
    user_data = users.get(username)
    
    return render_template('user_privacy.html', user_data=user_data)


@user_bp.route('/privacy/delete_account', methods=['POST'])
@login_required
def delete_account():
    """Permite al usuario eliminar su cuenta."""
    username = session.get('user_username')
    users = load_users()

    if username in users:
        del users[username]
        save_users(users)
        session.pop('user_logged_in', None)
        session.pop('user_username', None)
        session.pop('user_email', None)
        flash('Tu cuenta ha sido eliminada permanentemente.', 'info')
        return redirect(url_for('home'))
    
    flash('Error al intentar eliminar la cuenta.', 'error')
    return redirect(url_for('user_auth.user_privacy'))

@user_bp.route('/payment_methods', methods=['GET'])
@login_required
def user_payment_methods():
    """Muestra los métodos de pago del usuario."""
    username = session.get('user_username')
    users = load_users()
    user = users.get(username)
    
    if not user:
        flash('Usuario no encontrado.', 'error')
        return redirect(url_for('user_auth.user_dashboard'))

    payment_methods = user.get('payment_methods', [])
    return render_template('user_payment_methods.html', payment_methods=payment_methods)

@user_bp.route('/payment_methods/add', methods=['GET', 'POST'])
@login_required
def add_payment_method():
    """Permite al usuario añadir un nuevo método de pago."""
    username = session.get('user_username')
    users = load_users()
    user = users.get(username)

    if not user:
        flash('Usuario no encontrado.', 'error')
        return redirect(url_for('user_auth.user_dashboard'))

    if request.method == 'POST':
        card_number = request.form.get('card_number', '').strip()
        card_holder = request.form.get('card_holder', '').strip()
        expiry_date = request.form.get('expiry_date', '').strip() # MM/AA
        cvv = request.form.get('cvv', '').strip()

        # Validaciones básicas (puedes añadir más regex para número de tarjeta, CVV, etc.)
        if not all([card_number, card_holder, expiry_date, cvv]):
            flash('Todos los campos son obligatorios.', 'error')
            return render_template('add_payment_method.html')

        if not re.fullmatch(r'\d{16}', card_number):
            flash('Número de tarjeta inválido (debe ser 16 dígitos).', 'error')
            return render_template('add_payment_method.html', card_holder=card_holder, expiry_date=expiry_date)
        
        if not re.fullmatch(r'\d{3,4}', cvv):
            flash('CVV inválido (3 o 4 dígitos).', 'error')
            return render_template('add_payment_method.html', card_holder=card_holder, expiry_date=expiry_date, card_number=card_number)

        # Aquí no se guardan datos sensibles directamente, solo una representación.
        # En una aplicación real, se usaría un proveedor de pagos.
        new_method = {
            'id': secrets.token_hex(6), # ID único para el método de pago
            'type': 'Tarjeta de Crédito/Débito',
            'last_four': card_number[-4:],
            'expiry_date': expiry_date,
            'holder_name': card_holder,
            'added_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        user_payment_methods = user.get('payment_methods', [])
        user_payment_methods.append(new_method)
        user['payment_methods'] = user_payment_methods
        
        if save_users(users):
            flash('Método de pago añadido con éxito.', 'success')
            return redirect(url_for('user_auth.user_payment_methods'))
        else:
            flash('Error al añadir el método de pago.', 'error')

    return render_template('add_payment_method.html')

@user_bp.route('/payment_methods/delete/<method_id>', methods=['POST'])
@login_required
def delete_payment_method(method_id):
    """Permite al usuario eliminar un método de pago existente."""
    username = session.get('user_username')
    users = load_users()
    user = users.get(username)

    if not user:
        flash('Usuario no encontrado.', 'error')
        return redirect(url_for('user_auth.user_dashboard'))

    updated_payment_methods = [
        method for method in user.get('payment_methods', []) 
        if method['id'] != method_id
    ]

    if len(updated_payment_methods) < len(user.get('payment_methods', [])):
        user['payment_methods'] = updated_payment_methods
        if save_users(users):
            flash('Método de pago eliminado con éxito.', 'success')
        else:
            flash('Error al eliminar el método de pago.', 'error')
    else:
        flash('Método de pago no encontrado o no autorizado para eliminar.', 'error')
    
    return redirect(url_for('user_auth.user_payment_methods'))


@user_bp.route('/logout')
def logout():
    """Cierra la sesión del usuario."""
    session.pop('user_logged_in', None)
    session.pop('user_username', None)
    session.pop('user_email', None)
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('home'))

@user_bp.route('/get_unread_notifications_count')
@login_required
def get_unread_notifications_count():
    """Devuelve el número de notificaciones no leídas para el usuario."""
    username = session.get('user_username')
    all_notifications = load_notifications()
    user_notifications = all_notifications.get(username, [])
    unread_count = sum(1 for notif in user_notifications if not notif.get('read', False))
    return jsonify(count=unread_count)

@user_bp.route('/orders/delete/<order_id>', methods=['POST'])
@login_required
def delete_order(order_id):
    """Permite al usuario cancelar/borrar un pedido propio si es suyo y está pendiente."""
    username = session.get('user_username')
    orders = load_orders()
    order = orders.get(order_id)
    if not order or order.get('username') != username:
        flash('No tienes permiso para cancelar este pedido.', 'error')
        return redirect(url_for('user_auth.user_orders'))
    if order.get('status') != 'pending':
        flash('Solo puedes cancelar pedidos pendientes.', 'warning')
        return redirect(url_for('user_auth.user_orders'))
    # Eliminar el pedido
    del orders[order_id]
    save_orders(orders)
    # Eliminar de user_purchases.json si existe
    try:
        from app import load_user_purchases, save_user_purchases
        purchases = load_user_purchases()
        purchases = [p for p in purchases if p.get('order_id') != order_id]
        save_user_purchases(purchases)
    except Exception:
        pass
    flash('Pedido cancelado correctamente.', 'success')
    return redirect(url_for('user_auth.user_orders'))

# --- RUTAS DE ADMINISTRACIÓN (ejemplo básico) ---
# Si estas rutas estaban aquí, deberían estar en un blueprint de administrador separado.
# Por el momento, asegúrate de que no haya duplicidad si ya tienes admin_users.py
# @user_bp.route('/admin')
# @admin_required
# def admin_panel():
#    return render_template('admin_panel.html')