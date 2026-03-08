from flask import Blueprint, request, jsonify
from services.ai_service import AIService

feedback_bp = Blueprint('feedback', __name__)

@feedback_bp.route('/generate', methods=['POST'])
def generate_feedback():
    data = request.json
    answers = data.get('answers', [])
    
    feedback_json = AIService.analyze_feedback(answers)
    return jsonify(feedback_json), 200