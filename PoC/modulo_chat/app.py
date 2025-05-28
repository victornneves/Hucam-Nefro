from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import socket
from source import generate_medical_response

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Recarrega templates (HTML)
CORS(app)

@app.route('/')
def index():
    # Renderiza o template HTML
    return render_template('index.html')

# Rota para servir arquivos de áudio diretamente (opcional)
@app.route('/audio/<path:filename>')
def serve_audio(filename):
    return send_from_directory('static/audio', filename)

@app.route('/getMedicalResponse', methods=['POST'])
def get_medical_response():
    # Obtém os dados da requisição
    data = request.get_json()
    
    # Validação dos parâmetros
    if not data or 'patient' not in data or 'question' not in data:
        return jsonify({"error": "Parâmetros 'patient' e 'question' são obrigatórios"}), 400
    
    patient_id = data['patient']
    question = data['question'].strip()
    
    if not question:
        return jsonify({"error": "A pergunta não pode estar vazia"}), 400
    
    # Chama a função principal do source.py
    result = generate_medical_response(patient_id, question)
    
    if 'error' in result:
        return jsonify({"error": result['error']}), 500
    
    return jsonify(result)

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

if __name__ == '__main__':
    port = 5003
    if is_port_in_use(port):
        print(f"Port {port} is already in use. Please close the application using this port and try again.")
    else:
        app.run(host='localhost', port=port, debug=True)