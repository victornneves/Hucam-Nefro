from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
from source import generate_medical_response

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Recarrega templates (HTML)
app.run(debug=True)  # Ativa o modo debug (reinicia o servidor após mudanças)
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

if __name__ == '__main__':
    # Configuração para evitar problemas de porta ocupada
    os.system("fuser -k 5003/tcp")  # Linux/Mac
    app.run(host='localhost', port=5003, debug=True)