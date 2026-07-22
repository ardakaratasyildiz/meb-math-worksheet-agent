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


def render_latex_to_svg(
    latex: str,
    *,
    display: bool = False,
    font_size: int = 16,
) -> str | None:
    """LaTeX string → SVG metni (vektör; mobilde react-native-svg ile keskin).

    matplotlib mathtext + savefig(format='svg'). Şeffaf zemin (kart/tema üstünde
    blend olsun). Render başarısızsa None → caller Unicode fallback gösterir.
    Dönen: yalnız `<svg ...>...</svg>` (XML/DOCTYPE başlığı kırpılır).
    """
    try:
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
    except ImportError:
        logger.warning("matplotlib yüklü değil — LaTeX→SVG render atlanıyor.")
        return None

    fs = max(8, min(int(font_size), 40))
    expr = f"${latex}$"
    fig = Figure(figsize=(0.1, 0.1))
    FigureCanvasAgg(fig)  # backend bağlama
    try:
        fig.text(0, 0, expr, fontsize=fs, usetex=False)
        buf = io.BytesIO()
        fig.savefig(
            buf, format="svg", bbox_inches="tight", pad_inches=0.02, transparent=True
        )
        raw = buf.getvalue().decode("utf-8", errors="replace")
        start = raw.find("<svg")
        end = raw.rfind("</svg>")
        if start == -1 or end == -1:
            return None
        return raw[start : end + len("</svg>")]
    except Exception as exc:  # noqa: BLE001 — desteklenmeyen LaTeX → fallback
        logger.warning("LaTeX→SVG başarısız (%s): %s", exc, latex[:80])
        return None


# Tek istekte render edilecek azami LaTeX bloğu (DoS/aşırı yük koruması).
_MAX_MATH_BLOCKS = 40


def render_text_math_segments(text: str, *, font_size: int = 16) -> list[dict]:
    """Soru metnini segmentlere böler; matematik bloklarını SVG'ye render eder.

    Mobil `QuestionText` bunu tek çağrıda alır → düz metni yazar, matematik
    segmentlerini SVG (varsa) yoksa Unicode fallback ile gösterir. Segment:
      {"kind": "text", "text": "..."}
      {"kind": "math", "svg": "<svg>..."|None, "text": "<unicode fallback>", "display": bool}
    """
    out: list[dict] = []
    rendered = 0
    for kind, content, is_display in split_by_latex(text or ""):
        if kind == "text":
            if content:
                out.append({"kind": "text", "text": content})
            continue
        fallback = latex_to_inline_text(content)
        svg = None
        if rendered < _MAX_MATH_BLOCKS:
            svg = render_latex_to_svg(content, display=is_display, font_size=font_size)
            rendered += 1
        out.append(
            {"kind": "math", "svg": svg, "text": fallback, "display": is_display}
        )
    return out


# ─── Inline LaTeX → düz/Unicode metin ────────────────────────────────────────
# PDF'te satır içi $...$ ifadeleri görüntü olarak basılınca cümleyi parçalıyordu.
# Inline math artık akan metne çevrilir; display $$...$$ görüntü olarak kalır.

_LATEX_SYMBOLS = {
    r"\times": "×", r"\div": "÷", r"\cdot": "·", r"\pm": "±", r"\mp": "∓",
    r"\leq": "≤", r"\geq": "≥", r"\neq": "≠", r"\le": "≤", r"\ge": "≥",
    r"\ne": "≠", r"\approx": "≈", r"\equiv": "≡",
    r"\Rightarrow": "⇒", r"\Leftarrow": "⇐", r"\Leftrightarrow": "⇔",
    r"\rightarrow": "→", r"\leftarrow": "←", r"\to": "→",
    r"\circ": "°", r"\degree": "°", r"\infty": "∞",
    r"\ldots": "…", r"\dots": "…", r"\cdots": "…",
    r"\pi": "π", r"\alpha": "α", r"\beta": "β", r"\gamma": "γ",
    r"\theta": "θ", r"\lambda": "λ", r"\mu": "µ", r"\Delta": "Δ",
}
_SUPERSCRIPT = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵",
    "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹", "+": "⁺", "-": "⁻", "n": "ⁿ",
}
_FRAC_RE = re.compile(r"(?:(\d+)\s*)?\\[dt]?frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}")
_SQRT_RE = re.compile(r"\\sqrt\s*\{([^{}]*)\}")
_SUP_BRACE_RE = re.compile(r"\^\{([^{}]*)\}")
_SUP_CHAR_RE = re.compile(r"\^(\w)")
_SUB_BRACE_RE = re.compile(r"_\{([^{}]*)\}")
_TEXTCMD_RE = re.compile(r"\\(?:text|mathrm|mathbf|mathit|operatorname)\s*\{([^{}]*)\}")


def _to_superscript(body: str) -> str:
    body = body.strip()
    if body and all(c in _SUPERSCRIPT for c in body):
        return "".join(_SUPERSCRIPT[c] for c in body)
    return f"^({body})" if len(body) > 1 else f"^{body}"


def latex_to_inline_text(latex: str) -> str:
    """Tek bir LaTeX ifadesini okunabilir düz/Unicode metne çevirir.

    `\\frac{3}{4}` → `3/4`, `5\\frac{1}{2}` → `5 1/2`, `\\times` → `×`,
    `5^2` → `5²`. Karmaşık yapılar için yaklaşıktır — satır içi ifadeler
    cümleyi bölmesin diye yeterli.
    """
    if not latex:
        return latex
    s = latex.strip()
    # \frac{a}{b} → a/b ; önünde tam sayı varsa tam sayılı kesir (5\frac12 → 5 1/2)
    for _ in range(6):
        new = _FRAC_RE.sub(
            lambda m: (f"{m.group(1)} " if m.group(1) else "")
            + f"{m.group(2).strip()}/{m.group(3).strip()}",
            s,
        )
        if new == s:
            break
        s = new
    s = _SQRT_RE.sub(lambda m: f"√({m.group(1).strip()})", s)
    s = _SUP_BRACE_RE.sub(lambda m: _to_superscript(m.group(1)), s)
    s = _SUP_CHAR_RE.sub(lambda m: _to_superscript(m.group(1)), s)
    s = _SUB_BRACE_RE.sub(lambda m: f"_{m.group(1).strip()}", s)
    s = _TEXTCMD_RE.sub(r"\1", s)
    for cmd, sym in _LATEX_SYMBOLS.items():
        s = s.replace(cmd, sym)
    s = s.replace(r"\left", "").replace(r"\right", "")
    s = re.sub(r"\\[a-zA-Z]+", "", s)  # kalan komutları at
    s = s.replace("\\", "").replace("{", "").replace("}", "")
    s = re.sub(r"[ \t]+", " ", s).strip()
    return s


def render_latex_inline(text: str) -> str:
    """Metindeki tüm $...$ / $$...$$ bloklarını okunabilir düz metne çevirir.

    Çevredeki düz metin korunur. PDF'te cevap anahtarı ve çözüm adımları için.
    """
    if not text or "$" not in text:
        return text
    out: list[str] = []
    for kind, content, _is_display in split_by_latex(text):
        out.append(latex_to_inline_text(content) if kind == "latex" else content)
    return "".join(out)
