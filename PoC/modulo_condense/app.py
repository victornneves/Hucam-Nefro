from flask import Flask, jsonify, request
import os
import glob

app = Flask(__name__)

# Configuração de caminhos (relativos à localização deste arquivo)
CONDENSED_DIR = "data/condensed"  # Diretório onde os chunks condensados estão armazenados

@app.route('/getCondensedChunk', methods=['GET'])
def get_condensed_chunk():
    # Obtém parâmetros da query string
    patient = request.args.get('patient')
    chunk_number = request.args.get('chunkNumber')
    
    # Validação dos parâmetros
    if not patient or not chunk_number:
        return jsonify({"error": "Both patient and chunkNumber parameters are required"}), 400
    
    try:
        chunk_number = int(chunk_number)
        if chunk_number < 0:
            return jsonify({"error": "chunkNumber must be a positive integer"}), 400
    except ValueError:
        return jsonify({"error": "chunkNumber must be an integer"}), 400
    
    # Formata o ID do paciente com zeros à esquerda
    patient_str = f"{int(patient):03d}"
    directory = os.path.join(CONDENSED_DIR, patient_str)
    
    # Verifica se o diretório existe
    if not os.path.exists(directory):
        return jsonify({"error": f"No condensed data found for patient {patient}"}), 404
    
    # Constrói o caminho do arquivo
    chunk_filename = f"patient_{patient_str}_condensed_dialog_chunk_{chunk_number}.txt"
    chunk_path = os.path.join(directory, chunk_filename)
    
    # Verifica se o arquivo existe
    if not os.path.exists(chunk_path):
        return jsonify({
            "error": f"Condensed chunk {chunk_number} not found for patient {patient}"
        }), 404
    
    # Lê e retorna o conteúdo do arquivo
    with open(chunk_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return jsonify({
        "patient": patient,
        "chunk_number": chunk_number,
        "content": content
    })

if __name__ == '__main__':
    # Configuração para evitar problemas de porta ocupada durante desenvolvimento
    import os
    os.system("fuser -k 5002/tcp")  # Encerra processos na porta 5002 (Linux/Mac)
    
    app.run(host='localhost', port=5002, debug=True)