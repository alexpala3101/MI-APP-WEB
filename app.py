from flask import Flask, render_template_string, jsonify, request, session, redirect, url_for
import json
from datetime import datetime
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'  # Cambia esto por una clave segura

# Configuración de administradores
ADMIN_CREDENTIALS = {
    'admin': 'admin123',  # Cambia estas credenciales
    'led_admin': 'led2025'
}

def admin_required(f):
    """Decorador para rutas que requieren autenticación de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Enhanced HTML Template with admin panel
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ titulo }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            line-height: 1.6;
            min-height: 100vh;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }

        header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            padding: 20px 0;
        }

        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: white;
        }

        header h1 {
            font-size: 2.5em;
            font-weight: 700;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }

        .nav-buttons {
            display: flex;
            gap: 15px;
        }

        .nav-btn {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s ease;
            backdrop-filter: blur(5px);
        }

        .nav-btn:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
        }

        .admin-btn {
            background: rgba(255, 215, 0, 0.3);
            border: 2px solid #ffd700;
        }

        .admin-btn:hover {
            background: rgba(255, 215, 0, 0.5);
        }

        main {
            padding: 40px 0;
        }

        .welcome-section {
            text-align: center;
            background: white;
            margin: 20px 0;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }

        .welcome-section h2 {
            font-size: 2em;
            color: #667eea;
            margin-bottom: 20px;
        }

        .welcome-section p {
            font-size: 1.2em;
            margin-bottom: 30px;
            color: #666;
        }

        .action-buttons {
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
            margin: 30px 0;
        }

        .btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 1.1em;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }

        .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        }

        .btn.secondary {
            background: linear-gradient(45deg, #11998e, #38ef7d);
        }

        .btn.danger {
            background: linear-gradient(45deg, #fd746c, #ff9068);
        }

        .marketplace-section {
            background: white;
            margin: 30px 0;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }

        .marketplace-section h3 {
            color: #667eea;
            margin-bottom: 25px;
            font-size: 1.8em;
            text-align: center;
        }

        .products-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }

        .product-card {
            background: #f8f9ff;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            transition: transform 0.3s ease;
            border: 2px solid transparent;
        }

        .product-card:hover {
            transform: translateY(-5px);
            border-color: #667eea;
        }

        .product-card h4 {
            color: #667eea;
            margin-bottom: 10px;
        }

        .product-card .price {
            font-size: 1.5em;
            font-weight: bold;
            color: #11998e;
            margin: 10px 0;
        }

        .api-section {
            background: #2c3e50;
            color: white;
            margin: 30px 0;
            padding: 40px;
            border-radius: 20px;
        }

        .api-section h3 {
            color: #3498db;
            margin-bottom: 25px;
            text-align: center;
        }

        .api-buttons {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }

        .api-btn {
            background: #3498db;
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 8px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }

        .api-btn:hover {
            background: #2980b9;
        }

        #apiResult {
            background: #34495e;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #3498db;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            max-height: 300px;
            overflow-y: auto;
        }

        #messageArea {
            margin: 20px 0;
            padding: 15px;
            background: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 10px;
            color: #155724;
            text-align: center;
            display: none;
        }

        footer {
            background: rgba(0,0,0,0.8);
            color: white;
            text-align: center;
            padding: 30px 0;
            margin-top: 50px;
        }

        @media (max-width: 768px) {
            .header-content {
                flex-direction: column;
                gap: 15px;
            }
            
            .action-buttons {
                flex-direction: column;
                align-items: center;
            }
            
            .api-buttons {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <div class="header-content">
                <h1>{{ mensaje }}</h1>
                <div class="nav-buttons">
                    <button class="nav-btn" onclick="scrollToSection('marketplace')">Mercado</button>
                    <button class="nav-btn" onclick="scrollToSection('catalogo')">CATALOGO</button>
                    <button class="nav-btn admin-btn" onclick="window.location.href='/admin'">👨‍💼 Admin</button>
                </div>
            </div>
        </div>
    </header>

    <main class="container">
        <section class="welcome-section">
            <h2>🛍️ Mercado Digital LED</h2>
            <p>Tu plataforma completa para comprar y reparar productos digitales de alta calidad</p>
            
            <div class="action-buttons">
                <button class="btn" onclick="showMessage('¡Bienvenido al mercado!')">Explorar Productos</button>
                <button class="btn secondary" onclick="showMessage('Función de venta próximamente')">Vender Producto</button>
                <button class="btn danger" onclick="clearMessage()">Limpiar Mensajes</button>
            </div>
            
            <div id="messageArea"></div>
        </section>

        <section id="marketplace" class="marketplace-section">
            <h3>🏪 Productos Destacados</h3>
            <div class="products-grid">
                <div class="product-card">
                    <h4>📺 Tableros electronicos P10</h4>
                    <p>Tableros De Un Solo Color</p>
                    <div class="price">$330.000 Interior  $380.000 Exterior</div>
                    <button class="btn" onclick="selectProduct('Tableros electronicos', 299)">Ver Detalles</button>
                </div>
                <div class="product-card">
                    <h4>📺 Tableros electronicos </h4>
                    <p>Tableros De Luz RGB </p>
                    <div class="price">$480.000 InteriorP5 $580.000 ExteriorP6</div>
                    <button class="btn" onclick="selectProduct('Tableros electronicos', 299)">Ver Detalles</button>
                </div>
                <div class="product-card">
                    <h4>🎨 Diseños Neos Personalizados</h4>
                    <p>Personaliza Tu Logo En Neon</p>
                    <div class="price">$50.000 para adelante</div>
                    <button class="btn" onclick="selectProduct('Diseño Neon Personalizados', 149)">Ver Detalles</button>
                </div>
                
                <div class="product-card">
                    <h4>🖥️ Pantallas Para Imagenes Y Video</h4>
                    <p> Programarble Desde el Celular </p>
                    <div class="price">$1.500.000</div>
                    <button class="btn" onclick="selectProduct('Bot de Automatización', 99)">Ver Detalles</button>
                </div>
            </div>
        </section>

        <section id="api" class="api-section">
            <h3>🔧 Pruebas de API</h3>
            <div class="api-buttons">
                <button class="api-btn" onclick="testAPI('GET')">📥 Test GET</button>
                <button class="api-btn" onclick="testAPI('POST')">📤 Test POST</button>
                <button class="api-btn" onclick="testAPI('STATUS')">📊 Estado del Sistema</button>
                <button class="api-btn" onclick="testAPI('PRODUCTS')">🛍️ Obtener Productos</button>
            </div>
            <div id="apiResult">Presiona un botón para probar la API...</div>
        </section>
    </main>

    <footer>
        <div class="container">
            <p>&copy; 2025 LED Digital Marketplace - Todo Lo Que Necesites</p>
            <p>🚀 Flask • ⚡ JavaScript • 🎨 CSS3</p>
        </div>
    </footer>

    <script>
        // Message functions
        function showMessage(message) {
            const messageArea = document.getElementById('messageArea');
            messageArea.textContent = message;
            messageArea.style.display = 'block';
            messageArea.style.background = '#d4edda';
            messageArea.style.color = '#155724';
            
            // Auto-hide after 3 seconds
            setTimeout(() => {
                messageArea.style.display = 'none';
            }, 3000);
        }

        function clearMessage() {
            const messageArea = document.getElementById('messageArea');
            messageArea.style.display = 'none';
        }

        // Product selection
        function selectProduct(name, price) {
            showMessage(`Producto seleccionado: ${name} - $${price}`);
        }

        // Smooth scrolling
        function scrollToSection(sectionId) {
            const element = document.getElementById(sectionId);
            if (element) {
                element.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        }

        // Enhanced API testing
        async function testAPI(type) {
            const resultDiv = document.getElementById('apiResult');
            resultDiv.textContent = '⏳ Enviando solicitud...';

            try {
                let response;
                let url;
                let options = {};

                switch(type) {
                    case 'GET':
                        url = '/api/test';
                        break;
                    case 'POST':
                        url = '/api/test';
                        options = {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                nombre: 'Usuario de prueba',
                                timestamp: new Date().toISOString(),
                                action: 'marketplace_test'
                            })
                        };
                        break;
                    case 'STATUS':
                        url = '/status';
                        break;
                    case 'PRODUCTS':
                        url = '/api/products';
                        break;
                }

                response = await fetch(url, options);
                const data = await response.json();
                
                const timestamp = new Date().toLocaleString();
                const result = `🕒 ${timestamp}
📡 Endpoint: ${url}
🔥 Método: ${options.method || 'GET'}
✅ Status: ${response.status} ${response.statusText}

📋 Respuesta:
${JSON.stringify(data, null, 2)}`;
                
                resultDiv.textContent = result;
                resultDiv.style.borderLeftColor = response.ok ? '#27ae60' : '#e74c3c';
                
            } catch (error) {
                resultDiv.textContent = `❌ Error: ${error.message}`;
                resultDiv.style.borderLeftColor = '#e74c3c';
            }
        }

        // Initialize page
        document.addEventListener('DOMContentLoaded', function() {
            console.log('🚀 LED Digital Marketplace cargado correctamente');
        });
    </script>
</body>
</html>
"""

# Admin Login Template
ADMIN_LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login - LED Digital</title>
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

        .login-container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
        }

        .login-header {
            text-align: center;
            margin-bottom: 30px;
        }

        .login-header h1 {
            color: #667eea;
            font-size: 2em;
            margin-bottom: 10px;
        }

        .login-header p {
            color: #666;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-bottom: 5px;
            color: #333;
            font-weight: 500;
        }

        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e1e1;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }

        input[type="text"]:focus, input[type="password"]:focus {
            outline: none;
            border-color: #667eea;
        }

        .btn {
            width: 100%;
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 15px;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }

        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            text-align: center;
        }

        .back-link {
            text-align: center;
            margin-top: 20px;
        }

        .back-link a {
            color: #667eea;
            text-decoration: none;
        }

        .back-link a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h1>👨‍💼 Panel de Administrador</h1>
            <p>Ingresa tus credenciales para continuar</p>
        </div>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        <form method="POST">
            <div class="form-group">
                <label for="username">Usuario:</label>
                <input type="text" id="username" name="username" required>
            </div>
            
            <div class="form-group">
                <label for="password">Contraseña:</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit" class="btn">🔓 Iniciar Sesión</button>
        </form>
        
        <div class="back-link">
            <a href="/">← Volver al Marketplace</a>
        </div>
    </div>
</body>
</html>
"""

# Admin Dashboard Template
ADMIN_DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Admin - LED Digital</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            line-height: 1.6;
            min-height: 100vh;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }

        header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            padding: 20px 0;
        }

        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: white;
        }

        header h1 {
            font-size: 2.5em;
            font-weight: 700;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }

        .nav-buttons {
            display: flex;
            gap: 15px;
        }

        .nav-btn {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s ease;
            backdrop-filter: blur(5px);
            text-decoration: none;
            display: inline-block;
        }

        .nav-btn:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
        }

        .logout-btn {
            background: rgba(255, 82, 82, 0.3);
            border: 2px solid #ff5252;
        }

        main {
            padding: 40px 0;
        }

        .admin-section {
            background: white;
            margin: 20px 0;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }

        .admin-section h2 {
            color: #667eea;
            margin-bottom: 30px;
            font-size: 1.8em;
            text-align: center;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }

        .stat-card {
            background: #f8f9ff;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            border: 2px solid #667eea;
        }

        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }

        .stat-label {
            color: #666;
            margin-top: 10px;
        }

        .admin-actions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }

        .action-card {
            background: #f8f9ff;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            transition: transform 0.3s ease;
        }

        .action-card:hover {
            transform: translateY(-5px);
        }

        .action-card h3 {
            color: #667eea;
            margin-bottom: 15px;
        }

        .btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 10px 5px;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }

        .btn.secondary {
            background: linear-gradient(45deg, #11998e, #38ef7d);
        }

        .btn.danger {
            background: linear-gradient(45deg, #fd746c, #ff9068);
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <div class="header-content">
                <h1>👨‍💼 Panel de Administrador</h1>
                <div class="nav-buttons">
                    <a href="/" class="nav-btn">🏠 Inicio</a>
                    <a href="/admin/logout" class="nav-btn logout-btn">🚪 Cerrar Sesión</a>
                </div>
            </div>
        </div>
    </header>

    <main class="container">
        <section class="admin-section">
            <h2>📊 Estadísticas del Sistema</h2>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">1</div>
                    <div class="stat-label">Visitas Hoy</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">250+</div>
                    <div class="stat-label">Productos Activos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">1,200+</div>
                    <div class="stat-label">Usuarios Registrados</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">99%</div>
                    <div class="stat-label">Satisfacción</div>
                </div>
            </div>
        </section>

        <section class="admin-section">
            <h2>🛠️ Herramientas de Administración</h2>
            <div class="admin-actions">
                <div class="action-card">
                    <h3>📦 Gestión de Productos</h3>
                    <p>Administrar el catálogo de productos</p>
                    <button class="btn" onclick="alert('Función en desarrollo')">Gestionar</button>
                </div>
                <div class="action-card">
                    <h3>👥 Usuarios</h3>
                    <p>Ver y administrar usuarios registrados</p>
                    <button class="btn secondary" onclick="alert('Función en desarrollo')">Ver Usuarios</button>
                </div>
                <div class="action-card">
                    <h3>📈 Reportes</h3>
                    <p>Generar reportes de ventas y estadísticas</p>
                    <button class="btn" onclick="alert('Función en desarrollo')">Generar</button>
                </div>
                <div class="action-card">
                    <h3>⚙️ Configuración</h3>
                    <p>Ajustes del sistema y configuración</p>
                    <button class="btn danger" onclick="alert('Función en desarrollo')">Configurar</button>
                </div>
            </div>
        </section>
    </main>
</body>
</html>
"""

# Mock products data
PRODUCTS = [
    {"id": 1, "name": "Tableros electronicos P10", "price": 330000, "category": "led", "description": "Tableros De Un Solo Color"},
    {"id": 2, "name": "Tableros electronicos RGB", "price": 480000, "category": "led", "description": "Tableros De Luz RGB"},
    {"id": 3, "name": "Diseños Neos Personalizados", "price": 50000, "category": "neon", "description": "Personaliza Tu Logo En Neon"},
    {"id": 4, "name": "Pantallas Para Imagenes Y Video", "price": 1500000, "category": "display", "description": "Programarble Desde el Celular"}
]

@app.route('/')
def home():
    """Ruta principal del marketplace"""
    return render_template_string(HTML_TEMPLATE,
                                titulo='LED Digital Marketplace',
                                mensaje='🚀 LED Digital')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Página de login para administradores"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template_string(ADMIN_LOGIN_TEMPLATE, 
                                        error='usuario o contraseña incorrectas')
    
    return render_template_string(ADMIN_LOGIN_TEMPLATE)

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Dashboard de administrador"""
    return render_template_string(ADMIN_DASHBOARD_TEMPLATE)

@app.route('/admin/logout')
def admin_logout():
    """Cerrar sesión de administrador"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return redirect(url_for('home'))

@app.route('/api/test', methods=['GET', 'POST'])
def api_test():
    """API de prueba mejorada"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            return jsonify({
                'message': '✅ Datos recibidos correctamente',
                'data': data,
                'status': 'success',
                'method': 'POST',
                'timestamp': datetime.now().isoformat(),
                'server': 'LED Digital API v1.0'
            })
        except Exception as e:
            return jsonify({
                'message': '❌ Error al procesar datos',
                'error': str(e),
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            }), 400
    
    return jsonify({
        'message': '🟢 API funcionando correctamente',
        'status': 'success',
        'method': 'GET',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'endpoints': ['/api/test', '/api/products', '/status']
    })

@app.route('/api/products', methods=['GET'])
def get_products():
    """Endpoint para obtener productos del marketplace"""
    try:
        return jsonify({
            'message': '🛍️ Productos obtenidos exitosamente',
            'status': 'success',
            'data': PRODUCTS,
            'total': len(PRODUCTS),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'message': '❌ Error al obtener productos',
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Obtener un producto específico"""
    product = next((p for p in PRODUCTS if p['id'] == product_id), None)
    if product:
        return jsonify({
            'message': '✅ Producto encontrado',
            'status': 'success',
            'data': product,
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({
            'message': '❌ Producto no encontrado',
            'status': 'error',
            'product_id': product_id
        }), 404

@app.route('/api/admin/stats')
@admin_required
def admin_stats():
    """API de estadísticas solo para administradores"""
    return jsonify({
        'message': '📊 Estadísticas del sistema',
        'status': 'success',
        'data': {
            'visits_today': 1,
            'active_products': 250,
            'registered_users': 1200,
            'satisfaction_rate': 98,
            'total_sales': 150,
            'revenue_month': 2500000,
            'last_updated': datetime.now().isoformat()
        },
        'admin_user': session.get('admin_username'),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/status')
def status():
    """Estado completo del sistema"""
    import sys
    import platform
    
    return jsonify({
        'status': '🟢 ONLINE',
        'message': 'LED Digital Marketplace funcionando correctamente',
        'system_info': {
            'platform': platform.system(),
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'flask_version': '2.x',
            'directory': os.getcwd(),
            'timestamp': datetime.now().isoformat()
        },
        'api_endpoints': {
            'main': '/',
            'products': '/api/products',
            'test': '/api/test',
            'status': '/status',
            'admin': '/admin'
        },
        'features': [
            'Marketplace UI',
            'Product Catalog',
            'REST API',
            'Admin Panel',
            'Authentication System',
            'Responsive Design'
        ]
    })

@app.errorhandler(404)
def not_found(error):
    """Manejo de errores 404"""
    return jsonify({
        'message': '❌ Endpoint no encontrado',
        'status': 'error',
        'code': 404,
        'available_endpoints': [
            '/',
            '/api/test',
            '/api/products',
            '/status',
            '/admin'
        ]
    }), 404

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 LED DIGITAL MARKETPLACE CON PANEL ADMIN")
    print("=" * 60)
    print("📱 Página principal: http://127.0.0.1:5000/")
    print("🛍️ Productos API: http://127.0.0.1:5000/api/products") 
    print("🔧 Test API: http://127.0.0.1:5000/api/test")
    print("📊 Estado sistema: http://127.0.0.1:5000/status")
    print("👨‍💼 Panel Admin: http://127.0.0.1:5000/admin")
    print("=" * 60)
    print("🔐 Credenciales de Admin:")
    print("   • Usuario: admin | Contraseña: admin123")
    print("   • Usuario: led_admin | Contraseña: led2025")
    print("=" * 60)
    print("✨ Características:")
    print("   • Interfaz de marketplace moderna")
    print("   • API REST completa")
    print("   • Panel de administrador protegido")
    print("   • Sistema de autenticación")
    print("   • Estadísticas solo para admins")
    print("   • Diseño responsive")
    print("   • Manejo de errores")
    print("=" * 60)
    
    app.run(debug=True, host='127.0.0.1', port=5000)