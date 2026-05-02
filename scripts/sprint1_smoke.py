"""Sprint 1 smoke test: semantic dedup + critic + trace uçtan uca.

Aynı (grade, topic, kazanim, difficulty) parametreleriyle 3 ardışık üretim yapar
ve trace metriklerini raporlar. Beklenti:
  - 2. ve 3. çağrılarda semantic dedup ya da string dedup tetiklenmiş olmalı
    (history embedding'leri 1. çağrıdan kalmış olduğu için).
  - critic_rejected çoğu zaman 0 olur ama tetiklenirse trace'te görünür.
  - trace alanları (few_shot_source, model_used, vs.) dolu gelmeli.

Kullanım:
    python scripts/sprint1_smoke.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.models.enums import Difficulty
from app.services.agent import GeminiAgent
from app.services.history import GENERATION_HISTORY


def run_iteration(agent: GeminiAgent, label: str) -> dict:
    questions = agent.generate(
        grade=5,
        topic_id="cebir",
        kazanim_kod="M.5.5.1",
        difficulty=Difficulty.ORTA,
        question_count=5,
    )
    trace = agent.build_last_trace()
    print(f"\n--- {label} ---")
    print(f"Soru sayısı: {len(questions)}")
    print("Trace:")
    print(json.dumps(trace.model_dump(), indent=2, ensure_ascii=False))
    print("\nİlk 2 soru:")
    for q in questions[:2]:
        print(f"  [{q.number}] ({q.question_type.value}) {q.question[:100]}")
    return {
        "label": label,
        "trace": trace.model_dump(),
        "first_questions": [q.question[:80] for q in questions[:3]],
    }


def main() -> None:
    print("Sprint 1 smoke test başlıyor.")
    print("Not: 3 ardışık çağrı yapacak; her biri ~10-30s sürebilir.\n")

    # Temiz başlangıç için history'i sıfırla.
    GENERATION_HISTORY.clear()

    agent = GeminiAgent()
    results = []
    for i in range(1, 4):
        results.append(run_iteration(agent, f"Çağrı #{i}"))

    print("\n" + "=" * 60)
    print("ÖZET")
    print("=" * 60)
    for r in results:
        t = r["trace"]
        print(
            f"{r['label']:12s} | model={t['model_used']:25s} "
            f"| string_dup={t['dedup_rejected_string']} "
            f"| sem_dup={t['dedup_rejected_semantic']} "
            f"| critic_rej={t['critic_rejected']} "
            f"| retrieval_dist={t['retrieval_avg_distance']}"
        )

    # Validasyonlar
    print("\nValidasyonlar:")
    second_third_sem = [r["trace"]["dedup_rejected_semantic"] for r in results[1:]]
    if any(x > 0 for x in second_third_sem):
        print(" PASS: 2. veya 3. çağrıda semantic dedup tetiklendi (history embedding'leri çalışıyor).")
    else:
        print(
            " WARN: 2-3. çağrılarda semantic dedup tetiklenmedi. "
            "Üretilen sorular zaten farklıysa normal; aksi halde threshold'u (0.88) gözden geçir."
        )
    if all(r["trace"]["few_shot_count"] > 0 for r in results):
        print(" PASS: Few-shot enjekte edildi.")
    else:
        print(" FAIL: Few-shot havuzu boş kaldı.")
    if all(r["trace"]["delivered_count"] >= 1 for r in results):
        print(" PASS: Tüm çağrılar en az 1 soru üretti.")
    else:
        print(" FAIL: En az bir çağrı 0 soru döndürdü.")


if __name__ == "__main__":
    main()
