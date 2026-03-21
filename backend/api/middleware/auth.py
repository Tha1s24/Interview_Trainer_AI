import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from models.response import unauthorized, forbidden
from models.user import UserModel


def require_auth(fn):
    """
    Decorator que protege um endpoint exigindo JWT válido.
    Injeta o usuário autenticado como `current_user` no kwargs da função.

    Uso:
        @app.route('/protegido')
        @require_auth
        def rota(current_user):
            return jsonify(current_user)
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception:
            return unauthorized()

        user_id = get_jwt_identity()
        user = UserModel.find_by_id(user_id)

        if not user:
            return unauthorized("Usuário não encontrado.")

        kwargs["current_user"] = user
        return fn(*args, **kwargs)

    return wrapper


def check_session_limit(fn):
    """
    Decorator que verifica se o usuário pode iniciar uma nova sessão
    com base no plano (free = 3 sessões, pro = ilimitado).
    Deve ser usado APÓS @require_auth.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user = kwargs.get("current_user")
        if not current_user:
            return unauthorized()

        plan = current_user.get("plan", "free")
        if plan != "pro":
            from flask import current_app
            limit = current_app.config["PLAN_LIMITS"].get(plan, 3)
            used = UserModel.count_sessions(current_user["id"])
            if used >= limit:
                return forbidden(
                    f"Você atingiu o limite de {limit} sessões do plano gratuito.",
                    extra={"upgrade_url": "/planos"},
                )

        return fn(*args, **kwargs)

    return wrapper