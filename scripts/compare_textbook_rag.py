"""5. sınıf için A/B testi: sentetik+manuel few-shot vs sentetik+manuel+textbook.

Aynı kazanımlar için iki üretim koşusu yapılır:
    A) include_textbook=False — mevcut RAG-Lite davranışı
    B) include_textbook=True  — yeni textbook chunk'ları dahil

Metrikler:
    - Soru tipi dağılımı
    - Bağlam çeşitliliği (unique entity/context token sayısı)
    - Token-level Jaccard benzerliği (kümeler arası ortalama)
    - Karakter uzunluk dağılımı

Çıktı: docs/AŞAMA_A_REPORT.md + knowledge_base/processed/ab_test_results.json
"""
from __future__ import annotations

import json
import logging
import re
import sys
import time
from pathlib import Path
from statistics import mean, median, stdev

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.models.enums import Difficulty  # noqa: E402
from app.services.agent import GeminiAgent  # noqa: E402
from app.services.diversity import extract_context_tokens, normalize_question  # noqa: E402
from app.services.history import GENERATION_HISTORY  # noqa: E402

OUTPUT_JSON = ROOT / "knowledge_base" / "processed" / "ab_test_results.json"
OUTPUT_MD = ROOT / "docs" / "AŞAMA_A_REPORT.md"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("compare")


# Test kümesi — 5. sınıf farklı öğrenme alanlarından
TEST_CASES = [
    {"topic_id": "dogal_sayilar", "kazanim_kod": "M.5.1.5", "difficulty": Difficulty.ORTA, "n": 5},
    {"topic_id": "kesirler", "kazanim_kod": "M.5.2.4", "difficulty": Difficulty.ORTA, "n": 5},
    {"topic_id": "geometri", "kazanim_kod": "M.5.3.3", "difficulty": Difficulty.ORTA, "n": 5},
    {"topic_id": "cebir", "kazanim_kod": "M.5.5.2", "difficulty": Difficulty.ORTA, "n": 5},
]
GRADE = 5
SEED = 1234


def _tokens(text: str) -> set[str]:
    """Soru metnindeki anlamlı token'lar (3+ harfli, küçük harfe)."""
    return {w.lower() for w in re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü]{3,}", text)}


def _avg_pairwise_jaccard(questions: list[str]) -> float:
    if len(questions) < 2:
        return 0.0
    token_sets = [_tokens(q) for q in questions]
    sims: list[float] = []
    for i in range(len(token_sets)):
        for j in range(i + 1, len(token_sets)):
            a, b = token_sets[i], token_sets[j]
            if not a and not b:
                continue
            sims.append(len(a & b) / max(1, len(a | b)))
    return mean(sims) if sims else 0.0


def _question_type_counts(qs: list) -> dict[str, int]:
    out: dict[str, int] = {}
    for q in qs:
        t = q.question_type.value if hasattr(q.question_type, "value") else str(q.question_type)
        out[t] = out.get(t, 0) + 1
    return out


def _all_context_tokens(questions: list[str]) -> set[str]:
    s: set[str] = set()
    for q in questions:
        s |= set(extract_context_tokens(q))
    return s


def _run_one_case(agent: GeminiAgent, case: dict, include_textbook: bool, seed: int) -> dict:
    GENERATION_HISTORY.clear()  # her koşu temiz history ile başlasın → adil karşılaştırma
    t0 = time.time()
    qs = agent.generate(
        grade=GRADE,
        topic_id=case["topic_id"],
        kazanim_kod=case["kazanim_kod"],
        difficulty=case["difficulty"],
        question_count=case["n"],
        seed=seed,
        include_textbook=include_textbook,
    )
    elapsed = time.time() - t0

    questions_text = [q.question for q in qs]
    contexts = _all_context_tokens(questions_text)
    return {
        "kazanim_kod": case["kazanim_kod"],
        "topic_id": case["topic_id"],
        "difficulty": case["difficulty"].value,
        "include_textbook": include_textbook,
        "model_used": agent.last_model_used,
        "few_shot_source": agent.last_few_shot_source,
        "textbook_chunks_used": agent.last_textbook_count,
        "elapsed_sec": round(elapsed, 1),
        "produced": len(qs),
        "expected": case["n"],
        "type_distribution": _question_type_counts(qs),
        "avg_pairwise_jaccard": round(_avg_pairwise_jaccard(questions_text), 3),
        "unique_context_tokens": len(contexts),
        "sample_contexts": sorted(contexts)[:15],
        "avg_question_chars": round(mean(len(q) for q in questions_text), 0) if questions_text else 0,
        "questions": [
            {
                "n": q.number,
                "type": q.question_type.value if hasattr(q.question_type, "value") else str(q.question_type),
                "kazanim_kod": q.kazanim_kod,
                "question": q.question,
                "answer": q.answer,
                "solution_excerpt": q.solution_steps[:200],
            }
            for q in qs
        ],
    }


def _format_report(results: list[dict]) -> str:
    lines: list[str] = []
    lines.append("# Aşama A — Sentetik vs Sentetik+Textbook A/B Raporu (5. sınıf)\n")
    lines.append("> İki RAG modunun aynı kazanımlar üzerinde karşılaştırılması.\n")
    lines.append(f"- Test tarihi: {time.strftime('%Y-%m-%d %H:%M')}\n")
    lines.append(f"- Test kümesi: {len(TEST_CASES)} kazanım × 2 mod × {TEST_CASES[0]['n']} soru\n")
    lines.append(f"- Sabit seed: {SEED}\n")
    lines.append("\n## Özet Tablo\n")
    lines.append("| Kazanım | Mod | Üretilen | Ort. Jaccard ↓ | Unique Bağlam ↑ | Tip Dağılımı | Süre |")
    lines.append("|---------|-----|----------|----------------|-----------------|---------------|------|")
    for r in results:
        mode = "B (textbook)" if r["include_textbook"] else "A (sentetik)"
        td = ", ".join(f"{k}:{v}" for k, v in r["type_distribution"].items())
        lines.append(
            f"| {r['kazanim_kod']} | {mode} | {r['produced']}/{r['expected']} "
            f"| {r['avg_pairwise_jaccard']} | {r['unique_context_tokens']} "
            f"| {td} | {r['elapsed_sec']}s |"
        )

    # Aggregate karşılaştırma
    a_results = [r for r in results if not r["include_textbook"]]
    b_results = [r for r in results if r["include_textbook"]]

    def _agg(rs: list[dict], key: str) -> float:
        vals = [r[key] for r in rs if isinstance(r[key], (int, float))]
        return mean(vals) if vals else 0.0

    lines.append("\n## Toplulaştırılmış Metrikler\n")
    lines.append("| Metrik | A (sentetik) | B (textbook) | Δ |")
    lines.append("|--------|--------------|--------------|---|")
    metrics = [
        ("avg_pairwise_jaccard", "Ort. Jaccard (↓ iyi)"),
        ("unique_context_tokens", "Unique Bağlam (↑ iyi)"),
        ("avg_question_chars", "Ort. Soru Uzunluğu"),
        ("textbook_chunks_used", "Kullanılan Textbook Chunk"),
        ("elapsed_sec", "Süre (s)"),
    ]
    for key, label in metrics:
        a = _agg(a_results, key)
        b = _agg(b_results, key)
        delta = b - a
        lines.append(f"| {label} | {round(a, 2)} | {round(b, 2)} | {round(delta, 2)} |")

    # Üretilen sorular
    lines.append("\n## Üretilen Sorular (Karşılaştırma)\n")
    case_groups: dict[str, list[dict]] = {}
    for r in results:
        case_groups.setdefault(r["kazanim_kod"], []).append(r)
    for kod, rs in case_groups.items():
        lines.append(f"\n### {kod}\n")
        for r in rs:
            mode = "B (textbook)" if r["include_textbook"] else "A (sentetik)"
            lines.append(f"\n**Mod {mode}** — chunks={r['textbook_chunks_used']}, jaccard={r['avg_pairwise_jaccard']}, ctx={r['unique_context_tokens']}\n")
            for q in r["questions"]:
                lines.append(f"{q['n']}. [{q['type']}] {q['question']}")
                lines.append(f"   → Cevap: {q['answer']}")
            lines.append("")

    return "\n".join(lines)


def main() -> None:
    agent = GeminiAgent()
    results: list[dict] = []
    total_runs = len(TEST_CASES) * 2
    run_idx = 0
    for case in TEST_CASES:
        for include_tb in (False, True):
            run_idx += 1
            logger.info(
                "[%s/%s] Kazanım=%s | textbook=%s",
                run_idx, total_runs, case["kazanim_kod"], include_tb,
            )
            try:
                result = _run_one_case(agent, case, include_tb, seed=SEED)
            except Exception as exc:
                logger.exception("Koşu başarısız: %s", exc)
                result = {
                    "kazanim_kod": case["kazanim_kod"],
                    "include_textbook": include_tb,
                    "error": str(exc),
                    "produced": 0,
                    "expected": case["n"],
                    "avg_pairwise_jaccard": 0,
                    "unique_context_tokens": 0,
                    "type_distribution": {},
                    "elapsed_sec": 0,
                    "textbook_chunks_used": 0,
                    "avg_question_chars": 0,
                    "questions": [],
                }
            results.append(result)

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump({"results": results}, f, ensure_ascii=False, indent=2)
    logger.info("JSON yazıldı: %s", OUTPUT_JSON)

    report_md = _format_report(results)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text(report_md, encoding="utf-8")
    logger.info("Rapor yazıldı: %s", OUTPUT_MD)


if __name__ == "__main__":
    main()
