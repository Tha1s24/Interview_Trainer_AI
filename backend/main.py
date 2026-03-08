# backend/main.py
import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Importação das rotas (Blueprints)
from routes.auth import auth_bp
from routes.interview import interview_bp
from routes.feedback import feedback_bp
from database.connection import init_db

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configuração de Segurança: Permite requisições do seu frontend
    # Em produção, você substituiria o '*' pela URL real do seu site
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Configurações básicas
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-123')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite de 16MB para uploads (currículos/áudio)

    # Registro de Blueprints (Organização das rotas)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(interview_bp, url_prefix='/api/interview')
    app.register_blueprint(feedback_bp, url_prefix='/api/feedback')

    @app.route('/')
    def health_check():
        return {"status": "online", "message": "Interview Trainer AI API is running"}, 200

    return app

if __name__ == '__main__':
    app = create_app()
    init_db() # Cria o arquivo interview.db se não existir
    # Rodar em modo debug facilita o desenvolvimento
    app.run(debug=True, port=5000)