"""Kalite terazisi — ALTIN SET derleyici (docs/COST_QUALITY_V2_PLAN.md §2a).

Cevabı BİLİNEN, %100 GERÇEK soruları iki kaynaktan derler — sentetik üretim YOK:

  (a) Sözel ders few-shot modülleri (app/subjects/{turkce,sosyal,ingilizce,fen}/
      few_shot.py) — 138 soru, hepsi MEB ÖDSGM/EBA kaynaklı, cevaplar resmî
      anahtarla doğrulanmış.
  (b) ChromaDB gerçek matematik soru bankası (knowledge_base/chroma_db/chroma.sqlite3,
      `source LIKE 'questions/%'`) — doğrudan sqlite3 ile okunur (embedding/chromadb
      client'ı GEREKMEZ).

KESİNLİKLE HARİÇ (regresyon kilidi, bkz. tests/test_quality_bench.py):
  - `source LIKE 'synthetic%'`      → model kendi ürettiğini kopyalıyor (eko-odası)
  - `source = 'manual/few_shot'`    → app/data/few_shot/ (EXAMPLES_BY_GRADE), source
                                       alanı YOK → %100 sentetik
  - app/data/few_shot/ (EXAMPLES_BY_GRADE, 1-7) hiç İÇE AKTARILMAZ.

Deterministik: sabit seed (RNG_SEED) + sabit sıralama → aynı chroma.sqlite3 girdisiyle
her koşuda aynı gold_questions.json (bucket round-robin + seed'li iç karıştırma).

Kullanım:
    python scripts/eval/build_gold_set.py [--out PATH] [--math-target N]
"""
from __future__ import annotations

import argparse
import json
import random
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

# Windows konsol gotcha'sı: Türkçe karakter yazdırırken charmap hatası çıkabilir.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from app.data.curriculum import get_topics_for_grade  # noqa: E402
from app.services.structured import _parse_mcq  # noqa: E402
from app.subjects.fen.few_shot import FEN_EXAMPLES  # noqa: E402
from app.subjects.ingilizce.few_shot import ING_EXAMPLES  # noqa: E402
from app.subjects.sosyal.few_shot import SOS_EXAMPLES  # noqa: E402
from app.subjects.turkce.few_shot import TR_EXAMPLES  # noqa: E402

RNG_SEED = 20260728
CHROMA_DB = ROOT / "knowledge_base" / "chroma_db" / "chroma.sqlite3"
DEFAULT_OUT = ROOT / "knowledge_base" / "eval" / "gold" / "gold_questions.json"

# Ders → few-shot havuzu (dict[grade][kazanim_kod] -> list[dict]).
_FEWSHOT_POOLS: dict[str, dict[int, dict[str, list[dict]]]] = {
    "turkce": TR_EXAMPLES,
    "sosyal": SOS_EXAMPLES,
    "ingilizce": ING_EXAMPLES,
    "fen": FEN_EXAMPLES,
}

# Kesin regresyon kilidi: bu kaynak önekleri altın sete ASLA giremez.
FORBIDDEN_SOURCE_PREFIXES = ("synthetic", "synthetic_")
FORBIDDEN_SOURCES_EXACT = {"manual/few_shot"}


def _question_type_value(t: object) -> str:
    return t.value if hasattr(t, "value") else str(t)


def _options_and_index(question: str, answer: str) -> tuple[list[str] | None, int | None]:
    """Metinde A) B) C) D) şıkları varsa çıkar (mevcut yardımcıyla); yoksa None."""
    try:
        options, idx = _parse_mcq(question, answer)
    except Exception:
        return None, None
    return options, idx


def _fewshot_records(subject: str, pool: dict[int, dict[str, list[dict]]]) -> list[dict]:
    """Ders few-shot havuzunu altın-set kaydı şemasına çevirir."""
    out: list[dict] = []
    for grade, by_kod in pool.items():
        for kazanim_kod, items in by_kod.items():
            for ex in items:
                question = ex["question"]
                answer = ex["answer"]
                source = ex.get("source") or ""
                if source in FORBIDDEN_SOURCES_EXACT or source.startswith(FORBIDDEN_SOURCE_PREFIXES):
                    continue  # regresyon kilidi (bu havuzlarda pratikte olmaz)
                options, idx = _options_and_index(question, answer)
                out.append({
                    "subject": subject,
                    "grade": grade,
                    "kazanim_kod": kazanim_kod,
                    "question_type": _question_type_value(ex["type"]),
                    "difficulty": ex.get("difficulty") or "orta",
                    "question": question,
                    "answer": answer,
                    "solution_steps": ex.get("solution") or "",
                    "options": options,
                    "correct_index": idx,
                    "source": source,
                })
    return out


def _load_chroma_math_candidates(db_path: Path) -> list[dict]:
    """ChromaDB'den `questions/%` kaynaklı satırları pivotlar (sqlite3 doğrudan,
    embedding/chromadb client'ı GEREKMEZ)."""
    if not db_path.exists():
        print(f"UYARI: {db_path} bulunamadı — matematik altın-set boş kalacak.")
        return []
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM embedding_metadata WHERE key='source' "
            "AND string_value LIKE 'questions/%' ORDER BY id"
        )
        ids = [r[0] for r in cur.fetchall()]
        if not ids:
            return []
        placeholders = ",".join("?" * len(ids))
        cur.execute(
            f"SELECT id, key, string_value, int_value FROM embedding_metadata "
            f"WHERE id IN ({placeholders})",
            ids,
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    pivot: dict[int, dict[str, object]] = {}
    for id_, key, sv, iv in rows:
        d = pivot.setdefault(id_, {})
        d[key] = sv if sv is not None else iv

    candidates: list[dict] = []
    for id_ in ids:
        d = pivot.get(id_, {})
        source = str(d.get("source") or "")
        # Regresyon kilidi — plan §2a: yalnız 'questions/%' zaten SQL'de filtrelendi
        # ama çift-kontrol (defensive) — synthetic*/manual sızarsa burada da kesilir.
        if source.startswith(FORBIDDEN_SOURCE_PREFIXES) or source in FORBIDDEN_SOURCES_EXACT:
            continue
        kazanim_kod = str(d.get("kazanim_kod") or "").strip()
        answer = str(d.get("answer") or "").strip()
        question = str(d.get("chroma:document") or "")
        grade = d.get("grade")
        if not kazanim_kod or not answer or not grade:
            continue
        if not (40 <= len(question) <= 4000):
            continue
        candidates.append({
            "id": id_,
            "subject": "matematik",
            "grade": int(grade),
            "kazanim_kod": kazanim_kod,
            "question_type": str(d.get("question_type") or "sozel_problem"),
            "difficulty": str(d.get("difficulty") or "orta"),
            "question": question,
            "answer": answer,
            "solution_steps": str(d.get("solution") or ""),
            "source": source,
        })
    return candidates


def _select_math_balanced(candidates: list[dict], target: int, seed: int = RNG_SEED) -> list[dict]:
    """(grade, question_type) kovaları arasında round-robin ile dengeli seç.

    Deterministik: her kova sabit-seed'li (seed + kova anahtarı) RNG ile karıştırılır,
    sonra kovalar sıralı sırayla (deterministik) tek tek tüketilir.
    """
    buckets: dict[tuple[int, str], list[dict]] = {}
    for d in candidates:
        key = (d["grade"], d["question_type"])
        buckets.setdefault(key, []).append(d)
    for key, items in buckets.items():
        items.sort(key=lambda d: d["id"])  # deterministik taban sıra
        random.Random(f"{seed}:{key[0]}:{key[1]}").shuffle(items)

    order = sorted(buckets.keys())
    selected: list[dict] = []
    i = 0
    remaining = sum(len(v) for v in buckets.values())
    while len(selected) < target and remaining > 0:
        key = order[i % len(order)]
        if buckets[key]:
            selected.append(buckets[key].pop())
            remaining -= 1
        i += 1
    for d in selected:
        d.pop("id", None)
        options, idx = _options_and_index(d["question"], d["answer"])
        d["options"] = options
        d["correct_index"] = idx
    return selected


def _kazanim_valid_math(grade: int, kod: str) -> bool:
    for topic in get_topics_for_grade(grade):
        for k in topic["kazanimlar"]:
            if k["kod"] == kod:
                return True
    return False


def build_gold_set(math_target: int = 62) -> tuple[list[dict], dict]:
    records: list[dict] = []
    for subject, pool in _FEWSHOT_POOLS.items():
        records.extend(_fewshot_records(subject, pool))

    math_candidates = _load_chroma_math_candidates(CHROMA_DB)
    math_selected = _select_math_balanced(math_candidates, math_target)
    records.extend(math_selected)

    # Deterministik sıralama → gold_id sabit atanır.
    records.sort(key=lambda d: (d["subject"], d["grade"], d["kazanim_kod"], d["question"]))
    for i, rec in enumerate(records, start=1):
        rec["gold_id"] = f"gold-{i:04d}"
    # Alan sırasını plan şemasına göre sabitle.
    ordered: list[dict] = []
    for rec in records:
        ordered.append({
            "gold_id": rec["gold_id"],
            "subject": rec["subject"],
            "grade": rec["grade"],
            "kazanim_kod": rec["kazanim_kod"],
            "question_type": rec["question_type"],
            "difficulty": rec["difficulty"],
            "question": rec["question"],
            "answer": rec["answer"],
            "solution_steps": rec["solution_steps"],
            "options": rec.get("options"),
            "correct_index": rec.get("correct_index"),
            "source": rec["source"],
        })

    meta = {
        "total": len(ordered),
        "by_subject": dict(Counter(r["subject"] for r in ordered)),
        "by_grade": dict(sorted(Counter(r["grade"] for r in ordered).items())),
        "by_question_type": dict(Counter(r["question_type"] for r in ordered)),
        "by_difficulty": dict(Counter(r["difficulty"] for r in ordered)),
        "by_subject_grade": {
            f"{s}/{g}": c
            for (s, g), c in sorted(Counter((r["subject"], r["grade"]) for r in ordered).items())
        },
        "math_candidates_available": len(math_candidates),
        "math_selected": len(math_selected),
    }
    return ordered, meta


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument(
        "--math-target", type=int, default=62,
        help="Matematik kotasından seçilecek soru sayısı (few-shot 138 + bu = toplam).",
    )
    args = ap.parse_args()

    records, meta = build_gold_set(math_target=args.math_target)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = {"_meta": meta, "questions": records}
    args.out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Altın set yazıldı: {args.out}")
    print(f"Toplam: {meta['total']} soru (hedef >=180)")
    print(f"Ders dağılımı: {meta['by_subject']}")
    print(f"Sınıf dağılımı: {meta['by_grade']}")
    print(f"Tip dağılımı: {meta['by_question_type']}")
    print(f"Zorluk dağılımı: {meta['by_difficulty']}")
    print(
        f"Matematik: {meta['math_selected']}/{meta['math_candidates_available']} "
        "aday havuzundan seçildi."
    )
    if meta["total"] < 180:
        print("UYARI: toplam <180, kabul kriteri karşılanmıyor!")


if __name__ == "__main__":
    main()
