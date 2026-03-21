from flask import jsonify


def success(data: dict | list, status: int = 200):
    """Resposta de sucesso padronizada."""
    return jsonify(data), status


def created(data: dict):
    """Resposta 201 Created."""
    return jsonify(data), 201


def error(code: str, message: str, status: int = 400, extra: dict = None):
    """
    Resposta de erro padronizada.

    Args:
        code:    Código de erro legível por máquina (ex: 'SESSION_NOT_FOUND')
        message: Mensagem legível por humano
        status:  HTTP status code
        extra:   Campos adicionais opcionais (ex: upgrade_url)
    """
    body = {"error": {"code": code, "message": message}}
    if extra:
        body["error"].update(extra)
    return jsonify(body), status


def not_found(resource: str = "Recurso"):
    return error("NOT_FOUND", f"{resource} não encontrado.", 404)


def unauthorized(message: str = "Token ausente ou inválido."):
    return error("UNAUTHORIZED", message, 401)


def forbidden(message: str = "Acesso negado.", extra: dict = None):
    return error("FORBIDDEN", message, 403, extra)


def validation_error(errors: list):
    return jsonify({"error": {"code": "VALIDATION_ERROR", "errors": errors}}), 422


def rate_limited():
    return error("RATE_LIMIT_EXCEEDED", "Muitas requisições. Aguarde 60 segundos.", 429)