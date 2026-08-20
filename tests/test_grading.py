"""Otomatik puanlama + attempt/mastery testleri (Adım 2).

Pytest gerektirmez — `python tests/test_grading.py`. LLM/ağ çağrısı yok.
CI (eval.yml lint-import) bu dosyayı çalıştırır.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("GEMINI_API_KEY", "fake-key-for-tests")

from app.models.enums import QuestionType  # noqa: E402
from app.models.schemas import Question, SubmittedAnswer  # noqa: E402
from app.services.grading import grade_question, grade_quiz  # noqa: E402
from app.services.quiz_store import QuizStore  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")
    if not cond:
        _failures.append(msg)


def _q(n, qtype, answer, **extra) -> Question:
    return Question(
        number=n, question="?", answer=answer, solution_steps="",
        kazanim_kod=extra.pop("kazanim_kod", "M.5.1.1"),
        question_type=qtype, **extra,
    )


def _a(n, **kw) -> SubmittedAnswer:
    return SubmittedAnswer(number=n, **kw)


def test_grade_question_per_type() -> None:
    print("grade_question — tip bazında")
    # Çoktan seçmeli
    mcq = _q(1, QuestionType.COKTAN_SECMELI, "B", options=["4", "5", "6", "7"], correct_index=1)
    check(grade_question(mcq, _a(1, selected_index=1)) is True, "MCQ doğru şık")
    check(grade_question(mcq, _a(1, selected_index=2)) is False, "MCQ yanlış şık")
    check(grade_question(mcq, _a(1)) is False, "MCQ boş cevap yanlış")

    # Doğru/Yanlış
    dy = _q(2, QuestionType.DOGRU_YANLIS, "Doğru", correct_bool=True)
    check(grade_question(dy, _a(2, bool_answer=True)) is True, "D/Y doğru")
    check(grade_question(dy, _a(2, bool_answer=False)) is False, "D/Y yanlış")

    # Boşluk doldurma — sayısal denklik + string
    blank = _q(3, QuestionType.BOSLUK_DOLDURMA, "1/2", blanks=["1/2"])
    check(grade_question(blank, _a(3, texts=["0,5"])) is True, "boşluk 1/2 ≡ 0,5")
    check(grade_question(blank, _a(3, texts=["0.5"])) is True, "boşluk 1/2 ≡ 0.5")
    check(grade_question(blank, _a(3, texts=["2"])) is False, "boşluk yanlış sayı")

    blank_txt = _q(4, QuestionType.BOSLUK_DOLDURMA, "asal", blanks=["asal"])
    check(grade_question(blank_txt, _a(4, texts=[" Asal "])) is True, "boşluk metin normalize (Asal≡asal)")

    # Çoklu boşluk — hepsi doğru olmalı
    multi = _q(5, QuestionType.BOSLUK_DOLDURMA, "2;3", blanks=["2", "3"])
    check(grade_question(multi, _a(5, texts=["2", "3"])) is True, "çoklu boşluk hepsi doğru")
    check(grade_question(multi, _a(5, texts=["2", "4"])) is False, "çoklu boşluk biri yanlış")
    check(grade_question(multi, _a(5, texts=["2"])) is False, "çoklu boşluk eksik giriş")

    # Salt işlem — sayısal denklik
    num = _q(6, QuestionType.SALT_ISLEM, "3/4")
    check(grade_question(num, _a(6, texts=["0,75"])) is True, "salt_islem 3/4 ≡ 0,75")
    check(grade_question(num, _a(6, texts=["1/2"])) is False, "salt_islem yanlış")


def test_grade_quiz_aggregate() -> None:
    print("grade_quiz — agregasyon + kazanım kırılımı")
    qs = [
        _q(1, QuestionType.COKTAN_SECMELI, "A", options=["x", "y"], correct_index=0, kazanim_kod="M.5.1.1"),
        _q(2, QuestionType.DOGRU_YANLIS, "Yanlış", correct_bool=False, kazanim_kod="M.5.1.1"),
        _q(3, QuestionType.SALT_ISLEM, "10", kazanim_kod="M.5.1.2"),
    ]
    submitted = [
        _a(1, selected_index=0),   # doğru
        _a(2, bool_answer=True),   # yanlış (correct False)
        _a(3, texts=["10"]),       # doğru
    ]
    results, score, total, per_k = grade_quiz(qs, submitted)
    check(score == 2 and total == 3, f"skor 2/3: {score}/{total}")
    check([r.is_correct for r in results] == [True, False, True], "soru-bazlı doğruluk")
    # Çözüm sonrası cevap açığa çıkar
    check(results[0].correct_answer == "A", "doğru cevap sonuçta açık")
    check(results[0].correct_index == 0, "MCQ correct_index sonuçta açık")
    # Kazanım kırılımı
    by_k = {k.kazanim_kod: (k.correct, k.total) for k in per_k}
    check(by_k.get("M.5.1.1") == (1, 2), f"M.5.1.1 = 1/2: {by_k.get('M.5.1.1')}")
    check(by_k.get("M.5.1.2") == (1, 1), f"M.5.1.2 = 1/1: {by_k.get('M.5.1.2')}")

    # Eksik cevap (hiç gönderilmeyen soru) yanlış sayılır
    results2, score2, _, _ = grade_quiz(qs, [_a(1, selected_index=0)])
    check(score2 == 1, f"eksik cevaplar yanlış: skor {score2}")


def test_attempt_and_mastery_persistence() -> None:
    print("attempt + mastery kalıcılığı (kümülatif)")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        store = QuizStore(db_path=str(Path(tmp) / "t.sqlite3"))
        try:
            store.record_attempt(
                quiz_id="q1", solver_tenant_id="u1",
                answers=[{"number": 1, "selected_index": 0}],
                score=1, total=2, duration_seconds=30,
                per_kazanim=[{"kazanim_kod": "M.5.1.1", "correct": 1, "total": 2}],
            )
            store.update_mastery("u1", [{"kazanim_kod": "M.5.1.1", "correct": 1, "total": 2}])
            m = store.get_mastery("u1")
            check(len(m) == 1 and m[0]["correct"] == 1 and m[0]["total"] == 2, f"ilk mastery: {m}")

            # İkinci deneme — kümülatif toplanmalı
            store.update_mastery("u1", [{"kazanim_kod": "M.5.1.1", "correct": 2, "total": 3}])
            m2 = {x["kazanim_kod"]: (x["correct"], x["total"]) for x in store.get_mastery("u1")}
            check(m2["M.5.1.1"] == (3, 5), f"kümülatif mastery 3/5: {m2['M.5.1.1']}")

            # İzolasyon: başka tenant boş
            check(store.get_mastery("u2") == [], "başka tenant mastery boş")
        finally:
            store.close()


def test_open_ended_text_match() -> None:
    """Worksheet ödevi modu: açık uçlu/yapılandırılmamış tipler metin-eşleştirmeyle
    puanlanır (self-eval yok). Çöz&Geliş (open_ended_text_match=False) davranışı korunur."""
    print("open_ended_text_match — worksheet metin-eşleştirme")

    # Açık uçlu (sozel_problem)
    open_q = _q(1, QuestionType.SOZEL_PROBLEM, "12 elma")
    # Worksheet modu: metin normalize eşleşir
    check(
        grade_question(open_q, _a(1, texts=["12 Elma"]), open_ended_text_match=True) is True,
        "worksheet: açık uçlu normalize metin doğru",
    )
    check(
        grade_question(open_q, _a(1, texts=["5 elma"]), open_ended_text_match=True) is False,
        "worksheet: açık uçlu yanlış metin",
    )
    check(
        grade_question(open_q, _a(1, texts=["   "]), open_ended_text_match=True) is False,
        "worksheet: boş metin yanlış",
    )
    # Çöz&Geliş (varsayılan): açık uçlu ÖZ-DEĞERLENDİRME (bool_answer), metin sayılmaz
    check(
        grade_question(open_q, _a(1, bool_answer=True)) is True,
        "quiz: açık uçlu self-eval doğru bildim",
    )
    # KULLANICI KARARI (2026-08-13): Çöz&Geliş'te de cevap YAZILIR ve anahtara
    # eşleştirilir; öz-değerlendirme kaldırıldı. bool_answer yalnız metin hiç
    # gelmediğinde (eski istemci) okunur.
    check(
        grade_question(open_q, _a(1, texts=["12 elma"])) is True,
        "quiz: yazılan doğru cevap kabul edilir",
    )
    check(
        grade_question(open_q, _a(1, texts=["5 elma"])) is False,
        "quiz: yanlış metin yanlış kalır",
    )
    check(
        grade_question(open_q, _a(1, texts=["cevap 12 elma olur"])) is True,
        "quiz: cümle içinde geçen kısa cevap kabul (tam sözcük)",
    )
    check(
        grade_question(open_q, _a(1, bool_answer=False, texts=["12 elma"])) is True,
        "quiz: metin varsa bool_answer'a bakılmaz (metin otoriter)",
    )

    # Sayısal cevap — asıl saha vakası ("222 yazdım, yanlış dedi")
    num_q = _q(9, QuestionType.SOZEL_PROBLEM, "222")
    check(grade_question(num_q, _a(9, texts=["222"])) is True, "quiz: 222 → doğru")
    check(grade_question(num_q, _a(9, texts=[" 222 "])) is True, "quiz: boşluklu 222 → doğru")
    check(grade_question(num_q, _a(9, texts=["222 sayfa"])) is True, "quiz: '222 sayfa' → doğru")
    check(grade_question(num_q, _a(9, texts=["1222"])) is False, "quiz: 1222 → yanlış (sözcük sınırı)")

    # Yapılandırılmamış tip (tablo): quiz üretiminde havuza girmez ama gelirse
    # cevabı yok saymak yerine anahtara eşleştirilir.
    tbl = _q(2, QuestionType.TABLO_SORUSU, "45")
    check(grade_question(tbl, _a(2, texts=["45"])) is True, "quiz: tablo tipinde doğru metin kabul")
    check(grade_question(tbl, _a(2, texts=["9"])) is False, "quiz: tablo tipinde yanlış metin yanlış")
    check(
        grade_question(tbl, _a(2, texts=["45"]), open_ended_text_match=True) is True,
        "worksheet: tablo sayısal eşleşir",
    )

    # Yapısal 4 tip her iki modda da aynı deterministik kuralla puanlanır
    mcq = _q(3, QuestionType.COKTAN_SECMELI, "B", options=["x", "y"], correct_index=1)
    check(
        grade_question(mcq, _a(3, selected_index=1), open_ended_text_match=True) is True,
        "worksheet: çoktan seçmeli yine yapısal puanlanır",
    )

    # Agregasyon: worksheet quiz (1 açık uçlu doğru + 1 MCQ doğru + 1 tablo yanlış)
    qs = [open_q, mcq, tbl]
    subs = [_a(1, texts=["12 elma"]), _a(3, selected_index=1), _a(2, texts=["99"])]
    _, score, total, _ = grade_quiz(qs, subs, open_ended_text_match=True)
    check(score == 2 and total == 3, f"worksheet agregasyon 2/3: {score}/{total}")


def test_latex_and_exponent_answers() -> None:
    """Saha bildirimi 2026-08-20: LaTeX'li cevap anahtarı + `^` ile yazılan üs.

    Cevap anahtarı "$100 \\times 2^6$" gibi LaTeX taşıyor; öğrenci klavyeden
    "6400" ya da "100x2^6" yazıyordu. Sınırlayıcı/komutlar temizlenmediği için
    SymPy parse edemiyor, ham string karşılaştırmaya düşülüyor ve DOĞRU cevap
    yanlış sayılıyordu. Ayrıca NFKC "13⁶" ifadesini "136"ya çöktürdüğü için
    "136" yazan öğrenci DOĞRU sayılıyordu.
    """
    print("LaTeX / üslü / köklü cevap eşleşmesi")
    q = _q(1, QuestionType.SALT_ISLEM, r"$100 \times 2^6$")
    for typed in ("6400", "100x2^6", "100 x 2^6", "100*2^6"):
        check(grade_question(q, _a(1, texts=[typed])) is True, f"üslü anahtar ≡ '{typed}'")
    check(grade_question(q, _a(1, texts=["6,4x10^2"])) is False, "gerçekten yanlış cevap yanlış")

    kok = _q(2, QuestionType.SOZEL_PROBLEM, r"$\sqrt{18}$")
    for typed in ("3√2", "√18", "sqrt(18)"):
        check(grade_question(kok, _a(2, texts=[typed])) is True, f"köklü anahtar ≡ '{typed}'")

    # Üst simge ≠ düz rakam (NFKC çökmesi regresyonu)
    us = _q(3, QuestionType.SALT_ISLEM, "13⁶")
    check(grade_question(us, _a(3, texts=["13^6"])) is True, "13⁶ ≡ '13^6'")
    check(grade_question(us, _a(3, texts=["136"])) is False, "13⁶ ≢ '136' (NFKC çökmesi)")

    kesir = _q(4, QuestionType.BOSLUK_DOLDURMA, "1/2", blanks=[r"$\frac{1}{2}$"])
    check(grade_question(kesir, _a(4, texts=["0,5"])) is True, "LaTeX kesir boşluğu ≡ '0,5'")

    # Sözel cevap bozulmasın (LaTeX temizliği düz metinde etkisiz)
    sozel = _q(5, QuestionType.SOZEL_PROBLEM, "8 ile 9")
    check(grade_question(sozel, _a(5, texts=["8 ile 9"])) is True, "sözel cevap korunur")
    check(grade_question(sozel, _a(5, texts=["9 ile 10"])) is False, "yanlış sözel cevap yanlış")


def test_blank_display_answer() -> None:
    """Boşluk doldurmada gösterilen "doğru cevap" puanlanan anahtarla aynı olmalı.

    Model answer alanına yalnız ilk boşluğu yazdığında ekranda "Doğru cevap: 13"
    görünüp 4 boşluklu soru yanlış sayılıyordu.
    """
    print("boşluk doldurma — gösterilen doğru cevap")
    q = _q(1, QuestionType.BOSLUK_DOLDURMA, "13", blanks=["13", "5", "8", "16"])
    results, _, _, _ = grade_quiz([q], [_a(1, texts=["13", "5", "8", "13"])])
    check(
        results[0].correct_answer == "13; 5; 8; 16",
        f"tüm boşluklar gösterilir: {results[0].correct_answer!r}",
    )
    check(results[0].is_correct is False, "son boşluk yanlış → soru yanlış")


def main() -> int:
    for fn in (
        test_grade_question_per_type,
        test_grade_quiz_aggregate,
        test_open_ended_text_match,
        test_latex_and_exponent_answers,
        test_blank_display_answer,
        test_attempt_and_mastery_persistence,
    ):
        fn()
    print()
    if _failures:
        print(f"FAILED: {len(_failures)} assert düştü")
        return 1
    print("PASSED: puanlama + attempt/mastery testleri geçti")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
