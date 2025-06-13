from flask import Flask, render_template_string, request, session, redirect, url_for, flash, jsonify
from functools import wraps
from datetime import datetime
import hashlib
import json
import os
import re
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Clave secreta para sesiones

# Sistema de usuarios simulado (en producción usar base de datos)
USERS_FILE = 'users.json'

def load_users():
    """Cargar usuarios desde archivo JSON"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    """Guardar usuarios en archivo JSON"""
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error al guardar usuarios: {e}")
        return False

def hash_password(password):
    """Hashear contraseña con salt"""
    salt = secrets.token_hex(32)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return salt + password_hash.hex()

def verify_password(password, stored_password):
    """Verificar contraseña"""
    try:
        salt = stored_password[:64]
        stored_hash = stored_password[64:]
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return password_hash.hex() == stored_hash
    except:
        return False

def validate_email(email):
    """Validar formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validar fortaleza de contraseña"""
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    if not re.search(r'[A-Z]', password):
        return False, "La contraseña debe tener al menos una mayúscula"
    if not re.search(r'[a-z]', password):
        return False, "La contraseña debe tener al menos una minúscula"
    if not re.search(r'\d', password):
        return False, "La contraseña debe tener al menos un número"
    return True, "Contraseña válida"

def validate_phone(phone):
    """Validar formato de teléfono"""
    # Acepta formatos como +57 300 123 4567, 300 123 4567, 3001234567
    pattern = r'^(\+57\s?)?[3][0-9]{2}\s?[0-9]{3}\s?[0-9]{4}$'
    return re.match(pattern, phone.replace(' ', '').replace('-', '')) is not None

def login_required(f):
    """Decorador para rutas que requieren login de usuario"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_logged_in' not in session:
            return redirect(url_for('user_login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorador para rutas que requieren permisos de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_logged_in' not in session:
            return redirect(url_for('user_login'))
        
        users = load_users()
        user_email = session.get('user_email')
        user_data = users.get(user_email, {})
        
        if not user_data.get('is_admin', False):
            return jsonify({'error': 'Acceso denegado'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# Templates HTML (usando tu template existente con mejoras)
USER_LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Iniciar Sesión - LED Digital</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .auth-container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 450px;
            position: relative;
        }

        .auth-header {
            text-align: center;
            margin-bottom: 30px;
        }

        .auth-header h1 {
            color: #667eea;
            font-size: 2.2em;
            margin-bottom: 10px;
        }

        .auth-header p {
            color: #666;
            font-size: 1.1em;
        }

        .auth-tabs {
            display: flex;
            margin-bottom: 30px;
            background: #f8f9ff;
            border-radius: 10px;
            padding: 5px;
        }

        .tab-btn {
            flex: 1;
            padding: 12px;
            border: none;
            background: transparent;
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.3s ease;
            font-weight: 500;
        }

        .tab-btn.active {
            background: #667eea;
            color: white;
        }

        .auth-form {
            display: none;
        }

        .auth-form.active {
            display: block;
        }

        .form-group {
            margin-bottom: 20px;
            position: relative;
        }

        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 500;
        }

        input[type="text"], input[type="email"], input[type="password"], input[type="tel"] {
            width: 100%;
            padding: 14px;
            border: 2px solid #e1e1e1;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }

        input:focus {
            outline: none;
            border-color: #667eea;
        }

        input.error {
            border-color: #e74c3c;
        }

        input.success {
            border-color: #27ae60;
        }

        .error-message {
            color: #e74c3c;
            font-size: 0.85em;
            margin-top: 5px;
            display: none;
        }

        .success-message {
            color: #27ae60;
            font-size: 0.85em;
            margin-top: 5px;
            display: none;
        }

        .password-strength {
            margin-top: 10px;
        }

        .strength-bar {
            height: 4px;
            background: #e1e1e1;
            border-radius: 2px;
            overflow: hidden;
            margin-bottom: 5px;
        }

        .strength-fill {
            height: 100%;
            transition: all 0.3s ease;
        }

        .strength-weak { background: #e74c3c; width: 25%; }
        .strength-fair { background: #f39c12; width: 50%; }
        .strength-good { background: #f1c40f; width: 75%; }
        .strength-strong { background: #27ae60; width: 100%; }

        .btn {
            width: 100%;
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 16px;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .error, .success {
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
            font-weight: 500;
        }

        .error {
            background: #fee;
            color: #c33;
            border: 1px solid #fcc;
        }

        .success {
            background: #efe;
            color: #363;
            border: 1px solid #cfc;
        }

        .back-link {
            text-align: center;
            margin-top: 25px;
        }

        .back-link a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }

        .back-link a:hover {
            text-decoration: underline;
        }

        .form-footer {
            text-align: center;
            margin-top: 20px;
            color: #666;
            font-size: 14px;
        }

        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
        }

        .checkbox-group input[type="checkbox"] {
            width: auto;
        }

        @media (max-width: 480px) {
            .auth-container {
                margin: 20px;
                padding: 30px 25px;
            }
        }
    </style>
</head>
<body>
    <div class="auth-container">
        <div class="auth-header">
            <h1>🔐 Acceso de Usuario</h1>
            <p>Inicia sesión o crea tu cuenta</p>
        </div>
        
        <div class="auth-tabs">
            <button class="tab-btn active" onclick="switchTab('login')">Iniciar Sesión</button>
            <button class="tab-btn" onclick="switchTab('register')">Registrarse</button>
        </div>

        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}

        {% if success %}
        <div class="success">{{ success }}</div>
        {% endif %}
        
        <!-- Formulario de Login -->
        <form id="loginForm" class="auth-form active" method="POST" action="/user/login">
            <input type="hidden" name="form_type" value="login">
            
            <div class="form-group">
                <label for="login_email">📧 Email:</label>
                <input type="email" id="login_email" name="email" required placeholder="tu@email.com">
                <div class="error-message" id="login_email_error"></div>
            </div>
            
            <div class="form-group">
                <label for="login_password">🔒 Contraseña:</label>
                <input type="password" id="login_password" name="password" required placeholder="Tu contraseña">
                <div class="error-message" id="login_password_error"></div>
            </div>

            <div class="checkbox-group">
                <input type="checkbox" id="remember" name="remember">
                <label for="remember">Recordarme</label>
            </div>
            
            <button type="submit" class="btn" id="loginBtn">🚀 Iniciar Sesión</button>
            
            <div class="form-footer">
                <small>¿Olvidaste tu contraseña? <a href="#" style="color: #667eea;">Recuperar</a></small>
            </div>
        </form>

        <!-- Formulario de Registro -->
        <form id="registerForm" class="auth-form" method="POST" action="/user/register">
            <input type="hidden" name="form_type" value="register">
            
            <div class="form-group">
                <label for="reg_name">👤 Nombre Completo:</label>
                <input type="text" id="reg_name" name="name" required placeholder="Juan Pérez">
                <div class="error-message" id="reg_name_error"></div>
            </div>
            
            <div class="form-group">
                <label for="reg_email">📧 Email:</label>
                <input type="email" id="reg_email" name="email" required placeholder="juan@email.com">
                <div class="error-message" id="reg_email_error"></div>
                <div class="success-message" id="reg_email_success"></div>
            </div>

            <div class="form-group">
                <label for="reg_phone">📱 Teléfono:</label>
                <input type="tel" id="reg_phone" name="phone" placeholder="+57 300 123 4567">
                <div class="error-message" id="reg_phone_error"></div>
            </div>
            
            <div class="form-group">
                <label for="reg_password">🔒 Contraseña:</label>
                <input type="password" id="reg_password" name="password" required placeholder="Mínimo 8 caracteres">
                <div class="password-strength">
                    <div class="strength-bar">
                        <div class="strength-fill" id="strength-fill"></div>
                    </div>
                    <div class="strength-text" id="strength-text">Ingresa una contraseña</div>
                </div>
                <div class="error-message" id="reg_password_error"></div>
            </div>

            <div class="form-group">
                <label for="reg_confirm">🔒 Confirmar Contraseña:</label>
                <input type="password" id="reg_confirm" name="confirm_password" required placeholder="Repite tu contraseña">
                <div class="error-message" id="reg_confirm_error"></div>
                <div class="success-message" id="reg_confirm_success"></div>
            </div>

            <div class="checkbox-group">
                <input type="checkbox" id="terms" name="terms" required>
                <label for="terms">Acepto los términos y condiciones</label>
            </div>
            
            <button type="submit" class="btn" id="registerBtn">✨ Crear Cuenta</button>
            
            <div class="form-footer">
                <small>Al registrarte aceptas nuestros <a href="#" style="color: #667eea;">Términos de Servicio</a></small>
            </div>
        </form>
        
        <div class="back-link">
            <a href="/">← Volver al Marketplace</a>
        </div>
    </div>

    <script>
        // Validaciones en tiempo real
        document.addEventListener('DOMContentLoaded', function() {
            const regEmail = document.getElementById('reg_email');
            const regPassword = document.getElementById('reg_password');
            const regConfirm = document.getElementById('reg_confirm');
            const regPhone = document.getElementById('reg_phone');
            const regName = document.getElementById('reg_name');

            // Validación de email
            regEmail.addEventListener('blur', function() {
                const email = this.value;
                const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                
                if (email && !emailPattern.test(email)) {
                    showError('reg_email', 'Formato de email inválido');
                } else if (email) {
                    showSuccess('reg_email', 'Email válido');
                }
            });

            // Validación de contraseña
            regPassword.addEventListener('input', function() {
                const password = this.value;
                const strength = calculatePasswordStrength(password);
                updatePasswordStrength(strength);
                
                if (password.length > 0 && password.length < 8) {
                    showError('reg_password', 'La contraseña debe tener al menos 8 caracteres');
                } else if (password.length >= 8) {
                    hideError('reg_password');
                }
            });

            // Validación de confirmación de contraseña
            regConfirm.addEventListener('input', function() {
                const password = regPassword.value;
                const confirm = this.value;
                
                if (confirm && password !== confirm) {
                    showError('reg_confirm', 'Las contraseñas no coinciden');
                } else if (confirm && password === confirm) {
                    showSuccess('reg_confirm', 'Las contraseñas coinciden');
                }
            });

            // Validación de teléfono
            regPhone.addEventListener('blur', function() {
                const phone = this.value;
                const phonePattern = /^(\+57\s?)?[3][0-9]{2}\s?[0-9]{3}\s?[0-9]{4}$/;
                
                if (phone && !phonePattern.test(phone.replace(/\s/g, ''))) {
                    showError('reg_phone', 'Formato de teléfono inválido (ej: +57 300 123 4567)');
                } else if (phone) {
                    hideError('reg_phone');
                }
            });

            // Validación de nombre
            regName.addEventListener('blur', function() {
                const name = this.value.trim();
                
                if (name.length < 2) {
                    showError('reg_name', 'El nombre debe tener al menos 2 caracteres');
                } else {
                    hideError('reg_name');
                }
            });
        });

        function switchTab(tab) {
            // Remover clase active de todos los botones y formularios
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.auth-form').forEach(form => form.classList.remove('active'));
            
            // Activar el tab seleccionado
            event.target.classList.add('active');
            document.getElementById(tab + 'Form').classList.add('active');
            
            // Limpiar mensajes de error
            document.querySelectorAll('.error-message').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.success-message').forEach(el => el.style.display = 'none');
        }

        function showError(fieldId, message) {
            const field = document.getElementById(fieldId);
            const errorDiv = document.getElementById(fieldId + '_error');
            
            field.classList.add('error');
            field.classList.remove('success');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            
            // Ocultar mensaje de éxito si existe
            const successDiv = document.getElementById(fieldId + '_success');
            if (successDiv) {
                successDiv.style.display = 'none';
            }
        }

        function showSuccess(fieldId, message) {
            const field = document.getElementById(fieldId);
            const successDiv = document.getElementById(fieldId + '_success');
            
            field.classList.add('success');
            field.classList.remove('error');
            
            if (successDiv) {
                successDiv.textContent = message;
                successDiv.style.display = 'block';
            }
            
            // Ocultar mensaje de error
            hideError(fieldId);
        }

        function hideError(fieldId) {
            const field = document.getElementById(fieldId);
            const errorDiv = document.getElementById(fieldId + '_error');
            
            field.classList.remove('error');
            errorDiv.style.display = 'none';
        }

        function calculatePasswordStrength(password) {
            let strength = 0;
            
            if (password.length >= 8) strength += 1;
            if (password.match(/[a-z]/)) strength += 1;
            if (password.match(/[A-Z]/)) strength += 1;
            if (password.match(/[0-9]/)) strength += 1;
            if (password.match(/[^a-zA-Z0-9]/)) strength += 1;
            
            return strength;
        }

        function updatePasswordStrength(strength) {
            const strengthFill = document.getElementById('strength-fill');
            const strengthText = document.getElementById('strength-text');
            
            strengthFill.className = 'strength-fill';
            
            switch (strength) {
                case 0:
                case 1:
                    strengthFill.classList.add('strength-weak');
                    strengthText.textContent = 'Muy débil';
                    strengthText.style.color = '#e74c3c';
                    break;
                case 2:
                    strengthFill.classList.add('strength-fair');
                    strengthText.textContent = 'Débil';
                    strengthText.style.color = '#f39c12';
                    break;
                case 3:
                    strengthFill.classList.add('strength-good');
                    strengthText.textContent = 'Buena';
                    strengthText.style.color = '#f1c40f';
                    break;
                case 4:
                case 5:
                    strengthFill.classList.add('strength-strong');
                    strengthText.textContent = 'Fuerte';
                    strengthText.style.color = '#27ae60';
                    break;
            }
        }

        // Validación del formulario de registro
        document.getElementById('registerForm').addEventListener('submit', function(e) {
            const password = document.getElementById('reg_password').value;
            const confirm = document.getElementById('reg_confirm').value;
            const email = document.getElementById('reg_email').value;
            const name = document.getElementById('reg_name').value;
            const terms = document.getElementById('terms').checked;
            
            let hasErrors = false;
            
            // Validar nombre
            if (name.trim().length < 2) {
                showError('reg_name', 'El nombre debe tener al menos 2 caracteres');
                hasErrors = true;
            }
            
            // Validar email
            const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailPattern.test(email)) {
                showError('reg_email', 'Formato de email inválido');
                hasErrors = true;
            }
            
            // Validar contraseña
            if (password.length < 8) {
                showError('reg_password', 'La contraseña debe tener al menos 8 caracteres');
                hasErrors = true;
            }
            
            // Validar confirmación
            if (password !== confirm) {
                showError('reg_confirm', 'Las contraseñas no coinciden');
                hasErrors = true;
            }
            
            // Validar términos
            if (!terms) {
                alert('Debes aceptar los términos y condiciones');
                hasErrors = true;
            }
            
            if (hasErrors) {
                e.preventDefault();
                return false;
            }
        });

        // Auto-focus en el primer campo
        document.addEventListener('DOMContentLoaded', function() {
            document.getElementById('login_email').focus();
        });
    </script>
</body>
</html>
"""

# Funciones principales del sistema de usuarios
def create_user_routes(app):
    """Crear las rutas relacionadas con usuarios"""
    
    @app.route('/user/login', methods=['GET', 'POST'])
    def user_login():
        """Página de login/registro para usuarios"""
        if request.method == 'POST':
            form_type = request.form.get('form_type')
            
            if form_type == 'login':
                # Proceso de login
                email = request.form.get('email', '').lower().strip()
                password = request.form.get('password', '')
                
                # Validaciones básicas
                if not email or not password:
                    return render_template_string(USER_LOGIN_TEMPLATE, 
                                                error='Email y contraseña son requeridos')
                
                if not validate_email(email):
                    return render_template_string(USER_LOGIN_TEMPLATE, 
                                                error='Formato de email inválido')
                
                users = load_users()
                
                if email in users and verify_password(password, users[email]['password']):
                    # Login exitoso
                    session['user_logged_in'] = True
                    session['user_email'] = email
                    session['user_name'] = users[email]['name']
                    session['user_id'] = users[email].get('id', email)
                    
                    # Actualizar última conexión
                    users[email]['last_login'] = datetime.now().isoformat()
                    users[email]['login_count'] = users[email].get('login_count', 0) + 1
                    save_users(users)
                    
                    # Recordar usuario si se seleccionó
                    if request.form.get('remember'):
                        session.permanent = True
                    
                    return redirect(url_for('user_dashboard'))
                else:
                    return render_template_string(USER_LOGIN_TEMPLATE, 
                                                error='Email o contraseña incorrectos')
            
            elif form_type == 'register':
                # Proceso de registro
                name = request.form.get('name', '').strip()
                email = request.form.get('email', '').lower().strip()
                phone = request.form.get('phone', '').strip()
                password = request.form.get('password', '')
                confirm_password = request.form.get('confirm_password', '')
                terms = request.form.get('terms')
                
                # Validaciones
                if not all([name, email, password, confirm_password]):
                    return render_template_string(USER_LOGIN_TEMPLATE, 
                                                error='Todos los campos obligatorios deben estar llenos')
                
                if not terms:
                    return render_template_string(USER_LOGIN_TEMPLATE, 
                                                error='Debes aceptar los términos y condiciones')
                
                if len(name.strip()) < 2:
                    return render_template_string(USER_LOGIN_TEMPLATE, 
                                                error='El nombre debe tener al menos 2 caracteres')
                
                if not validate_email(email):
                    return render_template_string(USER_LOGIN_TEMPLATE, 
                                                error='Formato de email inválido')
                
                if phone and not validate_phone(phone):
                    return render_template_string(USER_LOGIN_TEMPLATE, 
                                                error='Formato de teléfono inválido')
                
                is_valid, password_message = validate_password(password)
                if not is_valid:
                    return render_template_string(USER_LOGIN_TEMPLATE, 
                                                error=password_message)
                
                if password != confirm_password:
                    return render_template_string(USER_LOGIN_TEMPLATE, 
                                                error='Las contraseñas no coinciden')
                
                users = load_users()
                
                if email in users:
                    return render_template_string(USER_LOGIN_TEMPLATE, 
                                                error='Ya existe una cuenta con este email')
                
                # Crear nuevo usuario
                user_id = len(users) + 1
                users[email] = {
                    'id': user_id,
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'password': hash_password(password),
                    'created_at': datetime.now().isoformat(),
                    'last_login': datetime.now().isoformat(),
                    'login_count': 0,
                    'active': True,
                    'is_admin': False,
                    'email_verified': False,
                    'profile_complete': bool(phone)
                }
                
                if save_users(users):
                    return render_template_string(USER_LOGIN_TEMPLATE, 
                                                success='¡Cuenta creada exitosamente! Ahora puedes iniciar sesión.')
                else:
                    return render_template_string(USER_LOGIN_TEMPLATE, 
                                                error='Error al crear la cuenta. Inténtalo de nuevo.')
        
        return render_template_string(USER_LOGIN_TEMPLATE)

    @app.route('/user/register', methods=['POST'])
    def user_register():
        """Endpoint específico para registro (redirecciona a login)"""
        return user_login()

    @app.route('/user/dashboard')
    @login_required
    def user_dashboard():
        """Dashboard del usuario"""
        users = load_users()
        user_email = session.get('user_email')
        user_data = users.get(user_email, {})
        
        # Formatear fechas
        created_at = user_data.get('created_at', '')
        last_login = user_data.get('last_login', '')
        
        try:
            joined_date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).strftime('%d/%m/%Y')
        except:
            joined_date = 'No disponible'
            
        try:
            last_login_date = datetime.fromisoformat(last_login.replace('Z', '+00:00')).strftime('%d/%m/%Y %H:%M')
        except:
            last_login_date = 'No disponible'
        
 