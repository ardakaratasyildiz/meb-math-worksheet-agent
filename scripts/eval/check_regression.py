"""A/B raw JSON çıktısını thresholds.json eşikleriyle karşılaştırır.

Her metric için pass/fail/warn sonucu üretir. Kritik fail varsa exit 1 → CI fail.

Kullanım:
    python scripts/eval/check_regression.py --raw knowledge_base/eval/ab_raw_<ts>.json \\
        [--config sprint2_full] [--thresholds scripts/eval/thresholds.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# Marker karakterleri ASCII — Windows konsolu UTF-8 olmasa da görünür.
PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"


def _check(
    label: str,
    value: float | None,
    *,
    min_v: float | None = None,
    max_v: float | None = None,
    is_critical: bool = True,
) -> tuple[str, str]:
    """min/max sınır kontrolü. Tuple(status, line)."""
    if value is None:
        return WARN, f"{WARN} {label}: değer yok"
    if min_v is not None and value < min_v:
        marker = FAIL if is_critical else WARN
        return marker, f"{marker} {label}: {value:.4f} < min {min_v:.4f}"
    if max_v is not None and value > max_v:
        marker = FAIL if is_critical else WARN
        return marker, f"{marker} {label}: {value:.4f} > max {max_v:.4f}"
    return PASS, f"{PASS} {label}: {value:.4f} (min={min_v}, max={max_v})"


def evaluate(
    raw: dict,
    thresholds: dict,
    config_name: str,
) -> tuple[bool, list[str]]:
    """Bir config'in metriklerini eşiklerle kıyaslar. (ok, lines) döndürür."""
    metrics = raw.get("metrics", {}).get(config_name)
    if metrics is None:
        return False, [f"{FAIL} '{config_name}' config raw çıktıda yok."]

    lines: list[str] = [f"--- {config_name} ---"]
    statuses: list[str] = []

    div = thresholds.get("diversity", {})
    s, line = _check(
        "intra_batch_distance",
        metrics.get("avg_intra_batch_distance"),
        min_v=div.get("avg_intra_batch_distance_min"),
    )
    statuses.append(s); lines.append(line)
    s, line = _check(
        "cross_batch_distance",
        metrics.get("avg_cross_batch_distance"),
        min_v=div.get("avg_cross_batch_distance_min"),
    )
    statuses.append(s); lines.append(line)

    qual = thresholds.get("quality", {})
    s, line = _check(
        "kazanım_alignment",
        metrics.get("avg_kazanim_alignment"),
        min_v=qual.get("avg_kazanim_alignment_min"),
    )
    statuses.append(s); lines.append(line)
    s, line = _check(
        "delivered_ratio",
        metrics.get("avg_delivered_ratio"),
        min_v=qual.get("avg_delivered_ratio_min"),
    )
    statuses.append(s); lines.append(line)
    s, line = _check(
        "critic_pass_rate",
        metrics.get("avg_critic_pass_rate"),
        min_v=qual.get("avg_critic_pass_rate_min"),
        max_v=qual.get("avg_critic_pass_rate_max"),
        is_critical=False,  # critic pasif/aktif değişebilir; warn yeterli
    )
    statuses.append(s); lines.append(line)

    stab = thresholds.get("stability", {})
    successful_ratio = (
        metrics["successful_runs"] / metrics["total_runs"]
        if metrics.get("total_runs") else 0.0
    )
    s, line = _check(
        "successful_runs_ratio",
        successful_ratio,
        min_v=stab.get("successful_runs_ratio_min"),
    )
    statuses.append(s); lines.append(line)

    perf = thresholds.get("performance", {})
    s, line = _check(
        "avg_duration_seconds",
        metrics.get("avg_duration_seconds"),
        max_v=perf.get("avg_duration_seconds_max"),
        is_critical=False,
    )
    statuses.append(s); lines.append(line)

    has_fail = FAIL in statuses
    return not has_fail, lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, help="ab_raw_<ts>.json yolu")
    parser.add_argument(
        "--thresholds",
        default=str(Path(__file__).parent / "thresholds.json"),
    )
    parser.add_argument(
        "--config",
        default="sprint2_full",
        help="Hangi config'in metriklerini kıyaslayalım",
    )
    args = parser.parse_args()

    raw = json.loads(Path(args.raw).read_text(encoding="utf-8"))
    thresholds = json.loads(Path(args.thresholds).read_text(encoding="utf-8"))

    print(f"Eşik dosyası: {args.thresholds}")
    print(f"Karşılaştırılan config: {args.config}")
    print()

    ok, lines = evaluate(raw, thresholds, args.config)
    for ln in lines:
        print(ln)

    print()
    if ok:
        print(f"{PASS} Tüm kritik eşikler geçildi.")
        sys.exit(0)
    print(f"{FAIL} Kritik regresyon tespit edildi.")
    sys.exit(1)


if __name__ == "__main__":
    main()
