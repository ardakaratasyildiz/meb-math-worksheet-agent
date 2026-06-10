"""İlerleme agregasyonu testleri (Adım 3).

Pytest gerektirmez — `python tests/test_progress.py`. LLM/ağ/DB yok (saf fonksiyon).
CI (eval.yml lint-import) bu dosyayı çalıştırır.
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

from datetime import date  # noqa: E402

from app.services.progress import (  # noqa: E402
    WEAK_MIN_TOTAL,
    WEAK_RATIO_THRESHOLD,
    build_daily_trend,
    build_progress,
)

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")
    if not cond:
        _failures.append(msg)


def _row(kod, correct, total, last="2026-06-10T00:00:00+00:00"):
    return {"kazanim_kod": kod, "correct": correct, "total": total, "last_seen_at": last}


def test_summary() -> None:
    print("özet agregasyon")
    rows = [_row("M.5.1.1", 4, 5), _row("M.5.1.2", 1, 5)]
    p = build_progress(rows, quizzes_solved=3)
    check(p.summary.total_answered == 10, f"toplam cevap 10: {p.summary.total_answered}")
    check(p.summary.total_correct == 5, f"toplam doğru 5: {p.summary.total_correct}")
    check(abs(p.summary.accuracy - 0.5) < 1e-9, f"doğru oranı 0.5: {p.summary.accuracy}")
    check(p.summary.kazanim_count == 2, "kazanım sayısı 2")
    check(p.summary.quizzes_solved == 3, "çözülen quiz 3")


def test_weak_sort_and_filter() -> None:
    print("zayıf kazanım sıralama + eşik")
    rows = [
        _row("STRONG", 5, 5),   # ratio 1.0 — zayıf değil
        _row("WEAK", 1, 5),     # ratio 0.2, total 5 — zayıf
        _row("MID", 3, 5),      # ratio 0.6 — eşik (dahil değil, < katı)
        _row("FEWDATA", 0, 2),  # ratio 0.0 ama total<3 — zayıf sayılmaz (az veri)
    ]
    p = build_progress(rows, quizzes_solved=4)
    # mastery zayıf→güçlü sırada
    order = [m.kazanim_kod for m in p.mastery]
    check(order[0] == "FEWDATA" or order[0] == "WEAK", f"en zayıf üstte: {order}")
    check(order[-1] == "STRONG", f"en güçlü altta: {order}")
    # weak listesi
    weak_kods = {w.kazanim_kod for w in p.weak}
    check("WEAK" in weak_kods, "düşük oran + yeterli veri zayıf")
    check("FEWDATA" not in weak_kods, f"az veri zayıf sayılmaz (min_total={WEAK_MIN_TOTAL})")
    check("MID" not in weak_kods, f"eşik tam değeri ({WEAK_RATIO_THRESHOLD}) zayıf değil")
    check("STRONG" not in weak_kods, "yüksek oran zayıf değil")


def test_empty() -> None:
    print("boş veri")
    p = build_progress([], quizzes_solved=0)
    check(p.summary.accuracy == 0.0 and p.summary.total_answered == 0, "boş özet 0")
    check(p.mastery == [] and p.weak == [] and p.recent == [], "boş listeler")


def test_recent_trend() -> None:
    print("trend (recent attempts)")
    recent = [
        {"completed_at": "2026-06-08T00:00:00+00:00", "score": 2, "total": 10},
        {"completed_at": "2026-06-09T00:00:00+00:00", "score": 7, "total": 10},
    ]
    p = build_progress([_row("M.5.1.1", 9, 20)], quizzes_solved=2, recent_attempts=recent)
    check(len(p.recent) == 2, f"2 deneme: {len(p.recent)}")
    check(abs(p.recent[0].ratio - 0.2) < 1e-9, f"ilk deneme oranı 0.2: {p.recent[0].ratio}")
    check(abs(p.recent[1].ratio - 0.7) < 1e-9, f"son deneme oranı 0.7: {p.recent[1].ratio}")


def test_daily_trend() -> None:
    print("30 günlük gün-bazlı trend")
    today = date(2026, 6, 10)
    attempts = [
        # Aynı gün 2 deneme → toplanmalı (Istanbul: 12:00 UTC = aynı gün)
        {"score": 4, "total": 10, "completed_at": "2026-06-08T12:00:00+00:00"},
        {"score": 6, "total": 10, "completed_at": "2026-06-08T15:00:00+00:00"},
        {"score": 8, "total": 10, "completed_at": "2026-06-09T09:00:00+00:00"},
        # 30 gün penceresi dışında → hariç
        {"score": 1, "total": 10, "completed_at": "2026-04-01T09:00:00+00:00"},
    ]
    pts = build_daily_trend(attempts, today=today, days=30)
    check(len(pts) == 2, f"2 aktif gün (pencere dışı hariç): {len(pts)}")
    check(pts[0].date == "2026-06-08" and pts[1].date == "2026-06-09", "eski→yeni sıra")
    # 08: (4+6)/(10+10) = 10/20 = 0.5, 2 deneme
    check(pts[0].score == 10 and pts[0].total == 20, f"aynı gün toplandı: {pts[0].score}/{pts[0].total}")
    check(abs(pts[0].ratio - 0.5) < 1e-9 and pts[0].attempts == 2, "08 oran 0.5 + 2 deneme")
    check(abs(pts[1].ratio - 0.8) < 1e-9, f"09 oran 0.8: {pts[1].ratio}")
    check(build_daily_trend([], today=today) == [], "boş → boş")


def main() -> int:
    for fn in (
        test_summary,
        test_weak_sort_and_filter,
        test_empty,
        test_recent_trend,
        test_daily_trend,
    ):
        fn()
    print()
    if _failures:
        print(f"FAILED: {len(_failures)} assert düştü")
        return 1
    print("PASSED: ilerleme agregasyon testleri geçti")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
