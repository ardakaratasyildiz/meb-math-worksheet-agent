"""Türkçe müfredatını (tema + kazanım) 2024 TYMM programlarından türetir — PRAGMATİK MODEL.

⚠️ Türkçe programı fen/sosyal'den FARKLI: temiz "tema→kazanım kodu" yapısı YOK.
Program tema × beceri × metin-türü MATRİSİ + ayrıca DYS (Dil Yapıları/dil bilgisi)
alt-çıktıları biçiminde. Bu yüzden (kullanıcı onaylı Pragmatik Model A):
  - Üniteler = TEMA'lar (programdan ÇIKARILDI, gerçek).
  - Kazanımlar = sınıf düzeyi ÇEKİRDEK YETKİNLİKLER (okuma-anlama, sözcük/cümle anlam,
    yazım, noktalama, metin türü, yazma; MEB Türkçe kapsamından — kısmen ELLE) +
    DYS dil bilgisi çıktıları (programdan ÇIKARILDI: DYS.DO/KY.{sınıf}.{no}).
  - Temalar içerik bağlamı, kazanımlar sınıf-düzeyi beceri → her tema aynı sınıf
    kazanım setini paylaşır (GRADE_KAZANIMLAR referansı; duplikasyon yok).

Üretim zaten SORU TİPİ (okuma_pasaji/dil_bilgisi/yazim_noktalama/kelime_bilgisi) +
tema bağlamıyla yürür; kazanım-kodu granülasyonu Türkçe'de kaliteyi belirlemez.

Kullanım:  python scripts/derive_turkce_curriculum.py
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parent.parent
MUF = ROOT / "knowledge_base" / "Turkce" / "mufredat"
ILK = MUF / "turkce_ogretim_programi_2024_TYMM_ilkokul_1-4.pdf"
ORTA = MUF / "turkce_ogretim_programi_2024_TYMM_ortaokul_5-8.pdf"
OUT = ROOT / "app" / "subjects" / "turkce" / "curriculum.py"

_TR = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
_TR_LOWER = str.maketrans("İIÇĞÖŞÜ", "iıçğöşü")


def tr_title(s: str) -> str:
    out = []
    for w in s.split():
        wl = w.translate(_TR_LOWER).lower()
        if not wl:
            continue
        out.append({"i": "İ", "ı": "I"}.get(wl[0], wl[0].upper()) + wl[1:])
    return " ".join(out)


def slugify(s: str) -> str:
    s = s.translate(_TR).lower()
    s = re.sub(r"['’´`\"]", "", s)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:55].strip("-")


# ── ÇEKİRDEK YETKİNLİKLER (elle, MEB Türkçe kapsamı; sınıf-bandına göre) ──────
# İlkokul (1-4): temel; Ortaokul (5-8): tam (LGS). Kod: TR.{sınıf}.{BECERI}.{no}
_ILK_SKILLS = [
    ("OKA", "Okuduğu/dinlediği metnin konusunu ve ana duygusunu/ana fikrini belirler."),
    ("OKA", "Metindeki olayları oluş sırasına göre sıralar ve neden-sonuç ilişkisi kurar."),
    ("SOZ", "Bağlamdan hareketle bilmediği sözcüklerin anlamını tahmin eder; eş/zıt anlamı bulur."),
    ("YAZ", "Büyük harf ve yazım kurallarını (ör. özel ad, gün/ay) doğru uygular."),
    ("NOK", "Nokta, virgül, soru işareti gibi temel noktalama işaretlerini yerinde kullanır."),
    ("YZM", "Görsel/konu üzerine kısa, anlamlı ve düzenli bir metin yazar."),
]
_ORTA_SKILLS = [
    ("OKA", "Metnin konusunu, ana fikrini ve yardımcı fikirlerini belirler."),
    ("OKA", "Metinden hareketle çıkarımda bulunur; başlık, akış ve bölümleri yorumlar."),
    ("OKA", "Metindeki olay/bilgi akışını, neden-sonuç ve amaç-sonuç ilişkilerini çözümler."),
    ("SOZ", "Sözcüğün gerçek, mecaz, terim ve yan anlamını bağlamdan belirler."),
    ("SOZ", "Deyim, atasözü ve söz gruplarının anlamını ve metne katkısını açıklar."),
    ("CUM", "Cümlede anlam ilişkilerini (neden-sonuç, koşul, karşılaştırma, öznel-nesnel) belirler."),
    ("SAN", "Metindeki söz sanatlarını ve anlatım biçimlerini (betimleme, öyküleme vb.) belirler."),
    ("MET", "Metin türünü (öykü, şiir, deneme, haber, bilgilendirici vb.) özelliklerinden tanır."),
    ("YAZ", "Yazım kurallarını (büyük harf, birleşik/ayrı yazım, sayıların yazımı vb.) doğru uygular."),
    ("NOK", "Noktalama işaretlerini işlevine uygun ve doğru kullanır."),
    ("YZM", "Bir konuda planlı, tutarlı ve tür özelliklerine uygun bir metin/paragraf yazar."),
]


def competencies(grade: int) -> list[tuple[str, str]]:
    skills = _ILK_SKILLS if grade <= 4 else _ORTA_SKILLS
    counts: dict[str, int] = defaultdict(int)
    out = []
    for prefix, metin in skills:
        counts[prefix] += 1
        out.append((f"TR.{grade}.{prefix}.{counts[prefix]}", metin))
    return out


def _clean(t: str) -> str:
    return re.sub(r"\s+", " ", t).strip(" .:\n\t")


# Ortaokul (5-8) tema adları — programın "TEMA ADI" tablolarından çıkarıldı
# (ortaokul PDF hücreleri ayrı satırlara böldüğü için ilkokuldaki tek-satır
# regex'i yakalayamıyor; bu yüzden CURATED sabit). Ham (BÜYÜK HARF) tutulur,
# tr_title ilkokulla aynı başlık biçimine getirir. Kaynak: turkce_ogretim_
# programi_2024_TYMM_ortaokul_5-8.pdf, "TEMA ADI" tabloları + tema başlıkları.
_ORTA_THEMES: dict[int, list[str]] = {
    5: [
        "OYUN DÜNYASI",
        "ATATÜRK’Ü TANIMAK",
        "DUYGULARIMI TANIYORUM",
        "GELENEKLERİMİZ",
        "İLETİŞİM VE SOSYAL İLİŞKİLER",
        "SAĞLIKLI YAŞIYORUM",
    ],
    6: [
        "DİLİMİZİN ZENGİNLİĞİ",
        "BAĞIMSIZLIK YOLU",
        "FARKLI DÜNYALAR",
        "İLETİŞİM VE SOSYAL İLİŞKİLER",
        "BİLİM VE TEKNOLOJİ",
        "LİDER RUHLAR",
    ],
    7: [
        "HAYAT BOYU GELİŞİM",
        "BİR HİLAL UĞRUNA",
        "İLETİŞİM VE SOSYAL İLİŞKİLER",
        "TÜRK SANATI",
        "OKUMA KÜLTÜRÜ",
        "HAK VE SORUMLULUKLAR",
    ],
    8: [
        "İLETİŞİM VE SOSYAL İLİŞKİLER",
        "VATAN SEVGİSİ",
        "DOĞA VE İNSAN",
        "TÜRK HİKÂYE GELENEĞİ VE DESTANLARI",
        "SANAT VE ESTETİK",
        "AKADEMİK DÜŞÜNME DÜNYASI",
    ],
}


def extract_themes() -> dict[int, list[tuple[int, str]]]:
    """grade -> [(no, ad)] temalar. İlkokul (1-4) PDF'ten; ortaokul (5-8) curated."""
    themes: dict[int, dict[int, str]] = defaultdict(dict)
    hdr = re.compile(r"(\d{1,2})\.\s*TEMA\s*:?\s*([^\n]{0,50})")
    ghdr = re.compile(r"\b([1-8])\.\s*SINIF\b")
    for pdf in (ILK, ORTA):
        doc = fitz.open(pdf)
        cur = None
        for line in "\n".join(p.get_text("text") for p in doc).splitlines():
            gm = ghdr.search(line)
            if gm:
                cur = int(gm.group(1))
            hm = hdr.search(line)
            if hm and cur is not None:
                no = int(hm.group(1))
                name = _clean(hm.group(2))
                if no not in themes[cur]:
                    themes[cur][no] = tr_title(name) if len(name) >= 3 else f"{no}. Tema"
    # Ortaokul tema adlarını curated (gerçek) adlarla ez — regex ortaokulu yakalayamıyor.
    for g, names in _ORTA_THEMES.items():
        themes[g] = {i + 1: tr_title(n) for i, n in enumerate(names)}
    return {g: [(no, themes[g][no]) for no in sorted(themes[g])] for g in sorted(themes)}


def extract_dilbilgisi() -> dict[int, list[tuple[str, str]]]:
    """grade -> [(kod, metin)] DYS (dil bilgisi) çıktıları — programdan çıkarıldı."""
    data: dict[int, list[tuple[str, str]]] = defaultdict(list)
    seen = set()
    doc = fitz.open(ORTA)
    t = "\n".join(p.get_text("text") for p in doc).replace("\xad\n", "").replace("\xad", "")
    tt = t.replace("\n", " \n ")
    code_re = re.compile(r"DYS\.(DO|KY)\.(\d)\.(\d{1,2})\.")
    matches = list(code_re.finditer(tt))
    for i, m in enumerate(matches):
        g = int(m.group(2))
        code = f"DYS.{m.group(1)}.{g}.{m.group(3)}"
        end = matches[i + 1].start() if i + 1 < len(matches) else len(tt)
        metin = _clean(tt[m.end():end])
        if not metin or len(metin) < 6 or code in seen:
            continue
        if len(metin) > 160:
            metin = metin[:157].rsplit(" ", 1)[0] + "…"
        seen.add(code)
        data[g].append((code, metin))
    return data


def render(themes, dilbilgisi) -> str:
    grades = sorted(set(themes) | set(range(1, 9)))
    L = []
    L.append('"""Türkçe müfredatı — 2024 TYMM, PRAGMATİK MODEL (yarı-otomatik).')
    L.append("")
    L.append("Üniteler = TEMA'lar (programdan çıkarıldı). Kazanımlar = sınıf düzeyi çekirdek")
    L.append("yetkinlikler (okuma-anlama/sözcük/cümle/yazım/noktalama/metin/yazma — kısmen elle)")
    L.append("+ DYS dil bilgisi (programdan çıkarıldı). Her tema sınıfın kazanım setini paylaşır")
    L.append("(GRADE_KAZANIMLAR referansı). Bkz. scripts/derive_turkce_curriculum.py, SOZEL_DERSLER_PLAN.md.")
    L.append('"""')
    L.append("from __future__ import annotations")
    L.append("")
    L.append("from typing import NotRequired, TypedDict")
    L.append("")
    L.append("")
    L.append("class TrKazanim(TypedDict):")
    L.append("    kod: str")
    L.append("    metin: str")
    L.append("    difficulty_hints: NotRequired[dict[str, str]]")
    L.append("")
    L.append("")
    L.append("class TrUnit(TypedDict):")
    L.append("    unit_id: str")
    L.append("    grade: int")
    L.append("    no: int")
    L.append("    name: str")
    L.append("    kazanimlar: list[TrKazanim]")
    L.append("")
    L.append("")
    # Sınıf düzeyi kazanım setleri
    L.append("GRADE_KAZANIMLAR: dict[int, list[TrKazanim]] = {")
    for g in grades:
        kz = competencies(g) + dilbilgisi.get(g, [])
        L.append(f"    {g}: [")
        for kod, metin in kz:
            L.append(f'        {{"kod": {kod!r}, "metin": {metin!r}}},')
        L.append("    ],")
    L.append("}")
    L.append("")
    # Temalar (kazanımsız; get_unit runtime'da GRADE_KAZANIMLAR ekler)
    L.append("_THEMES: dict[int, list[dict]] = {")
    for g in grades:
        L.append(f"    {g}: [")
        for no, name in themes.get(g, []):
            uid = f"turkce-{g}-tema-{no}-{slugify(name)}"
            L.append(f'        {{"unit_id": {uid!r}, "grade": {g}, "no": {no}, "name": {name!r}}},')
        L.append("    ],")
    L.append("}")
    L.append("")
    L.append("")
    L.append("def _with_kazanimlar(theme: dict) -> TrUnit:")
    L.append('    return {**theme, "kazanimlar": GRADE_KAZANIMLAR.get(theme["grade"], [])}  # type: ignore[return-value]')
    L.append("")
    L.append("")
    L.append("TURKCE_CURRICULUM: dict[int, list[TrUnit]] = {")
    L.append("    g: [_with_kazanimlar(t) for t in ts] for g, ts in _THEMES.items()")
    L.append("}")
    L.append("")
    L.append("")
    L.append("def get_units_for_grade(grade: int) -> list[TrUnit]:")
    L.append("    return list(TURKCE_CURRICULUM.get(grade, []))")
    L.append("")
    L.append("")
    L.append("def get_unit(grade: int, unit_id: str) -> TrUnit | None:")
    L.append("    for u in TURKCE_CURRICULUM.get(grade, []):")
    L.append('        if u["unit_id"] == unit_id:')
    L.append("            return u")
    L.append("    return None")
    L.append("")
    L.append("")
    L.append("def get_unit_kazanim(grade: int, unit_id: str, kazanim_kod: str) -> TrKazanim | None:")
    L.append("    for k in GRADE_KAZANIMLAR.get(grade, []):")
    L.append('        if k["kod"] == kazanim_kod:')
    L.append("            return k")
    L.append("    return None")
    L.append("")
    L.append("")
    L.append("def find_unit_by_kazanim(kazanim_kod: str) -> tuple[int, TrUnit] | None:")
    L.append("    # Kazanım sınıf-düzeyi (temaya bağlı değil) → sınıfın ilk teması döner.")
    L.append("    for grade, kzs in GRADE_KAZANIMLAR.items():")
    L.append('        if any(k["kod"] == kazanim_kod for k in kzs):')
    L.append("            units = get_units_for_grade(grade)")
    L.append("            if units:")
    L.append("                return grade, units[0]")
    L.append("    return None")
    L.append("")
    L.append("")
    L.append("def is_unit_available(grade: int, unit_id: str) -> bool:")
    L.append("    return get_unit(grade, unit_id) is not None")
    L.append("")
    return "\n".join(L)


def main() -> None:
    themes = extract_themes()
    dilbilgisi = extract_dilbilgisi()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(themes, dilbilgisi), encoding="utf-8")
    print(f"WROTE {OUT.relative_to(ROOT)}")
    for g in sorted(set(themes) | set(range(1, 9))):
        nt = len(themes.get(g, []))
        nk = len(competencies(g)) + len(dilbilgisi.get(g, []))
        print(f"  {g}. sınıf: {nt} tema, {nk} kazanım ({len(dilbilgisi.get(g, []))} dil bilgisi çıkarıldı)")


if __name__ == "__main__":
    main()
