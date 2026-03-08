import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class AIService:
    @staticmethod
    def generate_interview_question(history, resume_text=None):
        """Gera a próxima pergunta com base no histórico e currículo."""
        system_prompt = "Você é um recrutador sênior de uma startup tech. Seja profissional e direto."
        if resume_text:
            system_prompt += f" Baseie suas perguntas neste currículo: {resume_text}"

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt}] + history
        )
        return response.choices[0].message.content

    @staticmethod
    def analyze_feedback(answers):
        """Analisa todas as respostas e gera um feedback estruturado."""
        prompt = f"Analise estas respostas de entrevista e retorne um JSON com: pontos_fortes, pontos_fracos e sugestoes. Respostas: {answers}"
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content

    @staticmethod
    def transcribe_audio(audio_file_path):
        """Converte áudio em texto usando Whisper."""
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        return transcript.text