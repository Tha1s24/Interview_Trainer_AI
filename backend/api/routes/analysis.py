import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import json
from flask import Blueprint, send_file, request
from api.middleware.auth import require_auth
from models.session import SessionModel
from models.feedback import FeedbackModel
from models.response import success, not_found, error
from database.db import query
from services.report_generator import generate_pdf

analysis_bp = Blueprint("analysis", __name__, url_prefix="/api")


@analysis_bp.route("/analysis/session/<session_id>", methods=["GET"])
@require_auth
def get_speech_analysis(current_user, session_id):
    session = SessionModel.find_by_id(session_id)
    if not session or session["user_id"] != current_user["id"]:
        return not_found("Sessão")

    metrics = query(
        "SELECT * FROM speech_metrics WHERE session_id = ?",
        (session_id,),
        one=True,
    )

    if not metrics:
        return error("NO_METRICS", "Métricas ainda não disponíveis para esta sessão.", 404)

    # Desserializa os campos JSON
    for field in ["filler_words_json", "pause_analysis_json", "vocabulary_json"]:
        clean = field.replace("_json", "")
        try:
            metrics[clean] = json.loads(metrics.get(field, "{}"))
        except Exception:
            metrics[clean] = {}

    return success({"session_id": session_id, "speech_metrics": {
        "wpm_average": metrics.get("wpm_average"),
        "filler_words": metrics.get("filler_words", {}),
        "pause_analysis": metrics.get("pause_analysis", {}),
        "vocabulary": metrics.get("vocabulary", {}),
    }})


@analysis_bp.route("/feedback/<feedback_id>", methods=["GET"])
@require_auth
def get_feedback(current_user, feedback_id):
    feedback = FeedbackModel.find_by_id(feedback_id)
    if not feedback:
        return not_found("Feedback")

    # Verifica que o feedback pertence ao usuário
    session = SessionModel.find_by_id(feedback["session_id"])
    if not session or session["user_id"] != current_user["id"]:
        return not_found("Feedback")

    return success(feedback)


@analysis_bp.route("/feedback/<feedback_id>/report", methods=["GET"])
@require_auth
def download_report(current_user, feedback_id):
    feedback = FeedbackModel.find_by_id(feedback_id)
    if not feedback:
        return not_found("Feedback")

    session = SessionModel.find_by_id(feedback["session_id"])
    if not session or session["user_id"] != current_user["id"]:
        return not_found("Feedback")

    job = query("SELECT * FROM jobs WHERE id = ?", (session["job_id"],), one=True) if session.get("job_id") else None
    resume = query("SELECT * FROM resumes WHERE id = ?", (session["resume_id"],), one=True) if session.get("resume_id") else None
    speech = query("SELECT * FROM speech_metrics WHERE session_id = ?", (session["id"],), one=True)

    pdf_path = generate_pdf(feedback, session, job, resume, speech, current_user)

    candidate_name = current_user.get("name", "candidato").lower().replace(" ", "_")
    date_str = feedback.get("generated_at", "")[:10]
    filename = f"relatorio_{candidate_name}_{date_str}.pdf"

    return send_file(
        pdf_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )