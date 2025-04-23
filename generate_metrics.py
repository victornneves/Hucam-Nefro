import re
import difflib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rouge_score import rouge_scorer

PASS = "first"

def concatenate_speaker_lines(text, speaker):
    return " ".join([line.split(": ", 1)[1] for line in text.splitlines() if line.startswith(f"{speaker}:")])

def preprocess_text(text):
    # Convert to lowercase
    text = text.lower()
    # Remove common punctuation (dots, commas, etc.)
    text = re.sub(r'[^\w\s]', '', text)
    # Remove extra whitespace and split into words
    words = re.sub(r'\s+', ' ', text).strip().split()
    return words

def get_speakers(patient_id):
    patient_id = f"{patient_id:03}"
    gt_file = f"Dataset-Hucam-Nefro/patient_{patient_id}/patient_{patient_id}_transcription_gt.txt"
    with open(gt_file) as fp:
        lines = fp.readlines()
    speakers = [x.split(':')[0] for x in lines]
    speakers = list(set(speakers)) # unique
    return speakers

results = []

# for patient in range(1, 17):
for patient in [17]:
    print(f"Processing paciente {patient}")
    with open(f"Dataset-Hucam-Nefro/patient_{patient:03d}/patient_{patient:03d}_transcription_gt.txt", "r") as f:
        ground_truth = f.read()
    with open(f"Dataset-Hucam-Nefro/patient_{patient:03d}/patient_{patient:03d}_transcription_{PASS}_pass.txt", "r") as f:
        prediction = f.read()
    
    # replace {'MÉDICA_AUXILIAR', 'MÉDICA_SUPERVISOR', 'MÉDICO_SUPERVISOR', 'ASSISTENTE', 'MÉDICO', 'MÉDICA'} by 'MEDIC_TEAM'
    ground_truth = re.sub(r'MÉDICA_AUXILIAR|MÉDICA_SUPERVISOR|MÉDICO_SUPERVISOR|ASSISTENTE|MÉDICO|MÉDICA', 'MEDIC_TEAM', ground_truth)
    prediction = re.sub(r'MÉDICA_AUXILIAR|MÉDICA_SUPERVISOR|MÉDICO_SUPERVISOR|ASSISTENTE|MÉDICO|MÉDICA', 'MEDIC_TEAM', prediction)
    
    # replace  'PACIENTE',  'ACOMPANHANTE' by 'PATIENT_AND_FAMILY'
    ground_truth = re.sub(r'PACIENTE|ACOMPANHANTE', 'PATIENT_AND_FAMILY', ground_truth)
    prediction = re.sub(r'PACIENTE|ACOMPANHANTE', 'PATIENT_AND_FAMILY', prediction)
    
    patient_results = {
        "patient": patient,
    }
    
    ground_truth_clean = " ".join([line.split(": ", 1)[1] for line in ground_truth.splitlines()])
    ground_truth_clean = preprocess_text(ground_truth_clean)
    
    prediction_clean = " ".join([line.split(": ", 1)[1] for line in prediction.splitlines()])
    prediction_clean = preprocess_text(prediction_clean)
    
    # Metrics for the Whole text
    # print("\nWhole text")
    # Use SequenceMatcher to compare the preprocessed word lists
    matcher = difflib.SequenceMatcher(None, ground_truth_clean, prediction_clean)
    similarity_ratio = matcher.ratio()
    # print(f"Similarity Ratio: {similarity_ratio:.2f}")
    patient_results["all_similarity_ratio"] = similarity_ratio
    
    # Compute cosine similarity between the two TF-IDF vectors
    texts = [ground_truth, prediction]
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(texts)
    cosine_sim = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])
    # print(f"Cosine Similarity: {cosine_sim[0][0]:.2f}")
    patient_results["all_cosine_similarity"] = cosine_sim[0][0]
    
    # ROUGE metric evaluation
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    scores = scorer.score(" ".join(ground_truth_clean), " ".join(prediction_clean))
    # patient_results["all_rouge1_recall"] = scores['rouge1'].recall
    # patient_results["all_rouge1_precision"] = scores['rouge1'].precision
    # patient_results["all_rouge1_f1"] = scores['rouge1'].fmeasure
    # patient_results["all_rouge2_recall"] = scores['rouge2'].recall
    # patient_results["all_rouge2_precision"] = scores['rouge2'].precision
    # patient_results["all_rouge2_f1"] = scores['rouge2'].fmeasure
    patient_results["all_rougeL_recall"] = scores['rougeL'].recall
    patient_results["all_rougeL_precision"] = scores['rougeL'].precision
    patient_results["all_rougeL_f1"] = scores['rougeL'].fmeasure
    
    # Metrics for each speaker
    # speakers = get_speakers(patient)
    speakers = ['MEDIC_TEAM', 'PATIENT_AND_FAMILY']  
    for speaker in speakers:
        gt_text = concatenate_speaker_lines(ground_truth, speaker)
        pred_text = concatenate_speaker_lines(prediction, speaker)
        
        # Preprocess both texts
        gt_text_clean = preprocess_text(gt_text)
        pred_text_clean = preprocess_text(pred_text)

        # Use SequenceMatcher to compare the preprocessed word lists
        matcher = difflib.SequenceMatcher(None, gt_text_clean, pred_text_clean)
        similarity_ratio = matcher.ratio()

        # Output the similarity ratio
        patient_results[f"{speaker}_similarity_ratio"] = similarity_ratio
        
        # Combine both texts into a list for vectorization
        texts = [gt_text, pred_text]

        # Use TfidfVectorizer to convert the texts to TF-IDF vectors
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(texts)

        # Compute cosine similarity between the two TF-IDF vectors
        cosine_sim = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])

        # Output the cosine similarity
        patient_results[f"{speaker}_cosine_similarity"] = cosine_sim[0][0]

        # ROUGE metric evaluation
        scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
        scores = scorer.score(" ".join(gt_text_clean), " ".join(pred_text_clean))

        # patient_results[f"{speaker}_rouge1_recall"] = scores['rouge1'].recall
        # patient_results[f"{speaker}_rouge1_precision"] = scores['rouge1'].precision
        # patient_results[f"{speaker}_rouge1_f1"] = scores['rouge1'].fmeasure
        # patient_results[f"{speaker}_rouge2_recall"] = scores['rouge2'].recall
        # patient_results[f"{speaker}_rouge2_precision"] = scores['rouge2'].precision
        # patient_results[f"{speaker}_rouge2_f1"] = scores['rouge2'].fmeasure
        patient_results[f"{speaker}_rougeL_recall"] = scores['rougeL'].recall
        patient_results[f"{speaker}_rougeL_precision"] = scores['rougeL'].precision
        patient_results[f"{speaker}_rougeL_f1"] = scores['rougeL'].fmeasure
        
        
    results.append(patient_results)



df = pd.DataFrame(results)

df["Consult"] = df.index + 1

# Calculate means for all metrics columns
mean_all = df[["all_cosine_similarity", "all_rougeL_recall", "all_rougeL_precision", "all_rougeL_f1"]].mean()
mean_medics = df[["MEDIC_TEAM_cosine_similarity", "MEDIC_TEAM_rougeL_recall", "MEDIC_TEAM_rougeL_precision", "MEDIC_TEAM_rougeL_f1"]].mean()
mean_patients = df[["PATIENT_AND_FAMILY_cosine_similarity", "PATIENT_AND_FAMILY_rougeL_recall", "PATIENT_AND_FAMILY_rougeL_precision", "PATIENT_AND_FAMILY_rougeL_f1"]].mean()

# Prepare the DataFrames for LaTeX export
df_all = df[["Consult", "all_cosine_similarity", "all_rougeL_recall", "all_rougeL_precision", "all_rougeL_f1"]].copy()
df_all.columns = ["Consult", "Cosine Similarity", "ROUGE-L Recall", "ROUGE-L Precision", "ROUGE-L F1"]
df_all.loc["Mean"] = ["Mean"] + mean_all.tolist()
df_all.to_latex(f"all_metrics_{PASS}.tex", float_format="%.2f", index=False)

df_medics = df[["Consult", "MEDIC_TEAM_cosine_similarity", "MEDIC_TEAM_rougeL_recall", "MEDIC_TEAM_rougeL_precision", "MEDIC_TEAM_rougeL_f1"]].copy()
df_medics.columns = ["Consult", "Cosine Similarity", "ROUGE-L Recall", "ROUGE-L Precision", "ROUGE-L F1"]
df_medics.loc["Mean"] = ["Mean"] + mean_medics.tolist()
df_medics.to_latex(f"medics_metrics_{PASS}.tex", float_format="%.2f", index=False)

df_patients = df[["Consult", "PATIENT_AND_FAMILY_cosine_similarity", "PATIENT_AND_FAMILY_rougeL_recall", "PATIENT_AND_FAMILY_rougeL_precision", "PATIENT_AND_FAMILY_rougeL_f1"]].copy()
df_patients.columns = ["Consult", "Cosine Similarity", "ROUGE-L Recall", "ROUGE-L Precision", "ROUGE-L F1"]
df_patients.loc["Mean"] = ["Mean"] + mean_patients.tolist()
df_patients.to_latex(f"patients_metrics_{PASS}.tex", float_format="%.2f", index=False)


