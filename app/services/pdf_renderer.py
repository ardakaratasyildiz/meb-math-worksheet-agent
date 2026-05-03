"""ReportLab ile worksheet → PDF render.

Türkçe karakter desteği için font fallback sırası: DejaVu Sans → Helvetica
(reportlab default). DejaVu yoksa Helvetica latin-9 fallback'i Türkçe çoğu
karakter için zaten yeterli (ş, ğ, ü, ç, ö, ı). Çıktı bytes — endpoint streaming
yapar.
"""
from __future__ import annotations

import io
import logging
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.schemas import Question, SolutionStep, Worksheet, parse_solution_steps

logger = logging.getLogger(__name__)


_FONT_REGISTERED = False
_BODY_FONT = "Helvetica"
_BOLD_FONT = "Helvetica-Bold"


def _register_fonts() -> None:
    """DejaVu varsa kaydet — daha geniş Unicode kapsamı. Yoksa Helvetica latin-9."""
    global _FONT_REGISTERED, _BODY_FONT, _BOLD_FONT
    if _FONT_REGISTERED:
        return
    _FONT_REGISTERED = True
    candidates = [
        ("C:/Windows/Fonts/DejaVuSans.ttf", "C:/Windows/Fonts/DejaVuSans-Bold.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("/Library/Fonts/DejaVuSans.ttf", "/Library/Fonts/DejaVuSans-Bold.ttf"),
    ]
    import os
    for regular, bold in candidates:
        if os.path.exists(regular):
            try:
                pdfmetrics.registerFont(TTFont("DejaVu", regular))
                _BODY_FONT = "DejaVu"
                if os.path.exists(bold):
                    pdfmetrics.registerFont(TTFont("DejaVu-Bold", bold))
                    _BOLD_FONT = "DejaVu-Bold"
                logger.info("PDF font: DejaVu yüklendi.")
                return
            except Exception as exc:
                logger.warning("DejaVu yüklenemedi (%s); Helvetica fallback.", exc)
                break
    logger.info("PDF font: Helvetica fallback kullanılıyor.")


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    title = ParagraphStyle(
        "WorksheetTitle",
        parent=base["Title"],
        fontName=_BOLD_FONT,
        fontSize=18,
        spaceAfter=12,
        alignment=1,
    )
    meta = ParagraphStyle(
        "WorksheetMeta",
        parent=base["Normal"],
        fontName=_BODY_FONT,
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=18,
        alignment=1,
    )
    qheader = ParagraphStyle(
        "QHeader",
        parent=base["Normal"],
        fontName=_BOLD_FONT,
        fontSize=12,
        spaceAfter=6,
    )
    qbody = ParagraphStyle(
        "QBody",
        parent=base["Normal"],
        fontName=_BODY_FONT,
        fontSize=11,
        leading=16,
        spaceAfter=4,
    )
    answerline = ParagraphStyle(
        "AnswerLine",
        parent=base["Normal"],
        fontName=_BODY_FONT,
        fontSize=10,
        textColor=colors.darkgrey,
        spaceAfter=14,
    )
    section = ParagraphStyle(
        "Section",
        parent=base["Heading2"],
        fontName=_BOLD_FONT,
        fontSize=14,
        spaceAfter=10,
    )
    return {
        "title": title, "meta": meta,
        "qheader": qheader, "qbody": qbody,
        "answerline": answerline, "section": section,
    }


def _question_block(q: Question, styles: dict[str, ParagraphStyle]) -> list:
    flow = []
    flow.append(Paragraph(f"Soru {q.number}", styles["qheader"]))
    # HTML escape minimal — reportlab Paragraph &<> ister
    safe = q.question.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    flow.append(Paragraph(safe, styles["qbody"]))
    # Boş cevap satırı
    flow.append(Paragraph("Cevap: " + "_" * 40, styles["answerline"]))
    flow.append(Spacer(1, 0.2 * cm))
    return flow


def _answer_key_table(questions: Iterable[Question], styles: dict[str, ParagraphStyle]) -> list:
    flow = [Paragraph("Cevap Anahtarı", styles["section"])]
    rows = [["#", "Cevap", "Kazanım"]]
    for q in questions:
        ans = q.answer.replace("\n", " ").strip()
        rows.append([str(q.number), ans, q.kazanim_kod])
    table = Table(rows, colWidths=[1.2 * cm, 9 * cm, 4 * cm], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), _BOLD_FONT),
        ("FONTNAME", (0, 1), (-1, -1), _BODY_FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f7")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    flow.append(table)
    flow.append(Spacer(1, 0.5 * cm))
    return flow


def _solutions_section(questions: Iterable[Question], styles: dict[str, ParagraphStyle]) -> list:
    flow = [Paragraph("Çözüm Adımları", styles["section"])]
    for q in questions:
        flow.append(Paragraph(f"Soru {q.number} — {q.kazanim_kod}", styles["qheader"]))
        steps = q.solution_steps
        if isinstance(steps, str):
            parsed = parse_solution_steps(steps)
        else:
            parsed = steps
        if not parsed:
            flow.append(Paragraph("(çözüm boş)", styles["qbody"]))
        else:
            for s in parsed:
                line = f"<b>{s.step_no}.</b> {s.description}"
                if s.computation:
                    line += f" <font color='#555'>[{s.computation}]</font>"
                flow.append(Paragraph(line, styles["qbody"]))
        flow.append(Spacer(1, 0.3 * cm))
    return flow


def render_worksheet_pdf(worksheet: Worksheet) -> bytes:
    """Bir Worksheet'i PDF byte'larına render eder.

    Yapı:
        Sayfa 1+: Başlık + sınıf/zorluk + sorular (cevap satırlı, çözümsüz)
        Sayfa N: Cevap anahtarı tablo
        Sayfa N+1: Çözüm adımları
    """
    _register_fonts()
    styles = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title=worksheet.title,
        author="MEB Math Worksheet Agent",
    )

    flow = []
    flow.append(Paragraph(worksheet.title, styles["title"]))
    meta_line = (
        f"{worksheet.grade}. sınıf · {worksheet.topic} · "
        f"Zorluk: {worksheet.difficulty.value} · {worksheet.question_count} soru"
    )
    flow.append(Paragraph(meta_line, styles["meta"]))

    for q in worksheet.questions:
        flow.extend(_question_block(q, styles))

    flow.append(PageBreak())
    flow.extend(_answer_key_table(worksheet.questions, styles))

    flow.append(PageBreak())
    flow.extend(_solutions_section(worksheet.questions, styles))

    doc.build(flow)
    return buf.getvalue()
