import time
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from collections import defaultdict
from functools import wraps
from flask import request
from models.response import rate_limited

# Armazena requisições em memória: { chave: [timestamps] }
# Em produção, substituir por Redis para suportar múltiplos workers
_request_log: dict[str, list[float]] = defaultdict(list)

# Configuração de limites por tipo de rota
LIMITS = {
    "default":  {"max_requests": 60,  "window_seconds": 60},
    "auth":     {"max_requests": 10,  "window_seconds": 60},
    "audio":    {"max_requests": 120, "window_seconds": 60},
    "ai":       {"max_requests": 30,  "window_seconds": 60},
}


def rate_limit(limit_type: str = "default"):
    """
    Decorator de rate limiting por IP + user_id (se autenticado).

    Args:
        limit_type: Chave em LIMITS — 'default', 'auth', 'audio', 'ai'

    Uso:
        @route('/endpoint')
        @rate_limit('auth')
        def endpoint():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            config = LIMITS.get(limit_type, LIMITS["default"])
            max_req = config["max_requests"]
            window = config["window_seconds"]

            # Chave de identificação: prefere user_id via JWT, cai para IP
            try:
                from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
                verify_jwt_in_request(optional=True)
                identity = get_jwt_identity()
                key = f"user:{identity}" if identity else f"ip:{_get_ip()}"
            except Exception:
                key = f"ip:{_get_ip()}"

            key = f"{limit_type}:{key}"
            now = time.time()

            # Remove timestamps fora da janela
            _request_log[key] = [t for t in _request_log[key] if now - t < window]

            if len(_request_log[key]) >= max_req:
                return rate_limited()

            _request_log[key].append(now)
            return fn(*args, **kwargs)

        return wrapper
    return decorator


def _get_ip() -> str:
    """Retorna o IP real considerando proxies."""
    return (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.remote_addr
        or "unknown"
    )