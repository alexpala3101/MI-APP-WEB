# data_manager.py

import json
import os
from datetime import datetime
import secrets
import logging

# Configuración del logging para data_manager
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Rutas de Archivos de Datos ---
# Asegúrate de que estos nombres de archivo sean los que realmente usas.
# Si quieres guardar estos archivos en una carpeta 'data', puedes ajustar las rutas.
DATA_DIR = 'data' # Puedes crear una carpeta 'data' en tu proyecto

USERS_FILE = os.path.join(DATA_DIR, 'users.json')
PRODUCTS_FILE = os.path.join(DATA_DIR, 'products.json')
ORDERS_FILE = os.path.join(DATA_DIR, 'orders.json')
NOTIFICATIONS_FILE = os.path.join(DATA_DIR, 'notifications.json')
PAYMENT_METHODS_FILE = os.path.join(DATA_DIR, 'payment_methods.json')
USER_CARTS_FILE = os.path.join(DATA_DIR, 'user_carts.json')
REPORTS_FILE = os.path.join(DATA_DIR, 'reports.json')

# Asegurarse de que el directorio DATA_DIR exista
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# --- Funciones de Carga y Guardado Genéricas ---

def _load_data(filepath, default_value={}):
    """Carga datos desde un archivo JSON. Retorna el valor por defecto si el archivo no existe o está vacío."""
    if not os.path.exists(filepath):
        logger.info(f"Archivo no encontrado: {filepath}. Se creará con valor por defecto.")
        _save_data(filepath, default_value) # Crear el archivo vacío
        return default_value
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Asegurarse de que el tipo de dato cargado coincide con el valor por defecto
            if not isinstance(data, type(default_value)):
                logger.warning(f"Contenido de {filepath} no es del tipo esperado. Se inicializará con valor por defecto.")
                return default_value
            return data
    except json.JSONDecodeError:
        logger.error(f"Error al decodificar JSON desde {filepath}. El archivo podría estar corrupto. Se reiniciará con valor por defecto.")
        return default_value # Reiniciar si el JSON está corrupto
    except Exception as e:
        logger.error(f"Error inesperado al cargar {filepath}: {e}. Se reiniciará con valor por defecto.")
        return default_value

def _save_data(filepath, data):
    """Guarda datos en un archivo JSON."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error al guardar datos en {filepath}: {e}")
        return False

# --- Funciones Específicas de Carga y Guardado ---

def load_users():
    return _load_data(USERS_FILE, default_value={})

def save_users(users):
    return _save_data(USERS_FILE, users)

def load_products():
    return _load_data(PRODUCTS_FILE, default_value={})

def save_products(products):
    return _save_data(PRODUCTS_FILE, products)

def load_orders():
    return _load_data(ORDERS_FILE, default_value={})

def save_orders(orders):
    return _save_data(ORDERS_FILE, orders)

def load_notifications():
    return _load_data(NOTIFICATIONS_FILE, default_value={})

def save_notifications(notifications):
    return _save_data(NOTIFICATIONS_FILE, notifications)

def load_payment_methods():
    return _load_data(PAYMENT_METHODS_FILE, default_value={})

def save_payment_methods(payment_methods):
    return _save_data(PAYMENT_METHODS_FILE, payment_methods)

def load_user_carts():
    return _load_data(USER_CARTS_FILE, default_value={})

def save_user_carts(user_carts):
    return _save_data(USER_CARTS_FILE, user_carts)

def load_reports():
    return _load_data(REPORTS_FILE, default_value={})

def save_reports(reports):
    return _save_data(REPORTS_FILE, reports)

# --- Funciones de Utilidad (Notificaciones y Carrito) ---

def add_notification(username, message, notif_type='info'):
    """Añade una notificación para un usuario específico."""
    notifications = load_notifications()
    if username not in notifications:
        notifications[username] = []
    
    new_notification = {
        'id': str(secrets.token_hex(4)),
        'message': message,
        'type': notif_type, # 'info', 'success', 'warning', 'error', 'actualizacion', 'registro'
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'read': False
    }
    notifications[username].append(new_notification)
    return save_notifications(notifications)

def get_cart(username=None):
    """
    Obtiene el carrito de compras. Si se proporciona un nombre de usuario,
    intenta cargar el carrito persistente; de lo contrario, usa la sesión.
    """
    from flask import session # Importar aquí para evitar importación circular

    if username:
        user_carts = load_user_carts()
        return user_carts.get(username, {})
    else:
        return session.get('cart', {})

def add_to_cart(product_id, quantity=1, username=None):
    """Añade un producto al carrito."""
    from flask import session # Importar aquí para evitar importación circular

    if username:
        user_carts = load_user_carts()
        cart = user_carts.get(username, {})
        cart[product_id] = cart.get(product_id, 0) + quantity
        user_carts[username] = cart
        return save_user_carts(user_carts)
    else:
        cart = session.get('cart', {})
        cart[product_id] = cart.get(product_id, 0) + quantity
        session['cart'] = cart
        return True # La sesión se guarda automáticamente por Flask

def remove_from_cart(product_id, username=None):
    """Elimina un producto del carrito."""
    from flask import session # Importar aquí para evitar importación circular

    if username:
        user_carts = load_user_carts()
        cart = user_carts.get(username, {})
        if product_id in cart:
            del cart[product_id]
        user_carts[username] = cart
        return save_user_carts(user_carts)
    else:
        cart = session.get('cart', {})
        if product_id in cart:
            del cart[product_id]
        session['cart'] = cart
        return True # La sesión se guarda automáticamente por Flask

def update_cart_quantity(product_id, new_quantity, username=None):
    """Actualiza la cantidad de un producto en el carrito."""
    from flask import session # Importar aquí para evitar importación circular

    if new_quantity <= 0:
        return remove_from_cart(product_id, username)
    
    if username:
        user_carts = load_user_carts()
        cart = user_carts.get(username, {})
        cart[product_id] = new_quantity
        user_carts[username] = cart
        return save_user_carts(user_carts)
    else:
        cart = session.get('cart', {})
        cart[product_id] = new_quantity
        session['cart'] = cart
        return True # La sesión se guarda automáticamente por Flask

def clear_user_persistent_cart(username):
    """Limpia el carrito persistente de un usuario."""
    if not username:
        return False
    user_carts = load_user_carts()
    if username in user_carts:
        user_carts[username] = {} # Establece el carrito del usuario como vacío
        return save_user_carts(user_carts)
    return True # Considerar exitoso si no había carrito para el usuario