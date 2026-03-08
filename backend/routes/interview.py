from flask import Blueprint, request, jsonify
from services.ai_service import AIService

interview_bp = Blueprint('interview', __name__)

@interview_bp.route('/ask', methods=['POST'])
def ask_question():
    data = request.json
    history = data.get('history', [])
    resume = data.get('resume_text', '')
    
    # Chama o serviço de IA para gerar a próxima pergunta
    question = AIService.generate_interview_question(history, resume)
    return jsonify({"question": question}), 200

@interview_bp.route('/process-voice', methods=['POST'])
def process_voice():
    if 'audio' not in request.files:
        return jsonify({"error": "Nenhum áudio enviado"}), 400
    
    audio_file = request.files['audio']
    audio_path = "./temp_audio.webm"
    audio_file.save(audio_path)
    
    text = AIService.transcribe_audio(audio_path)
    return jsonify({"transcription": text}), 200