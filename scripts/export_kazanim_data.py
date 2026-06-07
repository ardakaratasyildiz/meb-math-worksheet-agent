"""Backend müfredatındaki kazanım verisini frontend'e statik export eder.

Programatik SEO: her MEB kazanımı için ayrı landing page üretilir
(/calismalar/<konu-slug>/<kazanim-slug>). Sayfalar build-time statik olduğu için
veri build-time'da hazır olmalı → bu script frontend/lib/kazanimlar.json'a yazar.

Her giriş benzersiz içerik taşır (resmi kazanım metni + zorluk ipuçları) → thin/
doorway içerik değil. LLM gerektirmez.

Müfredat değişince yeniden çalıştır:
  PYTHONIOENCODING=utf-8 python scripts/export_kazanim_data.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.data.curriculum import CURRICULUM  # noqa: E402

OUT = ROOT / "frontend" / "lib" / "kazanimlar.json"


def _topic_slug(grade: int, topic_id: str) -> str:
    # Frontend curriculum.ts ile aynı kural.
    return f"{grade}-sinif-{topic_id.replace('_', '-')}"


def _kazanim_slug(kod: str) -> str:
    # "M.5.2.1" -> "m-5-2-1" (URL-güvenli)
    return kod.lower().replace(".", "-")


def main() -> None:
    rows: list[dict] = []
    for grade in sorted(CURRICULUM.keys()):
        for topic_id, topic in CURRICULUM[grade].items():
            tslug = _topic_slug(grade, topic_id)
            for k in topic["kazanimlar"]:
                rows.append({
                    "topicSlug": tslug,
                    "grade": grade,
                    "topicId": topic_id,
                    "topicName": topic["name"],
                    "kazanimSlug": _kazanim_slug(k["kod"]),
                    "kod": k["kod"],
                    "metin": k["metin"],
                    "hints": k.get("difficulty_hints", {}) or {},
                })
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: {len(rows)} kazanim -> {OUT}")


if __name__ == "__main__":
    main()
