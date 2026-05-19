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
