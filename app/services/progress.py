"""İlerleme panosu agregasyonu (öğrenme döngüsü — Adım 3).

mastery_state satırlarından (kazanım × doğru/toplam) saf sayımla:
  - genel özet (doğru oranı, kazanım sayısı, çözülen quiz),
  - kazanım ustalık listesi (zayıf→güçlü),
  - zayıf kazanımlar (eşik altı + yeterli veri).

LLM yok, deterministik → router'dan ayrı tutuldu ki birim test edilebilsin.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from app.models.schemas import (
    AttemptSummary,
    DailyTrendPoint,
    KazanimProgress,
    ProgressResponse,
    ProgressSummary,
)

# Zayıf kazanım eşiği: doğru oranı < 0.6 VE en az 3 cevap (anlamlı veri).
# Az veride "zayıf" demek erken/yanıltıcı → min_total kapısı.
WEAK_RATIO_THRESHOLD = 0.6
WEAK_MIN_TOTAL = 3

# Türkiye günü — UTC gece 03:00'te kaymasın diye sabit +3 offset.
_IST = timezone(timedelta(hours=3))


def build_daily_trend(
    attempts: list[dict],
    today: date,
    days: int = 30,
) -> list[DailyTrendPoint]:
    """Denemeleri Europe/Istanbul gününe göre bucket'lar (son `days` gün).

    attempts: [{score, total, completed_at(iso)}]. Aktif gün başına bir nokta
    (eski→yeni); boş günler atlanır.
    """
    cutoff = today - timedelta(days=days - 1)
    buckets: dict[date, list[int]] = {}
    for a in attempts:
        ca = a.get("completed_at")
        if not ca:
            continue
        try:
            d = datetime.fromisoformat(ca).astimezone(_IST).date()
        except ValueError:
            continue
        if d < cutoff or d > today:
            continue
        b = buckets.setdefault(d, [0, 0, 0])
        b[0] += int(a.get("score", 0))
        b[1] += int(a.get("total", 0))
        b[2] += 1
    out: list[DailyTrendPoint] = []
    for d in sorted(buckets):
        sc, tot, cnt = buckets[d]
        out.append(
            DailyTrendPoint(
                date=d.isoformat(),
                score=sc,
                total=tot,
                ratio=(sc / tot) if tot else 0.0,
                attempts=cnt,
            )
        )
    return out


def build_progress(
    mastery_rows: list[dict],
    quizzes_solved: int,
    recent_attempts: list[dict] | None = None,
) -> ProgressResponse:
    """mastery_state satırları + attempt sayısı + son denemelerden ProgressResponse."""
    items: list[KazanimProgress] = []
    total_answered = 0
    total_correct = 0

    for m in mastery_rows:
        tot = int(m.get("total", 0))
        cor = int(m.get("correct", 0))
        total_answered += tot
        total_correct += cor
        ratio = (cor / tot) if tot else 0.0
        items.append(
            KazanimProgress(
                kazanim_kod=m.get("kazanim_kod", ""),
                correct=cor,
                total=tot,
                ratio=ratio,
                last_seen_at=m.get("last_seen_at", ""),
            )
        )

    # Zayıf önce: düşük oran üstte; eşitlikte daha çok denenmiş olan üstte.
    items.sort(key=lambda x: (x.ratio, -x.total))

    weak = [
        x for x in items
        if x.total >= WEAK_MIN_TOTAL and x.ratio < WEAK_RATIO_THRESHOLD
    ]

    recent = [
        AttemptSummary(
            completed_at=a.get("completed_at", ""),
            score=int(a.get("score", 0)),
            total=int(a.get("total", 0)),
            ratio=(int(a.get("score", 0)) / int(a["total"]))
            if a.get("total")
            else 0.0,
        )
        for a in (recent_attempts or [])
    ]

    summary = ProgressSummary(
        total_answered=total_answered,
        total_correct=total_correct,
        accuracy=(total_correct / total_answered) if total_answered else 0.0,
        kazanim_count=len(items),
        quizzes_solved=quizzes_solved,
    )
    return ProgressResponse(summary=summary, mastery=items, weak=weak, recent=recent)
