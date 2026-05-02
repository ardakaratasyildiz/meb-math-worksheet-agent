"""A/B değerlendirmesi: Sprint 1 ve Sprint 2 değişikliklerinin baseline'a göre etkisi.

3 config matris'i:
    baseline      → Tüm Sprint 1+2 özellikleri OFF
    sprint1_only  → Sadece semantic dedup + critic ON (Sprint 1)
    sprint2_full  → Hepsi ON (Sprint 1 + Sprint 2)

Her config × her senaryo × N iterasyon agent.generate çalıştırır,
sonuçları toplar, metrikleri hesaplar, markdown rapor üretir.

Kullanım:
    PYTHONIOENCODING=utf-8 python scripts/eval/ab_runner.py
    PYTHONIOENCODING=utf-8 python scripts/eval/ab_runner.py --iterations 3 --question-count 5

Maliyet uyarısı: 3 config × 4 senaryo × N iterasyon × ~3 LLM çağrı (gen + retry + critic)
                + her soru için 1 embedding. Default ayarda ~60 üretim, 300 embed.
"""
from __future__ import annotations

import argparse
import contextlib
import dataclasses
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from app.data.curriculum import get_topic  # noqa: E402
from app.services.agent import GeminiAgent  # noqa: E402
from app.services.embedder import GeminiEmbedder  # noqa: E402
from app.services.history import GENERATION_HISTORY  # noqa: E402
from scripts.eval.metrics import (  # noqa: E402
    ConfigMetrics,
    IterationRun,
    compute_metrics,
)
from scripts.eval.report import build_report, write_report  # noqa: E402
from scripts.eval.scenarios import SCENARIOS, Scenario  # noqa: E402

logger = logging.getLogger("ab_runner")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


# -- Config matris ---------------------------------------------------------

CONFIG_MATRIX: dict[str, dict] = {
    "baseline": {
        "enable_semantic_dedup": False,
        "enable_critic": False,
        "enable_history_persist": False,
        # Jitter ve MMR kod akışında; sıcaklık jitter'ı seed reproducibility ile
        # zaten oluşur ama jitter etkisi olmayan basit baseline için temperature
        # parametresini elle veririz. Aşağıda her config için bir temp_override.
        "temp_override": "fixed",  # base sıcaklığı kullan, jitter ekleme
        "use_rng_in_retrieval": False,  # deterministik retrieval
    },
    "sprint1_only": {
        "enable_semantic_dedup": True,
        "enable_critic": True,
        "enable_history_persist": False,
        "temp_override": "fixed",
        "use_rng_in_retrieval": False,
    },
    "sprint2_full": {
        "enable_semantic_dedup": True,
        "enable_critic": True,
        "enable_history_persist": True,
        "temp_override": None,  # jitter aktif
        "use_rng_in_retrieval": True,
    },
}


@contextlib.contextmanager
def patched_settings(overrides: dict) -> Iterator[None]:
    """Settings'i geçici overrides'la değiştir; çıkışta eski değerleri geri yükle."""
    original = {}
    for k, v in overrides.items():
        if not hasattr(settings, k):
            continue
        original[k] = getattr(settings, k)
        setattr(settings, k, v)
    try:
        yield
    finally:
        for k, v in original.items():
            setattr(settings, k, v)


# -- Agent çağrı sarmalayıcı -----------------------------------------------

def _patched_generate(
    agent: GeminiAgent,
    scenario: Scenario,
    question_count: int,
    cfg_name: str,
    cfg: dict,
    tenant_id: str,
) -> tuple[list[dict], dict, float, str | None]:
    """Bir scenario için agent.generate çağırır, retrieval rng'sini config'e göre ayarlar.

    Baseline'da rng=None geçirmek için _collect_few_shot_rag/textbook'taki rng'yi
    devre dışı bırakmak gerek; bu zor çünkü agent içinde rng oluşturuluyor.
    Pratik çözüm: monkey-patch ile retriever.retrieve'in rng parametresini yutturmak.

    Şimdilik: baseline + sprint1_only'da settings.use_rag aynen açık kalır,
    ama agent'a direkt etki etmek için agent içindeki rng'yi None'lamak yerine
    sadece flag-tabanlı override (sıcaklık fixed, dedup/critic flag) yeterli.
    Retrieval jitter etkisi, sadece sprint2_full için ON kabul edilecek
    (kod yolundaki rng zaten her zaman aktarılıyor; baseline'a o etkiyi
    izole etmek için aşağıda monkey-patch uygulanır).
    """
    import app.services.retriever as retriever_mod

    # Retrieval jitter'ı config'e göre kapat — rng=None geçilmiş gibi davran.
    original_retrieve = retriever_mod.ExampleRetriever.retrieve
    original_retrieve_textbook = retriever_mod.ExampleRetriever.retrieve_textbook

    def deterministic_retrieve(self, *args, **kwargs):
        kwargs["rng"] = None
        return original_retrieve(self, *args, **kwargs)

    def deterministic_retrieve_textbook(self, *args, **kwargs):
        kwargs["rng"] = None
        return original_retrieve_textbook(self, *args, **kwargs)

    if not cfg.get("use_rng_in_retrieval", True):
        retriever_mod.ExampleRetriever.retrieve = deterministic_retrieve
        retriever_mod.ExampleRetriever.retrieve_textbook = deterministic_retrieve_textbook

    # Sıcaklık override: fixed → DIFFICULTY_TEMPERATURES'tan base'i ver, jitter atla.
    from app.services.agent import DIFFICULTY_TEMPERATURES
    temperature = None
    if cfg.get("temp_override") == "fixed":
        temperature = DIFFICULTY_TEMPERATURES[scenario.difficulty]

    start = time.time()
    error: str | None = None
    questions_data: list[dict] = []
    trace_dict: dict = {}
    try:
        questions = agent.generate(
            grade=scenario.grade,
            topic_id=scenario.topic_id,
            kazanim_kod=scenario.kazanim_kod,
            difficulty=scenario.difficulty,
            question_count=question_count,
            tenant_id=tenant_id,
            temperature=temperature,
        )
        for q in questions:
            questions_data.append({
                "question": q.question,
                "answer": q.answer,
                "kazanim_kod": q.kazanim_kod,
                "question_type": q.question_type.value,
            })
        trace_dict = agent.build_last_trace().model_dump()
    except Exception as exc:
        logger.warning("[%s/%s] generate başarısız: %s", cfg_name, scenario.label, exc)
        error = str(exc)
    finally:
        duration = time.time() - start
        # Restore retriever methods
        if not cfg.get("use_rng_in_retrieval", True):
            retriever_mod.ExampleRetriever.retrieve = original_retrieve
            retriever_mod.ExampleRetriever.retrieve_textbook = original_retrieve_textbook

    return questions_data, trace_dict, duration, error


# -- Ana akış --------------------------------------------------------------

def run_config(
    cfg_name: str,
    cfg: dict,
    iterations: int,
    question_count: int,
    scenarios: list[Scenario] | None = None,
) -> list[IterationRun]:
    """Bir config için tüm senaryolar × iterasyon adetini çalıştırır."""
    logger.info("=" * 70)
    logger.info("Config: %s", cfg_name)
    logger.info("=" * 70)

    selected_scenarios = scenarios if scenarios is not None else SCENARIOS
    runs: list[IterationRun] = []
    settings_overrides = {k: v for k, v in cfg.items() if k.startswith("enable_")}
    with patched_settings(settings_overrides):
        # Her config için temiz history (cross-config sızıntı engelle)
        GENERATION_HISTORY.clear()
        agent = GeminiAgent()
        # Tenant'ı config'e bağla → history config'ler arasında karışmasın.
        tenant = f"eval_{cfg_name}"

        for scenario in selected_scenarios:
            logger.info("  Senaryo: %s", scenario.label)
            for it in range(iterations):
                qs, tr, dur, err = _patched_generate(
                    agent, scenario, question_count, cfg_name, cfg, tenant
                )
                runs.append(IterationRun(
                    scenario_label=scenario.label,
                    iteration_index=it,
                    questions=qs,
                    trace=tr,
                    duration_seconds=dur,
                    error=err,
                ))
                logger.info(
                    "    iter %d/%d: %d soru, %.2fs%s",
                    it + 1, iterations, len(qs), dur,
                    f" [HATA: {err[:60]}]" if err else "",
                )
        # Tenant temizliği eval sonrası
        GENERATION_HISTORY.clear()
    return runs


def collect_embeddings(all_runs: dict[str, list[IterationRun]]) -> tuple[dict, dict]:
    """Tüm config'lerin tüm sorularını + kazanım metinlerini tek seferde embed eder."""
    questions: list[str] = []
    kazanim_codes_seen: set[str] = set()
    for runs in all_runs.values():
        for r in runs:
            for q in r.questions:
                questions.append(q["question"])
                kazanim_codes_seen.add(q.get("kazanim_kod", ""))

    embedder = GeminiEmbedder()
    unique_questions = list(set(questions))
    logger.info("Embedding üretiliyor: %d soru, %d kazanım metni",
                len(unique_questions), len(kazanim_codes_seen))

    q_embs = embedder.embed_many(unique_questions) if unique_questions else []
    question_embeddings = dict(zip(unique_questions, q_embs))

    # Kazanım metinleri
    from app.data.curriculum import CURRICULUM
    kazanim_texts: dict[str, str] = {}
    for grade_topics in CURRICULUM.values():
        for topic in grade_topics.values():
            for k in topic["kazanimlar"]:
                if k["kod"] in kazanim_codes_seen:
                    kazanim_texts[k["kod"]] = k["metin"]

    kazanim_codes = list(kazanim_texts.keys())
    if kazanim_codes:
        k_texts = [kazanim_texts[c] for c in kazanim_codes]
        k_embs = embedder.embed_many(k_texts)
        kazanim_embeddings = dict(zip(kazanim_codes, k_embs))
    else:
        kazanim_embeddings = {}

    return question_embeddings, kazanim_embeddings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=3, help="Her senaryoda iterasyon sayısı")
    parser.add_argument("--question-count", type=int, default=5, help="Çağrı başına soru sayısı")
    parser.add_argument(
        "--out-dir",
        type=str,
        default=str(ROOT / "knowledge_base" / "eval"),
        help="Çıktı klasörü",
    )
    parser.add_argument(
        "--configs",
        type=str,
        default="baseline,sprint1_only,sprint2_full",
        help="Çalıştırılacak config'ler (virgülle ayrılmış)",
    )
    parser.add_argument(
        "--scenarios",
        type=str,
        default=None,
        help="Çalıştırılacak senaryo label'ları (virgülle ayrılmış). Boşsa hepsi.",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="PR gate için hızlı mod: sprint2_full × g5_cebir_orta × 1 iter × 3 soru (~1-2 dk).",
    )
    args = parser.parse_args()

    if args.quick:
        args.configs = "sprint2_full"
        args.iterations = 1
        args.question_count = 3
        args.scenarios = "g5_cebir_orta"
        logger.info("Quick mode aktif: 1 config × 1 senaryo × 1 iter × 3 soru")

    selected_configs = [c.strip() for c in args.configs.split(",") if c.strip()]
    invalid = [c for c in selected_configs if c not in CONFIG_MATRIX]
    if invalid:
        logger.error("Geçersiz config: %s", invalid)
        sys.exit(2)

    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    logger.info("A/B değerlendirmesi başlıyor: configs=%s, iter=%d, q_count=%d",
                selected_configs, args.iterations, args.question_count)

    selected_scenarios: list[Scenario] | None = None
    if args.scenarios:
        labels = {s.strip() for s in args.scenarios.split(",") if s.strip()}
        selected_scenarios = [s for s in SCENARIOS if s.label in labels]
        missing = labels - {s.label for s in SCENARIOS}
        if missing:
            logger.error("Geçersiz senaryo label'ı: %s", missing)
            sys.exit(2)

    all_runs: dict[str, list[IterationRun]] = {}
    for cfg_name in selected_configs:
        runs = run_config(
            cfg_name,
            CONFIG_MATRIX[cfg_name],
            iterations=args.iterations,
            question_count=args.question_count,
            scenarios=selected_scenarios,
        )
        all_runs[cfg_name] = runs

    logger.info("Tüm config'ler tamamlandı. Embedding hesaplanıyor...")
    q_embs, k_embs = collect_embeddings(all_runs)

    logger.info("Metrikler hesaplanıyor...")
    results: dict[str, ConfigMetrics] = {}
    for cfg_name, runs in all_runs.items():
        results[cfg_name] = compute_metrics(cfg_name, runs, q_embs, k_embs)

    # Çıktıları yaz
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_path = out_dir / f"ab_raw_{timestamp}.json"
    raw_payload = {
        "timestamp": timestamp,
        "iterations": args.iterations,
        "question_count": args.question_count,
        "configs": selected_configs,
        "runs": {
            cfg: [dataclasses.asdict(r) for r in runs]
            for cfg, runs in all_runs.items()
        },
        "metrics": {cfg: dataclasses.asdict(m) for cfg, m in results.items()},
    }
    raw_path.write_text(json.dumps(raw_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Ham çıktı: %s", raw_path)

    baseline_key = "baseline" if "baseline" in results else selected_configs[0]
    report_md = build_report(results, baseline_key=baseline_key)
    report_path = write_report(report_md, out_dir, timestamp)
    logger.info("Rapor: %s", report_path)

    print("\n" + report_md)


if __name__ == "__main__":
    main()
