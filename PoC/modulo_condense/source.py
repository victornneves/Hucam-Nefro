import os
from openai import OpenAI
import dotenv
import glob

dotenv.load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configuração de caminhos
REFINED_DIR = "../modulo_refine/data/refined"  # Origem dos arquivos refinados
CONDENSED_DIR = "data/condensed"               # Destino dos arquivos condensados
MAX_TOKENS = 3000

def condense_dialog(dialog):
    """Condenses a dialog into essential points using chunk processing."""
    condense_prompt = (
        "You will receive a portion of a medical consultation dialog. "
        "Please summarize the essential points relevant to the patient's condition, symptoms, "
        "medical history, and doctor's recommendations. Do not omit critical details but keep it concise."
        "Give the result in Brazillian Portuguese."
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": condense_prompt},
                {"role": "user", "content": dialog},
            ],
            max_tokens=1500,
            temperature=0.1  # Menor variabilidade para consistência
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Erro ao condensar diálogo: {e}")
        return None

def process_chunk(patient_id, chunk_num, refined_content):
    """Processa um chunk individual e salva a versão condensada"""
    condensed_content = condense_dialog(refined_content)
    if not condensed_content:
        return False
    
    # Garante que o diretório de saída existe
    output_dir = os.path.join(CONDENSED_DIR, patient_id)
    os.makedirs(output_dir, exist_ok=True)
    
    # Salva o arquivo condensado
    output_path = os.path.join(output_dir, f"patient_{patient_id}_condensed_dialog_chunk_{chunk_num}.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(condensed_content)
    
    return True

def get_refined_chunks(patient_id):
    """Lista todos os chunks refinados disponíveis em ordem numérica"""
    patient_dir = os.path.join(REFINED_DIR, patient_id)
    if not os.path.exists(patient_dir):
        return []
    
    chunk_files = glob.glob(os.path.join(patient_dir, "patient_*_refined_transcription_chunk_*.txt"))
    # Ordena numericamente pelo número do chunk
    chunk_files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
    return chunk_files

# COMEÇO !=0. para processar a partir de um chunk específico, ex.: 36
# def process_patient(patient_id, start_from=36):
def process_patient(patient_id, start_from=0):
    """Processa todos os chunks refinados de um paciente"""
    chunk_files = get_refined_chunks(patient_id)
    if not chunk_files:
        print(f"Nenhum chunk refinado encontrado para o paciente {patient_id}")
        return
    
    print(f"Processando paciente {patient_id} ({len(chunk_files)} chunks encontrados)...")
    
    # # COMEÇO !=0. Carrega o último chunk processado antes do start_from (se existir)
    # previous_chunk = None
    # if start_from > 0:
    #     try:
    #         previous_file = os.path.join(REFINED_DIR, patient_id, 
    #                                   f"patient_{patient_id}_refined_transcription_chunk_{start_from-1}.txt")
    #         if os.path.exists(previous_file):
    #             with open(previous_file, "r", encoding="utf-8") as f:
    #                 previous_chunk = f.read()
    #             print(f"Carregado chunk {start_from-1} como base para continuidade")
    #     except Exception as e:
    #         print(f"AVISO: Não foi possível carregar chunk anterior: {e}")

    for chunk_file in chunk_files:
        chunk_num = int(os.path.basename(chunk_file).split('_')[-1].split('.')[0])
        
        # Pula chunks antes do ponto de início
        if chunk_num < start_from:
            continue
        
        # Processa o chunk
        with open(chunk_file, "r", encoding="utf-8") as f:
            refined_content = f.read()
        
        # # NOVO: Se existir conteúdo prévio, adiciona ao atual
        # if previous_chunk and chunk_num == start_from:
        #     refined_content = previous_chunk + " " + refined_content

        print(f"Condensando chunk {chunk_num}...")
        success = process_chunk(patient_id, chunk_num, refined_content)
        
        if not success:
            print(f"Falha ao condensar chunk {chunk_num}")
            continue
        
        print(f"Chunk {chunk_num} condensado com sucesso")

def main():
    # Cria diretório base para arquivos condensados
    os.makedirs(CONDENSED_DIR, exist_ok=True)
    
    # Processa pacientes (no exemplo, apenas paciente 18)
    for patient_id in ["018"]:  # Formato com padding zero
        process_patient(patient_id, start_from=0)
        # process_patient(patient_id, start_from=36)  # COMEÇO !=0. start_from=14 para começar do chunk 14

if __name__ == "__main__":
    main()