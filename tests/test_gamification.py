"""Oyunlaştırma testleri (XP/seviye/seri — PR5).

Pytest gerektirmez — `python tests/test_gamification.py`. LLM/ağ/DB yok.
CI (eval.yml lint-import) bu dosyayı çalıştırır.
"""
from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("GEMINI_API_KEY", "fake-key-for-tests")

from app.services.gamification import (  # noqa: E402
    build_gamification,
    compute_level,
    compute_streak,
    level_threshold,
)

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")
    if not cond:
        _failures.append(msg)


def test_level() -> None:
    print("seviye eşikleri")
    check(level_threshold(1) == 0 and level_threshold(2) == 100, "L1=0, L2=100")
    check(level_threshold(3) == 300 and level_threshold(4) == 600, "L3=300, L4=600")
    check(compute_level(0) == 1, "0 xp → L1")
    check(compute_level(99) == 1, "99 → L1")
    check(compute_level(100) == 2, "100 → L2")
    check(compute_level(299) == 2, "299 → L2")
    check(compute_level(300) == 3, "300 → L3")


def test_xp_and_bar() -> None:
    print("xp + seviye barı")
    # 12 doğru, 2 quiz → 12*10 + 2*5 = 130 → L2 (100..300)
    g = build_gamification(total_correct=12, quizzes_solved=2, active_dates=[], today=date(2026, 6, 10))
    check(g.xp == 130, f"xp 130: {g.xp}")
    check(g.level == 2, f"seviye 2: {g.level}")
    check(g.xp_in_level == 30, f"seviyede 30 (130-100): {g.xp_in_level}")
    check(g.xp_for_next == 200, f"sonraki için 200 (300-100): {g.xp_for_next}")


def test_streak() -> None:
    print("seri (streak)")
    today = date(2026, 6, 10)
    d = lambda n: today - timedelta(days=n)  # noqa: E731
    # Bugün dahil 3 ardışık gün
    s = compute_streak([d(2), d(1), d(0)], today)
    check(s["current"] == 3 and s["longest"] == 3, f"3 ardışık (bugün dahil): {s}")
    # Bugün çözülmemiş ama dün → seri korunur
    s2 = compute_streak([d(2), d(1)], today)
    check(s2["current"] == 2, f"düne kadar seri korunur: {s2['current']}")
    # Boşluk → current kopar ama longest korunur
    s3 = compute_streak([d(10), d(9), d(8), d(1), d(0)], today)
    check(s3["current"] == 2 and s3["longest"] == 3, f"boşluk: current=2 longest=3: {s3}")
    # 2 günden eski son aktivite → current 0
    s4 = compute_streak([d(5), d(4)], today)
    check(s4["current"] == 0, f"eski seri current 0: {s4['current']}")
    # Boş
    s5 = compute_streak([], today)
    check(s5 == {"current": 0, "longest": 0, "total_active_days": 0}, "boş → 0")
    # total_active_days = benzersiz gün
    s6 = compute_streak([d(0), d(0), d(1)], today)
    check(s6["total_active_days"] == 2, f"benzersiz gün 2: {s6['total_active_days']}")


def main() -> int:
    for fn in (test_level, test_xp_and_bar, test_streak):
        fn()
    print()
    if _failures:
        print(f"FAILED: {len(_failures)} assert düştü")
        return 1
    print("PASSED: oyunlaştırma testleri geçti")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
