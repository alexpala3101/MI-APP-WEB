# user_auth.py

from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify, abort
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
    load_notifications, save_notifications, load_user_carts, save_user_carts,
    USERS_FILE, NOTIFICATIONS_FILE, USER_CARTS_FILE
)
# Aquí también, importas estas funciones directamente desde data_manager
from data_manager import add_notification, get_cart
from data_manager_chat import get_user_chats_by_order
from user_forms import UserLoginForm, UserRegisterForm, UserEditProfileForm, UserChangePasswordForm


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
    form = UserRegisterForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip()
        full_name = form.full_name.data.strip()
        phone = form.phone.data.strip() if form.phone.data else ''
        birthdate = form.birthdate.data.strftime('%Y-%m-%d') if form.birthdate.data else ''
        gender = form.gender.data or ''
        password = form.password.data
        users = load_users()
        # Validaciones personalizadas (puedes mantener las existentes si quieres)
        if any(u_data['username'] == username for u_data in users.values()):
            flash('Nombre de usuario ya existe.', 'error')
            return render_template('user_register.html', form=form)
        if any(u_data['email'] == email for u_data in users.values()):
            flash('Este email ya está registrado.', 'error')
            return render_template('user_register.html', form=form)
        hashed_password = generate_password_hash(password)
        users[username] = {
            'username': username,
            'email': email,
            'full_name': full_name,
            'phone': phone,
            'birthdate': birthdate,
            'gender': gender,
            'password': hashed_password,
            'role': 'user',
            'registration_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'last_login': None,
            'is_active': True,
            'delivery_address': ''
        }
        save_users(users)
        flash('Registro exitoso. ¡Ahora puedes iniciar sesión!', 'success')
        return redirect(url_for('user_auth.login'))
    return render_template('user_register.html', form=form)

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Ruta para el inicio de sesión de usuarios."""
    form = UserLoginForm()
    if form.validate_on_submit():
        username_or_email = form.username.data.strip()
        password = form.password.data
        users = load_users()
        user = None
        for u_data in users.values():
            if u_data['username'] == username_or_email or u_data['email'] == username_or_email:
                user = u_data
                break
        if user and check_password_hash(user['password'], password):
            session.permanent = True
            session['user_logged_in'] = True
            session['user_username'] = user['username']
            session['user_email'] = user['email']
            user['last_login'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            save_users(users)
            flash(f'¡Bienvenido de nuevo, {user["username"]}!', 'success')
            return redirect(url_for('user_auth.user_dashboard'))
        else:
            flash('Usuario, email o contraseña incorrectos.', 'error')
    return render_template('user_login.html', form=form)

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
    """Permite al usuario editar sus datos personales y dirección."""
    username = session.get('user_username')
    users = load_users()
    user = users.get(username)
    form = UserEditProfileForm(obj=user)
    if not user:
        flash('Error al cargar los datos del usuario.', 'error')
        return redirect(url_for('user_auth.login'))
    if form.validate_on_submit():
        user['full_name'] = form.full_name.data.strip()
        user['email'] = form.email.data.strip()
        user['phone'] = form.phone.data.strip() if form.phone.data else ''
        user['birthdate'] = form.birthdate.data.strftime('%Y-%m-%d') if form.birthdate.data else ''
        user['gender'] = form.gender.data or ''
        users[username] = user
        save_users(users)
        flash('Perfil actualizado correctamente.', 'success')
        return redirect(url_for('user_auth.user_profile'))
    # Pre-cargar datos actuales si es GET
    if request.method == 'GET':
        form.full_name.data = user.get('full_name', '')
        form.email.data = user.get('email', '')
        form.phone.data = user.get('phone', '')
        if user.get('birthdate'):
            try:
                form.birthdate.data = datetime.strptime(user['birthdate'], '%Y-%m-%d').date()
            except Exception:
                form.birthdate.data = None
        form.gender.data = user.get('gender', '')
    return render_template('user_edit_profile.html', form=form)

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

@user_bp.route('/profile')
@login_required
def user_profile():
    """Muestra el perfil profesional del usuario con todos los datos personales."""
    username = session.get('user_username')
    users = load_users()
    user = users.get(username)
    if not user:
        flash('Error al cargar los datos del usuario.', 'error')
        return redirect(url_for('user_auth.login'))
    return render_template('user_profile.html', user=user)

@user_bp.route('/change_password', methods=['GET', 'POST'])
def user_change_password():
    """Permite al usuario cambiar su contraseña de forma segura."""
    username = session.get('user_username')
    users = load_users()
    user = users.get(username)
    form = UserChangePasswordForm()
    if not user:
        flash('Error: Usuario no encontrado.', 'error')
        return redirect(url_for('user_auth.login'))
    if form.validate_on_submit():
        current_password = form.current_password.data
        new_password = form.new_password.data
        if not check_password_hash(user['password'], current_password):
            flash('La contraseña actual es incorrecta.', 'error')
            return render_template('user_change_password.html', form=form)
        if check_password_hash(user['password'], new_password):
            flash('La nueva contraseña no puede ser igual a la anterior.', 'error')
            return render_template('user_change_password.html', form=form)
        user['password'] = generate_password_hash(new_password)
        save_users(users)
        flash('Contraseña actualizada correctamente.', 'success')
        return redirect(url_for('user_auth.user_profile'))
    return render_template('user_change_password.html', form=form)

@user_bp.route('/settings')
@login_required
def user_settings():
    """Muestra la página de configuración de cuenta del usuario."""
    return render_template('user_settings.html')

# --- RUTAS DE ADMINISTRACIÓN (ejemplo básico) ---
# Si estas rutas estaban aquí, deberían estar en un blueprint de administrador separado.
# Por el momento, asegúrate de que no haya duplicidad si ya tienes admin_users.py
# @user_bp.route('/admin')
# @admin_required
# def admin_panel():
#    return render_template('admin_panel.html')