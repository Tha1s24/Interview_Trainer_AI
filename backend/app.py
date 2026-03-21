import os
import sys

# Garante que a pasta backend/ esteja no path para todos os imports absolutos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from config import get_config
from database.db import init_db, close_db


def create_app() -> Flask:
    """
    Factory da aplicação Flask.
    Centraliza configuração, extensões, blueprints e hooks.
    """
    app = Flask(__name__)
    app.config.from_object(get_config())

    # ── Extensões ──────────────────────────────────────────────
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    JWTManager(app)

    # ── Banco de dados ─────────────────────────────────────────
    init_db(app)
    app.teardown_appcontext(close_db)

    # ── Pasta de uploads ───────────────────────────────────────
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ── Blueprints (rotas) ─────────────────────────────────────
    from api.routes.auth import auth_bp
    from api.routes.user import user_bp
    from api.routes.interview import interview_bp
    from api.routes.analysis import analysis_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(interview_bp)
    app.register_blueprint(analysis_bp)

    # ── Handlers de erro globais ───────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Rota não encontrada."}}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": {"code": "METHOD_NOT_ALLOWED", "message": "Método não permitido."}}), 405

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return jsonify({"error": {"code": "FILE_TOO_LARGE", "message": "Arquivo excede o limite de 5 MB."}}), 413

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error(f"Erro interno: {e}")
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": "Erro interno do servidor."}}), 500

    # ── Health check ───────────────────────────────────────────
    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "version": "1.0.0"})

    return app


# ── Entry point ────────────────────────────────────────────────
app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=app.config.get("DEBUG", False),
    )