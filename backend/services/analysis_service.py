import re

class AnalysisService:
    @staticmethod
    def calculate_pacing(text, duration_seconds):
        """Calcula palavras por minuto (WPM). Média ideal: 120-150."""
        words = len(text.split())
        minutes = duration_seconds / 60
        return round(words / minutes) if minutes > 0 else 0

    @staticmethod
    def detect_filler_words(text):
        """Detecta vícios de linguagem comuns."""
        fillers = ['tipo', 'né', 'então', 'meio que', 'ah', 'eh', 'basicamente']
        found = {word: text.lower().count(word) for word in fillers if word in text.lower()}
        return found

    @staticmethod
    def analyze_clarity(text):
        """
        Analisa a clareza baseada no tamanho médio das sentenças.
        Sentenças muito longas podem indicar falta de clareza.
        """
        sentences = re.split(r'[.!?]+', text)
        sentences = [s for s in sentences if len(s.strip()) > 0]
        if not sentences:
            return "N/A"
        
        avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
        
        if avg_length < 15: return "Concisa e Clara"
        if avg_length < 25: return "Boa, mas cuidado com frases longas"
        return "Prolixa (Tente ser mais direto)"