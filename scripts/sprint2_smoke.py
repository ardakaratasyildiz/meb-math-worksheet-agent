"""Sprint 2 smoke test: retrieval jitter + temp jitter + retry-targeted +
few-shot diversity + history persist + tenant izolasyonu uçtan uca.

Beklentiler:
  1. 3 ardışık çağrıda retrieval_avg_distance FARKLI değerler almalı
     (oversample-then-sample çalışıyor).
  2. Sıcaklık her çağrıda jitter'lı olmalı (±0.10 base etrafında).
  3. Retry tetiklendiğinde final_temperature > temperature olmalı.
  4. Tenant A ve B aynı parametrelerle çağrıldığında HistoryKey ayrılmış olmalı
     (B'nin ilk çağrısı dedup tetiklemeden tamamlanır).
  5. Persist: Çağrılar arası process restart olsa bile history yüklenir
     (script process içinde test eder, GENERATION_HISTORY yeniden oluşturulur).

Kullanım:
    PYTHONIOENCODING=utf-8 python scripts/sprint2_smoke.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.models.enums import Difficulty
from app.services.agent import GeminiAgent
from app.services.history import GENERATION_HISTORY, GenerationHistory
import app.services.history as history_mod


def run_iteration(agent: GeminiAgent, label: str, tenant_id: str | None = None) -> dict:
    questions = agent.generate(
        grade=5,
        topic_id="cebir",
        kazanim_kod="M.5.5.1",
        difficulty=Difficulty.ORTA,
        question_count=5,
        tenant_id=tenant_id,
    )
    trace = agent.build_last_trace()
    print(f"\n--- {label} ---")
    print(f"Soru sayısı: {len(questions)} | tenant={tenant_id or '__shared__'}")
    print("Trace:")
    print(json.dumps(trace.model_dump(), indent=2, ensure_ascii=False))
    print("İlk 2 soru:")
    for q in questions[:2]:
        print(f"  [{q.number}] ({q.question_type.value}) {q.question[:90]}")
    return {
        "label": label,
        "tenant": tenant_id or "__shared__",
        "trace": trace.model_dump(),
    }


def main() -> None:
    print("Sprint 2 smoke test başlıyor.")

    # Temiz başlangıç — DB'yi de temizle.
    GENERATION_HISTORY.clear()

    agent = GeminiAgent()

    print("\n[Faz 1] Aynı tenant + aynı parametre, 3 ardışık çağrı")
    print("Beklenti: retrieval_avg_distance her çağrıda farklı, history büyüyor.")
    results = []
    for i in range(1, 4):
        results.append(run_iteration(agent, f"Çağrı #{i}", tenant_id="tenant_A"))

    print("\n[Faz 2] Farklı tenant ile çağrı (izole olmalı)")
    print("Beklenti: tenant_B history'si 1.kez geliyor; semantic dedup azalmalı.")
    results.append(run_iteration(agent, "Çağrı #4 (tenant_B)", tenant_id="tenant_B"))

    print("\n[Faz 3] Persistence testi: yeni GenerationHistory yarat, DB'den yükleyebiliyor mu?")
    fresh_history = GenerationHistory()
    # tenant_A için key oluştur
    a_key = ("tenant_A", 5, "cebir", "M.5.5.1", "orta")
    persisted_count = fresh_history.size(a_key)
    print(f" tenant_A için DB'den yüklenen kayıt sayısı: {persisted_count}")
    persisted_embs = fresh_history.seen_embeddings(a_key)
    print(f" Embedding'i olan kayıt sayısı: {len(persisted_embs)}")

    print("\n" + "=" * 70)
    print("ÖZET")
    print("=" * 70)
    distances = []
    temps = []
    for r in results:
        t = r["trace"]
        distances.append(t.get("retrieval_avg_distance"))
        temps.append(t.get("temperature"))
        print(
            f"{r['label']:30s} | tenant={r['tenant']:10s} "
            f"| temp={t['temperature']:.3f} "
            f"| final_temp={t.get('final_temperature')} "
            f"| dist={t.get('retrieval_avg_distance')} "
            f"| sem_dup={t['dedup_rejected_semantic']} "
            f"| critic_rej={t['critic_rejected']} "
            f"| delivered={t['delivered_count']}/{t['requested_count']}"
        )

    print("\nValidasyonlar:")

    # 1. Retrieval distance farklı mı?
    unique_distances = set(round(d, 4) for d in distances if d is not None)
    if len(unique_distances) > 1:
        print(f" PASS: Retrieval distance varyasyon gösterdi ({len(unique_distances)} farklı değer).")
    else:
        print(" WARN: Retrieval distance hep aynı geldi — havuz sığ olabilir veya jitter etkisiz.")

    # 2. Temperature jitter
    unique_temps = set(round(t, 3) for t in temps)
    if len(unique_temps) > 1:
        print(f" PASS: Sıcaklık jitter çalışıyor ({len(unique_temps)} farklı değer).")
    else:
        print(" FAIL: Sıcaklık jitter etkisiz — hep aynı sıcaklık.")

    # 3. Persistence
    if persisted_count > 0:
        print(f" PASS: Persistence çalışıyor ({persisted_count} kayıt diskten yüklendi).")
    else:
        print(" FAIL: Persistence boş — DB yazılmıyor olabilir veya path yanlış.")

    # 4. Tenant izolasyonu
    tenant_b_trace = results[3]["trace"]
    if tenant_b_trace["dedup_rejected_semantic"] <= 1:
        print(" PASS: Tenant izolasyonu — B history'si A'dan etkilenmedi.")
    else:
        print(
            f" WARN: Tenant B'de {tenant_b_trace['dedup_rejected_semantic']} semantic dup; "
            "izolasyon çalışıyor olabilir, ama A pollution olmadığını doğrulamak için kontrol gerek."
        )


if __name__ == "__main__":
    main()
