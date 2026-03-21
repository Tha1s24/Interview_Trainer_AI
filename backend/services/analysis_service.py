import re
import uuid
import json
from collections import Counter
import pandas as pd
from database.db import query, execute

# Vícios de linguagem mais comuns em PT-BR
FILLER_WORDS_PTBR = [
    "então", "tipo", "né", "assim", "sabe", "cara", "enfim",
    "basicamente", "literalmente", "obviamente", "ou seja",
    "na verdade", "de certa forma", "meio que",
]

FILLER_WORDS_EN = [
    "um", "uh", "like", "you know", "basically", "literally",
    "actually", "so", "right", "okay", "kind of", "sort of",
]


def analyze_speech(session_id: str, messages: list) -> dict:
    """
    Analisa métricas de comunicação a partir das mensagens do candidato.

    Args:
        session_id: ID da sessão
        messages:   Lista de mensagens [{role, content, created_at}]

    Returns:
        dict com métricas completas de fala
    """
    # Filtra apenas respostas do candidato
    user_messages = [m for m in messages if m["role"] == "user"]

    if not user_messages:
        return _empty_metrics()

    full_text = " ".join(m["content"] for m in user_messages)
    words = _tokenize(full_text)

    wpm_data = _calculate_wpm(user_messages)
    fillers = _detect_fillers(full_text)
    vocabulary = _analyze_vocabulary(words, user_messages)
    pauses = _analyze_pauses(user_messages)

    metrics = {
        "wpm_average": wpm_data["average"],
        "wpm_variation": wpm_data["variation"],
        "filler_words": fillers,
        "pause_analysis": pauses,
        "vocabulary": vocabulary,
    }

    # Persiste métricas no banco
    _save_metrics(session_id, metrics)

    return metrics


def _tokenize(text: str) -> list[str]:
    """Remove pontuação e retorna lista de palavras em minúsculo."""
    return re.findall(r'\b[a-záàãâéêíóôõúüç]+\b', text.lower())


def _calculate_wpm(messages: list) -> dict:
    """
    Calcula WPM médio e variação entre respostas.
    Usa timestamps das mensagens para estimar duração de fala.
    """
    try:
        df = pd.DataFrame(messages)
        df["created_at"] = pd.to_datetime(df["created_at"])
        df["word_count"] = df["content"].apply(lambda t: len(_tokenize(t)))
        df = df.sort_values("created_at")
        df["duration_min"] = df["created_at"].diff().dt.total_seconds().div(60).shift(-1)
        df = df.dropna(subset=["duration_min"])
        df = df[df["duration_min"] > 0]

        if df.empty:
            avg = _estimate_wpm_from_word_count(messages)
            return {"average": avg, "variation": "unknown"}

        df["wpm"] = df["word_count"] / df["duration_min"]
        avg = round(df["wpm"].mean(), 1)
        std = df["wpm"].std()

        variation = "stable"
        if std > 40:
            variation = "high"
        elif std > 20:
            variation = "moderate"

        return {"average": avg, "variation": variation}
    except Exception:
        avg = _estimate_wpm_from_word_count(messages)
        return {"average": avg, "variation": "unknown"}


def _estimate_wpm_from_word_count(messages: list) -> float:
    """Fallback: estima WPM assumindo velocidade média de fala (130 wpm)."""
    total_words = sum(len(_tokenize(m["content"])) for m in messages)
    return min(total_words, 130)  # estimativa conservadora


def _detect_fillers(text: str) -> dict:
    """Detecta e conta vícios de linguagem no texto."""
    text_lower = text.lower()
    counts = {}

    for filler in FILLER_WORDS_PTBR + FILLER_WORDS_EN:
        # Contagem com word boundary para palavras simples
        pattern = r'\b' + re.escape(filler) + r'\b'
        count = len(re.findall(pattern, text_lower))
        if count > 0:
            counts[filler] = count

    total = sum(counts.values())
    top_fillers = sorted(
        [{"word": w, "count": c} for w, c in counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )[:5]

    return {
        "count": total,
        "top_fillers": top_fillers,
    }


def _analyze_vocabulary(words: list, messages: list) -> dict:
    """Analisa riqueza e clareza do vocabulário."""
    total_words = len(words)
    unique_words = len(set(words))
    lexical_diversity = round(unique_words / total_words, 2) if total_words > 0 else 0

    avg_sentence_len = _avg_sentence_length(messages)

    # Score de clareza: penaliza frases muito longas (>25 palavras) ou muito curtas (<5)
    clarity_score = _compute_clarity_score(avg_sentence_len, lexical_diversity)

    return {
        "total_words": total_words,
        "unique_words": unique_words,
        "lexical_diversity": lexical_diversity,
        "avg_sentence_length": avg_sentence_len,
        "clarity_score": clarity_score,
    }


def _avg_sentence_length(messages: list) -> float:
    sentences = []
    for m in messages:
        parts = re.split(r'[.!?]', m["content"])
        sentences.extend([p.strip() for p in parts if p.strip()])
    if not sentences:
        return 0.0
    lengths = [len(_tokenize(s)) for s in sentences]
    return round(sum(lengths) / len(lengths), 1)


def _compute_clarity_score(avg_len: float, diversity: float) -> int:
    """Score de 0-100 baseado no comprimento médio de sentenças e diversidade léxica."""
    score = 70  # base

    # Penaliza sentenças muito longas (>25 palavras) ou muito curtas (<5)
    if avg_len > 25:
        score -= min(20, int((avg_len - 25) * 2))
    elif avg_len < 5:
        score -= 15

    # Diversidade léxica saudável: entre 0.4 e 0.7
    if diversity >= 0.4:
        score += min(20, int(diversity * 20))
    else:
        score -= 10

    return max(0, min(100, score))


def _analyze_pauses(messages: list) -> dict:
    """
    Analisa pausas entre mensagens do candidato.
    Pausas >5s entre perguntas e respostas indicam hesitação.
    """
    try:
        df = pd.DataFrame(messages)
        df["created_at"] = pd.to_datetime(df["created_at"])
        df = df.sort_values("created_at")
        df["gap_seconds"] = df["created_at"].diff().dt.total_seconds()

        long_pauses = df[df["gap_seconds"] > 10].shape[0]
        avg_pause = round(df["gap_seconds"].mean() * 1000, 0)  # em ms

        hesitation = "low"
        if long_pauses >= 5:
            hesitation = "high"
        elif long_pauses >= 2:
            hesitation = "moderate"

        return {
            "avg_pause_ms": avg_pause,
            "long_pauses_count": long_pauses,
            "hesitation_rate": hesitation,
        }
    except Exception:
        return {"avg_pause_ms": 0, "long_pauses_count": 0, "hesitation_rate": "unknown"}


def _save_metrics(session_id: str, metrics: dict):
    """Persiste as métricas no banco de dados."""
    metric_id = "spm_" + uuid.uuid4().hex
    execute(
        """INSERT OR REPLACE INTO speech_metrics
           (id, session_id, wpm_average, filler_words_json, pause_analysis_json, vocabulary_json)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            metric_id,
            session_id,
            metrics.get("wpm_average"),
            json.dumps(metrics.get("filler_words", {})),
            json.dumps(metrics.get("pause_analysis", {})),
            json.dumps(metrics.get("vocabulary", {})),
        ),
    )


def _empty_metrics() -> dict:
    return {
        "wpm_average": 0,
        "wpm_variation": "unknown",
        "filler_words": {"count": 0, "top_fillers": []},
        "pause_analysis": {"avg_pause_ms": 0, "long_pauses_count": 0, "hesitation_rate": "unknown"},
        "vocabulary": {"total_words": 0, "unique_words": 0, "clarity_score": 0},
    }