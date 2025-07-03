# admin_users.py - Admin User Management Blueprint
from flask import Blueprint, render_template_string, redirect, url_for, flash, session
import json
import os
from functools import wraps
from admin_delete_forms import AdminDeleteUserForm

# --- IMPORTACIONES DESDE data_manager.py ---
# Ahora importamos directamente desde data_manager.py
from data_manager import load_users, save_users, USERS_FILE # USERS_FILE también debe venir de data_manager

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
    <link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="bg-gray-100 font-sans">
    <div class="container mx-auto p-8">
        <div class="flex justify-between items-center bg-white shadow-md rounded-lg p-6 mb-8">
            <h1 class="text-3xl font-bold text-gray-800">{{ title }}</h1>
            <a href="{{ url_for('admin_dashboard') }}" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition duration-300">
                <i class="fas fa-tachometer-alt mr-2"></i>Ir al Dashboard
            </a>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="mb-6">
                    {% for category, message in messages %}
                        <div class="p-4 rounded-md {% if category == 'success' %}bg-green-100 text-green-800{% elif category == 'error' %}bg-red-100 text-red-800{% else %}bg-blue-100 text-blue-800{% endif %}">
                            {{ message }}
                        </div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}

        <div class="bg-white shadow-md rounded-lg p-6">
            <h2 class="text-2xl font-semibold text-gray-800 mb-4">Lista de Usuarios</h2>
            {% if users %}
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Usuario
                            </th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Email
                            </th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Fecha de Registro
                            </th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Acciones
                            </th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        {% for user in users %}
                        <tr>
                            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                {{ user.username }}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                                {{ user.email }}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                                {{ user.registration_date }}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                <form action="{{ url_for('admin_users.delete_user', username=user.username) }}" method="POST" onsubmit="return confirm('¿Estás seguro de que quieres eliminar al usuario {{ user.username }}?');">
                                    {{ delete_forms[user.username].hidden_tag() }}
                                    <button type="submit" class="text-red-600 hover:text-red-900">Eliminar</button>
                                </form>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% else %}
            <p class="text-gray-600 text-center py-4">No hay usuarios registrados.</p>
            {% endif %}
        </div>
        
        <div class="text-center mt-8">
            <a href="{{ url_for('admin_dashboard') }}" class="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded transition duration-300">
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
    users = load_users() # Ahora se llama a la función de data_manager.py
    # Convierte el diccionario de usuarios a una lista para facilitar la iteración en la plantilla
    users_list = list(users.values())
    # Crear un formulario de borrado por usuario
    delete_forms = {u['username']: AdminDeleteUserForm() for u in users_list}
    return render_template_string(ADMIN_USERS_TEMPLATE, title="Gestión de Usuarios", users=users_list, delete_forms=delete_forms)

@admin_users_bp.route('/admin/users/delete/<string:username>', methods=['POST'])
@admin_required
def delete_user(username):
    form = AdminDeleteUserForm()
    if form.validate_on_submit():
        users = load_users()
        if username == 'admin':
            flash('No puedes eliminar el usuario administrador.', 'error')
            return redirect(url_for('admin_users.manage_users'))
        if username in users:
            del users[username]
            save_users(users)
            flash(f'¡Usuario "{username}" eliminado exitosamente!', 'success')
        else:
            flash(f'No se pudo eliminar el usuario "{username}" porque no fue encontrado.', 'error')
    else:
        flash('Solicitud inválida o token CSRF incorrecto.', 'error')
    return redirect(url_for('admin_users.manage_users'))