import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from flask import Blueprint, request
from flask_jwt_extended import create_access_token
from models.user import UserModel
from models.response import created, error, validation_error
from api.middleware.rate_limit import rate_limit

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
@rate_limit("auth")
def register():
    data = request.get_json(silent=True) or {}

    # Validação básica
    errors = []
    if not data.get("name", "").strip():
        errors.append({"field": "name", "message": "Nome é obrigatório."})
    if not data.get("email", "").strip():
        errors.append({"field": "email", "message": "E-mail é obrigatório."})
    if not data.get("password") or len(data["password"]) < 6:
        errors.append({"field": "password", "message": "Senha deve ter ao menos 6 caracteres."})
    if errors:
        return validation_error(errors)

    user = UserModel.create(
        name=data["name"].strip(),
        email=data["email"].strip().lower(),
        password=data["password"],
    )

    if not user:
        return error("EMAIL_ALREADY_EXISTS", "Este e-mail já está cadastrado.", 409)

    token = create_access_token(identity=user["id"])
    return created({"user_id": user["id"], "token": token, "expires_in": 86400})


@auth_bp.route("/login", methods=["POST"])
@rate_limit("auth")
def login():
    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return error("MISSING_CREDENTIALS", "E-mail e senha são obrigatórios.", 400)

    user = UserModel.verify_password(email, password)
    if not user:
        return error("INVALID_CREDENTIALS", "E-mail ou senha incorretos.", 401)

    token = create_access_token(identity=user["id"])
    return created({
        "token": token,
        "user": {
            "user_id": user["id"],
            "name": user["name"],
            "plan": user["plan"],
        },
    })