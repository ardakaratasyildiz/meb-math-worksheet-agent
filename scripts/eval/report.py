"""A/B değerlendirmesi sonuçlarını markdown tabloya dönüştüren rapor üretici."""
from __future__ import annotations

from pathlib import Path

from scripts.eval.metrics import ConfigMetrics


def _delta_str(baseline: float, candidate: float, higher_is_better: bool = True) -> str:
    if baseline == 0:
        if candidate > 0:
            return "**+∞**" if higher_is_better else "+∞"
        return "—"
    delta_pct = (candidate - baseline) / abs(baseline) * 100
    sign = "+" if delta_pct >= 0 else ""
    arrow = ""
    if higher_is_better:
        if delta_pct > 5:
            arrow = " ⬆"
        elif delta_pct < -5:
            arrow = " ⬇"
    else:
        if delta_pct < -5:
            arrow = " ⬇"
        elif delta_pct > 5:
            arrow = " ⬆"
    return f"{sign}{delta_pct:.1f}%{arrow}"


def _row(name: str, values: dict[str, float], baseline_key: str, fmt: str = "{:.4f}",
         higher_is_better: bool = True) -> str:
    cells = [name]
    base = values.get(baseline_key, 0.0)
    base_is_num = isinstance(base, (int, float))
    for k, v in values.items():
        v_is_num = isinstance(v, (int, float))
        cell = fmt.format(v) if v_is_num else str(v)
        if k != baseline_key and base_is_num and v_is_num:
            cell += f" ({_delta_str(base, v, higher_is_better)})"
        cells.append(cell)
    return "| " + " | ".join(cells) + " |"


def build_report(results: dict[str, ConfigMetrics], baseline_key: str = "baseline") -> str:
    """Markdown rapor stringi döndürür."""
    configs = list(results.keys())
    header = "| Metrik | " + " | ".join(configs) + " |"
    separator = "|---" * (len(configs) + 1) + "|"

    lines = [
        "# A/B Değerlendirme Raporu — Sprint 1+2",
        "",
        f"Karşılaştırılan config'ler: {', '.join(configs)}",
        f"Baseline: `{baseline_key}` (delta hesaplaması bu sütuna göre).",
        "",
        "## Genel Metrikler",
        "",
        header,
        separator,
    ]

    def values_for(attr: str) -> dict[str, float]:
        return {c: getattr(results[c], attr) for c in configs}

    # Diversity (higher is better)
    lines.append(_row("Intra-batch semantic distance ⬆", values_for("avg_intra_batch_distance"), baseline_key))
    lines.append(_row("Cross-batch semantic distance ⬆", values_for("avg_cross_batch_distance"), baseline_key))
    lines.append(_row("Unique normalize ratio ⬆", values_for("unique_normalize_ratio"), baseline_key))
    lines.append(_row("Unique context tokens / batch ⬆", values_for("avg_unique_context_tokens_per_batch"), baseline_key, "{:.2f}"))
    # Quality
    lines.append(_row("Critic pass rate ⬆", values_for("avg_critic_pass_rate"), baseline_key))
    lines.append(_row("Delivered ratio ⬆", values_for("avg_delivered_ratio"), baseline_key))
    lines.append(_row("Kazanım alignment ⬆", values_for("avg_kazanim_alignment"), baseline_key))
    # Stability — variance higher is better (jitter/diversity yapıyor)
    lines.append(_row("Temperature variance ⬆", values_for("temperature_variance"), baseline_key))
    lines.append(_row("Retrieval distance variance ⬆", values_for("retrieval_distance_variance"), baseline_key))
    # Performance — duration lower is better
    lines.append(_row("Avg duration (s) ⬇", values_for("avg_duration_seconds"), baseline_key, "{:.2f}", higher_is_better=False))
    lines.append(_row("Total questions generated", values_for("total_questions_generated"), baseline_key, "{:.0f}"))
    lines.append(_row("Successful runs / total", {c: f"{results[c].successful_runs}/{results[c].total_runs}" for c in configs}, baseline_key, "{}"))

    # Per-scenario breakdown
    lines.append("")
    lines.append("## Senaryo Bazlı Cross-Batch Distance")
    lines.append("")
    all_scenarios: set[str] = set()
    for c in configs:
        all_scenarios.update(results[c].per_scenario.keys())
    if all_scenarios:
        scen_header = "| Senaryo | " + " | ".join(configs) + " |"
        scen_sep = "|---" * (len(configs) + 1) + "|"
        lines.append(scen_header)
        lines.append(scen_sep)
        for label in sorted(all_scenarios):
            row = [label]
            base_v = results[baseline_key].per_scenario.get(label, {}).get("cross_batch_distance", 0.0)
            for c in configs:
                v = results[c].per_scenario.get(label, {}).get("cross_batch_distance", 0.0)
                cell = f"{v:.4f}"
                if c != baseline_key:
                    cell += f" ({_delta_str(base_v, v, True)})"
                row.append(cell)
            lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def write_report(report_md: str, out_dir: str | Path, timestamp: str) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"ab_report_{timestamp}.md"
    out.write_text(report_md, encoding="utf-8")
    return out
