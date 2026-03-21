import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import json
from flask import Blueprint, request, current_app
from api.middleware.auth import require_auth
from api.middleware.rate_limit import rate_limit
from models.user import UserModel
from models.response import success, created, error, not_found, validation_error
from services.resume_parser import save_resume, parse_resume
from services.ai_orchestrator import analyze_job
from database.db import execute, query

user_bp = Blueprint("user", __name__, url_prefix="/api/user")


@user_bp.route("/profile", methods=["GET"])
@require_auth
def get_profile(current_user):
    prefs = UserModel.get_preferences(current_user["id"]) or {}
    sessions_used = UserModel.count_sessions(current_user["id"])
    plan = current_user.get("plan", "free")
    limit = current_app.config["PLAN_LIMITS"].get(plan, 3)

    return success({
        **current_user,
        "sessions_used": sessions_used,
        "sessions_limit": limit if limit != -1 else None,
        "preferences": prefs,
    })


@user_bp.route("/preferences", methods=["PATCH"])
@require_auth
def update_preferences(current_user):
    data = request.get_json(silent=True) or {}

    allowed_themes = {"light", "dark", "system"}
    allowed_fonts = {"small", "medium", "large", "x-large"}
    allowed_langs = {"pt-BR", "en-US", "es-ES"}

    errors = []
    if "theme" in data and data["theme"] not in allowed_themes:
        errors.append({"field": "theme", "message": f"Valores válidos: {allowed_themes}"})
    if "font_size" in data and data["font_size"] not in allowed_fonts:
        errors.append({"field": "font_size", "message": f"Valores válidos: {allowed_fonts}"})
    if "language" in data and data["language"] not in allowed_langs:
        errors.append({"field": "language", "message": f"Valores válidos: {allowed_langs}"})
    if errors:
        return validation_error(errors)

    updated = UserModel.update_preferences(current_user["id"], data)
    return success({"updated": True, "preferences": updated})


@user_bp.route("/resume", methods=["POST"])
@require_auth
@rate_limit("default")
def upload_resume(current_user):
    if "file" not in request.files:
        return error("NO_FILE", "Nenhum arquivo enviado.", 400)

    file = request.files["file"]
    if file.filename == "":
        return error("EMPTY_FILENAME", "Nome do arquivo inválido.", 400)

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in {"pdf", "docx"}:
        return error("INVALID_FORMAT", "Apenas PDF e DOCX são aceitos.", 415)

    # Salva e processa
    resume_id, file_path = save_resume(file, current_user["id"])
    parsed = parse_resume(file_path)

    # Persiste no banco
    execute(
        "INSERT INTO resumes (id, user_id, filename, parsed_json) VALUES (?, ?, ?, ?)",
        (resume_id, current_user["id"], file.filename, json.dumps(parsed)),
    )

    skill_count = len(parsed.get("skills", []))
    exp_count = len(parsed.get("experience", []))
    estimated_questions = min(15, 6 + skill_count + exp_count)

    return created({
        "resume_id": resume_id,
        "parsed": parsed,
        "suggested_questions_preview": estimated_questions,
    })


@user_bp.route("/job", methods=["POST"])
@require_auth
@rate_limit("default")
def create_job(current_user):
    data = request.get_json(silent=True) or {}

    errors = []
    if not data.get("title", "").strip():
        errors.append({"field": "title", "message": "Título da vaga é obrigatório."})
    if not data.get("description", "").strip():
        errors.append({"field": "description", "message": "Descrição da vaga é obrigatória."})
    if errors:
        return validation_error(errors)

    # Analisa a vaga via GPT
    analysis = analyze_job(data["description"])

    import uuid
    job_id = "job_" + uuid.uuid4().hex
    execute(
        """INSERT INTO jobs (id, user_id, title, company, description, type, seniority, job_url, analysis_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            job_id,
            current_user["id"],
            data["title"].strip(),
            data.get("company", "").strip(),
            data["description"].strip(),
            data.get("type", analysis.get("job_type_confirmed", "general")),
            data.get("seniority", "mid"),
            data.get("job_url"),
            json.dumps(analysis),
        ),
    )

    return created({
        "job_id": job_id,
        "analysis": analysis,
    })