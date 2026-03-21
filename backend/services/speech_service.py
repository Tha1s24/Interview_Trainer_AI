import os
import uuid
from openai import OpenAI
from flask import current_app

client = OpenAI()


def transcribe_audio(file_path: str, language: str = "pt") -> dict:
    """
    Envia o arquivo de áudio para o Whisper e retorna a transcrição.

    Args:
        file_path: Caminho para o arquivo de áudio (WebM, WAV, MP3)
        language:  Código de idioma BCP-47 (pt, en, es)

    Returns:
        dict com: text (transcrição), confidence (estimada)
    """
    try:
        with open(file_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model=current_app.config["OPENAI_WHISPER_MODEL"],
                file=audio_file,
                language=language,
                response_format="verbose_json",  # inclui metadados de segmentos
            )

        # verbose_json retorna objeto com text e segments
        text = response.text.strip()

        # Estimativa de confiança baseada na média dos segmentos (se disponível)
        confidence = _estimate_confidence(response)

        return {"text": text, "confidence": confidence}

    except Exception as e:
        current_app.logger.error(f"[SpeechService] Erro na transcrição: {e}")
        return {"text": "", "confidence": 0.0}


def save_audio_chunk(file, session_id: str, chunk_index: int) -> str:
    """
    Salva um chunk de áudio no sistema de arquivos.

    Returns:
        Caminho do arquivo salvo
    """
    upload_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "audio", session_id)
    os.makedirs(upload_folder, exist_ok=True)

    ext = ".webm"  # formato padrão do MediaRecorder
    filename = f"chunk_{chunk_index:04d}{ext}"
    path = os.path.join(upload_folder, filename)
    file.save(path)
    return path


def _estimate_confidence(response) -> float:
    """
    Estima confiança média com base nos segmentos do Whisper.
    verbose_json expõe avg_logprob por segmento.
    """
    try:
        segments = response.segments
        if not segments:
            return 0.85  # valor padrão razoável

        # avg_logprob é negativo; quanto mais próximo de 0, melhor
        avg_logprob = sum(s.avg_logprob for s in segments) / len(segments)
        # Converte para escala 0-1 (logprob de -1 ≈ conf 0.37, de 0 ≈ conf 1.0)
        confidence = min(1.0, max(0.0, 1.0 + avg_logprob))
        return round(confidence, 2)
    except Exception:
        return 0.85