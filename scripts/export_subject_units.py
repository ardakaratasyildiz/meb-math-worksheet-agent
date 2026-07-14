"""Matematik-dışı derslerin ünite/kazanım ağacını frontend'e export eder.

Konular (/calismalar) sayfası ve ana sayfa "Sınıfa göre göz at" bölümü artık yalnız
matematik değil; Fen/Türkçe/Sosyal/İngilizce'yi de gezinilebilir gösterir. Bu ağacın
KAYNAĞI backend `app/subjects/<ders>/curriculum.py` içindeki `*_CURRICULUM` dict'leri
(üretimin kullandığı gerçek tema+kazanım). Matematik zaten frontend/lib/units.json'da
(build_units.py) → burada TEKRAR üretilmez.

Çıktı: frontend/lib/subject-units.json
  { "fen": { "3": [ {unit_id,no,name,kazanimlar:[{kod,metin}]}, ... ], ... }, ... }

Müfredat değişince (backend curriculum güncellenince) TEK komut:
  PYTHONIOENCODING=utf-8 python scripts/export_subject_units.py

Deseni build_units.py / export_seo_data.py ile aynı: backend tek kaynak, frontend
snapshot okur (build-time backend bağımlılığı yok).
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # 'app' paketini repo kökünden bul (scripts/'ten koşarken)
OUT = ROOT / "frontend" / "lib" / "subject-units.json"

# frontend Subject slug → (curriculum modülü, dict sabiti)
SUBJECTS: list[tuple[str, str, str]] = [
    ("fen", "app.subjects.fen.curriculum", "FEN_CURRICULUM"),
    ("turkce", "app.subjects.turkce.curriculum", "TURKCE_CURRICULUM"),
    ("sosyal", "app.subjects.sosyal.curriculum", "SOS_CURRICULUM"),
    ("ingilizce", "app.subjects.ingilizce.curriculum", "ING_CURRICULUM"),
]


def _lite_unit(u: dict) -> dict:
    """Frontend'in ihtiyaç duyduğu minimal alanlar (boyut için)."""
    return {
        "unit_id": u["unit_id"],
        "no": u.get("no", 0),
        "name": u["name"],
        "kazanimlar": [
            {"kod": k["kod"], "metin": k["metin"]} for k in u.get("kazanimlar", [])
        ],
    }


def build() -> dict:
    out: dict[str, dict[str, list[dict]]] = {}
    for slug, mod_path, const in SUBJECTS:
        mod = importlib.import_module(mod_path)
        cur: dict[int, list[dict]] = getattr(mod, const)
        by_grade: dict[str, list[dict]] = {}
        for grade in sorted(cur.keys()):
            units = sorted(cur[grade], key=lambda u: u.get("no", 0))
            by_grade[str(grade)] = [_lite_unit(u) for u in units]
        out[slug] = by_grade
    return out


def main() -> int:
    data = build()
    OUT.write_text(
        json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    # özet
    total_u = sum(len(units) for g in data.values() for units in g.values())
    total_k = sum(
        len(u["kazanimlar"]) for g in data.values() for units in g.values() for u in units
    )
    print(f"Yazıldı: {OUT.relative_to(ROOT)}")
    for slug, g in data.items():
        nu = sum(len(v) for v in g.values())
        print(f"  {slug:10} sınıflar={sorted(int(x) for x in g)} ünite={nu}")
    print(f"TOPLAM: {total_u} ünite · {total_k} kazanım")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
