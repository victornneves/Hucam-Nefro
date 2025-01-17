# Hucam-Nefro

## Data Format

```yaml
relatorio_consulta_ambulatorial_nefrologia:
    identificacao_paciente:
        - Patient Identification
        - Description: Basic demographic and personal details about the patient, including age, gender, marital status, occupation, and place of residence.
        - Example: "65-year-old male, divorced, residing in São Paulo, Brazil."
    subjetivo:
        - Subjective
        - Description: The patient’s own account of their symptoms, complaints, and overall well-being as reported during the consultation. It provides insight into how the patient perceives their health.
        - Example: "Patient reports shortness of breath with mild exertion and occasional nocturnal dyspnea."
    exame_fisico:
        - Physical Examination
        - Description: A detailed assessment of the patient’s physical state, performed by the physician during the consultation. It involves observing and evaluating vital signs, general appearance, and specific organ systems.
        - Example: "Patient is afebrile, hydrated, with regular cardiac rhythm and no respiratory distress."
    exames_laboratoriais:
        - Laboratory Tests
        - Description: Includes all laboratory analyses of blood, urine, or other bodily fluids. These results help assess organ function, detect abnormalities, and guide diagnosis and treatment.
        - Example: "Creatinine levels of 2.3 mg/dL indicate chronic kidney disease progression."
    exames_complementares:
        - Complementary Exams
        - Description: Refers to diagnostic tests performed to support or confirm clinical findings. These may include imaging studies (e.g., ultrasound, CT scan) or specialized tests (e.g., Doppler studies, ECG).
        - Example: "Abdominal ultrasound showing no abnormalities; Doppler of the lower limbs indicating venous insufficiency."
    hipoteses_diagnosticas:
        - Diagnostic Hypotheses
        - Description: A list of possible medical conditions being considered based on the patient’s symptoms, physical examination, and preliminary tests. It guides further diagnostic and therapeutic actions.
        - Example: "Possible diagnoses include diabetic nephropathy and hypertensive nephrosclerosis."
    impressao:
        - Clinical Impression
        - Description: The physician’s consolidated evaluation of the patient’s condition after considering all available data, including history, examination, and test results. It often serves as the basis for treatment decisions.
        - Example: "Stable chronic kidney disease with good blood pressure control."
    conduta:
        - Conduct
        - Description: Refers to the medical plan or actions recommended by the healthcare provider to address the patient's condition. This includes treatment plans, prescriptions, lifestyle changes, follow-up schedules, or referrals to other specialists.
        - Example: "Increase medication dosage, monitor blood pressure daily, and schedule a follow-up in three months."
    medicamentos_em_uso:
        - Medications in Use
        - Description: A list of all medications currently prescribed or self-administered by the patient, including dosages and schedules. It provides critical information for managing drug interactions and treatment planning.
        - Example: "Patient is taking Losartan 50 mg twice daily and insulin as per sliding scale."
    historico_patologico_pregresso:
        - Past Medical History
        - Description: A record of the patient’s previous health conditions, surgeries, and treatments, as well as relevant family history or lifestyle factors that may influence current health.
        - Example: "History of hypertension for 10 years, diabetes mellitus since age 40, and coronary artery bypass surgery in 2015."
    preparo_para_terapia_de_substituicao_renal:
        - Preparation for Renal Replacement Therapy
        - Description: Details the steps taken to prepare the patient for renal replacement therapies like dialysis or kidney transplantation, including educational sessions, vascular access creation, and evaluations.
        - Example: "Patient has been briefed on hemodialysis and is awaiting arteriovenous fistula placement."

```