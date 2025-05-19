import os
from openai import OpenAI
import dotenv

dotenv.load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

DATASET_DIR = "/mnt/external8tb/datasets/Dataset-Hucam-Nefro/PoC"
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
                {"role": "user", "content": text_chunk},
            ],
            max_tokens=MAX_TOKENS,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error processing transcription: {e}")
        return None


def process_refinement(primer, processed_chunk):
    """Run the second pass for fine adjustments."""
    refinement_primer = (
        f"{primer}\n\n"
        "Refine the following dialogue by:\n"
        "- Correcting words out of context or non-existent words.\n"
        "- Substituting incorrect terms with the most likely clinical terms, especially for nephrology.\n"
        "- Removing noise, incoherent text, or redundant phrases.\n\n"
        "Dialogue for refinement:\n"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": refinement_primer},
                {"role": "user", "content": processed_chunk},
            ],
            max_tokens=MAX_TOKENS,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error refining transcription: {e}")
        return None


def process_interaction_coherence(primer, refined_chunk):
    """Run the third pass to ensure interaction coherence."""
    coherence_primer = (
        f"{primer}\n\n"
        "Ensure coherence in interactions by:\n"
        "- Verifying that the speech aligns with the role of each participant.\n"
        "- Doctors give guidance, ask technical questions, and request exams or treatment adjustments.\n"
        "- Patients answer questions, report symptoms or concerns, and confirm instructions.\n"
        "- Accompanying persons refer to the patient in the third person and may ask for clarifications.\n\n"
        "Review the dialogue below and correct any inconsistencies:\n"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": coherence_primer},
                {"role": "user", "content": refined_chunk},
            ],
            max_tokens=MAX_TOKENS,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error ensuring interaction coherence: {e}")
        return None


def get_speaker(patient_id):
    gt_file = f"/mnt/external8tb/datasets/Dataset-Hucam-Nefro/patient_{patient_id}/patient_{patient_id}_transcription_gt.txt"
    with open(gt_file) as fp:
        lines = fp.readlines()
    speakers = [x.split(":")[0] for x in lines]
    speakers = list(set(speakers))  # unique
    return speakers


def save_processed_transcription(output_path, content):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


def process_all_files():
    for i in range(19, 27):
        primer = load_primer(PRIMER_PATH)
        patient_id = f"{i:03}"
        whisper_file = f"{DATASET_DIR}/patient_{patient_id}/patient_{patient_id}_transcription_whisper.txt"

        # Output files for each pass
        output_file_first_pass = f"{DATASET_DIR}/patient_{patient_id}/patient_{patient_id}_transcription_first_pass.txt"

        speakers = get_speaker(patient_id)
        primer = f"{primer}\n\nOs participantes da conversa são: {', '.join(speakers)}"
        if i in [4, 5, 21]:
            primer = f"{primer}\n\nEssa consulta é feita com um médico residente, por volta do meio da consulta entra em cena o MEDICO_SUPERVISOR que repassa o trabalho do médico residente."

        with open(whisper_file, "r", encoding="utf-8") as fp:
            transcription = fp.read()

            chunks = split_into_chunks(
                transcription, max_length=MAX_TOKENS - len(primer) // 4
            )

            first_pass_results = []

            for idx, chunk in enumerate(chunks):
                print(f"Processing chunk {idx + 1}/{len(chunks)} (First Pass)...")
                first_result = process_transcription(primer, chunk)
                if first_result:
                    first_pass_results.append(first_result)
                else:
                    first_pass_results.append("[ERROR PROCESSING CHUNK]")

            # Save the results of each pass
            save_processed_transcription(
                output_file_first_pass, "\n".join(first_pass_results)
            )

            print(f"Saved first pass to {output_file_first_pass}")


if __name__ == "__main__":
    process_all_files()

"""
# usar o1 também

1 - fazer a predição do diagnotisco a partir do dialog predito e do ground truth, comparar
2 - ver como o diagnositico groud truth (do medico) compara com os dois

Se o ponto 1 ficar muito discrepantes, boa no paper a comparação com 2, pra ver o quão distante ficou

Testar passando os exames, e sem os exames (os exames como uma "melhoria fácil" do sistema)

O ponto 1, comparar o GT feito na mão com o  resultado final, diz o quão bom a gpt é 
considerando um método melhor de extrair os áudios (inclusive sabendo quem são os interlocutores)
(trabalhos futuros)
"""
