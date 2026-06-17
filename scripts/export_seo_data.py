"""Programatik SEO verisini backend müfredatından frontend'e export eder (TEK kaynak).

Frontend SEO landing page'leri (sitemap + statik sayfalar) backend
`app/data/curriculum.py`'den türer; build-time backend bağımlılığı olmasın diye
JSON snapshot'a yazılır. Bu script o snapshot'ları üretir:

  frontend/lib/kazanimlar.json        → kazanım-seviyesi long-tail landing'ler
  frontend/lib/curriculum-pages.json  → konu-seviyesi landing'ler + form dropdown

Böylece müfredata yeni sınıf/konu/kazanım eklenince SEO sayfaları ELLE değil
otomatik üretilir (Faz 1B: içerik→sayfa mekanikleşir). sitemap.ts bu listeleri
zaten otomatik toplar.

Müfredat değişince TEK komut:
  PYTHONIOENCODING=utf-8 python scripts/export_seo_data.py

LLM/ağ gerektirmez; deterministik; idempotent.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.data.curriculum import CURRICULUM  # noqa: E402

LIB = ROOT / "frontend" / "lib"
KAZANIM_OUT = LIB / "kazanimlar.json"
CURRICULUM_OUT = LIB / "curriculum-pages.json"


def _topic_slug(grade: int, topic_id: str) -> str:
    """Konu slug'ı — frontend ile aynı kural. Örn. (8, 'dogal_sayilar') → '8-sinif-dogal-sayilar'."""
    return f"{grade}-sinif-{topic_id.replace('_', '-')}"


def _kazanim_slug(kod: str) -> str:
    """Kazanım kodu → URL-güvenli slug. 'M.5.2.1' → 'm-5-2-1'."""
    return kod.lower().replace(".", "-")


def _build_curriculum_pages() -> list[dict]:
    """Konu-seviyesi landing verisi: her (sınıf × konu) bir sayfa."""
    rows: list[dict] = []
    for grade in sorted(CURRICULUM.keys()):
        for topic_id, topic in CURRICULUM[grade].items():
            rows.append({
                "grade": grade,
                "topicId": topic_id,
                "topicName": topic["name"],
                "description": topic["description"],
                "slug": _topic_slug(grade, topic_id),
                "kazanimCount": len(topic["kazanimlar"]),
            })
    return rows


def _build_kazanim_pages() -> list[dict]:
    """Kazanım-seviyesi landing verisi: her kazanım bir long-tail sayfa."""
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
    return rows


def _write(path: Path, rows: list[dict]) -> None:
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    curriculum_pages = _build_curriculum_pages()
    kazanim_pages = _build_kazanim_pages()
    _write(CURRICULUM_OUT, curriculum_pages)
    _write(KAZANIM_OUT, kazanim_pages)
    grades = sorted(CURRICULUM.keys())
    print(f"OK: {len(curriculum_pages)} konu sayfasi -> {CURRICULUM_OUT.name}")
    print(f"OK: {len(kazanim_pages)} kazanim sayfasi -> {KAZANIM_OUT.name}")
    print(f"Siniflar: {grades}")


if __name__ == "__main__":
    main()
