import whisper
import os
import sounddevice as sd
import numpy as np
from pydub import AudioSegment
from pydub.utils import make_chunks
from pydub.effects import compress_dynamic_range

def aplicar_preprocessamento(chunk):
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

# chunksize em segundos
def transcrever_audio_stream(paciente, chunksize=15):
    caminho_audio = f"/home/marianasegato/Documentos/audios-Hucam/patient_{paciente:03d}_consult_audio.wav"
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
        
        chunk_length = chunksize * 1000  # milissegundos
        chunks = make_chunks(audio, chunk_length)

        # Configuração de saída
        output_dir = os.path.join(os.path.dirname(__file__), f"data/transcriptions/{paciente:03d}")
        os.makedirs(output_dir, exist_ok=True)
        
        concatenated_text = ""

        '''para processar a partir de determinado (ex.: chunk 37)'''
        # # Carrega o texto já transcrito até o chunk 36 (se existir)
        # try:
        #     if os.path.exists(os.path.join(output_dir, f"patient_{paciente:03d}_consult_audio_chunk_36.txt")):
        #         with open(os.path.join(output_dir, f"patient_{paciente:03d}_consult_audio_chunk_36.txt"), "r", encoding="utf-8") as f:
        #             concatenated_text = f.read() + " "
        # except:
        #     pass

        for i, chunk in enumerate(chunks):

            '''para processar a partir de determinado (ex.: chunk 37)'''
            # # MODIFICAÇÃO TEMPORÁRIA - Pula chunks antes do 37
            # if i < 37:
            #     print(f"Pulando chunk {i} (processando apenas a partir do chunk 37)")
            #     continue
            
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
                compression_ratio_threshold=2.0,
                temperature=0.1  # Reduz variações para maior consistência
            )

            # Acumula o texto transcrito
            clean_text = resultado["text"].replace("  ", " ").strip()
            concatenated_text += clean_text + " "
            
            # Saída contínua
            output_path = os.path.join(output_dir, f"patient_{paciente:03d}_consult_audio_chunk_{i}.txt")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(concatenated_text.strip())
                f.flush()

            print(f"CHUNK {i+1}:\n{clean_text}\n{'-'*50}")
                
        print(f"\nProcessamento completo!")
        return True
        
    except Exception as e:
        print(f"Erro: {str(e)}")
        return False

# Uso
if __name__ == "__main__":
    paciente = 18
    transcricao_completa = transcrever_audio_stream(paciente)
    if transcricao_completa:
        print("\nTranscrição final consolidada:")