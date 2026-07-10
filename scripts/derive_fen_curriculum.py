"""Fen Bilimleri müfredatını (ünite + kazanım) resmî 2024 TYMM programından türetir.

Kaynak: knowledge_base/Fen/mufredat/fen_ogretim_programi_2024_TYMM.pdf
Çıktı:  app/subjects/fen/curriculum.py  (ünite bazlı, FB.{sınıf}.{ünite}[.{bölüm}].{çıktı})

Deterministik: PyMuPDF metin çıkarımı + FB kod eşleme. **LLM/Gemini KULLANILMAZ.**
Yeniden koşmak dosyayı yeniden üretir (elle düzenleme yapılırsa üzerine yazar →
düzenlemeleri koru/gözden geçir). Ünite adları programın özet tablosundan sabittir.

Kullanım:  python scripts/derive_fen_curriculum.py
"""
from __future__ import annotations

import importlib.util
import re
from collections import defaultdict
from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "knowledge_base" / "Fen" / "mufredat" / "fen_ogretim_programi_2024_TYMM.pdf"
OUT = ROOT / "app" / "subjects" / "fen" / "curriculum.py"
HINTS_PATH = ROOT / "app" / "subjects" / "fen" / "difficulty_hints.py"


def load_hints() -> dict[str, dict[str, str]]:
    """Elle yazılmış difficulty_hints'i dosyadan oku (paket import zinciri tetiklemeden).

    Yoksa boş döner → hints henüz yazılmamışsa curriculum yine üretilir.
    """
    if not HINTS_PATH.exists():
        return {}
    spec = importlib.util.spec_from_file_location("_fen_hints", HINTS_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return getattr(mod, "DIFFICULTY_HINTS", {})

# Ünite adları — 2024 TYMM programı özet tablosundan (docs/FEN_UNITE_YAPISI.md).
# Sıra = ünite numarası. FB kod sayıları ile doğrulanmıştır.
UNIT_NAMES: dict[int, list[str]] = {
    3: [
        "Bilimsel Keşif Yolculuğu", "Canlılar Dünyasına Yolculuk",
        "Yer Bilimciler İş Başında", "Maddeyi Tanıyalım, Karıştırıp Ayıralım",
        "Hareketi Keşfediyorum", "Yaşamımızı Kolaylaştıran Elektrik",
        "Toprağı Tanıyorum, Tarımı Keşfediyorum", "Canlıların Yaşam Alanlarına Yolculuk",
    ],
    4: [
        "Bilime Yolculuk", "Sağlıklı Besleniyorum", "Dünya'mızı Keşfedelim",
        "Maddenin Değişimi", "Mıknatısı Keşfediyorum", "Enerji Dedektifleri",
        "Işığın Peşinde", "Sürdürülebilir Şehirler ve Topluluklar",
    ],
    5: [
        "Gökyüzündeki Komşularımız ve Biz", "Kuvveti Tanıyalım",
        "Canlıların Yapısına Yolculuk", "Işığın Dünyası", "Maddenin Doğası",
        "Yaşamımızdaki Elektrik", "Sürdürülebilir Yaşam ve Geri Dönüşüm",
    ],
    6: [
        "Güneş Sistemi ve Tutulmalar", "Kuvvetin Etkisinde Hareket",
        "Canlılarda Sistemler", "Işığın Yansıması ve Renkler",
        "Maddenin Ayırt Edici Özellikleri", "Elektriğin İletimi ve Direnç",
        "Sürdürülebilir Yaşam ve Etkileşim",
    ],
    7: [
        "Uzay Çağı", "Kuvvet ve Enerjiyi Keşfedelim", "Vücudumuzdaki Sistemler",
        "Işığın Kırılması ve Mercekler", "Maddenin Doğasına Yolculuk",
        "Elektriklenme", "Sürdürülebilir Yaşam ve Enerji",
    ],
    8: [
        "Mevsimler ve İklim", "Yaşamı Kolaylaştıran Kuvvet", "Yaşamın Gizemi",
        "Sesin Dünyası", "Periyodik Tablo ve Maddenin Etkileşimi",
        "Elektriğin Yolculuğu", "Sürdürülebilir Yaşam ve Madde Döngüleri",
    ],
}

_TR = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def slugify(s: str) -> str:
    s = s.translate(_TR).lower()
    s = re.sub(r"['’´`]", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def extract() -> dict[int, dict[int, list[tuple[str, str]]]]:
    """grade -> unit_no -> [(kod, metin)] (öğrenme çıktıları, sıralı)."""
    doc = fitz.open(PDF)
    raw = "\n".join(pg.get_text("text") for pg in doc)
    t = raw.replace("­\n", "").replace("­", "")
    t = re.sub(r"-\n(?=[a-zçğıöşü])", "", t)
    t = t.replace("\n", " \n ")

    code_re = re.compile(r"\bFB\.(\d)\.(\d{1,2})\.(\d{1,2})(?:\.(\d{1,2}))?\.?")
    matches = list(code_re.finditer(t))
    data: dict[int, dict[int, dict[str, str]]] = defaultdict(lambda: defaultdict(dict))
    for i, m in enumerate(matches):
        g, u, l3, l4 = int(m.group(1)), int(m.group(2)), m.group(3), m.group(4)
        code = f"FB.{g}.{u}.{l3}" + (f".{l4}" if l4 else "")
        seg = t[m.end():(matches[i + 1].start() if i + 1 < len(matches) else len(t))]
        txt = re.split(r"\s+a\)\s", seg, maxsplit=1)[0]
        txt = re.sub(r"\s+", " ", txt).strip(" .\n")
        # Sadece öğrenme çıktısı cümlesi: kısa + "-bilme" ile biter (süreç
        # bileşenleri / öğretmen kılavuzu paragraflarını ele).
        if not txt or len(txt) > 170 or not re.search(r"bilme\b", txt):
            continue
        if code not in data[g][u]:
            data[g][u][code] = txt
    # dict -> sıralı liste
    out: dict[int, dict[int, list[tuple[str, str]]]] = {}
    for g in sorted(data):
        out[g] = {}
        for u in sorted(data[g]):
            def _key(c: str) -> list[int]:
                return [int(x) for x in c.split(".")[1:]]
            out[g][u] = [(c, data[g][u][c]) for c in sorted(data[g][u], key=_key)]
    return out


def render(data: dict[int, dict[int, list[tuple[str, str]]]], hints: dict[str, dict[str, str]]) -> str:
    L: list[str] = []
    L.append('"""Fen Bilimleri müfredatı — 2024 TYMM, ÜNİTE BAZLI (otomatik üretildi).')
    L.append("")
    L.append("Kaynak: knowledge_base/Fen/mufredat/fen_ogretim_programi_2024_TYMM.pdf")
    L.append("Üretici: scripts/derive_fen_curriculum.py (deterministik, LLM'siz).")
    L.append("Kod: FB.{sınıf}.{ünite}.{çıktı} (3-4. sınıf) / FB.{sınıf}.{ünite}.{bölüm}.{çıktı} (5-8).")
    L.append("")
    L.append("difficulty_hints: app/subjects/fen/difficulty_hints.py'den gömülür (elle")
    L.append("yazıldı; generator yeniden koşarsa korunur). İlk pass — Faz 6'da rafine edilir.")
    L.append('"""')
    L.append("from __future__ import annotations")
    L.append("")
    L.append("from typing import NotRequired, TypedDict")
    L.append("")
    L.append("")
    L.append("class FenKazanim(TypedDict):")
    L.append("    kod: str")
    L.append("    metin: str")
    L.append("    difficulty_hints: NotRequired[dict[str, str]]")
    L.append("")
    L.append("")
    L.append("class FenUnit(TypedDict):")
    L.append("    unit_id: str          # kararlı slug, örn. 'fen-5-unite-1-gokyuzundeki-komsularimiz-ve-biz'")
    L.append("    grade: int")
    L.append("    no: int               # ünite sırası")
    L.append("    name: str")
    L.append("    kazanimlar: list[FenKazanim]")
    L.append("")
    L.append("")
    L.append("FEN_CURRICULUM: dict[int, list[FenUnit]] = {")
    for g in sorted(data):
        L.append(f"    {g}: [")
        for u in sorted(data[g]):
            names = UNIT_NAMES.get(g, [])
            name = names[u - 1] if u - 1 < len(names) else f"Ünite {u}"
            uid = f"fen-{g}-unite-{u}-{slugify(name)}"
            L.append("        {")
            L.append(f'            "unit_id": {uid!r},')
            L.append(f'            "grade": {g},')
            L.append(f'            "no": {u},')
            L.append(f'            "name": {name!r},')
            L.append('            "kazanimlar": [')
            for kod, metin in data[g][u]:
                h = hints.get(kod)
                if h:
                    L.append("                {")
                    L.append(f'                    "kod": {kod!r},')
                    L.append(f'                    "metin": {metin!r},')
                    L.append('                    "difficulty_hints": {')
                    L.append(f'                        "kolay": {h["kolay"]!r},')
                    L.append(f'                        "orta": {h["orta"]!r},')
                    L.append(f'                        "zor": {h["zor"]!r},')
                    L.append("                    },")
                    L.append("                },")
                else:
                    L.append(f'                {{"kod": {kod!r}, "metin": {metin!r}}},')
            L.append("            ],")
            L.append("        },")
        L.append("    ],")
    L.append("}")
    L.append("")
    L.append("")
    L.append("# ── Erişimciler (units.py deseni, fen'e özel) ────────────────────────────────")
    L.append("def get_units_for_grade(grade: int) -> list[FenUnit]:")
    L.append("    return list(FEN_CURRICULUM.get(grade, []))")
    L.append("")
    L.append("")
    L.append("def get_unit(grade: int, unit_id: str) -> FenUnit | None:")
    L.append("    for u in FEN_CURRICULUM.get(grade, []):")
    L.append('        if u["unit_id"] == unit_id:')
    L.append("            return u")
    L.append("    return None")
    L.append("")
    L.append("")
    L.append("def get_unit_kazanim(grade: int, unit_id: str, kazanim_kod: str) -> FenKazanim | None:")
    L.append("    unit = get_unit(grade, unit_id)")
    L.append("    if unit is None:")
    L.append("        return None")
    L.append('    for k in unit["kazanimlar"]:')
    L.append('        if k["kod"] == kazanim_kod:')
    L.append("            return k")
    L.append("    return None")
    L.append("")
    L.append("")
    L.append("def find_unit_by_kazanim(kazanim_kod: str) -> tuple[int, FenUnit] | None:")
    L.append("    for grade, units in FEN_CURRICULUM.items():")
    L.append("        for u in units:")
    L.append('            for k in u["kazanimlar"]:')
    L.append('                if k["kod"] == kazanim_kod:')
    L.append("                    return grade, u")
    L.append("    return None")
    L.append("")
    L.append("")
    L.append("def is_unit_available(grade: int, unit_id: str) -> bool:")
    L.append("    return get_unit(grade, unit_id) is not None")
    L.append("")
    return "\n".join(L)


def main() -> None:
    data = extract()
    hints = load_hints()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(data, hints), encoding="utf-8")
    n_units = sum(len(v) for v in data.values())
    n_kaz = sum(len(ks) for v in data.values() for ks in v.values())
    all_kods = [kod for v in data.values() for ks in v.values() for kod, _ in ks]
    n_hinted = sum(1 for k in all_kods if k in hints)
    print(f"WROTE {OUT.relative_to(ROOT)}")
    print(f"  sınıflar: {sorted(data)}")
    for g in sorted(data):
        print(f"  {g}. sınıf: {len(data[g])} ünite, {sum(len(k) for k in data[g].values())} kazanım")
    print(f"  TOPLAM: {n_units} ünite, {n_kaz} kazanım")
    print(f"  difficulty_hints gömülü: {n_hinted}/{n_kaz}"
          + ("" if n_hinted == n_kaz else "  ⚠️ eksik var!"))


if __name__ == "__main__":
    main()
