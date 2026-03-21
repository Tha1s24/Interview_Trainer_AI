import uuid
import json
from database.db import query, execute


def _new_id():
    return "fbk_" + uuid.uuid4().hex


class FeedbackModel:

    @staticmethod
    def create(session_id: str, data: dict) -> dict:
        feedback_id = _new_id()
        execute(
            """INSERT INTO feedbacks
               (id, session_id, overall_score, score_breakdown_json,
                strengths_json, improvements_json, action_plan_json, next_session_focus_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                feedback_id,
                session_id,
                data.get("overall_score", 0),
                json.dumps(data.get("score_breakdown", {})),
                json.dumps(data.get("strengths", [])),
                json.dumps(data.get("improvements", [])),
                json.dumps(data.get("action_plan", [])),
                json.dumps(data.get("next_session_focus", [])),
            ),
        )
        return FeedbackModel.find_by_id(feedback_id)

    @staticmethod
    def find_by_id(feedback_id: str) -> dict | None:
        row = query(
            "SELECT * FROM feedbacks WHERE id = ?",
            (feedback_id,),
            one=True,
        )
        return FeedbackModel._deserialize(row) if row else None

    @staticmethod
    def find_by_session(session_id: str) -> dict | None:
        row = query(
            "SELECT * FROM feedbacks WHERE session_id = ?",
            (session_id,),
            one=True,
        )
        return FeedbackModel._deserialize(row) if row else None

    @staticmethod
    def _deserialize(row: dict) -> dict:
        """Converte os campos JSON de volta para dicionários Python."""
        if not row:
            return row
        for field in ["score_breakdown_json", "strengths_json", "improvements_json",
                      "action_plan_json", "next_session_focus_json"]:
            clean_key = field.replace("_json", "")
            try:
                row[clean_key] = json.loads(row.get(field, "{}"))
            except (json.JSONDecodeError, TypeError):
                row[clean_key] = {} if field == "score_breakdown_json" else []
        return row