from flask import Flask, jsonify, request
import os

app = Flask(__name__)

# Base directory where transcriptions are stored
BASE_DIR = "data/refined"

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

    # Format patient number with leading zeros
    patient_str = f"{int(patient):03d}"
    directory = os.path.join(BASE_DIR, patient_str)

    # Check if directory exists
    if not os.path.exists(directory):
        return jsonify({"error": f"Patient {patient} refined data not found"}), 404
    
    chunk_filename = f"patient_{patient_str}_refined_transcription_chunk_{chunk_number}.txt"
    chunk_path = os.path.join(directory, chunk_filename)

    if not os.path.exists(chunk_path):
        return jsonify({
            "error": f"Refined chunk {chunk_number} not found for patient {patient}"
        }), 404

    with open(chunk_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return jsonify({
        "patient": patient,
        "chunks_number": chunk_number,
        "content": content
    })

if __name__ == '__main__':
    app.run(host='localhost', port=5050, debug=True)
    