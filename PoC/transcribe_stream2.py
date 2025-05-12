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
        processed = chunk.high_pass_filter(800)
        
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
        
        # # Configurar caminhos de saída
        # dir_atual = os.path.dirname(os.path.abspath(__file__))
        # output_dir = os.path.join(dir_atual, "transcriptions")
        # os.makedirs(output_dir, exist_ok=True)
        
        # nome_base = os.path.splitext(os.path.basename(caminho_audio))[0]
        # output_path = os.path.join(output_dir, f"{nome_base}_stream_processed.txt")

        # Configuração de saída
        output_dir = os.path.join(os.path.dirname(__file__), "transcriptions")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 
                                f"{os.path.splitext(os.path.basename(caminho_audio))[0]}_processed.txt")
        
        with open(output_path, "w", encoding="utf-8") as f:
            print("Iniciando processamento do stream...\n")

            # # Teste de formato de áudio
            # print("Formato do áudio:")
            # print(f"• Canais: {audio.channels}")
            # print(f"• Sample rate: {audio.frame_rate}Hz")
            # print(f"• Duração: {len(audio)/1000}s")
            # print(f"• Bit depth: {audio.sample_width * 8}-bit")         

            # Contexto médico em português brasileiro
            medical_prompt = "Consulta médica em português do Brasil. Termos técnicos: anamnese, diagnóstico, tratamento, sintomas, medicamentos. Fala de médico e paciente"
            
            for i, chunk in enumerate(chunks):

                # Aplicar pré-processamento
                chunk_processado = aplicar_preprocessamento(chunk)

                # Converter para formato de reprodução correto
                samples = np.array(chunk.get_array_of_samples(), dtype=np.float32)
                samples /= 32768.0  # Normalizar para float32 [-1.0, 1.0]
                
                # # Reproduzir áudio
                # print(f"▶ Reproduzindo chunk {i+1} ({len(chunk)/1000}s)")
                # sd.play(samples, chunk.frame_rate)

                # Reprodução (opcional)
                try:
                    sd.play(samples, blocking=True)
                except Exception as e:
                    print(f"AVISO: Reprodução não disponível - {str(e)}")
                
                # # Processar com Whisper (sem configurações específicas para PT-BR médico)
                # resultado = model.transcribe(samples, fp16=False)
                # texto = resultado["text"]

                # Processar com Whisper com configurações específicas para PT-BR médico
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

                # # Escrever resultados de forma contínua (sem marcação de chunks)
                # f.write(texto + " ")  # Espaço entre segmentos para evitar junção de palavras
                # f.flush()

                # # Exibir resultados
                # print(f"✓ Transcrição {i+1}:\n{texto}\n{'-'*50}")
                # sd.wait()  # Aguardar término da reprodução
                
        print(f"\nProcessamento completo! Arquivo salvo em:\n{output_path}")
        return True
    
        # # Retornar a transcrição completa
        # with open(output_path, "r", encoding="utf-8") as f:
        #     return f.read()
        
    except Exception as e:
        print(f"Erro: {str(e)}")
        return False

# Uso
if __name__ == "__main__":
    caminho_audio = "/home/marianasegato/Documentos/patient_024_consult_audio.wav"
    transcricao_completa = transcrever_audio_stream(caminho_audio)
    if transcricao_completa:
        print("\nTranscrição final consolidada:")