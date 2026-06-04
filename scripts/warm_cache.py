"""Cache warming — popüler (sınıf, konu, zorluk) kombinasyonlarını önceden üretip
GENERATION_CACHE'i doldurur.

Neden: free-tier Gemini kotası kapasite tavanı. Bir büyüme/pazarlama push'unda
gelen trafiğin çoğu aynı ~birkaç düzine kombinasyonu ister. Bunları önceden
ısıtırsak ilk gerçek kullanıcı ANINDA + 0 LLM maliyeti + 0 kota ile sonuç alır.
Her cache-hit, kapasite tavanını bir kullanıcı kadar yukarı iter.

Nasıl: agent.generate başarılı tam-sayı üretimde sonucu kendiliğinden cache'e
yazar (GENERATION_CACHE.put). Bu script o çağrıyı popüler kombinasyonlar için
toplu yapar. Zaten cache'te olan kombinasyon agent içinde cache-hit'le döner
(yeni LLM çağrısı yok) → script idempotent ve tekrar çalıştırması ucuz.

Kombinasyon kaynağı:
  - Varsayılan: müfredat taraması (CURRICULUM'daki tüm grade×topic) × difficulties.
  - --popular <json>: GA4'ten export edilen popüler kombinasyonlar
    ([{"grade":5,"topic_id":"cebir","difficulty":"orta"}, ...]). Veri geldikçe
    körlemesine taramak yerine GERÇEK talebi ısıtın.

Kullanım:
  PYTHONIOENCODING=utf-8 python scripts/warm_cache.py --dry-run        # listele + maliyet tahmini
  PYTHONIOENCODING=utf-8 python scripts/warm_cache.py --grades 5,6 --difficulties orta,zor
  PYTHONIOENCODING=utf-8 python scripts/warm_cache.py --popular popular.json --variants 2

UYARI: gerçek koşu LLM çağrısı yapar (maliyet + kota). Önce --dry-run ile bak.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from app.data.curriculum import CURRICULUM  # noqa: E402
from app.models.enums import Difficulty  # noqa: E402
from app.services.agent import AgentError, GeminiAgent  # noqa: E402
from app.services.llm_cache import GENERATION_CACHE  # noqa: E402
from app.services.llm_providers import PRICING_USD_PER_1M_TOKENS  # noqa: E402

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger("warm_cache")
logger.setLevel(logging.INFO)

WARM_TENANT = "__cache_warm__"  # history exclusion → variants çeşitlenir


def _enumerate_combos(args) -> list[dict]:
    if args.popular:
        data = json.loads(Path(args.popular).read_text(encoding="utf-8"))
        combos = []
        for r in data:
            combos.append({
                "grade": int(r["grade"]),
                "topic_id": r["topic_id"],
                "difficulty": r.get("difficulty", "orta"),
            })
        return combos

    grades = [int(g) for g in args.grades.split(",")] if args.grades else sorted(CURRICULUM.keys())
    diffs = [d.strip() for d in args.difficulties.split(",") if d.strip()]
    topic_filter = {t.strip() for t in args.topics.split(",")} if args.topics else None

    combos: list[dict] = []
    for g in grades:
        if g not in CURRICULUM:
            logger.warning("Sınıf %s müfredatta yok, atlanıyor.", g)
            continue
        for topic_id in CURRICULUM[g].keys():
            if topic_filter and topic_id not in topic_filter:
                continue
            for d in diffs:
                combos.append({"grade": g, "topic_id": topic_id, "difficulty": d})
    return combos


def _estimate_cost(n_calls: int, avg_in: int, avg_out: int) -> float:
    price = PRICING_USD_PER_1M_TOKENS.get(settings.gemini_model)
    if not price:
        return float("nan")
    in_p, out_p = price
    return n_calls * (avg_in * in_p + avg_out * out_p) / 1_000_000


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grades", default=None, help="ör. 5,6,7 (boş = tümü)")
    ap.add_argument("--topics", default=None, help="topic_id filtresi (virgülle)")
    ap.add_argument("--difficulties", default="kolay,orta,zor")
    ap.add_argument("--question-count", type=int, default=10)
    ap.add_argument("--variants", type=int, default=1, help="kombinasyon başına cache set'i")
    ap.add_argument("--popular", default=None, help="GA4 popüler kombinasyon JSON yolu")
    ap.add_argument("--limit", type=int, default=None, help="toplam kombinasyon üst sınırı")
    ap.add_argument("--delay", type=float, default=0.0, help="çağrılar arası saniye (rate-limit)")
    ap.add_argument("--force", action="store_true", help="zaten warm olsa da yeniden üret")
    ap.add_argument("--dry-run", action="store_true", help="LLM çağrısı yapma, sadece listele+tahmin")
    ap.add_argument("--avg-in-tok", type=int, default=10000, help="tahmin için ort. girdi token")
    ap.add_argument("--avg-out-tok", type=int, default=5000, help="tahmin için ort. çıktı token")
    args = ap.parse_args()

    combos = _enumerate_combos(args)
    if args.limit:
        combos = combos[: args.limit]
    qc = args.question_count

    print(f"# Cache warming — model={settings.gemini_model} q={qc} variants={args.variants}")
    print(f"# Kombinasyon: {len(combos)}  | toplam çağrı (üst sınır): {len(combos) * args.variants}")
    print(f"# Başlangıç cache: {GENERATION_CACHE.stats()}\n")

    # Önceden warm olanları say (cache.get None değilse en az 1 set var).
    already = 0
    for c in combos:
        if GENERATION_CACHE.get(c["grade"], c["topic_id"], None, c["difficulty"], qc) is not None:
            already += 1
    cold = len(combos) - already
    print(f"# Zaten warm: {already}  | soğuk: {cold}")

    est_calls = (cold if not args.force else len(combos)) * args.variants
    est = _estimate_cost(est_calls, args.avg_in_tok, args.avg_out_tok)
    print(f"# Tahmini LLM çağrısı: ~{est_calls}  | tahmini maliyet: ~${est:.2f} "
          f"(varsayım {args.avg_in_tok}+{args.avg_out_tok} tok/çağrı; gerçek cost_meter logunda)\n")

    if args.dry_run:
        for c in combos:
            warm = GENERATION_CACHE.get(c["grade"], c["topic_id"], None, c["difficulty"], qc) is not None
            print(f"  {'WARM' if warm else 'soğuk'}  {c['grade']}. {c['topic_id']} / {c['difficulty']}")
        print("\n(dry-run — hiçbir üretim yapılmadı)")
        return

    agent = GeminiAgent()
    fresh = hit = fail = 0
    t_start = time.time()
    for i, c in enumerate(combos, 1):
        try:
            diff = Difficulty(c["difficulty"])
        except ValueError:
            logger.warning("Geçersiz zorluk '%s' (%s/%s) — atlanıyor.",
                           c["difficulty"], c["grade"], c["topic_id"])
            continue
        if not args.force and args.variants == 1 and \
                GENERATION_CACHE.get(c["grade"], c["topic_id"], None, diff.value, qc) is not None:
            hit += 1
            print(f"  [{i}/{len(combos)}] WARM (atlandı)  {c['grade']}.{c['topic_id']}/{diff.value}")
            continue
        for v in range(args.variants):
            try:
                agent.generate(
                    grade=c["grade"], topic_id=c["topic_id"], kazanim_kod=None,
                    difficulty=diff, question_count=qc, tenant_id=WARM_TENANT,
                )
                was_hit = agent.build_last_trace().cache_hit
                if was_hit:
                    hit += 1
                else:
                    fresh += 1
                print(f"  [{i}/{len(combos)}] {'cache-hit' if was_hit else 'ÜRETİLDİ '} "
                      f"{c['grade']}.{c['topic_id']}/{diff.value} v{v+1}")
            except AgentError as exc:
                fail += 1
                logger.warning("ÜRETİM HATASI %s.%s/%s: %s",
                               c["grade"], c["topic_id"], diff.value, exc)
            if args.delay > 0:
                time.sleep(args.delay)

    dur = time.time() - t_start
    print(f"\n## Özet ({dur:.0f}s)")
    print(f"  üretildi (fresh): {fresh}  | zaten warm/hit: {hit}  | hata: {fail}")
    print(f"  bitiş cache: {GENERATION_CACHE.stats()}")


if __name__ == "__main__":
    main()
