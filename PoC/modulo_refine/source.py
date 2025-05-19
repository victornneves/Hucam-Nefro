import os
from openai import OpenAI
import dotenv
import glob

dotenv.load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

DATASET_DIR = "../modulo_transcribe/data/transcriptions"
PRIMER_PATH = "../../GptPrompts/Primer.txt"
MAX_TOKENS = 3000


def load_primer(primer_path):
    with open(primer_path, "r", encoding="utf-8") as f:
        return f.read()


def split_into_chunks(text, max_length):
    words = text.split()
    chunks = []
    current_chunk = []
    for word in words:
        if len(" ".join(current_chunk + [word])) > max_length:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
        else:
            current_chunk.append(word)

    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks


def process_transcription(primer, text_chunk):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": primer},
                {"role": "user", "content": text_chunk},
            ],
            max_tokens=MAX_TOKENS,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error processing transcription: {e}")
        return None


def get_speaker(patient_id):
    gt_file = f"../../Dataset-Hucam-Nefro/patient_{patient_id}/patient_{patient_id}_transcription_gt.txt"
    with open(gt_file) as fp:
        lines = fp.readlines()
    speakers = [x.split(":")[0] for x in lines]
    speakers = list(set(speakers))  # unique
    return speakers


def save_processed_transcription(output_path, content):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


# Lista todos os arquivos de chunk em ordem numérica
def get_chunk_files(patient_dir):
    chunk_files = glob.glob(os.path.join(patient_dir, "patient_*_consult_audio_chunk_*.txt"))
    # Ordena numericamente pelo número do chunk
    chunk_files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
    return chunk_files


def process_all_files():
    # Cria o diretório base 'refined' se não existir
    os.makedirs("data/refined", exist_ok=True)

    # for i in range(19, 27):
    for i in [18]:
        patient_id = f"{i:03}"
        patient_dir = os.path.join(DATASET_DIR, patient_id)

        # Verifica se diretório do paciente existe
        if not os.path.exists(patient_dir):
            print(f"Patient {patient_dir} directory not found")
            continue

        # # Output files for each pass
        # output_file = f"data/refined/{patient_id}/patient_{patient_id}_refined_transcription.txt"

        # Carrega primer e informações uma vez por paciente
        primer = load_primer(PRIMER_PATH)
        speakers = get_speaker(patient_id)
        primer = f"{primer}\n\nOs participantes da conversa são: {', '.join(speakers)}"

        if i in [4, 5, 21]:
            primer = f"{primer}\n\nEssa consulta é feita com um médico residente, por volta do meio da consulta entra em cena o MEDICO_SUPERVISOR que repassa o trabalho do médico residente."

        # Obtém todos os chunks em ordem
        chunk_files = get_chunk_files(patient_dir)

        if not chunk_files:
            print(f"Nenhum chunk encontrado para o paciente {patient_id}")
            continue

        # Processa cada chunk em ordem
        for chunk_file in chunk_files:
            # Extrai número do chunk do nome do arquivo
            chunk_num = os.path.basename(chunk_file).split('_')[-1].split('.')[0]
            
            # Define arquivo de saída
            output_file = f"data/refined/{patient_id}/patient_{patient_id}_refined_transcription_chunk_{chunk_num}.txt"
            
            # Processa o chunk
            with open(chunk_file, "r", encoding="utf-8") as fp:
                transcription = fp.read()
                chunks = split_into_chunks(transcription, MAX_TOKENS - len(primer)//4)
                
                results = []
                for idx, chunk in enumerate(chunks):
                    print(f"Parte {idx + 1}/{len(chunks)}: processando chunk {chunk_num}...")
                    result = process_transcription(primer, chunk)
                    results.append(result if result else "[ERRO NO PROCESSAMENTO]")
                
                # Salva resultado refinado
                save_processed_transcription(output_file, "\n".join(results))
                print(f"Transcrição refinada salva em: {output_file}")


if __name__ == "__main__":
    process_all_files()
