import whisper
import os
import sounddevice as sd
import numpy as np
from pydub import AudioSegment
from pydub.utils import make_chunks
from pydub.effects import compress_dynamic_range
from openai import OpenAI
import threading
import queue
import dotenv

dotenv.load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# TO DO: alterar "Salva resumo final" para salvar em uma pasta, e com o nome do paciente(?)

# Configurações
AUDIO_CHUNK_SIZE = 15000  # 15s em ms
TRANSCRIPTION_CHUNK_SIZE = 30000  # 30s em ms (para condensação)
GPT_MODEL = "gpt-4"
WHISPER_MODEL = "small"
CONTEXT_FILE = "resumo_condensado.txt"
CONTEXT_HISTORY = []  # Armazena todos os resumos parciais

# Filas para comunicação entre threads
audio_queue = queue.Queue()  # Chunks de áudio para reprodução
transcription_queue = queue.Queue()  # Chunks de transcrição para condensação
summary_queue = queue.Queue()  # Resumos condensados

# Inicializa clients
whisper_model = whisper.load_model(WHISPER_MODEL)
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def aplicar_preprocessamento(chunk):
    try:
        processed = (chunk
                   .high_pass_filter(800)
                   .set_channels(1)
                   .set_frame_rate(16000))
        processed = compress_dynamic_range(processed, threshold=-26.0, ratio=4.0).apply_gain(8.0)
        return processed
    except Exception as e:
        print(f"AVISO: Pré-processamento parcial - {str(e)}")
        return chunk

def transcrever_chunk(chunk_audio):
    samples = np.array(chunk_audio.get_array_of_samples(), dtype=np.float32) / 32768.0
    resultado = whisper_model.transcribe(
        samples,
        language='pt',
        initial_prompt="Consulta médica em português. Termos técnicos: anamnese, diagnóstico, tratamento."
    )
    return resultado["text"].strip()

def reproduzir_audio():
    """Thread 1: Reproduz chunks de áudio em tempo real."""
    sd.default.samplerate = 16000
    sd.default.channels = 1
    sd.default.dtype = 'float32'
    sd.default.blocksize = 2048  # Aumenta o buffer para reduzir underruns
    sd.default.latency = 'high'  # Prioriza estabilidade sobre latência

    while True:
        chunk = audio_queue.get()
        if chunk is None:  # Sinal de parada
            break
        samples = np.array(chunk.get_array_of_samples()) / 32768.0
        sd.play(samples, blocking=True)

def processar_transcricao():
    """Thread 2: Acumula transcrições e condensa a cada TRANSCRIPTION_CHUNK_SIZE."""

    global CONTEXT_HISTORY

    buffer = []
    acumulado = ""
    output_path = "resumo_condensado.txt"  # Caminho do arquivo de saída

    # Cria/Clear o arquivo no início
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("")  # Inicializa vazio

    while True:
        texto = transcription_queue.get()
        if texto is None:
            # if buffer:  # Processa qualquer texto restante
            #     dialogo = " ".join(buffer)
            #     resumo = condensar_dialogo(dialogo)
            #     summary_queue.put(resumo)
            #     with open(output_path, "a", encoding="utf-8") as f:
            #         f.write(resumo + "\n\n")
            break

        buffer.append(texto)
        # Condensa a cada 30s (2 chunks de 15s)
        if len(buffer) >= (TRANSCRIPTION_CHUNK_SIZE // AUDIO_CHUNK_SIZE):
            dialogo = " ".join(buffer)
            novo_resumo = condensar_dialogo(dialogo, acumulado)

            # atualiza contexto
            acumulado = novo_resumo
            CONTEXT_HISTORY.append(novo_resumo)

            # Reescreve o arquivo completo com o resumo mais recente
            with open(CONTEXT_FILE, "w", encoding="utf-8") as f:
                f.write(acumulado)
            
            buffer = [] # Limpa o buffer após condensação

def condensar_dialogo(texto, acumulado_anterior):
    """Usa GPT-4 para condensar o diálogo."""
    prompt = f"""
    Você é um assistente médico que resume consultas de nefrologia em português.
    
    - **Contexto prévio**: {acumulado_anterior[:2000]}  # Limita para não exceder tokens
    - **Novo diálogo**: {texto}

    **Instruções**:
    1. Combine o contexto prévio com o novo diálogo.
    2. Mantenha apenas informações médicas relevantes:
       - Sintomas, diagnósticos, medicamentos, exames.
    3. Remova repetições e torne o texto coeso.
    4. **NUNCA** comente sobre qualidade do diálogo (ex: "confuso", "incoerente").
    5. Saída deve ser em português, claro e direto.

    **Exemplo de saída**:
    "Paciente relata dor lombar e edema. Médico ajusta dose de Losartan e solicita creatinina."
    """

    try:
        response = openai_client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": texto},
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Erro no GPT-4: {e}")
        return acumulado_anterior

def transcrever_audio_stream(caminho_audio):
    audio = AudioSegment.from_file(caminho_audio).set_frame_rate(16000).set_channels(1)
    chunks = make_chunks(audio, AUDIO_CHUNK_SIZE)

    # Inicia threads
    threads = [
        threading.Thread(target=reproduzir_audio),
        threading.Thread(target=processar_transcricao),
    ]

    for t in threads:
        t.start()

    # Inicia thread de processamento
    transcription_thread = threading.Thread(target=processar_transcricao)
    transcription_thread.start()

    # Processa chunks
    for i, chunk in enumerate(chunks):
        chunk_processado = aplicar_preprocessamento(chunk)
        audio_queue.put(chunk_processado)  # Reproduz em tempo real
        
        # Transcreve e envia para condensação (em velocidade acelerada)
        texto = transcrever_chunk(chunk_processado)
        transcription_queue.put(texto)
        print(f"Chunk {i+1} transcrito: {texto[:50]}...")

    # Finaliza threads
    audio_queue.put(None)
    transcription_queue.put(None)
    for t in threads:
        t.join()

    # Ao final, salva o contexto histórico se necessário
    with open("resumo_final_completo.txt", "w", encoding="utf-8") as f:
        f.write("\n\n---\n\n".join(CONTEXT_HISTORY))

    print(f"Resumo condensado salvo.")

if __name__ == "__main__":
    transcrever_audio_stream("/home/marianasegato/Documentos/audios-Hucam/patient_022_consult_audio.wav")