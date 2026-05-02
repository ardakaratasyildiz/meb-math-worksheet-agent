"""A/B değerlendirmesi metrikleri.

Bir config altında çalıştırılan tüm iterasyonların ham çıktısını alır,
her metrik için skaler değer üretir. Embedding çağrısı pahalı olduğundan
tüm sorular tek seferde batch embed edilir.
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Any

from app.services.diversity import _cosine_similarity, normalize_question, extract_context_tokens


@dataclass
class IterationRun:
    """Bir agent.generate çağrısının kayıt altına alınmış sonucu."""

    scenario_label: str
    iteration_index: int
    questions: list[dict]  # [{question, answer, kazanim_kod, question_type}, ...]
    trace: dict
    duration_seconds: float
    error: str | None = None


@dataclass
class ConfigMetrics:
    """Bir config (baseline / sprint1 / sprint2) için toplu metrikler."""

    config_name: str
    total_runs: int = 0
    successful_runs: int = 0

    # Diversity
    avg_intra_batch_distance: float = 0.0
    avg_cross_batch_distance: float = 0.0
    unique_normalize_ratio: float = 0.0
    avg_unique_context_tokens_per_batch: float = 0.0

    # Quality
    avg_critic_pass_rate: float = 0.0
    avg_delivered_ratio: float = 0.0
    avg_kazanim_alignment: float = 0.0  # cosine sim to kazanim text

    # Stability / Performance
    temperature_variance: float = 0.0
    retrieval_distance_variance: float = 0.0
    avg_duration_seconds: float = 0.0
    total_questions_generated: int = 0

    # Detay
    per_scenario: dict[str, dict[str, float]] = field(default_factory=dict)


def _pairwise_avg_distance(embeddings: list[list[float]]) -> float:
    """1 - ortalama pairwise cosine similarity. Yüksek değer = daha çeşitli."""
    n = len(embeddings)
    if n < 2:
        return 0.0
    total = 0.0
    pairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            total += 1.0 - _cosine_similarity(embeddings[i], embeddings[j])
            pairs += 1
    return total / pairs if pairs else 0.0


def compute_metrics(
    config_name: str,
    runs: list[IterationRun],
    question_embeddings: dict[str, list[float]],  # question_text -> embedding
    kazanim_embeddings: dict[str, list[float]],  # kazanim_kod -> embedding
) -> ConfigMetrics:
    """Bir config'in tüm iterasyon sonuçlarından metrik hesaplar.

    question_embeddings: tüm config'lerin tüm soruları için tek seferde embed edilmiş havuz.
    kazanim_embeddings: hizalama metriği için kazanım metni embedding'leri.
    """
    m = ConfigMetrics(config_name=config_name)
    m.total_runs = len(runs)
    successful = [r for r in runs if not r.error and r.questions]
    m.successful_runs = len(successful)

    if not successful:
        return m

    # Diversity: per-batch intra-batch + cross-batch (per scenario)
    intra_batch_distances: list[float] = []
    per_scenario_questions: dict[str, list[list[float]]] = {}

    for run in successful:
        embs = [question_embeddings.get(q["question"], []) for q in run.questions]
        embs = [e for e in embs if e]
        if len(embs) >= 2:
            intra_batch_distances.append(_pairwise_avg_distance(embs))
        per_scenario_questions.setdefault(run.scenario_label, []).extend(embs)

    m.avg_intra_batch_distance = (
        statistics.mean(intra_batch_distances) if intra_batch_distances else 0.0
    )

    cross_batch_distances: list[float] = []
    for label, embs in per_scenario_questions.items():
        if len(embs) >= 2:
            cross_batch_distances.append(_pairwise_avg_distance(embs))
    m.avg_cross_batch_distance = (
        statistics.mean(cross_batch_distances) if cross_batch_distances else 0.0
    )

    # Unique normalize ratio (yapısal çeşitlilik)
    all_normalized: list[str] = []
    for run in successful:
        for q in run.questions:
            all_normalized.append(normalize_question(q["question"]))
    m.unique_normalize_ratio = (
        len(set(all_normalized)) / len(all_normalized) if all_normalized else 0.0
    )

    # Unique context tokens per batch
    ctx_counts: list[int] = []
    for run in successful:
        all_ctx: set[str] = set()
        for q in run.questions:
            all_ctx.update(extract_context_tokens(q["question"]))
        ctx_counts.append(len(all_ctx))
    m.avg_unique_context_tokens_per_batch = statistics.mean(ctx_counts) if ctx_counts else 0.0

    # Quality
    delivered_ratios: list[float] = []
    critic_pass_rates: list[float] = []
    alignments: list[float] = []
    for run in successful:
        t = run.trace
        requested = t.get("requested_count", 0)
        delivered = t.get("delivered_count", 0)
        critic_rej = t.get("critic_rejected", 0)
        if requested > 0:
            delivered_ratios.append(delivered / requested)
        # Critic pass rate: critic'in ele aldığı soruların kaçı geçti.
        # delivered + critic_rejected = critic'in gördüğü soru sayısı.
        critic_seen = delivered + critic_rej
        if critic_seen > 0:
            critic_pass_rates.append(delivered / critic_seen)
        # Kazanım alignment: her sorunun kazanım embedding'iyle cosine sim ortalaması.
        for q in run.questions:
            q_emb = question_embeddings.get(q["question"], [])
            k_emb = kazanim_embeddings.get(q.get("kazanim_kod", ""), [])
            if q_emb and k_emb:
                alignments.append(_cosine_similarity(q_emb, k_emb))

    m.avg_delivered_ratio = statistics.mean(delivered_ratios) if delivered_ratios else 0.0
    m.avg_critic_pass_rate = statistics.mean(critic_pass_rates) if critic_pass_rates else 1.0
    m.avg_kazanim_alignment = statistics.mean(alignments) if alignments else 0.0

    # Stability
    temps = [r.trace.get("temperature", 0.0) for r in successful]
    dists = [r.trace.get("retrieval_avg_distance") for r in successful]
    dists = [d for d in dists if isinstance(d, (int, float))]
    m.temperature_variance = statistics.pstdev(temps) if len(temps) > 1 else 0.0
    m.retrieval_distance_variance = statistics.pstdev(dists) if len(dists) > 1 else 0.0

    # Performance
    durations = [r.duration_seconds for r in successful]
    m.avg_duration_seconds = statistics.mean(durations) if durations else 0.0
    m.total_questions_generated = sum(len(r.questions) for r in successful)

    # Per-scenario detay
    by_scenario: dict[str, list[IterationRun]] = {}
    for r in successful:
        by_scenario.setdefault(r.scenario_label, []).append(r)
    for label, scen_runs in by_scenario.items():
        embs_all: list[list[float]] = []
        for r in scen_runs:
            for q in r.questions:
                e = question_embeddings.get(q["question"], [])
                if e:
                    embs_all.append(e)
        m.per_scenario[label] = {
            "cross_batch_distance": _pairwise_avg_distance(embs_all),
            "delivered_ratio": (
                statistics.mean(
                    r.trace.get("delivered_count", 0) / r.trace.get("requested_count", 1)
                    for r in scen_runs
                ) if scen_runs else 0.0
            ),
            "questions": sum(len(r.questions) for r in scen_runs),
        }

    return m
