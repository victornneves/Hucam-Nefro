import whisper
import os
import sounddevice as sd
import numpy as np
from pydub import AudioSegment
from pydub.utils import make_chunks
from pydub.effects import compress_dynamic_range

# TO DO (quando/se necessário): configurar o ALSA para evitar underrun

def aplicar_preprocessamento(chunk):
    """Aplica o pipeline de pré-processamento descrito no paper"""
    try:
        # 1. High-pass filter (800 Hz cutoff)
        processed = (chunk
                   .high_pass_filter(800)  # Filtro para ruídos ambientais
                   .set_channels(1)       # Garante mono
                   .set_frame_rate(16000) # Taxa de amostragem ideal
                   )
        
        # 2. Dynamic range compression
        processed = compress_dynamic_range(
            processed,
            threshold=-26.0,  # dBFS
            ratio=4.0,        # 4:1
            attack=5,         # ms
            release=50        # ms
        ).apply_gain(8.0)    # 8dB post-gain (paper specification)
        
        return processed
    except Exception as e:
        print(f"AVISO: Pré-processamento parcialmente aplicado - {str(e)}")
        return chunk

def transcrever_audio_stream(caminho_audio):
    try:
        # Carregar modelo (escolha entre 'tiny', 'base', 'small', 'medium', 'large')
        model = whisper.load_model("small")

        # Configuração do sistema de áudio
        sd.default.samplerate = 16000
        sd.default.channels = 1
        sd.default.dtype = 'float32'
        sd.default.latency = 'high'
        
        # Carregar áudio e converter para formato adequado
        audio = AudioSegment.from_file(caminho_audio)
        audio = audio.set_frame_rate(16000).set_channels(1)  # Whisper prefere 16kHz mono
        
        # Dividir em chunks de 15 segundos
        chunk_length = 15000  # milissegundos
        chunks = make_chunks(audio, chunk_length)

        # Configuração de saída
        output_dir = os.path.join(os.path.dirname(__file__), "transcriptions")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 
                                f"{os.path.splitext(os.path.basename(caminho_audio))[0]}_processed.txt")
        
        with open(output_path, "w", encoding="utf-8") as f:
            print("Iniciando processamento do stream...\n")

            # Contexto médico em português brasileiro
            medical_prompt = "Consulta médica em português do Brasil. Termos técnicos: anamnese, diagnóstico, tratamento, sintomas, medicamentos. Fala de médico e paciente"
            
            for i, chunk in enumerate(chunks):

                chunk_processado = aplicar_preprocessamento(chunk)

                # Converter para formato de reprodução correto
                samples = np.array(chunk_processado.get_array_of_samples(), dtype=np.float32)
                samples /= 32768.0  # Normalizar para float32 [-1.0, 1.0]

                # Reproduzir áudio
                try:
                    sd.play(samples, blocking=True)
                except Exception as e:
                    print(f"AVISO: Reprodução não disponível - {str(e)}")

                # Processar com Whisper
                resultado = model.transcribe(
                    samples,
                    language='pt',
                    task='transcribe',
                    fp16=False,
                    initial_prompt=medical_prompt,
                    compression_ratio_threshold=2.0,
                    temperature=0.1  # Reduz variações para maior consistência
                )
                texto = resultado["text"]
                
                # Saída contínua
                clean_text = resultado["text"].replace("  ", " ").strip()
                f.write(clean_text + " ")
                f.flush()
                
                print(f"CHUNK {i+1}:\n{clean_text}\n{'-'*50}")
                
        print(f"\nProcessamento completo! Arquivo salvo em:\n{output_path}")
        return True
        
    except Exception as e:
        print(f"Erro: {str(e)}")
        return False

# Uso
if __name__ == "__main__":
    caminho_audio = "/home/marianasegato/Documentos/patient_018_consult_audio.wav"
    transcricao_completa = transcrever_audio_stream(caminho_audio)
    if transcricao_completa:
        print("\nTranscrição final consolidada:")