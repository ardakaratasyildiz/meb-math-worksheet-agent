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
    # Harici kaynak yükleme (SSRF): href / xlink:href'in http(s):// veya
    # protokol-göreli (//) bir hedefe işaret etmesi. svglib render sırasında
    # <image>/<use> hrefs'ini fetch eder → 169.254.169.254 gibi iç uçlara SSRF
    # (validator'daki no_network yalnız parse aşamasını korur, render'ı değil).
    # İç fragment (#id) ve data: URI güvenli → eşleşmez, engellenmez.
    re.compile(r"(?:xlink:)?href\s*=\s*['\"]?\s*(?:https?:)?//", re.IGNORECASE),
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


# ─── Deterministik ÖRÜNTÜ üretimi (LLM ham SVG çizmesin) ─────────────────────
# grafik gibi: LLM yalnız direktif verir, sistem güvenilir SVG üretir. oruntu_sekil
# ham <svg> ile güvenilmezdi (A/B: 2.5 & 3.5 ikisi de düşük-yield). İki biçim:
#   Dizi:    {{pattern:daire#kirmizi, kare#mavi, ucgen#yesil, daire#kirmizi, ?}}
#   Büyüyen: {{pattern:grow|1,3,5,?}}   (her hücrede o kadar nokta; ? = eksik)
# 'seq|' öneki opsiyonel (çıplak hücre dizisi = seq). ? = eksik slot.

_PATTERN_DIRECTIVE_RE = re.compile(r"\{\{pattern:([^{}]+)\}\}", flags=re.IGNORECASE)

_COLOR_NAMES = {
    "kirmizi": "#ef4444", "kırmızı": "#ef4444", "red": "#ef4444",
    "mavi": "#3b82f6", "blue": "#3b82f6",
    "yesil": "#10b981", "yeşil": "#10b981", "green": "#10b981",
    "sari": "#f59e0b", "sarı": "#f59e0b", "yellow": "#f59e0b",
    "mor": "#8b5cf6", "purple": "#8b5cf6",
    "turuncu": "#f97316", "orange": "#f97316",
    "pembe": "#ec4899", "pink": "#ec4899",
    "siyah": "#334155", "black": "#334155",
}
_SHAPE_ALIASES = {
    "daire": "circle", "circle": "circle",
    "kare": "square", "square": "square",
    "ucgen": "triangle", "üçgen": "triangle", "triangle": "triangle",
    "yildiz": "star", "yıldız": "star", "star": "star",
    "elmas": "diamond", "diamond": "diamond",
}


def _resolve_color(raw: str, idx: int) -> str:
    """Renk adı/hex → hex. Boş/bilinmeyen → palet döngüsü."""
    raw = (raw or "").strip().lower()
    if raw.startswith("#") and 4 <= len(raw) <= 7:
        return raw
    if raw in _COLOR_NAMES:
        return _COLOR_NAMES[raw]
    return _CHART_COLORS[idx % len(_CHART_COLORS)]


def _star_points(cx: float, cy: float, r: float) -> str:
    pts = []
    for k in range(10):
        ang = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append(f"{cx + rr * math.cos(ang):.1f},{cy + rr * math.sin(ang):.1f}")
    return " ".join(pts)


def _shape_svg(shape: str, cx: float, cy: float, s: float, color: str) -> str:
    if shape == "circle":
        return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{s:.1f}" fill="{color}"/>'
    if shape == "square":
        return f'<rect x="{cx - s:.1f}" y="{cy - s:.1f}" width="{2 * s:.1f}" height="{2 * s:.1f}" fill="{color}"/>'
    if shape == "triangle":
        return f'<polygon points="{cx:.1f},{cy - s:.1f} {cx - s:.1f},{cy + s:.1f} {cx + s:.1f},{cy + s:.1f}" fill="{color}"/>'
    if shape == "diamond":
        return f'<polygon points="{cx:.1f},{cy - s:.1f} {cx + s:.1f},{cy:.1f} {cx:.1f},{cy + s:.1f} {cx - s:.1f},{cy:.1f}" fill="{color}"/>'
    if shape == "star":
        return f'<polygon points="{_star_points(cx, cy, s)}" fill="{color}"/>'
    # bilinmeyen → daire fallback
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{s:.1f}" fill="{color}"/>'


def _q_cell(cx: float) -> str:
    return f'<text x="{cx:.1f}" y="40" font-size="34" text-anchor="middle" dominant-baseline="middle">?</text>'


def _parse_pattern_cells(spec: str) -> list[tuple[str, str] | None]:
    """'daire#kirmizi, kare#mavi, ?' → [('circle','#ef4444'), ('square','#3b82f6'), None]."""
    cells: list[tuple[str, str] | None] = []
    for i, part in enumerate(spec.split(",")):
        tok = part.strip()
        if not tok:
            continue
        if tok == "?":
            cells.append(None)
            continue
        name, _, color = tok.partition("#")
        shape = _SHAPE_ALIASES.get(name.strip().lower())
        if shape is None:
            continue  # bilinmeyen şekil → atla
        cells.append((shape, _resolve_color(color, i)))
    return cells[:10]


def _parse_counts(spec: str) -> list[int | None]:
    """'1,3,5,?' → [1,3,5,None]. Bozuk öğe atlanır; 0..12 arası."""
    out: list[int | None] = []
    for part in spec.split(","):
        tok = part.strip()
        if tok == "?":
            out.append(None)
            continue
        try:
            n = int(tok)
        except ValueError:
            continue
        if 0 <= n <= 12:
            out.append(n)
    return out[:8]


def render_pattern_svg(cells: list[tuple[str, str] | None]) -> str:
    """Yatay şekil dizisi + ? slotu. Güvenilir, çakışmasız."""
    cell_w, pad, h, cy, s = 54, 10, 60, 30, 18
    width = len(cells) * cell_w + 2 * pad
    parts = []
    for i, c in enumerate(cells):
        cx = pad + i * cell_w + cell_w / 2
        parts.append(_q_cell(cx) if c is None else _shape_svg(c[0], cx, cy, s, c[1]))
    return (
        f'<svg viewBox="0 0 {width} {h}" xmlns="http://www.w3.org/2000/svg">'
        + "".join(parts) + "</svg>"
    )


def render_growing_svg(counts: list[int | None]) -> str:
    """Her hücrede `n` nokta (büyüyen örüntü); ? = eksik hücre. Noktalar ≤3/satır."""
    cell_w, pad, h = 60, 10, 74
    width = len(counts) * cell_w + 2 * pad
    color = _CHART_COLORS[0]
    parts = []
    for i, n in enumerate(counts):
        cx0 = pad + i * cell_w
        cxc = cx0 + cell_w / 2
        if n is None:
            parts.append(_q_cell(cxc))
            continue
        for j in range(n):
            col, row = j % 3, j // 3
            dx = cxc + (col - 1) * 14
            dy = 22 + row * 14
            parts.append(f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="5" fill="{color}"/>')
        # hücre altına sayıyı yazma (örüntü görsel kalsın); ayraç çizgisi opsiyonel
    return (
        f'<svg viewBox="0 0 {width} {h}" xmlns="http://www.w3.org/2000/svg">'
        + "".join(parts) + "</svg>"
    )


def process_pattern_directives(text: str) -> str:
    """{{pattern:...}} direktiflerini deterministik SVG ile değiştirir. Bozuk → no-op."""
    def _repl(m: "re.Match[str]") -> str:
        spec = m.group(1).strip()
        low = spec.lower()
        if low.startswith("grow|"):
            counts = _parse_counts(spec[5:])
            return render_growing_svg(counts) if counts else m.group(0)
        if low.startswith("seq|"):
            spec = spec[4:]
        cells = _parse_pattern_cells(spec)
        if not cells or all(c is None for c in cells):
            return m.group(0)
        return render_pattern_svg(cells)

    return _PATTERN_DIRECTIVE_RE.sub(_repl, text)


# ─── Deterministik TABLO üretimi (LLM ham markdown yazmasın) ─────────────────
# tablo_sorusu markdown tabloyu ELLE yazdırıyordu → 2.5-flash bozuk üretiyor
# (hizasız pipe, eksik ayraç satırı, düzensiz sütun); 3.5 temiz yapabiliyordu.
# grafik/örüntü deseni: LLM yalnız veri direktifi verir, sistem KUSURSUZ GFM markdown
# üretir → mevcut PDF/_parse_table + frontend render yolu aynen çalışır (model-bağımsız).
# Format:  {{table: Baş1 | Baş2 ;; s1h1 | s1h2 ;; s2h1 | s2h2}}
#   ;; = satır ayracı · | = hücre ayracı · İLK satır = başlık.

_TABLE_DIRECTIVE_RE = re.compile(r"\{\{table:([^{}]+)\}\}", flags=re.IGNORECASE)


def _md_cell(s: str) -> str:
    """Hücreyi GFM-güvenli yap: pipe kaçışla, newline'ı boşluğa çevir."""
    return s.strip().replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def render_markdown_table(rows: list[list[str]]) -> str:
    """Satır listesinden hizalı, ayraç-satırlı GFM markdown tablosu. İlk satır başlık.

    Tüm satırlar başlığın sütun sayısına EŞİTLENİR (eksik→boş, fazla→kırp) → asla
    bozuk/düzensiz tablo çıkmaz.
    """
    ncol = len(rows[0])
    norm: list[list[str]] = []
    for r in rows:
        cells = [_md_cell(c) for c in r]
        if len(cells) < ncol:
            cells += [""] * (ncol - len(cells))
        norm.append(cells[:ncol])
    header, body = norm[0], norm[1:]
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * ncol) + "|"]
    lines += ["| " + " | ".join(r) + " |" for r in body]
    return "\n".join(lines)


def process_table_directives(text: str) -> str:
    """{{table:...}} direktiflerini temiz GFM markdown tablosuna çevirir. Bozuk → no-op.

    Tablo blok-seviye parse edilsin diye önü/arkası boş satırla sarılır.
    """
    def _repl(m: "re.Match[str]") -> str:
        spec = m.group(1).strip()
        rows = [
            [c for c in row.split("|")]
            for row in spec.split(";;")
            if row.strip()
        ]
        rows = [r for r in rows if any(c.strip() for c in r)]
        # En az başlık + 1 veri satırı ve ≥2 sütun.
        if len(rows) < 2 or len(rows[0]) < 2:
            return m.group(0)
        return "\n\n" + render_markdown_table(rows) + "\n\n"

    return _TABLE_DIRECTIVE_RE.sub(_repl, text)


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
