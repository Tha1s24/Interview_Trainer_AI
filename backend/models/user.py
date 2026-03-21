import uuid
import json
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import query, execute


def _new_id():
    return "usr_" + uuid.uuid4().hex


class UserModel:

    @staticmethod
    def create(name: str, email: str, password: str) -> dict | None:
        """Cria um novo usuário e suas preferências padrão."""
        if UserModel.find_by_email(email):
            return None  # e-mail já cadastrado

        user_id = _new_id()
        password_hash = generate_password_hash(password)

        execute(
            "INSERT INTO users (id, name, email, password_hash) VALUES (?, ?, ?, ?)",
            (user_id, name, email, password_hash),
        )
        # Cria preferências padrão
        execute(
            "INSERT INTO user_preferences (user_id) VALUES (?)",
            (user_id,),
        )
        return UserModel.find_by_id(user_id)

    @staticmethod
    def find_by_id(user_id: str) -> dict | None:
        return query(
            "SELECT id, name, email, plan, created_at FROM users WHERE id = ?",
            (user_id,),
            one=True,
        )

    @staticmethod
    def find_by_email(email: str) -> dict | None:
        return query(
            "SELECT * FROM users WHERE email = ?",
            (email,),
            one=True,
        )

    @staticmethod
    def verify_password(email: str, password: str) -> dict | None:
        """Verifica credenciais e retorna o usuário se válidas."""
        user = UserModel.find_by_email(email)
        if user and check_password_hash(user["password_hash"], password):
            return UserModel.find_by_id(user["id"])
        return None

    @staticmethod
    def get_preferences(user_id: str) -> dict | None:
        return query(
            "SELECT * FROM user_preferences WHERE user_id = ?",
            (user_id,),
            one=True,
        )

    @staticmethod
    def update_preferences(user_id: str, data: dict) -> dict:
        allowed = {"theme", "font_size", "libras_enabled", "high_contrast", "language"}
        fields = {k: v for k, v in data.items() if k in allowed}

        if not fields:
            return UserModel.get_preferences(user_id)

        set_clause = ", ".join(f"{k} = ?" for k in fields)
        execute(
            f"UPDATE user_preferences SET {set_clause} WHERE user_id = ?",
            (*fields.values(), user_id),
        )
        return UserModel.get_preferences(user_id)

    @staticmethod
    def count_sessions(user_id: str) -> int:
        row = query(
            "SELECT COUNT(*) as total FROM sessions WHERE user_id = ? AND status = 'completed'",
            (user_id,),
            one=True,
        )
        return row["total"] if row else 0