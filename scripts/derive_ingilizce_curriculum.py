"""İngilizce müfredatını (tema + öğrenme çıktısı) 2024 TYMM programından türetir.

Kaynak: knowledge_base/Ingilizce/mufredat/ingilizce_ogretim_programi_2024_TYMM.pdf
Çıktı:  app/subjects/ingilizce/curriculum.py

Kod: ENG.{sınıf}.{tema}.{beceri}{no}  (ör. ENG.5.1.L1 = 5.sınıf, 1.tema, Listening-1).
Beceri kodları: L=Listening, R=Reading, S=Speaking, V=Vocabulary, G=Grammar, P=Pronunciation,
W=Writing. Tema = "unit" karşılığı. İçerik/tema adı, temanın içerik tanımından ("on ...") türetilir.

Deterministik: PyMuPDF metin + ENG kod eşleme. **LLM/Gemini KULLANILMAZ.**
Kullanım:  python scripts/derive_ingilizce_curriculum.py
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "knowledge_base" / "Ingilizce" / "mufredat" / "ingilizce_ogretim_programi_2024_TYMM.pdf"
OUT = ROOT / "app" / "subjects" / "ingilizce" / "curriculum.py"

_TR = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def slugify(s: str) -> str:
    s = s.translate(_TR).lower()
    s = re.sub(r"['’´`\"]", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:60].strip("-")


def _clean(t: str) -> str:
    return re.sub(r"\s+", " ", t).strip(" .\n\t")


def extract() -> tuple[dict, dict]:
    """(data, theme_names): data[grade][theme]=[(kod,metin)]; theme_names[(grade,theme)]=ad."""
    doc = fitz.open(PDF)
    raw = "\n".join(pg.get_text("text") for pg in doc)
    t = raw.replace("\xad\n", "").replace("\xad", "")
    t = t.replace("\n", " \n ")

    code_re = re.compile(r"ENG\.(\d+)\.(\d+)\.([A-Z]\d+)\.")
    matches = list(code_re.finditer(t))
    data = defaultdict(lambda: defaultdict(list))
    seen = set()
    theme_names: dict = {}
    for i, m in enumerate(matches):
        g, th = int(m.group(1)), int(m.group(2))
        code = f"ENG.{g}.{th}.{m.group(3)}"
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(t)
        seg = t[start:end]
        # çıktı cümlesi = ilk "a)" süreç bileşenine kadar
        metin = _clean(re.split(r"\s+a\)\s", seg, maxsplit=1)[0])
        if not metin or len(metin) < 8:
            continue
        if len(metin) > 240:
            metin = metin[:237].rsplit(" ", 1)[0] + "…"
        if code in seen:
            continue
        seen.add(code)
        data[g][th].append((code, metin))
        # tema adı: içindeki `on "..."` / `on '...'` içerik tanımından ilk parça
        if (g, th) not in theme_names:
            mm = re.search(r'\bon\s+[“"\']([^”"\';]+)', seg)
            if mm:
                theme_names[(g, th)] = _clean(mm.group(1)).title()[:50]

    out = {}
    for g in sorted(data):
        out[g] = {th: data[g][th] for th in sorted(data[g])}
    return out, theme_names


def render(data: dict, theme_names: dict) -> str:
    L = []
    L.append('"""İngilizce müfredatı — 2024 TYMM, TEMA bazlı (otomatik üretildi).')
    L.append("")
    L.append("Kaynak: knowledge_base/Ingilizce/mufredat/ingilizce_ogretim_programi_2024_TYMM.pdf")
    L.append("Üretici: scripts/derive_ingilizce_curriculum.py (deterministik, LLM'siz).")
    L.append("Kod: ENG.{sınıf}.{tema}.{beceri}{no} (L/R/S/V/G/P/W becerileri).")
    L.append("difficulty_hints: app/subjects/ingilizce/difficulty_hints.py'den gömülür.")
    L.append('"""')
    L.append("from __future__ import annotations")
    L.append("")
    L.append("from typing import NotRequired, TypedDict")
    L.append("")
    L.append("")
    L.append("class IngKazanim(TypedDict):")
    L.append("    kod: str")
    L.append("    metin: str")
    L.append("    difficulty_hints: NotRequired[dict[str, str]]")
    L.append("")
    L.append("")
    L.append("class IngUnit(TypedDict):")
    L.append("    unit_id: str")
    L.append("    grade: int")
    L.append("    no: int")
    L.append("    name: str")
    L.append("    kazanimlar: list[IngKazanim]")
    L.append("")
    L.append("")
    L.append("ING_CURRICULUM: dict[int, list[IngUnit]] = {")
    for g in sorted(data):
        L.append(f"    {g}: [")
        for th in sorted(data[g]):
            name = theme_names.get((g, th), f"Tema {th}")
            uid = f"ingilizce-{g}-tema-{th}-{slugify(name)}"
            L.append("        {")
            L.append(f'            "unit_id": {uid!r},')
            L.append(f'            "grade": {g},')
            L.append(f'            "no": {th},')
            L.append(f'            "name": {name!r},')
            L.append('            "kazanimlar": [')
            for kod, metin in data[g][th]:
                L.append(f'                {{"kod": {kod!r}, "metin": {metin!r}}},')
            L.append("            ],")
            L.append("        },")
        L.append("    ],")
    L.append("}")
    L.append("")
    L.append("")
    L.append("def get_units_for_grade(grade: int) -> list[IngUnit]:")
    L.append("    return list(ING_CURRICULUM.get(grade, []))")
    L.append("")
    L.append("")
    L.append("def get_unit(grade: int, unit_id: str) -> IngUnit | None:")
    L.append("    for u in ING_CURRICULUM.get(grade, []):")
    L.append('        if u["unit_id"] == unit_id:')
    L.append("            return u")
    L.append("    return None")
    L.append("")
    L.append("")
    L.append("def get_unit_kazanim(grade: int, unit_id: str, kazanim_kod: str) -> IngKazanim | None:")
    L.append("    unit = get_unit(grade, unit_id)")
    L.append("    if unit is None:")
    L.append("        return None")
    L.append('    for k in unit["kazanimlar"]:')
    L.append('        if k["kod"] == kazanim_kod:')
    L.append("            return k")
    L.append("    return None")
    L.append("")
    L.append("")
    L.append("def find_unit_by_kazanim(kazanim_kod: str) -> tuple[int, IngUnit] | None:")
    L.append("    for grade, units in ING_CURRICULUM.items():")
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
    data, theme_names = extract()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(data, theme_names), encoding="utf-8")
    print(f"WROTE {OUT.relative_to(ROOT)}")
    for g in sorted(data):
        nk = sum(len(v) for v in data[g].values())
        print(f"  {g}. sınıf: {len(data[g])} tema, {nk} kazanım")
    tot_t = sum(len(v) for v in data.values())
    tot_k = sum(len(ks) for v in data.values() for ks in v.values())
    print(f"  TOPLAM: {tot_t} tema, {tot_k} kazanım")


if __name__ == "__main__":
    main()
