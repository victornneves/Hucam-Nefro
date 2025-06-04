from pydub import AudioSegment
from pydub.effects import compress_dynamic_range
import os

audio_file = "/home/lauro/Documents/audios-Hucam/patient_027_consult_audio.m4a"

try:
    # Carrega o áudio original
    original = AudioSegment.from_file(audio_file)

    # Pré-processamento
    processed = (
        original
        .high_pass_filter(800)     # Filtro para ruídos ambientais
        .set_channels(1)           # Mono
        .set_frame_rate(16000)     # Taxa de amostragem
    )

    processed = compress_dynamic_range(
        processed,
        threshold=-26.0,  # dBFS
        ratio=4.0,        # 4:1
        attack=5,         # ms
        release=50        # ms
    ).apply_gain(8.0)    # Ganho pós-compressão

    # Cria o caminho para salvar o novo arquivo
    base, ext = os.path.splitext(audio_file)
    processed_path = f"{base}_processed{ext}"

    # Exporta o áudio processado
    processed.export(processed_path, format="wav")
    print(f"Áudio processado salvo em: {processed_path}")

except Exception as e:
    print(f"AVISO: Pré-processamento parcialmente aplicado - {str(e)}")
