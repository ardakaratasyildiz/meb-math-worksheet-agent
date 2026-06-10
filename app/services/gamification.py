"""Oyunlaştırma — XP / seviye / seri (öğrenme döngüsü — PR5).

Saf/türetilmiş, yeni tablo yok. Mevcut verilerden hesaplanır:
  - XP = doğru sayısı × 10 + çözülen quiz × 5
  - Seviye = kümülatif eşik (threshold(L) = 50·(L-1)·L)
  - Seri (streak) = ardışık aktif gün (Europe/Istanbul)

Rozetler frontend'de mastery'den (konu-bazlı) türetilir → Python'da kazanım→konu
haritası gerekmez. LLM/DB yok → birim test edilebilir.
"""
from __future__ import annotations

from datetime import date, timedelta

from app.models.schemas import GamificationResponse

XP_PER_CORRECT = 10
XP_PER_QUIZ = 5


def level_threshold(level: int) -> int:
    """Bir seviyeye ulaşmak için gereken kümülatif XP. L1=0, L2=100, L3=300, L4=600…
    Sonraki seviyeye boşluk 100·L (lineer büyür)."""
    return 50 * (level - 1) * level


def compute_level(xp: int) -> int:
    """xp'nin karşılığı seviye (threshold(L) <= xp olan en büyük L)."""
    level = 1
    while level_threshold(level + 1) <= xp:
        level += 1
    return level


def compute_streak(active_dates: list[date], today: date) -> dict:
    """Aktif günlerden seri. current = bugüne VEYA düne kadar süren ardışık koşu
    (bugün çözmemiş seriyi sıfırlamaz). longest = en uzun ardışık koşu."""
    days = sorted(set(active_dates))
    if not days:
        return {"current": 0, "longest": 0, "total_active_days": 0}

    longest = 1
    run = 1
    for i in range(1, len(days)):
        if (days[i] - days[i - 1]).days == 1:
            run += 1
        else:
            run = 1
        longest = max(longest, run)

    current = 0
    last = days[-1]
    if last == today or last == today - timedelta(days=1):
        current = 1
        for i in range(len(days) - 2, -1, -1):
            if (days[i + 1] - days[i]).days == 1:
                current += 1
            else:
                break

    return {"current": current, "longest": longest, "total_active_days": len(days)}


def build_gamification(
    total_correct: int,
    quizzes_solved: int,
    active_dates: list[date],
    today: date,
) -> GamificationResponse:
    xp = total_correct * XP_PER_CORRECT + quizzes_solved * XP_PER_QUIZ
    level = compute_level(xp)
    base = level_threshold(level)
    nxt = level_threshold(level + 1)
    streak = compute_streak(active_dates, today)
    return GamificationResponse(
        xp=xp,
        level=level,
        xp_in_level=xp - base,
        xp_for_next=nxt - base,
        streak_current=streak["current"],
        streak_longest=streak["longest"],
        total_active_days=streak["total_active_days"],
    )
