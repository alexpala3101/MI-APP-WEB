from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/test', methods=['GET', 'POST'])
def api_test():
    if request.method == 'POST':
        data = request.get_json()
        return jsonify({'message': 'Datos recibidos', 'data': data})
    return jsonify({'message': 'API funcionando correctamente'})

if __name__ == '__main__':
    app.run(debug=True)