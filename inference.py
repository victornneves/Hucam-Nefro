import os
from openai import OpenAI
import dotenv

dotenv.load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

DATASET_DIR = "Dataset-Hucam-Nefro"
PRIMER_PATH = "GptPrompts/Primer.txt"
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
                {"role": "user", "content": text_chunk}
            ],
            max_tokens=MAX_TOKENS,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error processing transcription: {e}")
        return None

def save_processed_transcription(output_path, content):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

def process_all_files():
    primer = load_primer(PRIMER_PATH)

    
    # for i in range(1, 17):
    for i in [1]:
        patient_id = f"{i:03}"
        whisper_file = f"Dataset-Hucam-Nefro/patient_{patient_id}/patient_{patient_id}_transcription_whisper.txt"
        output_file = f"Dataset-Hucam-Nefro/patient_{patient_id}/patient_{patient_id}_transcription_pred_gpt4.txt"
        
        with open(whisper_file, "r", encoding="utf-8") as fp:
            transcription = fp.read()

            chunks = split_into_chunks(transcription, max_length=MAX_TOKENS - len(primer) // 4)
            # for chunk in chunks:
            #     print(len(chunk), chunk[:100])

            processed_content = []
            for idx, chunk in enumerate(chunks):
                print(f"Processing chunk {idx + 1}/{len(chunks)}...")
                result = process_transcription(primer, chunk)
                if result:
                    processed_content.append(result)
                else:
                    processed_content.append("[ERROR PROCESSING CHUNK]")

            save_processed_transcription(output_file, "\n".join(processed_content))
            print(f"Saved processed transcription to {output_file}")


if __name__ == "__main__":
    process_all_files()
