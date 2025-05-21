import os
import yaml
from pathlib import Path
from openai import OpenAI
import dotenv
from datetime import datetime

# Configuração do OpenAI
dotenv.load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Funções auxiliares
def readable_string(text):
    """Formata strings para melhor legibilidade."""
    if isinstance(text, str):
        return text.replace("_", " ").strip()
    return str(text)

def get_field(summary, field):
    """Extrai um campo específico do resumo em YAML."""
    field_value = summary["relatorio_consulta_ambulatorial_nefrologia"].get(field, "")
    if isinstance(field_value, list):
        return "\n".join([readable_string(x) for x in field_value])
    return readable_string(field_value)

def format_patient_id(patient_id):
    """Formata o ID do paciente para 3 dígitos."""
    return f"{int(patient_id):03d}"

def ensure_patient_dir(patient_id):
    """Garante que o diretório do paciente existe."""
    formatted_id = format_patient_id(patient_id)
    patient_dir = Path(f"data/chat/{formatted_id}")
    patient_dir.mkdir(parents=True, exist_ok=True)
    return patient_dir

def load_condensed_dialog(patient_id):
    """Carrega o último chunk condensado do diálogo."""
    formatted_id = format_patient_id(patient_id)
    condensed_dir = Path(f"../modulo_condense/data/condensed/{formatted_id}")
    chunks = list(condensed_dir.glob("*.txt"))
    if not chunks:
        raise FileNotFoundError(f"Nenhum diálogo condensado encontrado para o paciente {formatted_id}.")
    
    latest_chunk = max(chunks, key=lambda x: int(x.stem.split("_")[-1]))
    with open(latest_chunk, "r", encoding='utf-8') as f:
        return f.read()

def load_patient_data(patient_id):
    """Carrega o YAML com histórico, medicamentos e exames."""
    formatted_id = format_patient_id(patient_id)
    data_path = Path(f"data/chat/{formatted_id}/patient_{formatted_id}.yaml")
    with open(data_path, "r", encoding='utf-8') as f:
        return yaml.safe_load(f)

def call_gpt_api(prompt):
    """Chama a API do GPT para gerar uma resposta."""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Você é um nefrologista assistente especializado em análise de casos clínicos."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Erro ao chamar API do GPT: {e}")
        return None

BASE_PROMPT = """
Você é um especialista em nefrologia com ampla experiência em avaliação de casos clínicos e análises médicas. 
Você irá fornecer avaliações detalhadas e contextualizadas de informações clínicas. Use seu conhecimento em nefrologia, 
diretrizes clínicas e critérios diagnósticos para avaliar a validade e a coerência das informações fornecidas.

**Sumário da consulta em andamento**
{espaco_1}

**Histórico do paciente, medicamentos em uso, exames:**
{espaco_2}

---

**Pergunta do médico:** 
{user_prompt}
"""

def generate_medical_response(patient_id, question):
    """Função principal que gera a resposta médica."""
    try:
        # Carrega dados
        espaco_1 = load_condensed_dialog(patient_id)
        espaco_2 = load_patient_data(patient_id)
        
        # Formata o prompt final
        prompt = BASE_PROMPT.format(
            espaco_1=espaco_1,
            espaco_2=yaml.dump(espaco_2, allow_unicode=True),
            user_prompt=question
        )
        
        # Chama a API do GPT
        response = call_gpt_api(prompt)
        if not response:
            raise Exception("Não foi possível obter resposta do GPT")
        
        # Gera timestamp para os arquivos
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        formatted_id = format_patient_id(patient_id)
        patient_dir = ensure_patient_dir(patient_id)
        
        # Salva o prompt
        prompt_filename = f"patient_{formatted_id}_prompt_{timestamp}.txt"
        with open(patient_dir / prompt_filename, "w", encoding='utf-8') as f:
            f.write(prompt)
        
        # Salva a resposta
        response_filename = f"patient_{formatted_id}_response_{timestamp}.txt"
        with open(patient_dir / response_filename, "w", encoding='utf-8') as f:
            f.write(response)
        
        return {
            "patient_id": formatted_id,
            "question": question,
            "response": response,
            "prompt_file": prompt_filename,
            "response_file": response_filename
        }
    
    except Exception as e:
        return {"error": str(e)}
