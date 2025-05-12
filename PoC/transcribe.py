import whisper
import os

def transcrever_audio_local(caminho_audio):
    try:
        # Carregar modelo (escolha entre 'tiny', 'base', 'small', 'medium', 'large')
        model = whisper.load_model("small")
        
        # Transcrição
        resultado = model.transcribe(caminho_audio)
        texto = resultado["text"]
        
        # Obter diretório atual do script
        dir_atual = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(dir_atual, "transcriptions")
        
        # Criar pasta se não existir
        os.makedirs(output_dir, exist_ok=True)
        
        # Criar nome do arquivo de saída
        nome_base = os.path.splitext(os.path.basename(caminho_audio))[0]
        nome_arquivo = f"{nome_base}.txt"
        caminho_saida = os.path.join(output_dir, nome_arquivo)
        
        # Salvar arquivo
        with open(caminho_saida, "w", encoding="utf-8") as f:
            f.write(texto)
        
        print(f"Arquivo salvo com sucesso em: {caminho_saida}")
        return texto
        
    except Exception as e:
        print(f"Erro ao processar o arquivo: {str(e)}")
        return None

# Uso
if __name__ == "__main__":
    caminho_audio = "/home/marianasegato/Documentos/patient_024_consult_audio.wav"
    texto_transcrito = transcrever_audio_local(caminho_audio)
    
    if texto_transcrito:
        print("Texto transcrito com sucesso!")