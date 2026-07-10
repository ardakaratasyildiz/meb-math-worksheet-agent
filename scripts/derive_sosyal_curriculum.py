"""Sosyal Bilgiler müfredatını (ünite + kazanım) 2024 TYMM programlarından türetir.

Tek `sosyal` dersi, 3 programı birleştirir (sınıf koddan gelir):
- Hayat Bilgisi (HB.{sınıf}.{ünite}.{no})     — 1-3. sınıf
- Sosyal Bilgiler (SB.{sınıf}.{ünite}.{no})    — 4-7. sınıf
- T.C. İnkılap Tarihi (İTA.{sınıf}.{ünite}.{no}) — 8. sınıf (LGS)

Ünite adı: "N. ÜNİTE: AD" (İnkılap) veya "N. ÖĞRENME ALANI: AD" (Sosyal Bilgiler);
bulunamazsa "Ünite N". Deterministik PyMuPDF, LLM'siz.
Kullanım:  python scripts/derive_sosyal_curriculum.py
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parent.parent
MUF = ROOT / "knowledge_base" / "Sosyal" / "mufredat"
SOURCES = [
    MUF / "hayat_bilgisi_ogretim_programi_2024_TYMM.pdf",
    MUF / "sosyal_bilgiler_ogretim_programi_2024_TYMM.pdf",
    MUF / "inkilap_tarihi_ogretim_programi_2024_TYMM.pdf",
]
OUT = ROOT / "app" / "subjects" / "sosyal" / "curriculum.py"

_TR = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
# İ (U+0130) dahil kapsamlı kod prefix'i; TA → İTA normalize edilir.
_CODE = re.compile(r"\b(HB|SB|İTA|TA)\.(\d)\.(\d{1,2})\.(\d{1,2})\b")
_UNIT_HDR = re.compile(r"(\d{1,2})\.\s*(?:ÜNİTE|ÖĞRENME ALANI)\s*:?\s*([^\n]{3,60})")
_GRADE_HDR = re.compile(r"\b([1-8])\.\s*SINIF\b")


_TR_LOWER = str.maketrans("İIÇĞÖŞÜ", "iıçğöşü")


def tr_title(s: str) -> str:
    """Türkçe-güvenli başlık: İ→i, I→ı (combining-dot artığı olmadan)."""
    out = []
    for w in s.split():
        wl = w.translate(_TR_LOWER).lower()
        if not wl:
            continue
        c0 = {"i": "İ", "ı": "I"}.get(wl[0], wl[0].upper())
        out.append(c0 + wl[1:])
    return " ".join(out)


def slugify(s: str) -> str:
    s = s.translate(_TR).lower()
    s = re.sub(r"['’´`\"]", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:55].strip("-")


def _clean(t: str) -> str:
    return re.sub(r"\s+", " ", t).strip(" .:\n\t")


def extract() -> tuple[dict, dict]:
    data = defaultdict(lambda: defaultdict(list))   # grade -> unit -> [(kod, metin)]
    names: dict = {}                                # (grade, unit) -> ad
    seen = set()
    for pdf in SOURCES:
        doc = fitz.open(pdf)
        raw = "\n".join(pg.get_text("text") for pg in doc)
        t = raw.replace("\xad\n", "").replace("\xad", "")
        # 1) ünite adları — grade context'iyle (N. SINIF ile takip)
        cur_grade = None
        for line in t.splitlines():
            gm = _GRADE_HDR.search(line)
            if gm:
                cur_grade = int(gm.group(1))
            hm = _UNIT_HDR.search(line)
            if hm and cur_grade is not None:
                key = (cur_grade, int(hm.group(1)))
                if key not in names:
                    names[key] = tr_title(_clean(hm.group(2)))
        # 2) kazanım kodları + metin
        tt = t.replace("\n", " \n ")
        matches = list(_CODE.finditer(tt))
        for i, m in enumerate(matches):
            # Yalnız ÖĞRENME ÇIKTISI TANIMI ("CODE. <çıktı>") — kodun ardından "."
            # gelmeli. Beceri/çapraz-referans tabloları koda "(CODE)" biçiminde
            # atıfta bulunur (ardından ")"); bunlar atlanır → çöp metin engellenir.
            after = tt[m.end():]
            if not after.startswith("."):
                continue
            prefix = "İTA" if m.group(1) in ("TA", "İTA") else m.group(1)
            g, u, no = int(m.group(2)), int(m.group(3)), m.group(4)
            code = f"{prefix}.{g}.{u}.{no}"
            end = matches[i + 1].start() if i + 1 < len(matches) else len(tt)
            metin = _clean(re.split(r"\s+a\)\s", after[1:end - m.end()], maxsplit=1)[0])
            if not metin or len(metin) < 8:
                continue
            if len(metin) > 220:
                metin = metin[:217].rsplit(" ", 1)[0] + "…"
            if code in seen:
                continue
            seen.add(code)
            data[g][u].append((code, metin))
    out = {g: {u: data[g][u] for u in sorted(data[g])} for g in sorted(data)}
    return out, names


def render(data: dict, names: dict) -> str:
    L = []
    L.append('"""Sosyal Bilgiler müfredatı — 2024 TYMM (Hayat Bilgisi 1-3 + Sosyal Bilgiler')
    L.append('4-7 + İnkılap Tarihi 8), ünite bazlı (otomatik üretildi).')
    L.append("")
    L.append("Kaynak: knowledge_base/Sosyal/mufredat/*_2024_TYMM.pdf")
    L.append("Üretici: scripts/derive_sosyal_curriculum.py (deterministik, LLM'siz).")
    L.append("Kod: HB/SB/İTA.{sınıf}.{ünite}.{no}. difficulty_hints difficulty_hints.py'den gömülür.")
    L.append('"""')
    L.append("from __future__ import annotations")
    L.append("")
    L.append("from typing import NotRequired, TypedDict")
    L.append("")
    L.append("")
    L.append("class SosKazanim(TypedDict):")
    L.append("    kod: str")
    L.append("    metin: str")
    L.append("    difficulty_hints: NotRequired[dict[str, str]]")
    L.append("")
    L.append("")
    L.append("class SosUnit(TypedDict):")
    L.append("    unit_id: str")
    L.append("    grade: int")
    L.append("    no: int")
    L.append("    name: str")
    L.append("    kazanimlar: list[SosKazanim]")
    L.append("")
    L.append("")
    L.append("SOS_CURRICULUM: dict[int, list[SosUnit]] = {")
    for g in sorted(data):
        L.append(f"    {g}: [")
        for u in sorted(data[g]):
            name = names.get((g, u), f"Ünite {u}")
            uid = f"sosyal-{g}-unite-{u}-{slugify(name)}"
            L.append("        {")
            L.append(f'            "unit_id": {uid!r},')
            L.append(f'            "grade": {g},')
            L.append(f'            "no": {u},')
            L.append(f'            "name": {name!r},')
            L.append('            "kazanimlar": [')
            for kod, metin in data[g][u]:
                L.append(f'                {{"kod": {kod!r}, "metin": {metin!r}}},')
            L.append("            ],")
            L.append("        },")
        L.append("    ],")
    L.append("}")
    L.append("")
    L.append("")
    L.append("def get_units_for_grade(grade: int) -> list[SosUnit]:")
    L.append("    return list(SOS_CURRICULUM.get(grade, []))")
    L.append("")
    L.append("")
    L.append("def get_unit(grade: int, unit_id: str) -> SosUnit | None:")
    L.append("    for u in SOS_CURRICULUM.get(grade, []):")
    L.append('        if u["unit_id"] == unit_id:')
    L.append("            return u")
    L.append("    return None")
    L.append("")
    L.append("")
    L.append("def get_unit_kazanim(grade: int, unit_id: str, kazanim_kod: str) -> SosKazanim | None:")
    L.append("    unit = get_unit(grade, unit_id)")
    L.append("    if unit is None:")
    L.append("        return None")
    L.append('    for k in unit["kazanimlar"]:')
    L.append('        if k["kod"] == kazanim_kod:')
    L.append("            return k")
    L.append("    return None")
    L.append("")
    L.append("")
    L.append("def find_unit_by_kazanim(kazanim_kod: str) -> tuple[int, SosUnit] | None:")
    L.append("    for grade, units in SOS_CURRICULUM.items():")
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
    data, names = extract()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(data, names), encoding="utf-8")
    print(f"WROTE {OUT.relative_to(ROOT)}")
    for g in sorted(data):
        nk = sum(len(v) for v in data[g].values())
        named = sum(1 for u in data[g] if (g, u) in names)
        print(f"  {g}. sınıf: {len(data[g])} ünite ({named} adlı), {nk} kazanım")
    print(f"  TOPLAM: {sum(len(v) for v in data.values())} ünite, "
          f"{sum(len(k) for v in data.values() for k in v.values())} kazanım")


if __name__ == "__main__":
    main()
