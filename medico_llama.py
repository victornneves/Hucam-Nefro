import yaml

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


# def get_diagnosis(hd):
#     try:
#         stage = hd["estagio_drc"]
#         drc = ""
#         drc += f"DRC: G{stage['grau']}"
#         if alb := stage.get("albuminuria"):
#             drc += f"/A{alb}"
#         drc += "\nFunção renal atual: " + stage.get("funcao_rim_atual")
#         if et := hd.get("etiologia_doença_de_base"):
#             drc += "\nEtiologia: " + et
#         return drc
#     except TypeError:
#         return hd

def get_diagnosis(hd):
    try:
        stage = hd["estagio_drc"]
        drc = ""
        drc += f"{stage['grau']}"
        if et := hd.get("etiologia_doença_de_base"):
            drc += " " + et
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
    
def get_prediction(patient_id):
    with open(
        f"results/patient_{patient_id}/outputs.yaml"
    ) as fp:
        return yaml.safe_load(fp)

def load_yaml(file_path):
    """Load a YAML file and return its content."""
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_field(data, field_path):
    """Safely retrieve a nested field from a dictionary."""
    keys = field_path.split(".")
    for key in keys:
        data = data.get(key, {})
    return data


import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Define cache directory
cache_dir = "/media/dataset_ego4d/models"

# Load the LLama3 model and tokenizer
model_name = "aaditya/OpenBioLLM-Llama3-8B"
tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
model = AutoModelForCausalLM.from_pretrained(model_name, cache_dir=cache_dir)

# Define prompt template for the medical evaluator
# prompt_template = (
#     "You are a medical evaluator tasked with comparing two texts related to medical diagnoses, clinical impressions, or proposed conduct. "
#     "Your job is to assign a similarity score from 0 to 10, where 0 indicates complete discrepancy (e.g., antonyms or unrelated terms) "
#     "and 10 indicates total similarity (e.g., synonymous terms or identical meanings). "
#     "Consider the context, medical terminology, and overall meaning.\n\n"
#     "Ground Truth: {ground_truth}\n"
#     "Prediction: {prediction}\n\n"
#     "Score: "
# )
def evaluate_similarity_with_prompt(gt_text, pred_text):
    """
    Evaluate the similarity between ground truth and predicted text using the model.
    """
    prompt_template = (
        "You are a medical evaluator. Your task is to rate the similarity between two medical texts: "
        "the ground truth and the predicted text. Provide a score from 0 to 10, where 0 means no similarity "
        "and 10 means perfect similarity. Consider synonyms, clinical context, and overall meaning.\n\n"
        "Ground Truth:\n{gt_text}\n\nPredicted Text:\n{pred_text}\n\n"
        "Your response should only contain the similarity score."
    )

    # Build the prompt
    prompt = prompt_template.format(gt_text=gt_text, pred_text=pred_text)
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, padding=True, max_length=1024)  # Truncate long inputs

    # Generate a response
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=256)  # Use max_new_tokens instead of max_length
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response    

def evaluate_patient(patient_id):
    """Evaluate a single patient's predictions against the ground truth."""
    # Load YAML files
    ground_truth = get_summary(patient_id)
    prediction = get_prediction(patient_id)

    # Extract fields
    gt_diagnosis = get_diagnosis(ground_truth["relatorio_consulta_ambulatorial_nefrologia"]["hipoteses_diagnosticas"])
    pred_diagnosis = get_diagnosis(prediction["hipoteses_diagnosticas"])

    gt_conduct = "\n".join(readable_string(x) for x in get_field(ground_truth["relatorio_consulta_ambulatorial_nefrologia"], "conduta"))
    pred_conduct = "\n".join(readable_string(x) for x in get_field(prediction, "conduta"))

    impressão = ground_truth["relatorio_consulta_ambulatorial_nefrologia"].get("impressão", [])
    if impressão is None:
        gt_impression = "Não há impressão diagnóstica."
    else:
        gt_impression = "\n".join(readable_string(x) for x in impressão)
    pred_impression = "\n".join(readable_string(x) for x in prediction.get("impressão", []))

    # Evaluate similarity
    diagnosis_score = evaluate_similarity_with_prompt(gt_diagnosis, pred_diagnosis)
    conduct_score = evaluate_similarity_with_prompt(gt_conduct, pred_conduct)
    impression_score = evaluate_similarity_with_prompt(gt_impression, pred_impression)

    # Compile results
    return {
        "patient_id": patient_id,
        "Diagnosis Similarity": diagnosis_score,
        "Conduct Similarity": conduct_score,
        "Impression Similarity": impression_score
    }

# Iterate over patients and compile results
results = []
# for patient_id in range(1, 17):
for patient_id in [1]:
    print(f"Evaluating patient {patient_id}")
    patient_results = evaluate_patient(patient_id)
    if patient_results:
        results.append(patient_results)

# Save results to a DataFrame
results_df = pd.DataFrame(results)
results_df.to_csv("medical_similarity_results.csv", index=False)
print("Evaluation complete. Results saved to 'medical_similarity_results.csv'.")
