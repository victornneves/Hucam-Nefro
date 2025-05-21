from flask import Flask, request, jsonify, render_template
import os
from source import generate_medical_response

app = Flask(__name__, template_folder='templates')

@app.route('/')
def index():
    # Renderiza o template HTML
    return render_template('index.html')

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