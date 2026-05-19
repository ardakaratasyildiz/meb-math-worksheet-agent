"""ReportLab ile worksheet → PDF render.

Türkçe karakter desteği için font fallback sırası: DejaVu Sans → Helvetica
(reportlab default). DejaVu yoksa Helvetica latin-9 fallback'i Türkçe çoğu
karakter için zaten yeterli (ş, ğ, ü, ç, ö, ı). Çıktı bytes — endpoint streaming
yapar.

Soru metni Markdown blokları içerebilir (LLM prompt'unda talimat verildi):
- ```kod bloğu``` — ASCII çubuk grafik / Unicode geometri şekli (monospace gerek)
- | GFM | tablosu |
- Inline **bold**, *italic*, `code`

Aşağıdaki _segment_markdown text/code/table'a böler, her segment uygun
flowable'a (Paragraph / Preformatted / Table) dönüşür. Bu olmadan code block
proportional font'ta yamuk, tablo pipe'lı ham metin olarak basılırdı.
"""
from __future__ import annotations

import io
import logging
import re
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
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
_MONO_FONT = "Courier"  # reportlab builtin; ASCII-only Unicode
_MONO_BOLD_FONT = "Courier-Bold"


def _register_fonts() -> None:
    """DejaVu varsa kaydet — daha geniş Unicode kapsamı (█ ▇ △ □ ○ vb).
    Yoksa Helvetica/Courier latin-9 fallback. Mono için ayrıca DejaVu Sans Mono
    aranır — code block'taki ASCII çubuk + Unicode geometri şekilleri için kritik.
    """
    global _FONT_REGISTERED, _BODY_FONT, _BOLD_FONT, _MONO_FONT, _MONO_BOLD_FONT
    if _FONT_REGISTERED:
        return
    _FONT_REGISTERED = True

    import os

    # Body font (DejaVu Sans)
    body_candidates = [
        ("C:/Windows/Fonts/DejaVuSans.ttf", "C:/Windows/Fonts/DejaVuSans-Bold.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("/Library/Fonts/DejaVuSans.ttf", "/Library/Fonts/DejaVuSans-Bold.ttf"),
    ]
    for regular, bold in body_candidates:
        if os.path.exists(regular):
            try:
                pdfmetrics.registerFont(TTFont("DejaVu", regular))
                _BODY_FONT = "DejaVu"
                if os.path.exists(bold):
                    pdfmetrics.registerFont(TTFont("DejaVu-Bold", bold))
                    _BOLD_FONT = "DejaVu-Bold"
                logger.info("PDF font: DejaVu yüklendi.")
                break
            except Exception as exc:
                logger.warning("DejaVu yüklenemedi (%s); Helvetica fallback.", exc)
                break
    else:
        logger.info("PDF font: Helvetica fallback kullanılıyor.")

    # Mono font (DejaVu Sans Mono) — code block'taki Unicode/ASCII çubuk için
    mono_candidates = [
        ("C:/Windows/Fonts/DejaVuSansMono.ttf",
         "C:/Windows/Fonts/DejaVuSansMono-Bold.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"),
        ("/Library/Fonts/DejaVuSansMono.ttf",
         "/Library/Fonts/DejaVuSansMono-Bold.ttf"),
        # Windows Consolas — DejaVu yoksa makul fallback
        ("C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/consolab.ttf"),
    ]
    for regular, bold in mono_candidates:
        if os.path.exists(regular):
            try:
                pdfmetrics.registerFont(TTFont("DejaVuMono", regular))
                _MONO_FONT = "DejaVuMono"
                if os.path.exists(bold):
                    pdfmetrics.registerFont(TTFont("DejaVuMono-Bold", bold))
                    _MONO_BOLD_FONT = "DejaVuMono-Bold"
                logger.info("PDF mono font: %s yüklendi.", regular)
                return
            except Exception as exc:
                logger.warning("Mono font yüklenemedi (%s); Courier fallback.", exc)
                break
    logger.info("PDF mono font: Courier fallback (sadece ASCII).")


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
    qcode = ParagraphStyle(
        "QCode",
        parent=base["Normal"],
        fontName=_MONO_FONT,
        fontSize=9,
        leading=11,
        leftIndent=8,
        spaceBefore=4,
        spaceAfter=6,
        backColor=colors.HexColor("#F4F4F5"),  # zinc-100
        borderColor=colors.HexColor("#E4E4E7"),
        borderWidth=0.5,
        borderPadding=6,
        textColor=colors.HexColor("#18181B"),  # zinc-900
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
        "qheader": qheader, "qbody": qbody, "qcode": qcode,
        "answerline": answerline, "section": section,
    }


# ─── Markdown segmenter & inline render ──────────────────────────────────────

_FENCE_RE = re.compile(
    r"```(?P<lang>[a-zA-Z0-9_+\-]*)\n?(?P<body>.*?)```",
    flags=re.DOTALL,
)
_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
_TABLE_SEP_RE = re.compile(r"^\s*\|?[\s:|\-]+\|?\s*$")


def _segment_markdown(text: str) -> list[tuple[str, str]]:
    """Soru metnini ('text' | 'code' | 'table', içerik) parçalarına böler.

    Sıra korunur. Code fence (```...```) önce çıkarılır; geri kalan 'text'
    segmentleri içinde GFM tablo blokları (`| ... |\\n|---|---|\\n| ... |`) ayrı
    'table' segmentine geçer. Düz metin segmentleri Paragraph'a, code blokları
    Preformatted'a, tablolar reportlab Table'a dönüşür.
    """
    if not text:
        return []
    segments: list[tuple[str, str]] = []
    pos = 0
    for m in _FENCE_RE.finditer(text):
        if m.start() > pos:
            segments.append(("text", text[pos:m.start()]))
        body = m.group("body").rstrip("\n")
        segments.append(("code", body))
        pos = m.end()
    if pos < len(text):
        segments.append(("text", text[pos:]))

    # 'text' segmentleri içinde GFM tabloları ayrıştır
    final: list[tuple[str, str]] = []
    for kind, content in segments:
        if kind != "text":
            final.append((kind, content))
            continue
        lines = content.split("\n")
        buf: list[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            is_row = bool(_TABLE_ROW_RE.match(line))
            next_sep = (
                i + 1 < len(lines)
                and _TABLE_ROW_RE.match(lines[i + 1])
                and _TABLE_SEP_RE.match(lines[i + 1])
                and "-" in lines[i + 1]
            )
            if is_row and next_sep:
                if buf:
                    final.append(("text", "\n".join(buf)))
                    buf = []
                table_lines = [line, lines[i + 1]]
                i += 2
                while i < len(lines) and _TABLE_ROW_RE.match(lines[i]):
                    table_lines.append(lines[i])
                    i += 1
                final.append(("table", "\n".join(table_lines)))
            else:
                buf.append(line)
                i += 1
        if buf:
            final.append(("text", "\n".join(buf)))
    return final


def _parse_table(md_table: str) -> list[list[str]]:
    """GFM tablo metnini hücre matrisine çevirir. Separator satırı atılır."""
    rows: list[list[str]] = []
    for ln in md_table.split("\n"):
        ln = ln.strip()
        if not ln:
            continue
        if _TABLE_SEP_RE.match(ln) and "-" in ln:
            continue
        # | a | b | c |  →  ['a', 'b', 'c']
        inner = ln.strip("|")
        cells = [c.strip() for c in inner.split("|")]
        rows.append(cells)
    return rows


_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_ITALIC_RE = re.compile(r"(?<!\*)\*(?!\*)([^*]+)\*(?!\*)")


def _md_inline_to_rl(text: str) -> str:
    """Paragraph içine geçecek metni reportlab markup'una çevirir.

    Sıra önemli: önce HTML escape, sonra Markdown → reportlab tag çevirisi.
    """
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = _BOLD_RE.sub(r"<b>\1</b>", text)
    text = _ITALIC_RE.sub(r"<i>\1</i>", text)
    text = _INLINE_CODE_RE.sub(
        lambda m: (
            f'<font name="{_MONO_FONT}" backColor="#F4F4F5">'
            f"&#8202;{m.group(1)}&#8202;</font>"
        ),
        text,
    )
    return text


def _escape_for_pre(text: str) -> str:
    """Preformatted reportlab için sadece &<> escape; satırlar olduğu gibi kalır."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _render_markdown_blocks(
    text: str,
    styles: dict[str, ParagraphStyle],
) -> list:
    """Soru metnini segmentlere bölüp her segment için bir flowable üretir."""
    flow: list = []
    segments = _segment_markdown(text)
    if not segments:
        return flow
    for kind, content in segments:
        if kind == "code":
            # Preformatted satır satır basar — ASCII çubuk grafik ve Unicode
            # geometri şekilleri için kritik (proportional font hizalamaz).
            if not content.strip():
                continue
            flow.append(Preformatted(_escape_for_pre(content), styles["qcode"]))
        elif kind == "table":
            rows = _parse_table(content)
            if not rows:
                continue
            # İlk satır header. Hücre içeriği inline markdown içerebilir.
            table_data = [
                [Paragraph(_md_inline_to_rl(c), styles["qbody"]) for c in row]
                for row in rows
            ]
            col_count = max(len(r) for r in rows)
            # Eşit genişlik dağıt — page width ≈ 17cm (A4 - 2*2cm margin)
            usable_width = 17 * cm
            col_widths = [usable_width / col_count] * col_count
            t = Table(table_data, colWidths=col_widths, hAlign="LEFT")
            t.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, 0), _BOLD_FONT),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F4F4F5")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D4D4D8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            flow.append(t)
            flow.append(Spacer(1, 0.15 * cm))
        else:  # text
            # Boş paragrafları atla, satır içi markdown'ı reportlab tag'ına çevir.
            # Çok satırlı düz metni satır gruplarına böl (boş satır = yeni paragraf).
            blocks = re.split(r"\n\s*\n", content.strip("\n"))
            for block in blocks:
                clean = block.strip()
                if not clean:
                    continue
                # Tek satır içindeki <br/> ile satırları koru
                escaped = _md_inline_to_rl(clean).replace("\n", "<br/>")
                flow.append(Paragraph(escaped, styles["qbody"]))
    return flow


def _question_block(q: Question, styles: dict[str, ParagraphStyle]) -> list:
    flow: list = [Paragraph(f"Soru {q.number}", styles["qheader"])]
    blocks = _render_markdown_blocks(q.question, styles)
    if not blocks:
        # Hiç içerik üretilmediyse boş soru riski — fallback olarak ham metin bas.
        safe = q.question.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        blocks = [Paragraph(safe, styles["qbody"])]
    flow.extend(blocks)
    flow.append(Paragraph("Cevap: " + "_" * 40, styles["answerline"]))
    flow.append(Spacer(1, 0.2 * cm))
    # Tüm soruyu mümkünse aynı sayfada tut — şekil sayfa sonunda bölünürse okunmuyor.
    return [KeepTogether(flow)]


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


def render_worksheet_pdf(
    worksheet: Worksheet,
    include_answer_key: bool = True,
    include_solutions: bool = True,
) -> bytes:
    """Bir Worksheet'i PDF byte'larına render eder.

    Yapı (toggle'lara göre):
        Sayfa 1+: Başlık + sınıf/zorluk + sorular (cevap satırlı, çözümsüz)
        [Opsiyonel] Sayfa N: Cevap anahtarı tablo (include_answer_key)
        [Opsiyonel] Sayfa N+1: Çözüm adımları (include_solutions)

    Sprint 12-A toggle paketi (2026-05-19):
        - include_answer_key=False → sınav modu, sadece sorular basılır.
        - include_solutions=False → öğrenci kağıdı, cevap olabilir ama çözüm yok.
        - Her ikisi de False → temiz öğrenci versiyonu.
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

    if include_answer_key:
        flow.append(PageBreak())
        flow.extend(_answer_key_table(worksheet.questions, styles))

    if include_solutions:
        flow.append(PageBreak())
        flow.extend(_solutions_section(worksheet.questions, styles))

    doc.build(flow)
    return buf.getvalue()
