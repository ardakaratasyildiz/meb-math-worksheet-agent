"""Kalite terazisi — BOZUK SET üreticileri (docs/COST_QUALITY_V2_PLAN.md §2b).

Altın sorulardan KOD İLE üretilen mutasyonlar: ground truth kesin (hangi kusuru
enjekte ettiğimizi biliyoruz), tekrar üretilebilir, elle etiketleme gerekmez.
Kusur tipleri GERÇEK arızalardan alınmıştır (commit referansları aşağıda).

Her mutasyon fonksiyonu DETERMİNİSTİKTİR: sabit RNG_SEED + gold_id'ye göre
sıralı seçim → aynı gold_questions.json'dan her koşuda AYNI broken_questions.json.

`should_be_caught_by` alanı bir HİPOTEZ etiketidir (bu görevi yazan kişinin "hangi
katman yakalamalı" beklentisi) — quality_bench.py'nin GERÇEKTEN neyi yakaladığıyla
karşılaştırılır. İkisinin uyuşmaması (ör. "deterministic" etiketli ama hiçbir
deterministik doğrulayıcı yakalamıyor) BİZZAT terazinin ortaya çıkarması gereken
bir "kör nokta" bulgusudur — bug değildir.

Kullanım:
    python scripts/eval/mutations.py [--gold PATH] [--out PATH]
"""
from __future__ import annotations

import argparse
import copy
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from app.data.curriculum import get_topics_for_grade  # noqa: E402
from app.models.enums import SubjectId  # noqa: E402
from app.subjects import get_content_module  # noqa: E402

RNG_SEED = 20260728
DEFAULT_GOLD = ROOT / "knowledge_base" / "eval" / "gold" / "gold_questions.json"
DEFAULT_OUT = ROOT / "knowledge_base" / "eval" / "gold" / "broken_questions.json"

# Ders başına GEÇERLİ ama İLGİSİZ bir kazanım kodu (kazanim_mismatch mutasyonu için).
# Her biri app/data/curriculum.py veya app/subjects/<ders>/curriculum.py'de GERÇEKTEN
# var (find_unit_by_kazanim / get_topics_for_grade ile doğrulandı) — sözdizimsel değil
# ANLAMSAL bir uyumsuzluk (örn. matematik sorusuna Türkçe söz-sanatı kazanımı).
_FOREIGN_KAZANIM: dict[str, str] = {
    "matematik": "TR.8.SAN.1",
    "turkce": "SB.5.1.1",
    "sosyal": "ENG.5.1.G1",
    "ingilizce": "FB.8.3.3.2",
    "fen": "M.5.1.1",
}

_CEVAP_LETTER_RE = re.compile(r"(cevap|answer)(\s*[:\-]?\s*)([A-D])\b", re.IGNORECASE)
_LAST_NUMBER_RE = re.compile(r"(\d+)(?!.*\d)", re.DOTALL)


def _rng(tag: str) -> random.Random:
    return random.Random(f"{RNG_SEED}:{tag}")


def _pick(gold: list[dict], predicate, n: int, tag: str) -> list[dict]:
    """Deterministik seçim: predicate'e uyanları gold_id'ye göre sırala, seed'li
    karıştır, ilk n'i al (n'den az varsa hepsini döner)."""
    pool = sorted((q for q in gold if predicate(q)), key=lambda q: q["gold_id"])
    _rng(tag).shuffle(pool)
    return pool[:n]


def _base(
    gold_q: dict,
    defect_type: str,
    should_be_caught_by: str,
    synthesized: bool,
    production_possible: bool = True,
) -> dict:
    """Kaydın kopyasını + mutasyon meta alanlarını hazırlar (henüz question/answer
    alanları bozulmamış — her mutator kendi alanlarını üzerine yazar).

    `production_possible=False`: bu kusur agent.py'nin bugünkü akışında ASLA
    üretilemez (yalnız referans/karşılaştırma amaçlı) — bkz. §3g-1b
    (kazanim_mismatch_cross_subject, agent.py:1758 fallback'i tarafından elenir).
    """
    rec = copy.deepcopy(gold_q)
    rec["defect_type"] = defect_type
    rec["source_gold_id"] = gold_q["gold_id"]
    rec["should_be_caught_by"] = should_be_caught_by
    rec["synthesized"] = synthesized
    rec["production_possible"] = production_possible
    rec.pop("gold_id", None)
    return rec


def _sibling_kazanim_pool(subject: str, grade: int, kazanim_kod: str) -> tuple[list[str], bool] | None:
    """`kazanim_kod`'un ait olduğu ünitenin/konunun DİĞER geçerli kodlarını döner
    — bu, agent.py'de tek bir üretim isteğinin `kazanimlar` listesinde GERÇEKTEN
    bulunabilecek kodlardır (§3g-1b: gerçekçi `kazanim_mismatch`, üretimde mümkün
    olan TEK senaryo). Ünitede/konuda başka kod yoksa aynı sınıfın BAŞKA bir
    ünitesinden/konusundan alınır (`same_unit=False`). Hiçbir yerde bulunamazsa
    None (çağıran o gold kaydını atlar).

    Dönüş: (kod_listesi_sıralı, same_unit) | None.
    """
    if subject == "matematik":
        topics = get_topics_for_grade(grade)
        own_topic = None
        for topic in topics:
            if any(k["kod"] == kazanim_kod for k in topic["kazanimlar"]):
                own_topic = topic
                break
        if own_topic is None:
            return None
        own_codes = sorted(k["kod"] for k in own_topic["kazanimlar"] if k["kod"] != kazanim_kod)
        if own_codes:
            return own_codes, True
        for topic in topics:
            if topic is own_topic:
                continue
            other_codes = sorted(k["kod"] for k in topic["kazanimlar"])
            if other_codes:
                return other_codes, False
        return None

    try:
        content = get_content_module(SubjectId(subject))
    except ValueError:
        return None
    if content is None:
        return None
    found = content.find_unit_by_kazanim(kazanim_kod)
    if found is None:
        return None
    grade_found, unit = found
    own_codes = sorted(k["kod"] for k in unit["kazanimlar"] if k["kod"] != kazanim_kod)
    if own_codes:
        return own_codes, True
    for u in content.get_units_for_grade(grade_found):
        if u["unit_id"] == unit["unit_id"]:
            continue
        other_codes = sorted(k["kod"] for k in u["kazanimlar"])
        if other_codes:
            return other_codes, False
    return None


# ── 1) empty_matching_body (det.) — commit ee86598 ───────────────────────────
# Eşleştirme/sıralama sorusu yönergeyi basar ama öğe/şık listesini SİLER.
# Dil-bağımsız (TR/EN her ikisinde de çalışır): "öğe" satırları YAPISAL olarak
# (satır başında Roma rakamı/numara) tanınır, anahtar kelime aranmaz.

_ITEM_LINE_RE = re.compile(
    r"^\s*(?:(?:I{1,3}|IV|V)|[1-9])\s*[.\)]\s*\S|^\s*[•\-\*]\s+\S", re.IGNORECASE
)
_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")

_SYNTHETIC_MATCHING_TEMPLATE = (
    "Aşağıdaki kavramları açıklamalarıyla eşleştiriniz."
)


def _strip_enum_item_lines(text: str) -> str:
    """Satır-bazlı: numaralı/Roma öğe satırlarını (ve GFM tablo satırlarını)
    SİLER, geri kalan metni (yönerge + varsa şık/soru kısmı) korur."""
    kept = [
        line for line in text.split("\n")
        if not _ITEM_LINE_RE.match(line) and not _TABLE_ROW_RE.match(line)
    ]
    return "\n".join(kept).strip()


def mutate_empty_matching_body(gold: list[dict]) -> list[dict]:
    candidates = _pick(
        gold,
        lambda q: q["question_type"] in ("eslestirme", "siralama"),
        5,
        "empty_matching_body",
    )
    out: list[dict] = []
    for q in candidates:
        rec = _base(q, "empty_matching_body", "deterministic", synthesized=False)
        stripped = _strip_enum_item_lines(q["question"])
        assert stripped != q["question"], f"öğe satırı bulunamadı: {q['gold_id']}"
        rec["question"] = stripped
        rec["options"] = None
        rec["correct_index"] = None
        out.append(rec)

    # Altın havuzda yeterli gerçek örnek yoksa (<5), gold içerikten KURULMUŞ
    # (synthesized=True) ek örneklerle tamamla — yalnız yönerge, öğe/şık YOK.
    missing = 5 - len(out)
    if missing > 0:
        donors = _pick(gold, lambda q: q["question_type"] == "kelime_bilgisi", missing,
                        "empty_matching_body_synth")
        if not donors:
            donors = _pick(gold, lambda q: True, missing, "empty_matching_body_synth_fallback")
        for donor in donors:
            rec = _base(donor, "empty_matching_body", "deterministic", synthesized=True)
            rec["question"] = _SYNTHETIC_MATCHING_TEMPLATE
            rec["question_type"] = "eslestirme"
            rec["options"] = None
            rec["correct_index"] = None
            out.append(rec)
    return out[:5]


# ── 2) inline_duplicated_options (det.) — commit 417d639 ─────────────────────
# Şıklar hem stem metnine hem `.options`'a yazılı → çift görünüm (PDF'te run-on).

def mutate_inline_duplicated_options(gold: list[dict]) -> list[dict]:
    candidates = _pick(
        gold,
        lambda q: q["question_type"] == "coktan_secmeli" and q["options"] and len(q["options"]) >= 2,
        5,
        "inline_duplicated_options",
    )
    out: list[dict] = []
    for q in candidates:
        rec = _base(q, "inline_duplicated_options", "deterministic", synthesized=False)
        letters = "ABCDEFGH"
        dup_block = " ".join(
            f"{letters[i]}) {opt}" for i, opt in enumerate(q["options"])
        )
        # Şıkları STEM'E YENİDEN yazıyoruz (zaten .options'ta var) → çift görünüm.
        rec["question"] = q["question"].rstrip() + "\n" + dup_block
        out.append(rec)
    return out


# ── 3) wrong_answer_key (critic) — genel güven riski ─────────────────────────
# MCQ: correct_index'i BAŞKA bir şıkka kaydır (answer+correct_index tutarlı ama
# YANLIŞ). Numeric: cevabı +1 kaydır.

def mutate_wrong_answer_key(gold: list[dict]) -> list[dict]:
    out: list[dict] = []

    mcq_candidates = _pick(
        gold,
        lambda q: q["options"] and q["correct_index"] is not None and len(q["options"]) >= 2,
        3,
        "wrong_answer_key_mcq",
    )
    for q in mcq_candidates:
        rec = _base(q, "wrong_answer_key", "critic", synthesized=False)
        n = len(q["options"])
        new_idx = (q["correct_index"] + 1) % n
        assert new_idx != q["correct_index"]
        rec["correct_index"] = new_idx
        new_letter = "ABCD"[new_idx] if new_idx < 4 else chr(ord("A") + new_idx)
        # answer'ı DAİMA yeni şıkkın gerçek metninden kur (eski harf/metin karışımı
        # bırakılırsa answer+correct_index TUTARSIZ olur — plan "tutarlı ama YANLIŞ"
        # istiyor, "tutarsız" değil).
        rec["answer"] = f"{new_letter}) {q['options'][new_idx]}"
        assert rec["answer"] != q["answer"]
        out.append(rec)

    numeric_candidates = _pick(
        gold,
        lambda q: re.match(r"^-?\d+(\.\d+)?$", (q["answer"] or "").strip()) is not None,
        2,
        "wrong_answer_key_numeric",
    )
    for q in numeric_candidates:
        rec = _base(q, "wrong_answer_key", "critic", synthesized=False)
        old_val = q["answer"].strip()
        try:
            new_val = str(int(old_val) + 1) if "." not in old_val else str(float(old_val) + 1)
        except ValueError:
            continue
        assert new_val != old_val
        rec["answer"] = new_val
        out.append(rec)
    return out


# ── 4) solution_contradicts_answer (critic) — critic'in 1. görevi ────────────
# Çözüm adımlarındaki SONUCU değiştir, `answer`'ı OLDUĞU GİBİ bırak.

def mutate_solution_contradicts_answer(gold: list[dict]) -> list[dict]:
    with_letter = _pick(
        gold,
        lambda q: bool(_CEVAP_LETTER_RE.search(q["solution_steps"] or "")),
        3,
        "solution_contradicts_answer_letter",
    )
    with_number = _pick(
        gold,
        lambda q: (
            not _CEVAP_LETTER_RE.search(q["solution_steps"] or "")
            and bool(_LAST_NUMBER_RE.search(q["solution_steps"] or ""))
        ),
        2,
        "solution_contradicts_answer_number",
    )
    out: list[dict] = []
    for q in with_letter:
        rec = _base(q, "solution_contradicts_answer", "critic", synthesized=False)

        def _flip(m: re.Match) -> str:
            cur = m.group(3).upper()
            alt = "ABCD".replace(cur, "")[0]
            return f"{m.group(1)}{m.group(2)}{alt}"

        new_sol, n = _CEVAP_LETTER_RE.subn(_flip, q["solution_steps"], count=1)
        assert n == 1 and new_sol != q["solution_steps"]
        rec["solution_steps"] = new_sol
        out.append(rec)
    for q in with_number:
        rec = _base(q, "solution_contradicts_answer", "critic", synthesized=False)
        sol = q["solution_steps"]
        m = _LAST_NUMBER_RE.search(sol)
        assert m is not None
        old_num = m.group(1)
        new_num = str(int(old_num) + 3)
        new_sol = sol[: m.start(1)] + new_num + sol[m.end(1):]
        assert new_sol != sol
        rec["solution_steps"] = new_sol
        out.append(rec)
    return out


# ── 5a) kazanim_mismatch (critic) — GERÇEKÇİ, §3g-1b ─────────────────────────
# ÖN BULGU (docs/COST_QUALITY_V2_PLAN.md §3g-0): agent.py:1758
#   `kod = raw.kazanim_kod if raw.kazanim_kod in valid_kazanim_codes else fallback_kazanim`
# GEÇERSİZ (istek listesinde olmayan) bir kod asla hayatta kalmaz — sessizce
# `kazanimlar[0]`'a çevrilir. Yani "başka bir DERSTEN kod" senaryosu üretimde
# İMKÂNSIZ (bkz. aşağıdaki `kazanim_mismatch_cross_subject`, yalnız referans).
# Üretimde mümkün olan TEK senaryo: kodu AYNI isteğin GEÇERLİ kazanım
# listesinden BAŞKA (ama içerikle örtüşmeyen) bir kodla değiştirmek — bu,
# critic'i gerçek işe zorlar (kod-üyeliği değil, metin-içerik uyumu).

def mutate_kazanim_mismatch(gold: list[dict]) -> list[dict]:
    pool = sorted(gold, key=lambda q: q["gold_id"])
    _rng("kazanim_mismatch").shuffle(pool)
    out: list[dict] = []
    for q in pool:
        sib = _sibling_kazanim_pool(q["subject"], q["grade"], q["kazanim_kod"])
        if sib is None:
            continue
        codes, same_unit = sib
        chosen = _rng(f"kazanim_mismatch:{q['gold_id']}").choice(codes)
        assert chosen != q["kazanim_kod"]
        rec = _base(q, "kazanim_mismatch", "critic", synthesized=False)
        rec["kazanim_kod"] = chosen
        rec["same_unit"] = same_unit
        out.append(rec)
        if len(out) >= 15:
            break
    return out


# ── 5b) kazanim_mismatch_cross_subject (referans — ÜRETİMDE İMKÂNSIZ) ───────
# Eski mutasyon: kazanim_kod'u BAŞKA bir dersin GEÇERLİ ama anlamsal olarak
# ilgisiz koduyla değiştirir. `production_possible=False` — agent.py:1758'in
# fallback'i bu kodu geçersiz sayıp `kazanimlar[0]`'a çevirir, yani bu kusur
# canlıda hiç ortaya ÇIKAMAZ. Yalnız karşılaştırma değeri için tutuluyor
# (terazinin "kolay ama sahte" hedefe kıyasla ne kadar farklı ölçtüğünü görmek).

def mutate_kazanim_mismatch_cross_subject(gold: list[dict]) -> list[dict]:
    candidates = _pick(gold, lambda q: True, 5, "kazanim_mismatch_cross_subject")
    out: list[dict] = []
    for q in candidates:
        rec = _base(
            q, "kazanim_mismatch_cross_subject", "critic", synthesized=False,
            production_possible=False,
        )
        foreign = _FOREIGN_KAZANIM[q["subject"]]
        assert foreign != q["kazanim_kod"]
        rec["kazanim_kod"] = foreign
        out.append(rec)
    return out


# ── 5c) kazanim_silent_repair (critic) — agent.py:1758'in BİREBİR taklidi ────
# İçerik kazanım A'ya AİT KALIR; yalnız ETİKET (kazanim_kod), o isteğin GERÇEK
# kazanım listesindeki İLK kod (`kazanimlar[0]` — agent.py'deki `fallback_kazanim`)
# olacak biçimde geçerli-ama-yanlış B'ye çevrilir. Fark 5a'dan (rastgele geçerli
# kod, genel "model yanlış kod üretti" senaryosu) ŞUDUR: burada seçim rastgele
# DEĞİL, sistemin SESSİZ ONARIM mekanizmasının GERÇEKTEN üreteceği kod —
# "model kodu bilemedi, sistem ilk kazanımı yapıştırdı" senaryosu.

def mutate_kazanim_silent_repair(gold: list[dict]) -> list[dict]:
    pool = sorted(gold, key=lambda q: q["gold_id"])
    _rng("kazanim_silent_repair").shuffle(pool)
    out: list[dict] = []
    for q in pool:
        sib = _sibling_kazanim_pool(q["subject"], q["grade"], q["kazanim_kod"])
        if sib is None:
            continue
        codes, same_unit = sib
        fallback_kod = codes[0]  # kazanimlar[0] taklidi — sıralı liste, deterministik.
        assert fallback_kod != q["kazanim_kod"]
        rec = _base(q, "kazanim_silent_repair", "critic", synthesized=False)
        rec["kazanim_kod"] = fallback_kod
        rec["same_unit"] = same_unit
        out.append(rec)
        if len(out) >= 15:
            break
    return out


# ── 6) difficulty_mismatch (critic) — critic'in 4. görevi ────────────────────
# `difficulty="kolay"` + tek-adımlı (kısa çözüm) soruyu `zor` etiketle.

def mutate_difficulty_mismatch(gold: list[dict]) -> list[dict]:
    candidates = sorted(
        (q for q in gold if q["difficulty"] == "kolay"),
        key=lambda q: (len(q["solution_steps"] or ""), q["gold_id"]),
    )
    _rng("difficulty_mismatch_tiebreak").shuffle(candidates)
    # En kısa çözümlü (= en "tek adımlık") ilk 5 → gerçekten kolay olanlar.
    candidates = sorted(candidates, key=lambda q: len(q["solution_steps"] or ""))[:5]
    out: list[dict] = []
    for q in candidates:
        rec = _base(q, "difficulty_mismatch", "critic", synthesized=False)
        assert q["difficulty"] == "kolay"
        rec["difficulty"] = "zor"
        out.append(rec)
    return out


# ── 7) truncated_stem (det.) — format-drop belirtisi ─────────────────────────
# Gövdeyi ~%60'ında, cümle ortasında kes.

def mutate_truncated_stem(gold: list[dict]) -> list[dict]:
    # Öncelik: eşleştirme/sıralama/atıflı sorular (kesilince deterministik
    # doğrulayıcılara da çarpma ihtimali daha yüksek — gerçekçi format-drop).
    preferred = _pick(
        gold,
        lambda q: q["question_type"] in ("eslestirme", "siralama", "tablo_sorusu", "grafik_okuma"),
        3,
        "truncated_stem_preferred",
    )
    rest = _pick(
        gold,
        lambda q: q["question_type"] not in ("eslestirme", "siralama", "tablo_sorusu", "grafik_okuma"),
        5 - len(preferred),
        "truncated_stem_rest",
    )
    out: list[dict] = []
    for q in preferred + rest:
        rec = _base(q, "truncated_stem", "deterministic", synthesized=False)
        text = q["question"]
        cut_at = max(20, int(len(text) * 0.6))
        rec["question"] = text[:cut_at]
        assert len(rec["question"]) < len(text)
        out.append(rec)
    return out


# ── 8) dangling_reference (det.) — reference_integrity_issue alanı ───────────
# Başına "Yukarıdaki tabloya göre," ekle; metinde GERÇEK tablo/svg/chart OLMASIN.

def mutate_dangling_reference(gold: list[dict]) -> list[dict]:
    def _no_visual(q: dict) -> bool:
        low = q["question"].lower()
        return "<svg" not in low and "{{chart" not in low and "|" not in q["question"]

    candidates = _pick(gold, _no_visual, 5, "dangling_reference")
    out: list[dict] = []
    for q in candidates:
        rec = _base(q, "dangling_reference", "deterministic", synthesized=False)
        rec["question"] = "Yukarıdaki tabloya göre, " + q["question"]
        out.append(rec)
    return out


MUTATORS = [
    mutate_empty_matching_body,
    mutate_inline_duplicated_options,
    mutate_wrong_answer_key,
    mutate_solution_contradicts_answer,
    mutate_kazanim_mismatch,
    mutate_difficulty_mismatch,
    mutate_truncated_stem,
    mutate_dangling_reference,
]

# ⏸ DURDURULDU (2026-07-28, kullanıcı kararı: "komple durdur bu kısmı").
# `mutate_kazanim_mismatch_cross_subject` ve `mutate_kazanim_silent_repair`
# YAZILDI ama MUTATORS'a BİLİNÇLİ olarak eklenmedi → bozuk sete girmiyorlar,
# bench çıktısını değiştirmiyorlar. Bunlar körlük deneyinin (§3g) Aşama 1
# parçasıydı; deney ertelendi. Devreye almak için tek iş: aşağıdaki iki satırı
# yukarıdaki listeye ekleyip `build_broken_set`'i yeniden koşmak (LLM harcaması
# YOK — mutasyon üretimi saf koddur; harcama yalnız bench'in LLM'li koşusunda).
#     mutate_kazanim_mismatch_cross_subject,   # referans: üretimde İMKÂNSIZ
#     mutate_kazanim_silent_repair,            # agent.py:1758'in gerçek kusuru
# Gerekçe ve karar eşikleri: docs/COST_QUALITY_V2_PLAN.md §3g.


def build_broken_set(gold: list[dict]) -> tuple[list[dict], dict]:
    records: list[dict] = []
    for fn in MUTATORS:
        records.extend(fn(gold))

    records.sort(key=lambda r: (r["defect_type"], r["source_gold_id"]))
    for i, rec in enumerate(records, start=1):
        rec["broken_id"] = f"broken-{i:04d}"

    ordered = []
    for r in records:
        ordered.append({
            "broken_id": r["broken_id"],
            "defect_type": r["defect_type"],
            "source_gold_id": r["source_gold_id"],
            "should_be_caught_by": r["should_be_caught_by"],
            "synthesized": r["synthesized"],
            "subject": r["subject"],
            "grade": r["grade"],
            "kazanim_kod": r["kazanim_kod"],
            "question_type": r["question_type"],
            "difficulty": r["difficulty"],
            "question": r["question"],
            "answer": r["answer"],
            "solution_steps": r["solution_steps"],
            "options": r.get("options"),
            "correct_index": r.get("correct_index"),
            "source": r["source"],
        })

    from collections import Counter
    meta = {
        "total": len(ordered),
        "by_defect_type": dict(Counter(r["defect_type"] for r in ordered)),
        "by_should_be_caught_by": dict(Counter(r["should_be_caught_by"] for r in ordered)),
        "synthesized_count": sum(1 for r in ordered if r["synthesized"]),
    }
    return ordered, meta


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    if not args.gold.exists():
        print(f"HATA: altın set bulunamadı ({args.gold}). Önce build_gold_set.py koş.")
        raise SystemExit(1)

    payload = json.loads(args.gold.read_text(encoding="utf-8"))
    gold = payload["questions"]

    records, meta = build_broken_set(gold)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    out_payload = {"_meta": meta, "questions": records}
    args.out.write_text(json.dumps(out_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Bozuk set yazıldı: {args.out}")
    print(f"Toplam: {meta['total']} soru (hedef >=40, 8 kusur tipi)")
    print(f"Kusur tipi dağılımı: {meta['by_defect_type']}")
    print(f"Beklenen katman dağılımı: {meta['by_should_be_caught_by']}")
    print(f"Sentezlenmiş (gold'da örnek yoktu, kuruldu): {meta['synthesized_count']}")


if __name__ == "__main__":
    main()
