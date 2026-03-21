import os
import uuid
import json
from openai import OpenAI
from flask import current_app

client = OpenAI()  # usa OPENAI_API_KEY do ambiente


def save_resume(file, user_id: str) -> tuple[str, str]:
    """
    Salva o arquivo de currículo no sistema de arquivos.

    Returns:
        (resume_id, file_path)
    """
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)

    ext = os.path.splitext(file.filename)[1].lower()
    resume_id = "res_" + uuid.uuid4().hex
    filename = f"{resume_id}{ext}"
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)

    return resume_id, file_path


def extract_text_from_pdf(file_path: str) -> str:
    """Extrai texto bruto de um PDF usando PyMuPDF."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text.strip()
    except Exception as e:
        current_app.logger.error(f"[ResumeParser] Erro ao ler PDF: {e}")
        return ""


def parse_resume(file_path: str) -> dict:
    """
    Extrai informações estruturadas do currículo via GPT-4o.

    Returns:
        dict com: name, summary, skills, experience, education
    """
    raw_text = extract_text_from_pdf(file_path)

    if not raw_text:
        return _empty_resume()

    prompt = f"""Analise o currículo abaixo e retorne APENAS um JSON válido com esta estrutura:
{{
  "name": "Nome completo",
  "summary": "Resumo profissional em 2-3 frases",
  "skills": ["lista de habilidades técnicas"],
  "experience": [
    {{
      "title": "Cargo",
      "company": "Empresa",
      "period": "2022 – atual",
      "highlights": ["conquista 1", "conquista 2"]
    }}
  ],
  "education": ["Graduação – Instituição, ano"]
}}

Currículo:
{raw_text[:4000]}

Retorne apenas o JSON, sem explicações."""

    try:
        response = client.chat.completions.create(
            model=current_app.config["OPENAI_CHAT_MODEL"],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.2,
        )
        raw = response.choices[0].message.content.strip()
        # Remove blocos de código markdown se presentes
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        current_app.logger.error(f"[ResumeParser] Erro ao parsear com GPT: {e}")
        return _empty_resume()


def _empty_resume() -> dict:
    return {
        "name": "",
        "summary": "",
        "skills": [],
        "experience": [],
        "education": [],
    }