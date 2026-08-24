"""Ders ↔ soru tipi uyumu — "Türkçe istedim, matematik geldi" regresyonu.

Pytest gerektirmez — `python tests/test_subject_type_gate.py`. LLM/ağ çağrısı yok.

SAHA BULGUSU (2026-08-24, canlıda birebir üretilerek doğrulandı): istemciler
(apps/mobile generator-setup.tsx + frontend/lib/types.ts) soru-tipi gruplarını
MATEMATİĞE göre sabit tutuyor ve ders seçicisi geldikten sonra da her ders için
aynı listeyi gönderiyordu. Backend `question_types`'ı olduğu gibi kabul edip
prompt'a "salt_islem: 2 adet" yazıyor, model de Türkçe kazanım koduyla ETİKETLİ
matematik soruları üretiyordu:

    POST /api/worksheets/generate {subject: turkce, unit_id: turkce-5-tema-3-...,
      question_types: [salt_islem, islem, sozel_problem, gunluk_hayat, ...]}
    → "Bir kütüphanede 5 katlı rafın her katında 12 kitap bulunmaktadır..."
      (question_type=salt_islem, kazanim_kod=TR.5.OKA.1)

Kapı SUNUCUDA: istemci ne gönderirse göndersin dersin desteklemediği tip üretime
girmez. Eski istemciler (mağazadaki mobil sürüm) kırılmasın diye hata değil FİLTRE.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("GEMINI_API_KEY", "fake-key-for-tests")

from app.models.enums import QuestionType as Q  # noqa: E402
from app.models.enums import SubjectId  # noqa: E402
from app.routers.quizzes import _resolve_solvable_types  # noqa: E402
from app.subjects import filter_types_for_subject, supported_types  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if cond:
        print(f"  ok   {msg}")
    else:
        _failures.append(msg)
        print(f"  FAIL {msg}")


# İstemcilerin gönderdiği gerçek liste ("Açık uçlu" grubu + gizli görsel grup).
MOBILE_OPEN_ENDED = [
    Q.SALT_ISLEM, Q.TABLO_SORUSU, Q.GORSEL_GEOMETRI, Q.GRAFIK_OKUMA,
    Q.ORUNTU_SEKIL, Q.ISLEM, Q.SOZEL_PROBLEM, Q.KAVRAM_SORUSU,
    Q.AKIL_YURUTME, Q.MODELLEME, Q.GUNLUK_HAYAT,
]
MATH_ONLY = {
    Q.ISLEM, Q.SALT_ISLEM, Q.GORSEL_GEOMETRI, Q.ORUNTU_SEKIL,
    Q.MODELLEME, Q.SOZEL_PROBLEM, Q.GUNLUK_HAYAT, Q.AKIL_YURUTME,
}
NON_MATH = [SubjectId.TURKCE, SubjectId.SOSYAL, SubjectId.FEN, SubjectId.INGILIZCE]


def test_math_types_never_reach_verbal_subjects() -> None:
    print("\n[1] matematik tipleri sözel/fen derslerine SIZMAZ")
    for s in NON_MATH:
        allowed = supported_types(s)
        leaked = sorted(t.value for t in (allowed & MATH_ONLY))
        check(not leaked, f"{s.value}: matematiğe özgü tip desteklenmiyor (sızan: {leaked})")


def test_client_open_ended_group_falls_back_to_subject_default() -> None:
    print("\n[2] istemcinin matematik 'Açık uçlu' grubu → dersin varsayılanı")
    for s in NON_MATH:
        kept, dropped = filter_types_for_subject(s, MOBILE_OPEN_ENDED)
        check(kept is None, f"{s.value}: kırpıntıya uymaz, varsayılan dağılıma döner")
        check(bool(dropped), f"{s.value}: düşen tipler raporlanır ({len(dropped)} adet)")


def test_valid_narrow_selection_is_honoured() -> None:
    print("\n[3] geçerli dar seçim AYNEN korunur (kullanıcı tercihi yenilmez)")
    kept, dropped = filter_types_for_subject(SubjectId.TURKCE, [Q.COKTAN_SECMELI])
    check(kept == [Q.COKTAN_SECMELI] and not dropped, "Türkçe + yalnız çoktan seçmeli")
    other = [Q.BOSLUK_DOLDURMA, Q.DOGRU_YANLIS, Q.ESLESTIRME, Q.SIRALAMA]
    kept, dropped = filter_types_for_subject(SubjectId.TURKCE, other)
    check(kept == other and not dropped, "Türkçe + 'Diğer tipler' grubu (ders-nötr)")
    kept, _ = filter_types_for_subject(SubjectId.TURKCE, [Q.OKUMA_PASAJI, Q.DIL_BILGISI])
    check(kept == [Q.OKUMA_PASAJI, Q.DIL_BILGISI], "Türkçe + kendi tipleri")


def test_math_behaviour_unchanged() -> None:
    print("\n[4] MATEMATİK davranışı DEĞİŞMEZ (regresyon kapısı)")
    kept, dropped = filter_types_for_subject(SubjectId.MATEMATIK, MOBILE_OPEN_ENDED)
    check(kept == MOBILE_OPEN_ENDED and not dropped, "matematik: tüm tipler aynen geçer")
    kept, _ = filter_types_for_subject(SubjectId.MATEMATIK, None)
    check(kept is None, "tip gönderilmemişse kısıt yok")
    # Ters yön: sözel tipler matematiğe girmez (burada kalan istenenin yarısından
    # az olduğu için kırpıntı eşiği devreye girer → matematiğin varsayılan dağılımı).
    kept, dropped = filter_types_for_subject(
        SubjectId.MATEMATIK, [Q.ISLEM, Q.OKUMA_PASAJI, Q.YAZIM_NOKTALAMA]
    )
    check(
        kept is None or Q.OKUMA_PASAJI not in kept,
        "matematik: sözel tipler üretime girmez (ters sızıntı)",
    )
    check(
        len(dropped) == 2, "matematik: düşen sözel tipler raporlanır"
    )
    # Kalan çoğunluktaysa aynen korunur.
    kept, _ = filter_types_for_subject(
        SubjectId.MATEMATIK, [Q.ISLEM, Q.COKTAN_SECMELI, Q.OKUMA_PASAJI]
    )
    check(kept == [Q.ISLEM, Q.COKTAN_SECMELI], "matematik: geçerli çoğunluk korunur")


def test_quiz_solvable_types_are_subject_aware() -> None:
    print("\n[5] quiz (çöz modu) çözülebilir tipleri de derse göre süzülür")
    tr = _resolve_solvable_types(None, SubjectId.TURKCE)
    check(Q.SOZEL_PROBLEM not in tr, "Türkçe quiz: matematik sözel problemi yok")
    check(Q.COKTAN_SECMELI in tr, "Türkçe quiz: çoktan seçmeli var")
    tr2 = _resolve_solvable_types([Q.SOZEL_PROBLEM, Q.ISLEM], SubjectId.TURKCE)
    check(
        tr2 and all(t != Q.SOZEL_PROBLEM for t in tr2),
        "Türkçe quiz: matematik tipleri istenmişse dersin varsayılanına düşer",
    )
    mat = _resolve_solvable_types(None, SubjectId.MATEMATIK)
    check(Q.SOZEL_PROBLEM in mat, "matematik quiz: sozel_problem korunur")
    check(len(_resolve_solvable_types(None)) == 4, "subject verilmezse eski davranış")


def main() -> int:
    for fn in (
        test_math_types_never_reach_verbal_subjects,
        test_client_open_ended_group_falls_back_to_subject_default,
        test_valid_narrow_selection_is_honoured,
        test_math_behaviour_unchanged,
        test_quiz_solvable_types_are_subject_aware,
    ):
        fn()
    print()
    if _failures:
        print(f"FAILED: {len(_failures)} assert düştü")
        return 1
    print("PASSED: ders ↔ soru tipi kapısı çalışıyor")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
