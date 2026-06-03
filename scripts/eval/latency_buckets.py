"""#1 ölçümü: mixed/progressive modda bucket PARALELLİĞİNİN süreye etkisi.

ab_runner agent.generate'i doğrudan çağırır (tek difficulty) → router'daki
_build_worksheet'in bucket paralelliğini GÖRMEZ. Bu script onu izole ölçer:
aynı isteği settings.parallel_difficulty_buckets False (ardışık) ve True (paralel)
ile N kez koşturup süreleri karşılaştırır.

Cache kapatılır (aksi halde 2. koşu anında cache'ten döner, ölçüm anlamsızlaşır),
her koşu öncesi GENERATION_HISTORY temizlenir (dedup koşular arası sızmasın),
tenant_id=None → worksheet_history yazımı atlanır.

Kullanım:
    PYTHONIOENCODING=utf-8 python scripts/eval/latency_buckets.py \
        [--mode mixed] [--question-count 10] [--iterations 3] \
        [--grade 5] [--topic cebir]
"""
from __future__ import annotations

import argparse
import statistics as st
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from app.models.enums import Difficulty  # noqa: E402
from app.models.schemas import GenerateWorksheetRequest  # noqa: E402
from app.routers.worksheets import _build_worksheet  # noqa: E402
from app.services.history import GENERATION_HISTORY  # noqa: E402


def _time_runs(req: GenerateWorksheetRequest, parallel: bool, iterations: int) -> list[float]:
    settings.parallel_difficulty_buckets = parallel
    durs: list[float] = []
    for i in range(iterations):
        GENERATION_HISTORY.clear()  # dedup'ı koşular arası izole et
        t = time.time()
        try:
            ws, _ = _build_worksheet(req)
            dt = time.time() - t
            n = ws.question_count
        except Exception as exc:  # noqa: BLE001
            dt = time.time() - t
            n = 0
            print(f"    [{'PARALEL' if parallel else 'ARDIŞIK'}] iter {i+1}: HATA {str(exc)[:70]} ({dt:.1f}s)")
            continue
        durs.append(dt)
        print(f"    [{'PARALEL' if parallel else 'ARDIŞIK'}] iter {i+1}/{iterations}: {n} soru, {dt:.1f}s")
    return durs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="mixed", choices=["mixed", "progressive"])
    ap.add_argument("--question-count", type=int, default=10)
    ap.add_argument("--iterations", type=int, default=3)
    ap.add_argument("--grade", type=int, default=5)
    ap.add_argument("--topic", default="cebir")
    args = ap.parse_args()

    # Cache kapat — tekrar koşular cache'ten dönmesin.
    settings.enable_generation_cache = False

    req = GenerateWorksheetRequest(
        grade=args.grade,
        topic_id=args.topic,
        kazanim_kod=None,
        difficulty=Difficulty.ORTA,  # mixed'te yalnızca etiket
        question_count=args.question_count,
        tenant_id=None,  # history yazımını atla
        difficulty_mode=args.mode,
    )

    print(f"# Mixed-bucket latency: mode={args.mode} q={args.question_count} "
          f"grade={args.grade} topic={args.topic} iter={args.iterations}\n")

    print("ARDIŞIK (parallel_difficulty_buckets=False):")
    seq = _time_runs(req, parallel=False, iterations=args.iterations)
    print("\nPARALEL (parallel_difficulty_buckets=True):")
    par = _time_runs(req, parallel=True, iterations=args.iterations)

    print("\n## Özet")
    if seq:
        print(f"  ardışık : medyan={st.median(seq):.1f}s  ort={st.mean(seq):.1f}s  "
              f"min={min(seq):.1f}  max={max(seq):.1f}  (n={len(seq)})")
    if par:
        print(f"  paralel : medyan={st.median(par):.1f}s  ort={st.mean(par):.1f}s  "
              f"min={min(par):.1f}  max={max(par):.1f}  (n={len(par)})")
    if seq and par:
        sp = st.median(seq) / max(0.01, st.median(par))
        print(f"  hızlanma (medyan): {sp:.2f}×")


if __name__ == "__main__":
    main()
