import os
import json
from openai import OpenAI
from flask import current_app

client = OpenAI()

# Número máximo de trocas completas mantidas no histórico sem compressão
MAX_FULL_HISTORY = 6


def _load_prompt(persona: str) -> str:
    """Carrega o arquivo de prompt da persona a partir da pasta /prompts."""
    prompts_folder = current_app.config["PROMPTS_FOLDER"]
    path = os.path.join(prompts_folder, f"{persona}.txt")
    if not os.path.exists(path):
        # Fallback para o recrutador sênior se a persona não existir
        path = os.path.join(prompts_folder, "senior_recruiter.txt")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _fill_template(template: str, context: dict) -> str:
    """Substitui variáveis {{chave}} no template pelo contexto."""
    for key, value in context.items():
        template = template.replace(f"{{{{{key}}}}}", str(value))
    return template


def _build_system_prompt(session: dict, job: dict, resume: dict) -> str:
    """Monta o system prompt completo com contexto dinâmico."""
    persona = session.get("persona", "senior_recruiter")
    template = _load_prompt(persona)

    resume_parsed = json.loads(resume.get("parsed_json", "{}")) if isinstance(resume, dict) else {}
    job_analysis = json.loads(job.get("analysis_json", "{}")) if isinstance(job, dict) else {}

    context = {
        "candidate_name": resume_parsed.get("name", "candidato"),
        "job_title": job.get("title", "vaga") if job else "vaga",
        "company_name": job.get("company", "empresa") if job else "empresa",
        "job_type": job.get("type", "general") if job else "general",
        "seniority": job.get("seniority", "mid") if job else "mid",
        "key_requirements": ", ".join(job_analysis.get("key_requirements", [])),
        "culture_signals": ", ".join(job_analysis.get("culture_signals", [])),
        "resume_summary": resume_parsed.get("summary", ""),
        "candidate_skills": ", ".join(resume_parsed.get("skills", [])),
        "pressure_mode": "true" if session.get("pressure_mode") else "false",
        "time_limit": f"{session.get('time_limit')} minutos" if session.get("time_limit") else "sem limite",
        "language": "pt-BR",
    }

    return _fill_template(template, context)


def _compress_history(messages: list) -> str:
    """
    Resume as mensagens antigas em um parágrafo para reduzir tokens
    mantendo coerência na conversa.
    """
    history_text = "\n".join(
        f"{'Recrutador' if m['role'] == 'assistant' else 'Candidato'}: {m['content']}"
        for m in messages
    )
    try:
        response = client.chat.completions.create(
            model=current_app.config["OPENAI_CHAT_MODEL"],
            messages=[{
                "role": "user",
                "content": f"Resuma em 3 frases o que foi discutido nesta entrevista:\n\n{history_text}"
            }],
            max_tokens=200,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "Entrevista em andamento com trocas anteriores."


def get_next_question(session: dict, messages: list, job: dict, resume: dict) -> str:
    """
    Gera a próxima pergunta do recrutador com base no histórico da sessão.

    Args:
        session:  Dados da sessão (persona, modo, etc.)
        messages: Histórico de mensagens [{role, content}]
        job:      Dados da vaga
        resume:   Dados do currículo

    Returns:
        Texto da próxima pergunta/resposta do recrutador
    """
    system_prompt = _build_system_prompt(session, job, resume)

    # Janela deslizante: comprime histórico antigo se necessário
    if len(messages) > MAX_FULL_HISTORY * 2:
        old_messages = messages[:-MAX_FULL_HISTORY * 2]
        recent_messages = messages[-MAX_FULL_HISTORY * 2:]
        summary = _compress_history(old_messages)
        chat_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"[Resumo das trocas anteriores]: {summary}"},
            *[{"role": m["role"], "content": m["content"]} for m in recent_messages],
        ]
    else:
        chat_messages = [
            {"role": "system", "content": system_prompt},
            *[{"role": m["role"], "content": m["content"]} for m in messages],
        ]

    response = client.chat.completions.create(
        model=current_app.config["OPENAI_CHAT_MODEL"],
        messages=chat_messages,
        max_tokens=400,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def analyze_job(job_description: str) -> dict:
    """
    Extrai requisitos e sinais de cultura da descrição de vaga.

    Returns:
        dict com: key_requirements, culture_signals, soft_skills,
                  difficulty, estimated_questions, job_type_confirmed
    """
    prompt = f"""Analise a seguinte descrição de vaga e retorne APENAS um JSON válido:
{{
  "key_requirements": ["3-5 requisitos técnicos principais"],
  "culture_signals": ["2-4 palavras de cultura inferida"],
  "soft_skills": ["2-4 competências comportamentais esperadas"],
  "difficulty": "low",
  "estimated_questions": 8,
  "job_type_confirmed": "tech"
}}

Valores válidos para difficulty: "low", "medium", "high"
Valores válidos para job_type_confirmed: "tech", "design", "marketing", "hr", "sales", "finance", "general"

Vaga:
{job_description[:3000]}

Retorne apenas o JSON."""

    try:
        response = client.chat.completions.create(
            model=current_app.config["OPENAI_CHAT_MODEL"],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.2,
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        current_app.logger.error(f"[AIOrchestrator] Erro ao analisar vaga: {e}")
        return {
            "key_requirements": [],
            "culture_signals": [],
            "soft_skills": [],
            "difficulty": "medium",
            "estimated_questions": 8,
            "job_type_confirmed": "general",
        }