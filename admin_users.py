# admin_users.py
from flask import Blueprint, render_template_string, redirect, url_for, flash, session
import json
import os
from functools import wraps

# Importa funciones de user_auth.py para manejar los datos de usuario
from user_auth import load_users, save_users, USERS_FILE

admin_users_bp = Blueprint('admin_users', __name__)

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

# Plantilla HTML para la gestión de usuarios (ahora enlaza CSS externo)
ADMIN_USERS_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <!-- Enlace a Tailwind CSS CDN -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css" rel="stylesheet">
    <!-- Enlace a tu archivo CSS personalizado -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ title }}</h1>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <ul class="flash-messages">
                    {% for category, message in messages %}
                        <li class="{{ category }}">{{ message }}</li>
                    {% endfor %}
                </ul>
            {% endif %}
        {% endwith %}

        <div class="table-container">
            <table class="styled-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Nombre de Usuario</th>
                        <th>Email</th>
                        <th>Fecha de Registro</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    {% for user in users %}
                    <tr>
                        <td>{{ loop.index }}</td>
                        <td>{{ user.username }}</td>
                        <td>{{ user.email }}</td>
                        <td>{{ user.registration_date }}</td>
                        <td>
                            <form action="{{ url_for('admin_users.delete_user', username=user.username) }}" method="POST" onsubmit="return confirm('¿Estás seguro de que quieres eliminar a {{ user.username }}?');">
                                <button type="submit" class="btn-delete">Eliminar</button>
                            </form>
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="5" class="text-center">No hay usuarios registrados.</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <div class="text-center mt-6">
            <a href="{{ url_for('admin_dashboard') }}" class="inline-block bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded transition duration-300">
                Volver al Panel de Administrador
            </a>
        </div>
    </div>
</body>
</html>
"""

@admin_users_bp.route('/admin/users')
@admin_required
def manage_users():
    """
    Muestra una lista de todos los usuarios registrados en el sistema.
    """
    users = load_users()
    # Convierte el diccionario de usuarios a una lista para facilitar la iteración en la plantilla
    users_list = list(users.values())
    return render_template_string(ADMIN_USERS_TEMPLATE, title="Gestión de Usuarios", users=users_list)

@admin_users_bp.route('/admin/users/delete/<string:username>', methods=['POST'])
@admin_required
def delete_user(username):
    """
    Gestiona la eliminación de un usuario por su nombre de usuario.
    """
    users = load_users()
    if username in users:
        del users[username]
        if save_users(users):
            flash(f'¡Usuario "{username}" eliminado exitosamente!', 'success')
        else:
            flash(f'Error al eliminar el usuario "{username}".', 'error')
    else:
        flash(f'No se pudo eliminar el usuario "{username}" porque no fue encontrado.', 'error')

    return redirect(url_for('admin_users.manage_users'))

def create_admin_users_routes(app):
    """
    Registra el blueprint de gestión de usuarios de administrador en la aplicación Flask.
    """
    app.register_blueprint(admin_users_bp)
