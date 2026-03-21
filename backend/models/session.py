import uuid
import json
from database.db import query, execute


def _new_id():
    return "sess_" + uuid.uuid4().hex


class SessionModel:

    @staticmethod
    def create(user_id: str, data: dict) -> dict:
        session_id = _new_id()
        execute(
            """INSERT INTO sessions
               (id, user_id, job_id, resume_id, mode, persona, pressure_mode, time_limit)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                user_id,
                data.get("job_id"),
                data.get("resume_id"),
                data.get("mode", "text"),
                data.get("persona", "senior_recruiter"),
                1 if data.get("pressure_mode") else 0,
                data.get("time_limit_minutes"),
            ),
        )
        return SessionModel.find_by_id(session_id)

    @staticmethod
    def find_by_id(session_id: str) -> dict | None:
        return query(
            "SELECT * FROM sessions WHERE id = ?",
            (session_id,),
            one=True,
        )

    @staticmethod
    def list_by_user(user_id: str, page: int = 1, limit: int = 10) -> list:
        offset = (page - 1) * limit
        return query(
            """SELECT s.*, j.title as job_title, j.company,
                      f.overall_score as score
               FROM sessions s
               LEFT JOIN jobs j ON s.job_id = j.id
               LEFT JOIN feedbacks f ON f.session_id = s.id
               WHERE s.user_id = ?
               ORDER BY s.started_at DESC
               LIMIT ? OFFSET ?""",
            (user_id, limit, offset),
        )

    @staticmethod
    def count_by_user(user_id: str) -> int:
        row = query(
            "SELECT COUNT(*) as total FROM sessions WHERE user_id = ?",
            (user_id,),
            one=True,
        )
        return row["total"] if row else 0

    @staticmethod
    def end(session_id: str) -> dict | None:
        execute(
            "UPDATE sessions SET status = 'completed', ended_at = datetime('now') WHERE id = ?",
            (session_id,),
        )
        return SessionModel.find_by_id(session_id)

    @staticmethod
    def add_message(session_id: str, role: str, content: str, audio_path: str = None) -> str:
        msg_id = "msg_" + uuid.uuid4().hex
        execute(
            "INSERT INTO messages (id, session_id, role, content, audio_path) VALUES (?, ?, ?, ?, ?)",
            (msg_id, session_id, role, content, audio_path),
        )
        return msg_id

    @staticmethod
    def get_messages(session_id: str) -> list:
        return query(
            "SELECT role, content, created_at FROM messages WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,),
        )

    @staticmethod
    def count_messages(session_id: str) -> int:
        row = query(
            "SELECT COUNT(*) as total FROM messages WHERE session_id = ? AND role = 'user'",
            (session_id,),
            one=True,
        )
        return row["total"] if row else 0