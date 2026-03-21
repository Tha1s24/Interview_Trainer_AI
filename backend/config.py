import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configurações base compartilhadas por todos os ambientes."""

    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-insecure")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-insecure")
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 horas em segundos

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_CHAT_MODEL = "gpt-4o"
    OPENAI_WHISPER_MODEL = "whisper-1"

    DATABASE_PATH = os.getenv("DATABASE_PATH", "database/interview_trainer.db")
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads/")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))  # 5 MB

    PROMPTS_FOLDER = os.path.join(os.path.dirname(__file__), "prompts")

    # Tipos de vaga suportados
    JOB_TYPES = ["tech", "design", "marketing", "hr", "sales", "finance", "general"]

    # Personas de recrutador disponíveis
    RECRUITER_PERSONAS = ["senior_recruiter", "hr_generalist", "tech_lead"]

    # Planos e limites de sessão
    PLAN_LIMITS = {
        "free": 3,
        "pro": -1,  # ilimitado
    }


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    # Em produção, JWT_SECRET_KEY DEVE vir do ambiente — nunca hardcoded
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hora


class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    DATABASE_PATH = ":memory:"


# Mapa para seleção via variável de ambiente FLASK_ENV
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config():
    env = os.getenv("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)