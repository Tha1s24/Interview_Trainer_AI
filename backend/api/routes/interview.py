import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import json
from flask import Blueprint, request
from api.middleware.auth import require_auth, check_session_limit
from api.middleware.rate_limit import rate_limit
from models.session import SessionModel
from models.feedback import FeedbackModel
from models.response import success, created, error, not_found, validation_error
from services.ai_orchestrator import get_next_question
from services.speech_service import save_audio_chunk, transcribe_audio
from services.analysis_service import analyze_speech
from services.feedback_builder import build_feedback
from database.db import query

interview_bp = Blueprint("interview", __name__, url_prefix="/api/interview")


def _get_job(job_id: str, user_id: str) -> dict | None:
    return query(
        "SELECT * FROM jobs WHERE id = ? AND user_id = ?",
        (job_id, user_id),
        one=True,
    )


def _get_resume(resume_id: str, user_id: str) -> dict | None:
    return query(
        "SELECT * FROM resumes WHERE id = ? AND user_id = ?",
        (resume_id, user_id),
        one=True,
    )


@interview_bp.route("/session", methods=["POST"])
@require_auth
@check_session_limit
@rate_limit("ai")
def create_session(current_user):
    data = request.get_json(silent=True) or {}

    errors = []
    allowed_modes = {"text", "voice"}
    allowed_personas = {"senior_recruiter", "hr_generalist", "tech_lead"}

    if data.get("mode") and data["mode"] not in allowed_modes:
        errors.append({"field": "mode", "message": f"Valores válidos: {allowed_modes}"})
    if data.get("persona") and data["persona"] not in allowed_personas:
        errors.append({"field": "persona", "message": f"Valores válidos: {allowed_personas}"})
    if errors:
        return validation_error(errors)

    # Carrega job e resume opcionais
    job = _get_job(data["job_id"], current_user["id"]) if data.get("job_id") else None
    resume = _get_resume(data["resume_id"], current_user["id"]) if data.get("resume_id") else None

    # Cria sessão
    session = SessionModel.create(current_user["id"], data)

    # Gera primeira pergunta do recrutador
    first_question = get_next_question(session, [], job, resume)
    SessionModel.add_message(session["id"], "assistant", first_question)

    return created({
        "session_id": session["id"],
        "status": "active",
        "first_message": first_question,
        "time_limit": session.get("time_limit"),
        "started_at": session["started_at"],
    })


@interview_bp.route("/session/<session_id>/message", methods=["POST"])
@require_auth
@rate_limit("ai")
def send_message(current_user, session_id):
    session = SessionModel.find_by_id(session_id)
    if not session or session["user_id"] != current_user["id"]:
        return not_found("Sessão")
    if session["status"] != "active":
        return error("SESSION_ENDED", "Esta sessão já foi encerrada.", 400)

    data = request.get_json(silent=True) or {}
    content = data.get("content", "").strip()
    if not content:
        return error("EMPTY_MESSAGE", "A resposta não pode ser vazia.", 400)

    # Salva resposta do candidato
    SessionModel.add_message(session_id, "user", content)

    # Busca histórico e contexto
    messages = SessionModel.get_messages(session_id)
    job = query("SELECT * FROM jobs WHERE id = ?", (session["job_id"],), one=True) if session.get("job_id") else None
    resume = query("SELECT * FROM resumes WHERE id = ?", (session["resume_id"],), one=True) if session.get("resume_id") else None

    # Gera próxima pergunta
    ai_response = get_next_question(session, messages, job, resume)
    msg_id = SessionModel.add_message(session_id, "assistant", ai_response)

    return success({
        "message_id": msg_id,
        "ai_response": ai_response,
        "session_status": "active",
        "question_count": SessionModel.count_messages(session_id),
    })


@interview_bp.route("/session/<session_id>/audio", methods=["POST"])
@require_auth
@rate_limit("audio")
def send_audio(current_user, session_id):
    session = SessionModel.find_by_id(session_id)
    if not session or session["user_id"] != current_user["id"]:
        return not_found("Sessão")
    if session["status"] != "active":
        return error("SESSION_ENDED", "Esta sessão já foi encerrada.", 400)
    if session.get("mode") != "voice":
        return error("WRONG_MODE", "Esta sessão não é de modo voz.", 400)

    if "audio" not in request.files:
        return error("NO_AUDIO", "Arquivo de áudio não enviado.", 400)

    chunk_index = int(request.form.get("chunk_index", 0))
    is_final = request.form.get("is_final", "false").lower() == "true"

    audio_file = request.files["audio"]
    audio_path = save_audio_chunk(audio_file, session_id, chunk_index)

    # Transcreve o chunk
    result = transcribe_audio(audio_path)
    transcript = result["text"]
    confidence = result["confidence"]

    response_data = {
        "transcript": transcript,
        "confidence": confidence,
        "ai_response": None,
        "speech_preview": {},
    }

    # No chunk final, consolida e gera resposta da IA
    if is_final and transcript:
        SessionModel.add_message(session_id, "user", transcript, audio_path)
        messages = SessionModel.get_messages(session_id)
        job = query("SELECT * FROM jobs WHERE id = ?", (session["job_id"],), one=True) if session.get("job_id") else None
        resume = query("SELECT * FROM resumes WHERE id = ?", (session["resume_id"],), one=True) if session.get("resume_id") else None

        ai_response = get_next_question(session, messages, job, resume)
        SessionModel.add_message(session_id, "assistant", ai_response)
        response_data["ai_response"] = ai_response

    return success(response_data)


@interview_bp.route("/session/<session_id>/end", methods=["POST"])
@require_auth
def end_session(current_user, session_id):
    session = SessionModel.find_by_id(session_id)
    if not session or session["user_id"] != current_user["id"]:
        return not_found("Sessão")
    if session["status"] == "completed":
        return error("ALREADY_ENDED", "Esta sessão já foi encerrada.", 400)

    session = SessionModel.end(session_id)
    messages = SessionModel.get_messages(session_id)
    question_count = sum(1 for m in messages if m["role"] == "assistant")

    # Busca contexto para gerar feedback
    job = query("SELECT * FROM jobs WHERE id = ?", (session["job_id"],), one=True) if session.get("job_id") else None
    resume = query("SELECT * FROM resumes WHERE id = ?", (session["resume_id"],), one=True) if session.get("resume_id") else None

    # Analisa métricas de fala (se modo voz)
    speech_metrics = {}
    if session.get("mode") == "voice":
        speech_metrics = analyze_speech(session_id, messages)

    feedback_data = build_feedback(session, messages, job, resume, speech_metrics)
    feedback = FeedbackModel.create(session_id, feedback_data)

    return success({
        "session_id": session_id,
        "status": "completed",
        "total_exchanges": question_count,
        "feedback_id": feedback["id"],
        "feedback_ready": True,
    })


@interview_bp.route("/sessions", methods=["GET"])
@require_auth
def list_sessions(current_user):
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))
    sessions = SessionModel.list_by_user(current_user["id"], page, limit)
    total = SessionModel.count_by_user(current_user["id"])

    return success({"sessions": sessions, "total": total, "page": page})