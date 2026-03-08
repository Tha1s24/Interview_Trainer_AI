import os
import logging
from flask import Blueprint, request, jsonify
from services.ai_service import AIService

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

interview_bp = Blueprint('interview', __name__)

# Diretório para áudios temporários
TEMP_DIR = "./backend/temp"
os.makedirs(TEMP_DIR, exist_ok=True)

@interview_bp.route('/ask', methods=['POST'])
def ask_question():
    try:
        data = request.json
        if not data or 'history' not in data:
            return jsonify({"error": "Dados inválidos: histórico necessário"}), 400
            
        history = data.get('history', [])
        resume = data.get('resume_text', '')
        
        question = AIService.generate_interview_question(history, resume)
        return jsonify({"question": question}), 200
        
    except Exception as e:
        logger.error(f"Erro ao gerar pergunta: {e}")
        return jsonify({"error": "Erro interno ao processar pergunta"}), 500

@interview_bp.route('/process-voice', methods=['POST'])
def process_voice():
    if 'audio' not in request.files:
        return jsonify({"error": "Nenhum áudio enviado"}), 400
    
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({"error": "Arquivo vazio"}), 400
        
    audio_path = os.path.join(TEMP_DIR, "temp_audio.webm")
    
    try:
        audio_file.save(audio_path)
        # Transcrição via IA
        text = AIService.transcribe_audio(audio_path)
        
        # Limpeza do arquivo temporário
        if os.path.exists(audio_path):
            os.remove(audio_path)
            
        return jsonify({"transcription": text}), 200
        
    except Exception as e:
        logger.error(f"Erro no processamento de áudio: {e}")
        return jsonify({"error": "Falha na transcrição"}), 500