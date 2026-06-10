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

import base64
import io
import logging
import re
from typing import Iterable

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
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
    """Soru metnini ('text' | 'code' | 'table' | 'svg' | 'latex', içerik) parçalarına böler.

    Sıra korunur. Öncelik:
        1) <svg>...</svg> blokları (Sprint 12-B/Phase A — gorsel_geometri tipi)
        2) $$...$$ ve $...$ LaTeX blokları (Phase C — salt_islem)
        3) ```...``` kod blokları
        4) GFM tablo blokları (| ... | ile başlayan satırlar + |---| ayırıcı)

    Düz metin → Paragraph, code → Preformatted, tablo → reportlab Table,
    SVG → svglib Drawing, LaTeX → matplotlib mathtext PNG → Image.
    """
    if not text:
        return []

    # Önce SVG bloklarını çıkar — code/table/latex parser'larına takılmasın.
    from app.services.svg_utils import split_text_by_svg
    pre_svg: list[tuple[str, str]] = []
    for kind, content in split_text_by_svg(text):
        if kind == "svg":
            pre_svg.append(("svg", content))
        else:
            pre_svg.append(("text", content))

    # Sonra her 'text' parçası içinde LaTeX ayrıştır:
    #   - $$...$$ display → standalone ortalı Image bloğu (matplotlib PNG)
    #   - $...$  inline   → akan metne çevrilir (görüntü blok cümleyi parçalıyordu)
    from app.services.math_renderer import latex_to_inline_text, split_by_latex
    pre_latex: list[tuple[str, str]] = []
    for pkind, ptext in pre_svg:
        if pkind != "text":
            pre_latex.append((pkind, ptext))
            continue
        buf = ""
        for lkind, lcontent, is_display in split_by_latex(ptext):
            if lkind == "latex" and is_display:
                if buf:
                    pre_latex.append(("text", buf))
                    buf = ""
                pre_latex.append(("latex", lcontent))
            elif lkind == "latex":
                # inline math → düz metin, çevre metinle aynı paragrafta akar
                buf += latex_to_inline_text(lcontent)
            else:
                buf += lcontent
        if buf:
            pre_latex.append(("text", buf))

    # Sonra her 'text' parçası içinde code fence + GFM tablo ayrıştır.
    final: list[tuple[str, str]] = []
    for pkind, ptext in pre_latex:
        if pkind != "text":
            final.append((pkind, ptext))
            continue
        # Code fence
        segments: list[tuple[str, str]] = []
        pos = 0
        for m in _FENCE_RE.finditer(ptext):
            if m.start() > pos:
                segments.append(("text", ptext[pos:m.start()]))
            body = m.group("body").rstrip("\n")
            segments.append(("code", body))
            pos = m.end()
        if pos < len(ptext):
            segments.append(("text", ptext[pos:]))

        # 'text' segmentleri içinde GFM tabloları ayrıştır
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


def _normalize_svg_fonts(svg: str) -> str:
    """SVG metin fontunu kayıtlı gövde fontuna (DejaVu) çevirir.

    svglib, SVG <text>'i font-family'si tanınmazsa Helvetica'ya düşürür; Helvetica
    Türkçe ı/ğ/ş gliflerini içermez → daire grafiği etiketlerinde 'Gıda'→'G■da'
    gibi ■ (tofu) çıkar. Gövde metni zaten DejaVu (Türkçe tam) kullandığından,
    SVG metnini de aynı fonta sabitleriz. _BODY_FONT, _register_fonts'tan sonra
    DejaVu (Render/Linux) veya Helvetica (DejaVu yoksa) olur.
    """
    import re
    font = _BODY_FONT
    # style/CSS biçimi: font-family: X
    svg = re.sub(r"font-family\s*:\s*[^;\"'<>}]+", f"font-family:{font}", svg)
    # attribute biçimi: font-family="X" / 'X' → değeri değiştir
    svg = re.sub(r'font-family\s*=\s*"[^"]*"', f'font-family="{font}"', svg)
    svg = re.sub(r"font-family\s*=\s*'[^']*'", f'font-family="{font}"', svg)

    # font-family taşımayan <text>/<tspan> tag'lerine ekle
    def _inject(m: "re.Match[str]") -> str:
        tag = m.group(0)
        if "font-family" in tag:
            return tag
        return tag[:-1] + f' font-family="{font}"' + tag[-1]

    return re.sub(r"<(?:text|tspan)\b[^>]*>", _inject, svg)


def _render_svg_block(svg_str: str, max_width_cm: float = 12.0) -> object | None:
    """SVG string'i svglib ile reportlab Drawing'e çevirir.

    Bozuk/tehlikeli SVG None döner — caller fallback metin gösterir.
    max_width_cm: A4 yararlı genişliği ~17 cm; geometri şekilleri için 12 cm
    görsel olarak daha okunabilir (santrale yatırılır).
    """
    from app.services.svg_utils import is_valid_svg
    ok, _reason = is_valid_svg(svg_str)
    if not ok:
        return None
    try:
        from io import BytesIO
        from svglib.svglib import svg2rlg
        # Türkçe ■ sorununu önle: SVG metnini kayıtlı DejaVu fontuna sabitle.
        svg_str = _normalize_svg_fonts(svg_str)
        drawing = svg2rlg(BytesIO(svg_str.encode("utf-8")))
        if drawing is None:
            return None
        # Scale: SVG intrinsic boyutu sayfa genişliğini aşıyorsa daralt
        max_w = max_width_cm * cm
        if drawing.width and drawing.width > max_w:
            scale = max_w / drawing.width
            drawing.width *= scale
            drawing.height *= scale
            drawing.scale(scale, scale)
        return drawing
    except Exception as exc:  # noqa: BLE001
        logger.warning("SVG → Drawing dönüşümü başarısız: %s", exc)
        return None


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
        if kind == "svg":
            drawing = _render_svg_block(content)
            if drawing is not None:
                # Drawing flowable kendi başına bir line break gibi davranır.
                flow.append(Spacer(1, 0.2 * cm))
                flow.append(drawing)
                flow.append(Spacer(1, 0.2 * cm))
            else:
                # Fallback: bozuk SVG, kullanıcıya bilgilendirici not.
                flow.append(Paragraph(
                    "<i>[Görsel yüklenemedi]</i>", styles["qbody"],
                ))
        elif kind == "latex":
            # Phase C: matplotlib mathtext ile LaTeX → PNG → Image embed.
            from io import BytesIO
            from app.services.math_renderer import (
                latex_to_inline_text,
                render_latex_to_png,
            )
            png = render_latex_to_png(content, display=True, font_size=14)
            if png:
                img = Image(BytesIO(png))
                # PNG'nin DPI'ı 220, ama reportlab Image varsayılan boyutu
                # native pixel dimensions. Sayfa genişliğine fit etmek için
                # ölçeklendir. Tipik formül ~50-200px geniş; cm'ye çevir.
                from reportlab.lib.utils import ImageReader
                ir = ImageReader(BytesIO(png))
                iw, ih = ir.getSize()
                # 1 inch = 72 pt = 96 px (web) ama matplotlib PNG dpi=220
                # → mm'ye geçmek için px / dpi * 25.4
                px_per_mm = 220 / 25.4
                w_mm = iw / px_per_mm
                h_mm = ih / px_per_mm
                # Max 12cm genişlik
                max_w_mm = 120.0
                if w_mm > max_w_mm:
                    scale = max_w_mm / w_mm
                    w_mm *= scale
                    h_mm *= scale
                img.drawWidth = w_mm * 0.1 * cm  # mm → reportlab "cm" point
                img.drawHeight = h_mm * 0.1 * cm
                flow.append(Spacer(1, 0.15 * cm))
                flow.append(img)
                flow.append(Spacer(1, 0.15 * cm))
            else:
                # PNG render başarısız → düz metne düş ("[yüklenemedi]" yerine).
                flow.append(Paragraph(
                    _md_inline_to_rl(latex_to_inline_text(content)),
                    styles["qbody"],
                ))
        elif kind == "code":
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


def _clean_answer_for_table(answer: str) -> str:
    """Cevap anahtarı tablo hücresi için sade metin üret.

    answer alanındaki LaTeX ($$...$$ / $...$ sınırlayıcıları ve \\frac, \\times
    gibi komutlar) okunabilir düz metne çevrilir; çok satırlı içerik tek satıra
    indirilir, fazla boşluk normalize edilir.
    """
    from app.services.math_renderer import render_latex_inline
    a = render_latex_inline(answer.replace("\n", " ")).strip()
    a = re.sub(r"\s+", " ", a)
    # Boş kaldıysa orijinal answer'ı geri ver (failsafe)
    return a if a else answer.strip()


def _answer_key_table(questions: Iterable[Question], styles: dict[str, ParagraphStyle]) -> list:
    flow = [Paragraph("Cevap Anahtarı", styles["section"])]
    # Hücre stili — Paragraph wrap için kompakt body.
    cell_style = ParagraphStyle(
        "AnswerKeyCell",
        parent=styles["qbody"],
        fontSize=10,
        leading=12,
        spaceBefore=0,
        spaceAfter=0,
    )
    num_style = ParagraphStyle(
        "AnswerKeyNum",
        parent=cell_style,
        fontName=_BOLD_FONT,
        alignment=1,
    )
    header = [
        Paragraph("<b>#</b>", num_style),
        Paragraph("<b>Cevap</b>", cell_style),
        Paragraph("<b>Kazanım</b>", cell_style),
    ]
    rows: list[list] = [header]
    for q in questions:
        ans = _clean_answer_for_table(q.answer)
        # HTML escape — '<' veya '&' içeriği Paragraph'ı kırmasın
        ans_safe = ans.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        rows.append([
            Paragraph(str(q.number), num_style),
            Paragraph(ans_safe, cell_style),
            Paragraph(q.kazanim_kod, cell_style),
        ])
    # Toplam genişlik = 17 cm (A4 - 2*2cm margin). 1.2 + 11 + 3.8 = 16 cm.
    table = Table(rows, colWidths=[1.2 * cm, 11 * cm, 3.8 * cm], hAlign="LEFT", repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f7")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
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
            from app.services.math_renderer import render_latex_inline
            for s in parsed:
                # LaTeX'i düz metne çevir, sonra &<> escape — ham $...$ ve
                # \frac çözüm adımlarında görünmesin.
                desc = _escape_for_pre(render_latex_inline(s.description))
                line = f"<b>{s.step_no}.</b> {desc}"
                if s.computation:
                    comp = _escape_for_pre(render_latex_inline(s.computation))
                    line += f" <font color='#555'>[{comp}]</font>"
                flow.append(Paragraph(line, styles["qbody"]))
        flow.append(Spacer(1, 0.3 * cm))
    return flow


# ─── Büyüme döngüsü: PDF alt bilgisi (marka + QR) ────────────────────────────
# Öğretmenler ürettikleri PDF'i WhatsApp/Facebook gruplarında paylaşıyor; her
# paylaşılan kağıt bir reklam. Alt bilgiye marka + QR koyarak döngüyü kapatırız:
# QR'ı tarayan yeni kullanıcı siteye gelir. UTM ile GA4'te kaynak ölçülür.
_SITE_LABEL = "soruatolyesi.com"
_QR_TARGET = "https://soruatolyesi.com/?utm_source=pdf&utm_medium=qr&utm_campaign=worksheet_footer"


def _make_qr(data: str, size: float) -> Drawing:
    """URL'i verilen kenar uzunluğunda (point) bir QR Drawing'ine çevirir."""
    widget = QrCodeWidget(data)
    bx0, by0, bx1, by1 = widget.getBounds()
    w = (bx1 - bx0) or 1
    h = (by1 - by0) or 1
    d = Drawing(size, size, transform=[size / w, 0, 0, size / h, 0, 0])
    d.add(widget)
    return d


def _decode_logo(brand_logo: str | None):
    """base64 data-URL logoyu ReportLab ImageReader'a çevirir. Bozuksa None
    (PDF üretimini asla bozmaz)."""
    if not brand_logo or not brand_logo.strip():
        return None
    try:
        from reportlab.lib.utils import ImageReader

        data = brand_logo.strip()
        if data.lower().startswith("data:") and "," in data:
            data = data.split(",", 1)[1]
        raw = base64.b64decode(data)
        return ImageReader(io.BytesIO(raw))
    except Exception:  # noqa: BLE001 — bozuk logo PDF'i bozmasın
        logger.warning("brand_logo çözülemedi — logo atlanıyor")
        return None


def _page_furniture(
    brand_name: str | None = None,
    brand_subtitle: str | None = None,
    brand_logo: str | None = None,
):
    """Her sayfaya çizilen onPage callback'i üretir.

    Üst bilgi (white-label, opsiyonel): kurum/öğretmen logosu (sol) + adı + alt
    satır (sağ). brand_* boşsa header çizilmez → mevcut davranış korunur.
    Alt bilgi (büyüme döngüsü): site etiketi + sayfa no + QR.
    """
    logo_reader = _decode_logo(brand_logo)

    def _draw(canvas, doc) -> None:
        canvas.saveState()
        # --- Üst bilgi: white-label marka ---
        if brand_name or brand_subtitle or logo_reader is not None:
            top_y = A4[1] - 1.15 * cm
            name_x = 2 * cm
            if logo_reader is not None:
                try:
                    iw, ih = logo_reader.getSize()
                    logo_h = 1.0 * cm
                    logo_w = (logo_h * iw / ih) if ih else logo_h
                    logo_w = min(logo_w, 4 * cm)
                    canvas.drawImage(
                        logo_reader,
                        2 * cm,
                        top_y - 0.28 * cm,
                        width=logo_w,
                        height=logo_h,
                        mask="auto",
                        preserveAspectRatio=True,
                    )
                    name_x = 2 * cm + logo_w + 0.35 * cm
                except Exception:  # noqa: BLE001
                    name_x = 2 * cm
            if brand_name:
                canvas.setFont(_BOLD_FONT, 9)
                canvas.setFillColor(colors.HexColor("#1e3a8a"))
                canvas.drawString(name_x, top_y, brand_name[:80])
            if brand_subtitle:
                canvas.setFont(_BODY_FONT, 8)
                canvas.setFillColor(colors.grey)
                canvas.drawRightString(A4[0] - 2 * cm, top_y, brand_subtitle[:60])
            canvas.setStrokeColor(colors.HexColor("#d0d7e2"))
            canvas.setLineWidth(0.5)
            canvas.line(2 * cm, top_y - 0.45 * cm, A4[0] - 2 * cm, top_y - 0.45 * cm)
        # --- Alt bilgi: site + sayfa no + QR ---
        canvas.setFont(_BODY_FONT, 7)
        canvas.setFillColor(colors.grey)
        canvas.drawString(
            2 * cm, 1.0 * cm,
            f"{_SITE_LABEL} ile üretildi — ücretsiz MEB matematik çalışma kağıdı",
        )
        canvas.drawCentredString(A4[0] / 2.0, 1.0 * cm, f"- {doc.page} -")
        qr_size = 1.1 * cm
        try:
            renderPDF.draw(
                _make_qr(_QR_TARGET, qr_size),
                canvas,
                A4[0] - 2 * cm - qr_size,
                0.5 * cm,
            )
        except Exception:  # noqa: BLE001 — QR çizimi PDF üretimini bozmasın
            pass
        canvas.restoreState()

    return _draw


def render_worksheet_pdf(
    worksheet: Worksheet,
    include_answer_key: bool = True,
    include_solutions: bool = True,
    brand_name: str | None = None,
    brand_subtitle: str | None = None,
    brand_logo: str | None = None,
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

    furniture = _page_furniture(brand_name, brand_subtitle, brand_logo)
    doc.build(flow, onFirstPage=furniture, onLaterPages=furniture)
    return buf.getvalue()
