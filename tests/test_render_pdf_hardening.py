"""render.pdf sertleştirme testleri (güvenlik: SSRF + girdi-DoS).

1) SVG SSRF: <image>/<use> içindeki harici href/xlink:href (http(s):// veya //)
   tehlikeli sayılır; iç fragment (#id) ve data: URI güvenlidir.
2) Girdi sınırları: Worksheet.questions ≤ 60; Question.question/answer max_length.

Pytest gerektirmez — `python tests/test_render_pdf_hardening.py` da çalışır
(CI eval test dosyalarını doğrudan koşar).
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

from pydantic import ValidationError  # noqa: E402

from app.models.schemas import Question, Worksheet  # noqa: E402
from app.services.svg_utils import is_dangerous  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")
    if not cond:
        _failures.append(msg)


def _mkq(n: int, question: str = "2+2?", answer: str = "4") -> dict:
    return {
        "number": n, "question": question, "answer": answer,
        "solution_steps": "", "kazanim_kod": "M.5.1.1",
        "question_type": "salt_islem",
    }


def test_svg_ssrf_external_href_blocked() -> None:
    print("SVG SSRF — harici href engellenir, iç/veri URI güvenli")
    blocked = [
        '<svg><image xlink:href="http://169.254.169.254/latest/meta-data/"/></svg>',
        '<svg><image href="https://evil.example.com/x.png"/></svg>',
        '<svg><image href="//evil.example.com/x.png"/></svg>',
        '<svg><use xlink:href="http://evil.example.com/x"/></svg>',
    ]
    safe = [
        '<svg><use href="#localmarker"/></svg>',
        '<svg><image href="data:image/png;base64,AAAA"/></svg>',
        '<svg><rect x="1" y="2" width="3" height="4"/></svg>',
    ]
    for s in blocked:
        check(is_dangerous(s) is True, f"engellendi: {s[:48]}")
    for s in safe:
        check(is_dangerous(s) is False, f"izin verildi: {s[:48]}")


def test_worksheet_question_count_capped() -> None:
    print("Worksheet.questions ≤ 60 (DoS sınırı)")
    base = dict(title="T", grade=5, topic="x", difficulty="orta",
                question_count=1, answer_key=[])
    try:
        Worksheet(**base, questions=[_mkq(i) for i in range(61)])
        check(False, "61 soru reddedilmeli")
    except ValidationError:
        check(True, "61 soru reddedildi")
    try:
        w = Worksheet(**base, questions=[_mkq(i) for i in range(60)])
        check(len(w.questions) == 60, "60 soru kabul (sınır içi)")
    except ValidationError:
        check(False, "60 soru kabul edilmeliydi")


def test_question_field_length_capped() -> None:
    print("Question.question/answer max_length (tek-devasa-alan DoS)")
    try:
        Question(**_mkq(1, question="x" * 50_001))
        check(False, "50001-char question reddedilmeli")
    except ValidationError:
        check(True, "aşırı uzun question reddedildi")
    # Makul boyut (inline SVG payı) kabul edilmeli
    try:
        Question(**_mkq(1, question="<svg>" + "a" * 4000 + "</svg>"))
        check(True, "makul boyutlu question kabul")
    except ValidationError:
        check(False, "makul question reddedilmemeliydi")


def test_render_endpoint_registered_and_limited() -> None:
    print("render.pdf kayıtlı + throttle'lı + gövde tavanı sabiti var")
    from app.main import app  # noqa: PLC0415
    from app.routers import worksheets  # noqa: PLC0415

    paths = {r.path for r in app.routes}
    check("/api/worksheets/render.pdf" in paths, "render.pdf endpoint kayıtlı")
    check(
        getattr(worksheets, "_MAX_RENDER_BODY_BYTES", 0) == 8 * 1024 * 1024,
        "gövde tavanı sabiti 8MB",
    )


def test_render_endpoint_oversized_returns_422_not_500() -> None:
    """61 soruluk gövde → temiz 422 (500 DEĞİL). Modeller elle kurulduğu için
    ValidationError'ı endpoint yakalayıp 422'ye çevirmeli."""
    print("render.pdf aşırı girdi → 422 (500 değil)")
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from app.main import app  # noqa: PLC0415

    c = TestClient(app)

    def q(n: int) -> dict:
        return {"number": n, "question": "2+2?", "answer": "4",
                "solution_steps": "adım", "kazanim_kod": "M.5.1.1",
                "question_type": "salt_islem"}

    def ws(count: int) -> dict:
        return {"worksheet": {"title": "T", "grade": 5, "topic": "x",
                "difficulty": "orta", "question_count": count,
                "questions": [q(i) for i in range(count)],
                "answer_key": [{"number": i, "answer": "4"} for i in range(count)]}}

    r_big = c.post("/api/worksheets/render.pdf", json=ws(61))
    check(r_big.status_code == 422, f"61 soru → 422 (got {r_big.status_code})")
    r_ok = c.post("/api/worksheets/render.pdf", json=ws(2))
    check(r_ok.status_code == 200, f"2 soru → 200 PDF (got {r_ok.status_code})")


def _run() -> int:
    test_svg_ssrf_external_href_blocked()
    test_worksheet_question_count_capped()
    test_question_field_length_capped()
    test_render_endpoint_registered_and_limited()
    test_render_endpoint_oversized_returns_422_not_500()
    print()
    if _failures:
        print(f"❌ {len(_failures)} test BAŞARISIZ")
        for f in _failures:
            print(f"   - {f}")
        return 1
    print("✅ Tüm render.pdf sertleştirme testleri geçti.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_run())
