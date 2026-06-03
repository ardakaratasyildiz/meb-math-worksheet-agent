"""Model A/B raw çıktısından birleşik KALİTE + MALİYET raporu üretir.

ab_runner.py'nin yazdığı ab_raw_<ts>.json dosyasını okur; her config için
kalite metriklerini (critic pass, kazanım alignment, delivered ratio, çeşitlilik)
ve generator token kullanımını/maliyetini birlikte tablolar.

Fiyatlar: ai.google.dev/gemini-api/docs/pricing (2026-06, ücretli tier, <=200k
prompt). Generator maliyeti trace'ten ölçülür (prompt+completion token).
Critic maliyeti trace'e DAHİL DEĞİLDİR (ayrı client) — kıyasta critic sabit
tutulduğu sürece generator kıyası adildir; critic kaldıracı configlerinde
critic maliyeti ayrıca not edilir.

Kullanım:
    PYTHONIOENCODING=utf-8 python scripts/eval/cost_report.py [--raw <path>] \
        [--worksheet-questions 10] [--monthly-worksheets 1000]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# (input_usd_per_1M, output_usd_per_1M) — güncel ücretli tier, <=200k prompt.
PRICES: dict[str, tuple[float, float]] = {
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-2.5-flash-lite": (0.10, 0.40),
    "gemini-2.5-pro": (1.25, 10.00),
    "gemini-3.5-flash": (1.50, 9.00),
    "gemini-3.1-pro-preview": (2.00, 12.00),
}

# config_name -> (generator_model, critic_model) — ab_runner CONFIG_MATRIX ile aynı.
CONFIG_MODELS: dict[str, tuple[str, str]] = {
    "gen_25flash":   ("gemini-2.5-flash",       "gemini-2.5-flash-lite"),
    "gen_25pro":     ("gemini-2.5-pro",         "gemini-2.5-flash-lite"),
    "gen_35flash":   ("gemini-3.5-flash",       "gemini-2.5-flash-lite"),
    "gen_3pro":      ("gemini-3-pro-preview",   "gemini-2.5-flash-lite"),
    "gen_31pro":     ("gemini-3.1-pro-preview", "gemini-2.5-flash-lite"),
    "critic_25flash":("gemini-2.5-flash",       "gemini-2.5-flash"),
    "critic_35flash":("gemini-2.5-flash",       "gemini-3.5-flash"),
}


def _cost(model: str, in_tok: float, out_tok: float) -> float:
    p = PRICES.get(model)
    if not p:
        return float("nan")
    return (in_tok * p[0] + out_tok * p[1]) / 1_000_000


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=str, default=None, help="ab_raw_*.json yolu (boşsa en yeni)")
    ap.add_argument("--worksheet-questions", type=int, default=10,
                    help="Prod kağıt başına soru (maliyet ölçeklemesi için)")
    ap.add_argument("--monthly-worksheets", type=int, default=1000,
                    help="Aylık üretilen kağıt sayısı (projeksiyon)")
    args = ap.parse_args()

    raw_path = args.raw
    if not raw_path:
        cands = sorted(glob.glob(str(ROOT / "knowledge_base" / "eval" / "ab_raw_*.json")),
                       key=os.path.getmtime)
        if not cands:
            print("ab_raw_*.json bulunamadı."); return
        raw_path = cands[-1]
    print(f"# Kaynak: {raw_path}\n")

    data = json.loads(Path(raw_path).read_text(encoding="utf-8"))
    eval_q = data.get("question_count", 5)
    metrics = data.get("metrics", {})
    runs = data.get("runs", {})
    scale = args.worksheet_questions / max(1, eval_q)

    # --- KALİTE TABLOSU ---
    print("## Kalite (sabit critic ile generator kıyası; proxy metrikler)\n")
    hdr = f"{'config':<16}{'gen model':<24}{'ok/tot':>8}{'critic_pass':>12}{'kazanım_align':>14}{'delivered':>11}{'çeşit(cross)':>13}{'süre(s)':>9}"
    print(hdr); print("-" * len(hdr))
    for cfg, m in metrics.items():
        gen, _crit = CONFIG_MODELS.get(cfg, (cfg, "?"))
        print(f"{cfg:<16}{gen:<24}"
              f"{str(m.get('successful_runs'))+'/'+str(m.get('total_runs')):>8}"
              f"{m.get('avg_critic_pass_rate',0):>12.3f}"
              f"{m.get('avg_kazanim_alignment',0):>14.3f}"
              f"{m.get('avg_delivered_ratio',0):>11.3f}"
              f"{m.get('avg_cross_batch_distance',0):>13.3f}"
              f"{m.get('avg_duration_seconds',0):>9.1f}")

    # --- MALİYET TABLOSU ---
    print(f"\n## Maliyet (generator; ölçek: eval {eval_q} soru → prod {args.worksheet_questions} soru)\n")
    hdr2 = f"{'config':<16}{'gen model':<24}{'in_tok/üretim':>14}{'out_tok/üretim':>15}{'$/kağıt':>11}{'$/ay@'+str(args.monthly_worksheets):>14}{'×flash':>8}"
    print(hdr2); print("-" * len(hdr2))
    base_cost = None
    rows = []
    for cfg, m in metrics.items():
        gen, _crit = CONFIG_MODELS.get(cfg, (cfg, "?"))
        cfg_runs = [r for r in runs.get(cfg, []) if not r.get("error") and r.get("trace")]
        n = len(cfg_runs)
        if n == 0:
            rows.append((cfg, gen, 0, 0, float("nan"))); continue
        in_tok = sum(r["trace"].get("prompt_tokens", 0) for r in cfg_runs) / n
        out_tok = sum(r["trace"].get("completion_tokens", 0) for r in cfg_runs) / n
        cost_per_ws = _cost(gen, in_tok * scale, out_tok * scale)
        rows.append((cfg, gen, in_tok, out_tok, cost_per_ws))

    for cfg, gen, in_tok, out_tok, cost_per_ws in rows:
        if cfg == "gen_25flash":
            base_cost = cost_per_ws
    for cfg, gen, in_tok, out_tok, cost_per_ws in rows:
        monthly = cost_per_ws * args.monthly_worksheets
        mult = (cost_per_ws / base_cost) if (base_cost and base_cost == base_cost and cost_per_ws == cost_per_ws) else float("nan")
        print(f"{cfg:<16}{gen:<24}{in_tok:>14.0f}{out_tok:>15.0f}{cost_per_ws:>11.5f}{monthly:>14.2f}{mult:>8.2f}")

    print("\nNot: $/kağıt = generator maliyeti (critic hariç). Critic kaldıracı")
    print("configlerinde (critic_*) fark critic'tedir ve burada GÖRÜNMEZ —")
    print("critic generate başına ~1 ek çağrıdır, ayrı değerlendirilmeli.")


if __name__ == "__main__":
    main()
