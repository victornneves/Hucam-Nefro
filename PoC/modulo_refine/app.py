from flask import Flask, jsonify, request
import requests
import os

app = Flask(__name__)

# Base directory where transcriptions are stored
BASE_DIR = "data/refined"

api_whisper_ip = "http://localhost:5000"

@app.route('/getRefineChunk', methods=['GET'])

def get_refined_chunk():
    # Get parameters from query string
    patient = request.args.get('patient')
    chunk_number = request.args.get('chunkNumber')
    
    # Validate parameters
    if not patient or not chunk_number:
        return jsonify({"error": "Both patient and chunkNumber parameters are required"}), 400
    
    try:
        chunk_number = int(chunk_number)
        if chunk_number < 0:
            return jsonify({"error": "chunkNumber must be a positive integer"}), 400
    except ValueError:
        return jsonify({"error": "chunkNumber must be an integer"}), 400

    url = api_whisper_ip + f"/getWhisperChunk?patient={patient}&chunkNumber={chunk_number}"

    with requests.Session() as s:
        result = s.get(url)
        result = result.json()
        print(result["content"])

    refined_content = result["content"]

    # fazer- ao inves retoar result["content"]
    # retornar o refined do gpt

    return jsonify({
        "content": refined_content
    })

    
if __name__ == '__main__':
    app.run(host='localhost', port=5050, debug=True)



