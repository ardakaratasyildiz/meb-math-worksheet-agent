"""Claude'un PDF'lerden elle çıkardığı soruları questions_grade{N}.json'a ekler.

Gemini'siz (sıfır API maliyeti) çıkarım için. Claude bir JSON dosyasına soru listesi
yazar; bu script id/topic_id/source/format'ı doğru kurup mevcut çıktıya birleştirir.

Girdi JSON formatı (liste):
  [{"kazanim_kod":"M.7.3.1","difficulty":"kolay","question_type":"gorsel_geometri",
    "question":"<svg...>...\\nA) ..\\nB) ..","answer":"B) 100","solution":"..."}, ...]

Kullanım:
  python scripts/add_manual_questions.py --grade 7 --source "24-...pdf" --input /tmp/q.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.data.curriculum import CURRICULUM  # noqa: E402

PROCESSED_DIR = ROOT / "knowledge_base" / "processed"


def _stable_id(grade: int, source: str, idx: int, stem: str) -> str:
    key = f"{grade}|{source}|{idx}|{stem[:80]}"
    return f"q{grade}_" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:14]


def _topic_map(grade: int) -> dict[str, str]:
    return {k["kod"]: tid for tid, t in CURRICULUM.get(grade, {}).items() for k in t["kazanimlar"]}


def run(grade: int, source: str, input_path: str) -> None:
    out_path = PROCESSED_DIR / f"questions_grade{grade}.json"
    data = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {"examples": []}
    examples = data["examples"]
    existing_ids = {e["id"] for e in examples}
    kod2topic = _topic_map(grade)

    new_qs = json.loads(Path(input_path).read_text(encoding="utf-8"))
    added = 0
    for i, q in enumerate(new_qs):
        stem = q["question"]
        sid = _stable_id(grade, source, i, stem)
        if sid in existing_ids:
            continue
        kod = q.get("kazanim_kod") or ""
        examples.append({
            "id": sid,
            "grade": grade,
            "topic_id": kod2topic.get(kod, ""),
            "kazanim_kod": kod,
            "difficulty": q.get("difficulty", "orta"),
            "question_type": q.get("question_type", "coktan_secmeli"),
            "question": stem,
            "answer": q["answer"],
            "solution": q.get("solution", ""),
            "source": f"questions/grade{grade}/{source}",
            "tagged_by": "claude_manual",
        })
        existing_ids.add(sid)
        added += 1

    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"grade{grade} <- {source}: +{added} soru (toplam {len(examples)})")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--grade", type=int, required=True)
    p.add_argument("--source", type=str, required=True)
    p.add_argument("--input", type=str, required=True)
    args = p.parse_args()
    run(args.grade, args.source, args.input)


if __name__ == "__main__":
    main()
