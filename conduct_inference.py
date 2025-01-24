import os
from openai import OpenAI
import dotenv
import yaml


dotenv.load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MAX_TOKENS = 3000  # Token limit to leave room for the response


def format_dict(data, indent=0):
    """
    Recursively formats a dictionary or list into a readable string.
    """
    formatted = []
    prefix = "  " * indent  # Indentation for nesting
    if isinstance(data, dict):
        for key, value in data.items():
            formatted.append(f"{prefix}{key}:")
            formatted.append(format_dict(value, indent + 1))
    elif isinstance(data, list):
        for item in data:
            formatted.append(f"{prefix}- {format_dict(item, indent + 1).strip()}")
    else:
        # For strings, numbers, or other types
        formatted.append(f"{prefix}{data}")
    return "\n".join(formatted)


def readable_string(data):
    if isinstance(data, dict):
        # return json.dumps(data, indent=2, ensure_ascii=False)
        return format_dict(data)
    return data


def get_diagnosis(summary):
    hd = summary["relatorio_consulta_ambulatorial_nefrologia"]["hipoteses_diagnosticas"]
    try:
        stage = hd["estagio_drc"]
        drc = ""
        drc += f"DRC: G{stage['grau']}"
        if alb := stage.get("albuminuria"):
            drc += f"/A{alb}"
        drc += "\nFunção renal atual: " + stage.get("funcao_rim_atual")
        if et := hd.get("etiologia_doença_de_base"):
            drc += "\nEtiologia: " + et
        return drc
    except TypeError:
        return hd


def get_field(summary, field):
    field = summary["relatorio_consulta_ambulatorial_nefrologia"][field]
    if isinstance(field, list):
        field = [readable_string(x) for x in field]
        return "\n".join(field)
    else:
        return field


def get_summary(patient_id):
    with open(
        f"Dataset-Hucam-Nefro/patient_{patient_id:03d}/patient_{patient_id:03d}_medical_summary.yaml"
    ) as fp:
        return yaml.safe_load(fp)


def split_into_chunks(text, max_length=2000):
    """Splits the text into chunks based on token limit."""
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

def condense_dialog(dialog):
    """Condenses a dialog into essential points using chunk processing."""
    condense_prompt = (
        "You will receive a portion of a medical consultation dialog. "
        "Please summarize the essential points relevant to the patient's condition, symptoms, "
        "medical history, and doctor's recommendations. Do not omit critical details but keep it concise."
        "Give the result in Brazillian Portuguese."
    )
    
    chunks = split_into_chunks(dialog, max_length=3000)  # Split dialog into manageable chunks
    condensed_chunks = []

    for idx, chunk in enumerate(chunks):
        print(f"Condensing chunk {idx + 1}/{len(chunks)}...")
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": condense_prompt},
                    {"role": "user", "content": chunk},
                ],
                max_tokens=1500,  # Allow room for responses
            )
            condensed_chunks.append(response.choices[0].message.content)
        except Exception as e:
            print(f"Error condensing chunk {idx + 1}: {e}")
            condensed_chunks.append("[ERROR PROCESSING CHUNK]")

    # Combine condensed chunks into a single summary
    final_summary = "\n\n".join(condensed_chunks)
    return final_summary


def derive_outputs(condensed_dialog, summary_fields):
    """Derives diagnosis hypothesis, clinical impression, and conduct from provided inputs."""
    # Define the prompt
    derive_prompt = (
        f"IMPORTANT: Dates are always in the format day/month/year. For example, '09/12/2025' means the 9th of January, 2024. "
        f"Using the provided medical consultation summary and patient file information, "
        f"generate the following outputs:\n"
        f"1. Diagnosis Hypothesis\n"
        f"The diagnosis hypothesis should include the patient's current stage of chronic kidney disease (CKD) the current renal function, and the etiology of the disease.\n"
        f"- The current renal function CURRENT_RENAL_FUNCTION can be calculated using the CKD-EPI formula. The results can be stage 1, 2, 3a, 3b, 4, or 5.\n"
        f"- For the CKD-EPI formula, use the patient's age and gender from the 'Patient Identification' section\n"
        f"- The creatinine level from the MOST RECENT exam from the 'Lab Exams' section. It should be as 'Cr' or similar\n"
        f"The formula is as follows: CKD-EPI Creatinine = 142 × (Scr / A)^B × 0.9938^age × (1.012 if female). \n"
        f"Where the constants A and B depend on the patient's gender and serum creatinine (Scr) level: \n"
        f"- For females: \n"
        f"  - If Scr ≤ 0.7: A = 0.7, B = -0.241. \n"
        f"  - If Scr > 0.7: A = 0.7, B = -1.2. \n"
        f"- For males: \n"
        f"  - If Scr ≤ 0.9: A = 0.9, B = -0.302. \n"
        f"  - If Scr > 0.9: A = 0.9, B = -1.2. \n"
        f"Use this formula to calculate the GFR accurately, considering the patient's age, sex, and most recent serum creatinine value.\n"
        f"\n"
        f"- The dates in the exam are in format day/month/year. The MOST RECENT exam refers to the exam closest to today's date (01/01/2025). Calculate an exact result using the CKD-EPI formula.\n"
        f"- From the CURRENT_RENAL_FUNCTION, determine the stage of CKD (STAGE_OF_CKD). Which is one of1, 2, 3, 3b, 4, 5\n"
        f"- The albuminuria can be calculated using the albumin/creatinine ratio from the laboratory exams. If these values are not present, leave it blank.\n"
        f"\n"
        f"2. Clinical Impression\n"
        f"3. Conduct\n"
        f"The conduct should include the doctor's recommendations, treatment plan, and follow-up instructions. If necessary, include medication adjustments such as dosage or frequency changes, interruptions, or new prescriptions.\n"
        f"The conduct should also specify the time for the next appointment in months and the need for new exams.\n"
        f"Make sure the outputs are precise and concise.\n"
        f"If there is not sufficent data for etiologia_doença_de_base, albuminuria, or funcao_rim_atual, leave the respective field blank.\n"
        f"Provide the result in Brazilian Portuguese."
        f"Provide the results in the yaml format like this:\n"
        """
        hipoteses_diagnosticas:
            estagio_drc:
                idade_paciente: XX anos
                sexo_paciente: XXX
                creatinina: XX mg/dL
                grau: STAGE_OF_CKD (put here just the value, do NOT write anything else)
                albuminuria: one of 1, 2, 3 (put here just the value, do NOT write anything else)
                funcao_rim_atual: CURRENT_RENAL_FUNCTION in ml/min/1.73m² (put here just the value and the unit, do NOT write anything else)
            etiologia_doença_de_base: XXX
        conduta: XXX
        impressão: XXX
        """
    )

    concatenated_info = (
        f"Condensed Dialog:\n{condensed_dialog}\n\n"
        f"Patient Identification:\n{summary_fields.get('identificacao_paciente', '')}\n\n"
        f"Historical Data:\n{summary_fields.get('historico_patologico_pregresso', '')}\n\n"
        f"Lab Exams:\n{summary_fields.get('exames_laboratoriais', '')}\n\n"
        f"Complementary Exams:\n{summary_fields.get('exames_complementares', '')}\n\n"
        f"Physical Exam:\n{summary_fields.get('exame_fisico', '')}\n\n"
        f"Medications:\n{summary_fields.get('medicamentos_em_uso', '')}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": derive_prompt},
                {"role": "user", "content": concatenated_info},
            ],
            max_tokens=MAX_TOKENS,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error deriving outputs: {e}")
        return None


def load_dialog(patient_id):
    PASS = "first"
    with open(
        f"Dataset-Hucam-Nefro/patient_{patient_id:03d}/patient_{patient_id:03d}_transcription_{PASS}_pass.txt",
        "r",
    ) as f:
        prediction = f.read()
    return prediction


def process_patient(patient_id, load_condensed=False):
    """Processes a single patient by summarizing dialog and deriving outputs."""
    # Fetch dialog and patient summary
    dialog = load_dialog(patient_id)
    summary = get_summary(patient_id)
    
    # Get fields from the summary
    fields = {
        "historico_patologico_pregresso": get_field(summary, "historico_patologico_pregresso"),
        "exames_laboratoriais": get_field(summary, "exames_laboratoriais"),
        "exames_complementares": get_field(summary, "exames_complementares"),
        "exame_fisico": get_field(summary, "exame_fisico"),
        "medicamentos_em_uso": get_field(summary, "medicamentos_em_uso"),
        "identificacao_paciente": get_field(summary, "identificacao_paciente"),
    }
    
    # Step 1: Condense the dialog in chunks
    print("Condensing dialog...")
    if load_condensed:
        print("Loading condensed dialog...")
        try:
            with open(f"old_results/patient_{patient_id}/condensed_dialog.txt", "r", encoding="utf-8") as f:
                condensed_dialog = f.read()
        except FileNotFoundError:
            condensed_dialog = None
    
    if not load_condensed or not condensed_dialog:
        print("Generating condensed dialog...")
        condensed_dialog = condense_dialog(dialog)
    
    if not condensed_dialog or "[ERROR PROCESSING CHUNK]" in condensed_dialog:
        print("Failed to fully condense dialog. Skipping patient.")
        return
    
    # Step 2: Derive outputs
    print("Deriving outputs...")
    outputs = derive_outputs(condensed_dialog, fields)
    if outputs:
        save_results(patient_id, condensed_dialog, outputs)
    else:
        print("Failed to derive outputs.")


def save_results(patient_id, condensed_dialog, outputs):
    """Saves the results to disk."""
    output_dir = f"results/patient_{patient_id}"
    os.makedirs(output_dir, exist_ok=True)

    with open(f"{output_dir}/condensed_dialog.txt", "w", encoding="utf-8") as f:
        f.write(condensed_dialog)

    with open(f"{output_dir}/outputs.yaml", "w", encoding="utf-8") as f:
        f.write(outputs)

    print(f"Results saved for patient {patient_id}.")


def main():
    # for patient_id in [6]:
    for patient_id in range(1, 17):  # Process all patients
        print(f"Processing patient {patient_id}...")
        process_patient(patient_id, load_condensed=True)


if __name__ == "__main__":
    main()
