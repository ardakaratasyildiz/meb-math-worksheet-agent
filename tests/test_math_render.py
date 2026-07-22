"""Matematik render (LaTeX→SVG + metin segmentleri) testleri.

Pytest gerektirmez — `python tests/test_math_render.py`.
matplotlib kuruluysa SVG içeriği doğrulanır; değilse graceful None + fallback
metni beklenir (test yine geçer — endpoint fallback sözleşmesi).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("GEMINI_API_KEY", "fake-key-for-tests")

from app.services import math_renderer  # noqa: E402

try:
    import matplotlib  # noqa: F401
    _HAS_MPL = True
except ImportError:
    _HAS_MPL = False

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")
    if not cond:
        _failures.append(msg)


def test_render_svg() -> None:
    print("test_render_svg")
    svg = math_renderer.render_latex_to_svg(r"\frac{3}{4}")
    if _HAS_MPL:
        check(svg is not None and svg.strip().startswith("<svg"), "kesir → <svg> ile başlar")
        check(svg is not None and svg.rstrip().endswith("</svg>"), "SVG </svg> ile biter (başlık kırpıldı)")
    else:
        check(svg is None, "matplotlib yok → None (graceful)")


def test_render_svg_failure_graceful() -> None:
    print("test_render_svg_failure_graceful")
    # Desteklenmeyen yapı → None (patlamaz)
    svg = math_renderer.render_latex_to_svg(r"\begin{cases} x \\ y \end{cases}")
    check(svg is None or "<svg" in svg, "desteklenmeyen LaTeX → None veya svg (patlamaz)")


def test_segments_mixed() -> None:
    print("test_segments_mixed")
    text = r"Kesir $\frac{1}{2}$ ve blok $$x^2$$ bitti"
    segs = math_renderer.render_text_math_segments(text)
    kinds = [s["kind"] for s in segs]
    check(kinds.count("math") == 2, "2 matematik segmenti")
    check(kinds.count("text") >= 2, "aradaki düz metinler korunur")
    math_segs = [s for s in segs if s["kind"] == "math"]
    check(all(s["text"] for s in math_segs), "her matematik segmentinde Unicode fallback var")
    check(any(s["display"] for s in math_segs), "$$...$$ display=True işaretli")
    check(not all(s["display"] for s in math_segs), "$...$ display=False")
    if _HAS_MPL:
        check(all(s["svg"] and "<svg" in s["svg"] for s in math_segs), "matplotlib → her matematik SVG'li")


def test_segments_plain_text() -> None:
    print("test_segments_plain_text")
    segs = math_renderer.render_text_math_segments("Matematik yok, düz cümle.")
    check(len(segs) == 1 and segs[0]["kind"] == "text", "matematiksiz → tek text segmenti")


def test_endpoint_smoke() -> None:
    print("test_endpoint_smoke")
    from fastapi.testclient import TestClient
    import app.main as m

    c = TestClient(m.app)
    r = c.post("/api/render/math", json={"text": r"Şu: $\frac{1}{2}$"})
    check(r.status_code == 200, "POST /api/render/math → 200")
    body = r.json()
    check("segments" in body and len(body["segments"]) >= 2, "segments döner (text + math)")
    # font_size sınırı (Field ge/le) — geçersiz → 422
    r2 = c.post("/api/render/math", json={"text": "x", "font_size": 999})
    check(r2.status_code == 422, "font_size>40 → 422 (sınır)")


def _run() -> int:
    for fn in [
        test_render_svg, test_render_svg_failure_graceful, test_segments_mixed,
        test_segments_plain_text, test_endpoint_smoke,
    ]:
        fn()
    print()
    if _failures:
        print(f"❌ {len(_failures)} test BAŞARISIZ:")
        for f in _failures:
            print(f"   - {f}")
        return 1
    print("✅ Tüm math render testleri geçti.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_run())
