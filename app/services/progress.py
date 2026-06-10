"""İlerleme panosu agregasyonu (öğrenme döngüsü — Adım 3).

mastery_state satırlarından (kazanım × doğru/toplam) saf sayımla:
  - genel özet (doğru oranı, kazanım sayısı, çözülen quiz),
  - kazanım ustalık listesi (zayıf→güçlü),
  - zayıf kazanımlar (eşik altı + yeterli veri).

LLM yok, deterministik → router'dan ayrı tutuldu ki birim test edilebilsin.
"""
from __future__ import annotations

from app.models.schemas import (
    KazanimProgress,
    ProgressResponse,
    ProgressSummary,
)

# Zayıf kazanım eşiği: doğru oranı < 0.6 VE en az 3 cevap (anlamlı veri).
# Az veride "zayıf" demek erken/yanıltıcı → min_total kapısı.
WEAK_RATIO_THRESHOLD = 0.6
WEAK_MIN_TOTAL = 3


def build_progress(mastery_rows: list[dict], quizzes_solved: int) -> ProgressResponse:
    """mastery_state satırları + attempt sayısından ProgressResponse üretir."""
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

    summary = ProgressSummary(
        total_answered=total_answered,
        total_correct=total_correct,
        accuracy=(total_correct / total_answered) if total_answered else 0.0,
        kazanim_count=len(items),
        quizzes_solved=quizzes_solved,
    )
    return ProgressResponse(summary=summary, mastery=items, weak=weak)
