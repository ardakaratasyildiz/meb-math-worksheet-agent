"""Bir A/B raw JSON dosyasından markdown raporu yeniden üretir.

Kullanım:
    PYTHONIOENCODING=utf-8 python scripts/eval/rerun_report.py knowledge_base/eval/ab_raw_<ts>.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.eval.metrics import ConfigMetrics
from scripts.eval.report import build_report, write_report


def main() -> None:
    if len(sys.argv) < 2:
        print("Kullanım: rerun_report.py <ab_raw.json>")
        sys.exit(2)
    raw_path = Path(sys.argv[1])
    payload = json.loads(raw_path.read_text(encoding="utf-8"))

    metrics: dict[str, ConfigMetrics] = {}
    for cfg, m_dict in payload["metrics"].items():
        # per_scenario alt-dict'i ayrı; ConfigMetrics dataclass alanlarına eşleştir
        m = ConfigMetrics(config_name=cfg)
        for k, v in m_dict.items():
            if hasattr(m, k):
                setattr(m, k, v)
        metrics[cfg] = m

    baseline_key = "baseline" if "baseline" in metrics else next(iter(metrics))
    report_md = build_report(metrics, baseline_key=baseline_key)

    timestamp = payload.get("timestamp", "rerun")
    out_path = write_report(report_md, raw_path.parent, timestamp)
    print(f"Rapor: {out_path}\n")
    print(report_md)


if __name__ == "__main__":
    main()
