import os
import json
from openai import OpenAI
from flask import current_app

client = OpenAI()


def build_feedback(session: dict, messages: list, job: dict, resume: dict, speech_metrics: dict) -> dict:
    """
    Gera o feedback estruturado da entrevista usando GPT-4o.

    Args:
        session:        Dados da sessão
        messages:       Histórico completo de mensagens
        job:            Dados da vaga
        resume:         Dados do currículo
        speech_metrics: Métricas de fala do analysis_service

    Returns:
        dict com: overall_score, score_breakdown, strengths,
                  improvements, action_plan, next_session_focus
    """
    prompt = _build_prompt(session, messages, job, resume, speech_metrics)

    try:
        response = client.chat.completions.create(
            model=current_app.config["OPENAI_CHAT_MODEL"],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1200,
            temperature=0.4,
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        current_app.logger.error(f"[FeedbackBuilder] Erro ao gerar feedback: {e}")
        return _fallback_feedback()


def _build_prompt(session, messages, job, resume, speech_metrics) -> str:
    """Monta o prompt completo para geração de feedback."""

    # Transcrição resumida (últimas 10 trocas)
    recent = messages[-20:] if len(messages) > 20 else messages
    transcript = "\n".join(
        f"{'Recrutador' if m['role'] == 'assistant' else 'Candidato'}: {m['content']}"
        for m in recent
    )

    resume_parsed = json.loads(resume.get("parsed_json", "{}")) if resume else {}
    job_analysis = json.loads(job.get("analysis_json", "{}")) if job else {}

    # Calcula duração
    duration = 0
    if session.get("started_at") and session.get("ended_at"):
        from datetime import datetime
        fmt = "%Y-%m-%d %H:%M:%S"
        try:
            start = datetime.strptime(session["started_at"], fmt)
            end = datetime.strptime(session["ended_at"], fmt)
            duration = int((end - start).total_seconds() / 60)
        except Exception:
            duration = 0

    question_count = sum(1 for m in messages if m["role"] == "assistant")

    # Seção de métricas de fala (apenas para modo voz)
    speech_section = ""
    if session.get("mode") == "voice" and speech_metrics:
        fillers = speech_metrics.get("filler_words", {})
        top_fillers = ", ".join(
            f['word'] for f in fillers.get("top_fillers", [])[:3]
        )
        speech_section = f"""
MÉTRICAS DE FALA:
- WPM médio: {speech_metrics.get('wpm_average', 'N/A')}
- Vícios detectados: {top_fillers or 'nenhum'}
- Taxa de hesitação: {speech_metrics.get('pause_analysis', {}).get('hesitation_rate', 'N/A')}
- Score de clareza: {speech_metrics.get('vocabulary', {}).get('clarity_score', 'N/A')}/100
"""

    return f"""Você é um coach de carreira especializado em preparação para entrevistas. Analise a transcrição e gere um feedback profissional, honesto e acionável.

CONTEXTO:
- Vaga: {job.get('title', 'N/A') if job else 'N/A'} em {job.get('company', 'N/A') if job else 'N/A'}
- Candidato: {resume_parsed.get('name', 'N/A')}
- Duração: {duration} minutos
- Perguntas respondidas: {question_count}
- Modo: {session.get('mode', 'text')}
{speech_section}
REQUISITOS DA VAGA:
{', '.join(job_analysis.get('key_requirements', ['N/A']))}

TRANSCRIÇÃO (trecho recente):
{transcript}

Retorne APENAS um JSON válido com esta estrutura:
{{
  "overall_score": 0-100,
  "score_breakdown": {{
    "technical_knowledge": 0-100,
    "communication": 0-100,
    "structure_clarity": 0-100,
    "cultural_fit": 0-100,
    "confidence": 0-100
  }},
  "strengths": ["3 pontos fortes específicos baseados nas respostas reais"],
  "improvements": ["3 pontos de melhoria específicos e acionáveis"],
  "action_plan": ["3 ações práticas para melhorar antes da próxima entrevista"],
  "next_session_focus": ["2 temas para praticar na próxima simulação"]
}}

Seja específico. Baseie TUDO nas respostas reais do candidato. Nunca seja genérico."""


def _fallback_feedback() -> dict:
    """Retorna feedback mínimo em caso de falha na API."""
    return {
        "overall_score": 0,
        "score_breakdown": {
            "technical_knowledge": 0,
            "communication": 0,
            "structure_clarity": 0,
            "cultural_fit": 0,
            "confidence": 0,
        },
        "strengths": ["Não foi possível gerar o feedback automaticamente."],
        "improvements": ["Tente novamente ou entre em contato com o suporte."],
        "action_plan": [],
        "next_session_focus": [],
    }