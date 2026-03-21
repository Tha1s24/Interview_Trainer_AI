import os
import json
import uuid
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from flask import current_app

# ── Paleta de cores ────────────────────────────────────────────
BRAND_DARK   = colors.HexColor("#0F172A")   # títulos principais
BRAND_MID    = colors.HexColor("#1E40AF")   # azul primário
BRAND_LIGHT  = colors.HexColor("#DBEAFE")   # fundo de destaque
ACCENT_GREEN = colors.HexColor("#166534")
BG_GREEN     = colors.HexColor("#DCFCE7")
ACCENT_RED   = colors.HexColor("#991B1B")
BG_RED       = colors.HexColor("#FEE2E2")
ACCENT_AMBER = colors.HexColor("#92400E")
BG_AMBER     = colors.HexColor("#FEF3C7")
GRAY_700     = colors.HexColor("#374151")
GRAY_400     = colors.HexColor("#9CA3AF")
GRAY_100     = colors.HexColor("#F3F4F6")
WHITE        = colors.white


def generate_pdf(
    feedback: dict,
    session: dict,
    job: dict | None,
    resume: dict | None,
    speech: dict | None,
    user: dict,
) -> str:
    """
    Gera o relatório PDF da sessão de entrevista.

    Returns:
        Caminho absoluto do arquivo PDF gerado.
    """
    output_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "reports")
    os.makedirs(output_folder, exist_ok=True)

    filename = f"report_{uuid.uuid4().hex}.pdf"
    pdf_path = os.path.join(output_folder, filename)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2 * cm,
        title="Relatório de Entrevista — Interview Trainer IA",
    )

    styles = _build_styles()
    story = []

    _add_header(story, styles, feedback, session, job, resume, user)
    _add_score_table(story, styles, feedback)
    _add_section(story, styles, "Pontos Fortes", feedback.get("strengths", []),
                 BG_GREEN, ACCENT_GREEN, "✓")
    _add_section(story, styles, "Pontos de Melhoria", feedback.get("improvements", []),
                 BG_RED, ACCENT_RED, "!")
    _add_section(story, styles, "Plano de Ação", feedback.get("action_plan", []),
                 BG_AMBER, ACCENT_AMBER, "→")

    if speech and session.get("mode") == "voice":
        _add_speech_metrics(story, styles, speech)

    _add_next_focus(story, styles, feedback.get("next_session_focus", []))
    _add_footer_note(story, styles)

    doc.build(story)
    return pdf_path


# ── Estilos ────────────────────────────────────────────────────

def _build_styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("h1", fontSize=22, fontName="Helvetica-Bold",
                              textColor=BRAND_DARK, spaceAfter=4),
        "h2": ParagraphStyle("h2", fontSize=13, fontName="Helvetica-Bold",
                              textColor=BRAND_MID, spaceBefore=14, spaceAfter=6),
        "subtitle": ParagraphStyle("subtitle", fontSize=10, fontName="Helvetica",
                                   textColor=GRAY_700, spaceAfter=2),
        "body": ParagraphStyle("body", fontSize=10, fontName="Helvetica",
                               textColor=GRAY_700, leading=15, spaceAfter=4),
        "item": ParagraphStyle("item", fontSize=10, fontName="Helvetica",
                               textColor=GRAY_700, leading=14,
                               leftIndent=8, spaceAfter=5),
        "score_label": ParagraphStyle("score_label", fontSize=9, fontName="Helvetica",
                                      textColor=GRAY_700, alignment=TA_CENTER),
        "score_value": ParagraphStyle("score_value", fontSize=20, fontName="Helvetica-Bold",
                                      textColor=BRAND_MID, alignment=TA_CENTER),
        "footer": ParagraphStyle("footer", fontSize=8, fontName="Helvetica",
                                 textColor=GRAY_400, alignment=TA_CENTER),
        "tag": ParagraphStyle("tag", fontSize=9, fontName="Helvetica-Bold",
                              textColor=BRAND_MID, alignment=TA_CENTER),
    }


# ── Seções do PDF ──────────────────────────────────────────────

def _add_header(story, styles, feedback, session, job, resume, user):
    """Cabeçalho com nome, vaga, score geral e data."""
    resume_parsed = json.loads(resume.get("parsed_json", "{}")) if resume else {}
    candidate_name = resume_parsed.get("name") or user.get("name", "Candidato")
    job_title = job.get("title", "—") if job else "—"
    company = job.get("company", "—") if job else "—"
    mode_label = "Voz" if session.get("mode") == "voice" else "Texto"
    date_str = datetime.now().strftime("%d/%m/%Y")
    score = feedback.get("overall_score", 0)

    # Faixa de cor do score
    if score >= 75:
        score_color = ACCENT_GREEN
        score_label = "Bom desempenho"
    elif score >= 50:
        score_color = ACCENT_AMBER
        score_label = "Desempenho moderado"
    else:
        score_color = ACCENT_RED
        score_label = "Necessita praticar"

    # Linha decorativa superior
    story.append(HRFlowable(width="100%", thickness=4, color=BRAND_MID, spaceAfter=12))

    # Título e meta
    story.append(Paragraph("Relatório de Entrevista Simulada", styles["h1"]))
    story.append(Paragraph(f"Interview Trainer IA — {date_str}", styles["subtitle"]))
    story.append(Spacer(1, 0.3 * cm))

    # Tabela: info do candidato + score geral
    info_data = [
        [Paragraph("Candidato", styles["score_label"]),
         Paragraph("Vaga", styles["score_label"]),
         Paragraph("Empresa", styles["score_label"]),
         Paragraph("Modo", styles["score_label"]),
         Paragraph("Score Geral", styles["score_label"])],
        [Paragraph(f"<b>{candidate_name}</b>", styles["body"]),
         Paragraph(job_title, styles["body"]),
         Paragraph(company, styles["body"]),
         Paragraph(mode_label, styles["body"]),
         Paragraph(f"<font color='#{score_color.hexval()[2:]}'><b>{score}/100</b></font>",
                   styles["score_value"])],
        [Paragraph(""), Paragraph(""), Paragraph(""), Paragraph(""),
         Paragraph(score_label, styles["score_label"])],
    ]

    t = Table(info_data, colWidths=[3.8 * cm, 4 * cm, 3.8 * cm, 2.2 * cm, 3 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GRAY_100),
        ("BACKGROUND", (4, 1), (4, 2), BRAND_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, GRAY_400),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, GRAY_400),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("SPAN", (4, 1), (4, 2)),
        ("VALIGN", (4, 1), (4, 2), "MIDDLE"),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY_400, spaceAfter=10))


def _add_score_table(story, styles, feedback):
    """Tabela de breakdown de scores por categoria."""
    story.append(Paragraph("Desempenho por Categoria", styles["h2"]))

    breakdown = feedback.get("score_breakdown", {})
    categories = {
        "technical_knowledge": "Conhecimento Técnico",
        "communication":       "Comunicação",
        "structure_clarity":   "Clareza e Estrutura",
        "cultural_fit":        "Fit Cultural",
        "confidence":          "Confiança",
    }

    header = [Paragraph(label, styles["score_label"]) for label in categories.values()]
    values = []
    for key in categories:
        val = breakdown.get(key, 0)
        color = ACCENT_GREEN if val >= 75 else (ACCENT_AMBER if val >= 50 else ACCENT_RED)
        values.append(
            Paragraph(f"<font color='#{color.hexval()[2:]}'><b>{val}</b></font>",
                      styles["score_value"])
        )

    t = Table([header, values], colWidths=[3.36 * cm] * 5)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GRAY_100),
        ("BOX", (0, 0), (-1, -1), 0.5, GRAY_400),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, GRAY_400),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.3 * cm))


def _add_section(story, styles, title: str, items: list,
                 bg_color, text_color, icon: str):
    """Seção genérica de itens com fundo colorido."""
    if not items:
        return

    story.append(Paragraph(title, styles["h2"]))

    elements = []
    for item in items:
        p = Paragraph(f"{icon}  {item}", styles["item"])
        row = Table([[p]], colWidths=[16.6 * cm])
        row.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg_color),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("ROUNDEDCORNERS", [4, 4, 4, 4]),
        ]))
        elements.append(row)
        elements.append(Spacer(1, 0.15 * cm))

    story.append(KeepTogether(elements))
    story.append(Spacer(1, 0.2 * cm))


def _add_speech_metrics(story, styles, speech: dict):
    """Seção de métricas de fala (apenas para sessões em modo voz)."""
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY_400,
                             spaceBefore=6, spaceAfter=10))
    story.append(Paragraph("Análise de Comunicação Verbal", styles["h2"]))

    wpm = speech.get("wpm_average", "—")
    fillers_raw = speech.get("filler_words_json") or speech.get("filler_words", {})
    if isinstance(fillers_raw, str):
        try:
            fillers_raw = json.loads(fillers_raw)
        except Exception:
            fillers_raw = {}

    pause_raw = speech.get("pause_analysis_json") or speech.get("pause_analysis", {})
    if isinstance(pause_raw, str):
        try:
            pause_raw = json.loads(pause_raw)
        except Exception:
            pause_raw = {}

    vocab_raw = speech.get("vocabulary_json") or speech.get("vocabulary", {})
    if isinstance(vocab_raw, str):
        try:
            vocab_raw = json.loads(vocab_raw)
        except Exception:
            vocab_raw = {}

    filler_count = fillers_raw.get("count", 0)
    top_fillers = ", ".join(
        f["word"] for f in fillers_raw.get("top_fillers", [])[:3]
    ) or "nenhum"
    hesitation = pause_raw.get("hesitation_rate", "—")
    clarity = vocab_raw.get("clarity_score", "—")

    data = [
        [Paragraph("Métricas", styles["score_label"]),
         Paragraph("WPM Médio", styles["score_label"]),
         Paragraph("Vícios Detectados", styles["score_label"]),
         Paragraph("Hesitação", styles["score_label"]),
         Paragraph("Clareza", styles["score_label"])],
        [Paragraph("Valor", styles["score_label"]),
         Paragraph(f"<b>{wpm}</b>", styles["score_value"]),
         Paragraph(f"<b>{filler_count}</b>", styles["score_value"]),
         Paragraph(f"<b>{hesitation}</b>", styles["body"]),
         Paragraph(f"<b>{clarity}/100</b>", styles["score_value"])],
    ]

    if top_fillers != "nenhum":
        story.append(
            Paragraph(f"Principais vícios identificados: <b>{top_fillers}</b>",
                      styles["body"])
        )

    t = Table(data, colWidths=[3 * cm, 3.15 * cm, 3.65 * cm, 3.4 * cm, 3.4 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GRAY_100),
        ("BOX", (0, 0), (-1, -1), 0.5, GRAY_400),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, GRAY_400),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.3 * cm))


def _add_next_focus(story, styles, focus_items: list):
    """Seção de foco para a próxima sessão."""
    if not focus_items:
        return

    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY_400,
                             spaceBefore=6, spaceAfter=10))
    story.append(Paragraph("Foco para a Próxima Sessão", styles["h2"]))

    tags = [[Paragraph(f"  {item}  ", styles["tag"]) for item in focus_items]]
    t = Table(tags, colWidths=[16.6 / len(focus_items) * cm] * len(focus_items))
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, BRAND_MID),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.4 * cm))


def _add_footer_note(story, styles):
    story.append(Spacer(1, 0.6 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY_400, spaceAfter=6))
    story.append(Paragraph(
        "Relatório gerado automaticamente pelo Interview Trainer IA. "
        "Use este documento como guia de desenvolvimento — pratique regularmente para evoluir.",
        styles["footer"],
    ))