"""LLM çıktısı içindeki SVG bloklarını ayrıştırma + sanitization + parse.

Hem PDF renderer (svglib ile reportlab Drawing'e çevirmek için) hem de
sentetik üretim validator'ı bu modülü kullanır. Frontend tarafında
SafeSvg.tsx ayrı bir DOMPurify sanitization yapar — Python tarafı sadece
parse-validity kontrolü yapıyor (XSS frontend katmanında elenmeli).
"""
from __future__ import annotations

import re
from typing import Iterator

_SVG_BLOCK_RE = re.compile(
    r"<svg\b[^>]*>[\s\S]*?</svg>",
    flags=re.IGNORECASE,
)

# Tehlikeli SVG patternleri — sentetik üretim sırasında reject et.
# Frontend DOMPurify zaten bunları kesiyor ama burada da erken eleme.
_DANGEROUS_PATTERNS = [
    re.compile(r"<script\b", re.IGNORECASE),
    re.compile(r"\bon[a-z]+\s*=", re.IGNORECASE),  # onclick, onerror, ...
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"<foreignObject\b", re.IGNORECASE),
    re.compile(r"<use\b[^>]*href\s*=\s*['\"]?https?://", re.IGNORECASE),  # external use
]


def extract_svg_blocks(text: str) -> list[tuple[int, int, str]]:
    """Metin içindeki tüm <svg>...</svg> bloklarını döndürür.

    Returns:
        list of (start_idx, end_idx, svg_content) — text'i parçalamak için.
    """
    out: list[tuple[int, int, str]] = []
    for m in _SVG_BLOCK_RE.finditer(text):
        out.append((m.start(), m.end(), m.group(0)))
    return out


def split_text_by_svg(text: str) -> Iterator[tuple[str, str]]:
    """('text' | 'svg', content) tuple'larını sırayla yield eder.

    PDF renderer ve frontend QuestionCard aynı pattern'i izler.
    """
    last = 0
    for start, end, svg in extract_svg_blocks(text):
        if start > last:
            yield ("text", text[last:start])
        yield ("svg", svg)
        last = end
    if last < len(text):
        yield ("text", text[last:])


# ─── Deterministik grafik üretimi (LLM SVG çizmesin) ─────────────────────────
# LLM inline SVG pasta/sütun grafiklerini güvenilmez (dilim/etiket bozuk) üretir.
# Çözüm: LLM yalnız VERİ direktifi versin → sistem doğru SVG'yi üretir.
# Direktif formatı:  {{chart:pie|Futbol=40|Basketbol=30}}  /  {{chart:bar|Ocak=10|Şubat=14}}

import math

_CHART_COLORS = [
    "#3b82f6", "#10b981", "#f59e0b", "#ef4444",
    "#8b5cf6", "#14b8a6", "#ec4899", "#64748b",
]

_CHART_DIRECTIVE_RE = re.compile(
    r"\{\{chart:(pie|bar)\|([^{}]+)\}\}", flags=re.IGNORECASE
)


def _xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _parse_chart_items(spec: str) -> list[tuple[str, float]]:
    """'Futbol=40|Basketbol=30' → [('Futbol',40.0), ...]. Bozuk öğe atlanır."""
    items: list[tuple[str, float]] = []
    for part in spec.split("|"):
        if "=" not in part:
            continue
        label, _, val = part.partition("=")
        label = label.strip()
        try:
            num = float(val.strip().replace(",", "."))
        except ValueError:
            continue
        if label and num >= 0:
            items.append((label, num))
    return items[:8]  # aşırı kalabalığı önle


def render_pie_chart_svg(items: list[tuple[str, float]]) -> str:
    """Doğru oranlı, çakışmayan etiketli pasta grafiği SVG'si üretir."""
    total = sum(v for _, v in items) or 1.0
    cx, cy, r = 130.0, 100.0, 70.0
    parts: list[str] = []
    # Tek dilim (tam daire) — yay dejenere olmasın diye <circle>.
    if len(items) == 1:
        label, val = items[0]
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{_CHART_COLORS[0]}"/>')
        parts.append(
            f'<text x="{cx}" y="{cy}" font-size="12" text-anchor="middle" '
            f'dominant-baseline="middle">{_xml_escape(label)} %100</text>'
        )
    else:
        a0 = -math.pi / 2
        for i, (label, val) in enumerate(items):
            frac = val / total
            a1 = a0 + frac * 2 * math.pi
            x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
            x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
            large = 1 if frac > 0.5 else 0
            color = _CHART_COLORS[i % len(_CHART_COLORS)]
            parts.append(
                f'<path d="M {cx:.1f} {cy:.1f} L {x0:.1f} {y0:.1f} '
                f'A {r} {r} 0 {large} 1 {x1:.1f} {y1:.1f} Z" '
                f'fill="{color}" stroke="#ffffff" stroke-width="1"/>'
            )
            am = (a0 + a1) / 2
            lx, ly = cx + (r + 14) * math.cos(am), cy + (r + 14) * math.sin(am)
            anchor = "start" if math.cos(am) >= 0 else "end"
            pct = round(val / total * 100)
            parts.append(
                f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="12" '
                f'text-anchor="{anchor}" dominant-baseline="middle">'
                f'{_xml_escape(label)} %{pct}</text>'
            )
            a0 = a1
    return (
        '<svg viewBox="0 0 320 200" xmlns="http://www.w3.org/2000/svg">'
        + "".join(parts)
        + "</svg>"
    )


def render_bar_chart_svg(items: list[tuple[str, float]]) -> str:
    """Doğru oranlı sütun grafiği SVG'si üretir (etiket altta, değer üstte)."""
    maxv = max((v for _, v in items), default=1.0) or 1.0
    bar_w, gap, left, base_y, top_y = 40, 26, 40, 160, 24
    plot_h = base_y - top_y
    parts: list[str] = []
    x = left
    for i, (label, val) in enumerate(items):
        h = (val / maxv) * plot_h
        y = base_y - h
        color = _CHART_COLORS[i % len(_CHART_COLORS)]
        parts.append(f'<rect x="{x}" y="{y:.1f}" width="{bar_w}" height="{h:.1f}" fill="{color}"/>')
        cxb = x + bar_w / 2
        parts.append(
            f'<text x="{cxb:.1f}" y="{base_y + 14}" font-size="11" '
            f'text-anchor="middle">{_xml_escape(label)}</text>'
        )
        parts.append(
            f'<text x="{cxb:.1f}" y="{y - 4:.1f}" font-size="11" '
            f'text-anchor="middle">{val:g}</text>'
        )
        x += bar_w + gap
    width = left + len(items) * (bar_w + gap) + 10
    axis = (
        f'<line x1="{left - 10}" y1="{base_y}" x2="{x - gap + 10}" y2="{base_y}" '
        f'stroke="#555555" stroke-width="1"/>'
    )
    return (
        f'<svg viewBox="0 0 {width} 185" xmlns="http://www.w3.org/2000/svg">'
        + axis + "".join(parts)
        + "</svg>"
    )


def process_chart_directives(text: str) -> str:
    """Metindeki {{chart:...}} direktiflerini deterministik SVG ile değiştirir.

    Bozuk/boş direktif olduğu gibi bırakılır (veri yine metinde görünür)."""
    def _repl(m: "re.Match[str]") -> str:
        kind = m.group(1).lower()
        items = _parse_chart_items(m.group(2))
        if not items:
            return m.group(0)
        return render_pie_chart_svg(items) if kind == "pie" else render_bar_chart_svg(items)

    return _CHART_DIRECTIVE_RE.sub(_repl, text)


def is_dangerous(svg: str) -> bool:
    """Tehlikeli SVG patterni (script, on* handler, javascript: vs.) var mı?"""
    return any(p.search(svg) for p in _DANGEROUS_PATTERNS)


def is_valid_svg(svg: str) -> tuple[bool, str]:
    """SVG'nin parse edilebilirliğini ve güvenliğini doğrular.

    Returns:
        (is_valid, reason). Geçerliyse reason boş string.
    """
    if not svg or not svg.strip().startswith("<svg"):
        return False, "SVG <svg> ile başlamıyor"
    if "</svg>" not in svg:
        return False, "Kapanış etiketi yok"
    if is_dangerous(svg):
        return False, "Tehlikeli pattern (script/on-handler/external)"
    # lxml ile parse — namespace eksikliği veya bozuk XML reddet
    try:
        from lxml import etree
        # SVG fragment, defusedxml de düşünülebilir ama lxml + DTD off yeterli.
        parser = etree.XMLParser(
            resolve_entities=False, no_network=True, dtd_validation=False,
            load_dtd=False, huge_tree=False,
        )
        etree.fromstring(svg.encode("utf-8"), parser=parser)
    except ImportError:
        # lxml yoksa fallback: yalnızca string-bazlı kontrol (zaten yukarıda yapıldı).
        return True, ""
    except Exception as exc:  # noqa: BLE001
        return False, f"XML parse hatası: {exc}"
    return True, ""
