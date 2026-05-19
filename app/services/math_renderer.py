"""LaTeX matematik ifadelerini PNG'ye render eder (matplotlib mathtext).

salt_islem tipinde LLM `$\\frac{3}{4} + \\frac{1}{6} = ?$` gibi LaTeX
matematik notasyonu üretir. Frontend bunu rehype-katex ile gerçek matematik
sembollerine dönüştürür; PDF tarafı için aynı görsel kalite gerekli — bu
modül matplotlib mathtext kullanarak PNG byte'ları üretir.

mathtext desteği (LaTeX subset):
    - \\frac, \\sqrt, ^, _
    - Yunan harfleri: \\alpha, \\beta, \\pi, ...
    - Toplama/integral: \\sum, \\int
    - Trigonometri: \\sin, \\cos, \\tan
    - Eşitsizlik: \\leq, \\geq, \\neq
    - Sembol: \\cdot, \\times, \\div, \\pm

System LaTeX kurulumu GEREKMİYOR — matplotlib kendi mathtext parser'ını
kullanır (usetex=False default).
"""
from __future__ import annotations

import io
import logging
import re

logger = logging.getLogger(__name__)


# $...$ (inline) ve $$...$$ (display) blokları yakalar.
# Display'in inline'dan ÖNCE eşleşmesi gerekiyor (greedy değil, eşleştirme
# sırası önemli) — bu yüzden ayrı regex'ler kullanılıyor.
_DISPLAY_RE = re.compile(r"\$\$([^$]+?)\$\$", re.DOTALL)
_INLINE_RE = re.compile(r"(?<!\$)\$([^\$\n]+?)\$(?!\$)")


def extract_latex_blocks(text: str) -> list[tuple[int, int, str, bool]]:
    """LaTeX bloklarını çıkarır: (start, end, content, is_display).

    Display blokları ($$...$$) önce yakalanır; geri kalan metin içinde
    inline ($...$) blokları aranır. Çakışma olmaması için işaretli aralıklar
    skip edilir.
    """
    blocks: list[tuple[int, int, str, bool]] = []
    masked = list(text)

    for m in _DISPLAY_RE.finditer(text):
        blocks.append((m.start(), m.end(), m.group(1).strip(), True))
        for i in range(m.start(), m.end()):
            masked[i] = "\x00"

    masked_text = "".join(masked)
    for m in _INLINE_RE.finditer(masked_text):
        blocks.append((m.start(), m.end(), m.group(1).strip(), False))

    blocks.sort(key=lambda b: b[0])
    return blocks


def split_by_latex(text: str) -> list[tuple[str, str, bool]]:
    """Yield (kind, content, is_display) — kind 'text' veya 'latex'.

    PDF renderer aynı pattern'i izleyerek text segmentleri Paragraph,
    latex bloklarını matplotlib PNG'sine çevirir.
    """
    if not text:
        return []
    blocks = extract_latex_blocks(text)
    if not blocks:
        return [("text", text, False)]
    out: list[tuple[str, str, bool]] = []
    last = 0
    for start, end, content, is_display in blocks:
        if start > last:
            out.append(("text", text[last:start], False))
        out.append(("latex", content, is_display))
        last = end
    if last < len(text):
        out.append(("text", text[last:], False))
    return out


def render_latex_to_png(
    latex: str,
    *,
    display: bool = False,
    font_size: int = 14,
    dpi: int = 220,
) -> bytes | None:
    """LaTeX string → PNG byte. Render başarısızsa None.

    matplotlib mathtext bazı kompleks LaTeX ifadelerini desteklemez
    (örn. \\begin{cases}); başarısızlık durumunda None döner, caller
    fallback metin gösterir.
    """
    try:
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
    except ImportError:
        logger.warning("matplotlib yüklü değil — LaTeX render atlanıyor.")
        return None

    expr = f"${latex}$"  # $...$ ile sarmaladık (mathtext bekler)
    # Geçici figure — boyut text uzunluğuna göre tahmini, savefig bbox_inches
    # tight ile kırpıyor.
    fig = Figure(figsize=(0.1, 0.1))
    canvas = FigureCanvasAgg(fig)  # noqa: F841 — bağlama gerekli
    try:
        fig.text(
            0, 0, expr,
            fontsize=font_size,
            usetex=False,  # mathtext (system LaTeX gerektirmez)
        )
        buf = io.BytesIO()
        fig.savefig(
            buf,
            format="png",
            dpi=dpi,
            bbox_inches="tight",
            pad_inches=0.05,
            transparent=False,
        )
        return buf.getvalue()
    except Exception as exc:  # noqa: BLE001
        logger.warning("LaTeX render başarısız (%s): %s", exc, latex[:80])
        return None
