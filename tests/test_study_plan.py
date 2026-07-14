"""Haftalık çalışma programı testleri (WS-6a — 7 gün, çeşitli).

Pytest gerektirmez — `python tests/test_study_plan.py`. LLM'i kapatıp (deterministik)
programın YAPISINI test eder: 7 gün, gün adları, odak/tekrar/karışık dağılımı, karışık
günlerin kazanıma bağlı olmaması. CI (eval.yml) bu dosyayı çalıştırır.
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

from app.config import settings  # noqa: E402
from app.models.schemas import (  # noqa: E402
    KazanimProgress,
    ProgressResponse,
    ProgressSummary,
)
from app.services import study_plan as sp  # noqa: E402

# LLM'i KAPAT → deterministik, hızlı, ağsız (fail-open zaten var; burada hiç denemesin).
settings.gemini_api_key = ""

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")
    if not cond:
        _failures.append(msg)


def _kp(kod, correct, total, subject, topic, grade):
    return KazanimProgress(
        kazanim_kod=kod,
        correct=correct,
        total=total,
        ratio=correct / total,
        last_seen_at="",
        subject=subject,
        topic_name=topic,
        grade=grade,
    )


def _progress(mastery):
    mastery = sorted(mastery, key=lambda x: (x.ratio, -x.total))
    weak = [x for x in mastery if x.total >= 3 and x.ratio < 0.6]
    answered = sum(m.total for m in mastery)
    correct = sum(m.correct for m in mastery)
    return ProgressResponse(
        summary=ProgressSummary(
            total_answered=answered,
            total_correct=correct,
            accuracy=(correct / answered) if answered else 0.0,
            kazanim_count=len(mastery),
            quizzes_solved=3,
        ),
        mastery=mastery,
        weak=weak,
        recent=[],
    )


def test_seven_day_varied():
    prog = _progress(
        [
            _kp("M.5.2.1", 1, 5, "matematik", "Cebir", 5),  # weak
            _kp("F.6.1.1", 2, 6, "fen", "Hücre", 6),  # weak
            _kp("T.7.4.2", 7, 8, "turkce", "Yazım", 7),  # strong
            _kp("SB.8.2.1", 9, 10, "sosyal", "İnkılap", 8),  # strong
            _kp("M.6.1.1", 5, 6, "matematik", "Kesirler", 6),  # decent
        ]
    )
    plan = sp.build_study_plan(prog)
    check(len(plan.days) == 7, f"7 gün: {len(plan.days)}")
    check([d.day_no for d in plan.days] == list(range(1, 8)), "day_no 1..7")
    check(all(d.weekday for d in plan.days), "her günün adı var")
    kinds = {d.kind for d in plan.days}
    check(kinds <= {"focus", "review", "mixed"}, f"geçerli türler: {kinds}")
    check(any(d.kind == "focus" for d in plan.days), "en az bir odak günü")
    check(any(d.kind == "review" for d in plan.days), "en az bir tekrar günü")
    check(any(d.kind == "mixed" for d in plan.days), "en az bir karışık gün")
    mixed = [d for d in plan.days if d.kind == "mixed"]
    check(all(d.kazanim_kod == "" for d in mixed), "karışık günler kazanıma bağlı değil")
    check(all(d.question_count > 0 for d in plan.days), "her günde soru sayısı > 0")
    # odak günleri gerçekten zayıf kazanımlardan gelmeli
    focus = [d for d in plan.days if d.kind == "focus"]
    check(
        all(d.kazanim_kod in {"M.5.2.1", "F.6.1.1"} for d in focus),
        "odak günleri zayıf kazanımlardan",
    )
    check(not plan.ai_generated, "LLM kapalı → ai_generated False")


def test_no_data_encourages():
    prog = _progress([])
    plan = sp.build_study_plan(prog)
    check(plan.days == [], "veri yok → gün yok")
    check("İlk quizini" in plan.summary or "quiz" in plan.summary.lower(), "teşvik mesajı")


def test_all_strong_still_full_week():
    # Zayıf konu YOK → yine de 7 günlük tekrar+karışık program çıkmalı.
    prog = _progress(
        [
            _kp("M.5.1.1", 9, 10, "matematik", "Doğal Sayılar", 5),
            _kp("T.6.3.5", 8, 9, "turkce", "Sözcükte Anlam", 6),
        ]
    )
    plan = sp.build_study_plan(prog)
    check(len(plan.days) == 7, f"zayıf yokken de 7 gün: {len(plan.days)}")
    check(all(d.kind in {"review", "mixed"} for d in plan.days), "yalnız tekrar+karışık")


def main() -> int:
    for fn in (test_seven_day_varied, test_no_data_encourages, test_all_strong_still_full_week):
        fn()
    print()
    if _failures:
        print(f"FAILED: {len(_failures)} assert düştü")
        return 1
    print("PASSED: haftalık çalışma programı testleri geçti")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
