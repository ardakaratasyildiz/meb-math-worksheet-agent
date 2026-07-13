"""Olgusal kritik eval seti (WS-5.26) — Fen critic'in kavram-yanılgılarını yakalama oranı.

Etiketli BAD (bilimsel hata içeren → reddedilmeli) + GOOD (doğru → geçmeli) Fen
sorularını Fen critic'inden geçirir, catch-rate raporlar. GERÇEK Gemini çağrısı
gerektirir (deterministik değil) → MANUEL eval aracı, CI değil. Kritik prompt'u
değiştikçe buradan koşup regresyonu ölç.

Kullanım:  python scripts/eval_factual_critic.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.models.enums import Difficulty, QuestionType, SubjectId  # noqa: E402
from app.models.schemas import Question  # noqa: E402
from app.services.agent import _collect_critic_context  # noqa: E402
from app.services.critic import GeminiCritic  # noqa: E402
from app.subjects.fen import CRITIC_SYSTEM_PROMPT as FEN_CRITIC  # noqa: E402


def _q(grade, kod, question, answer, qtype=QuestionType.COKTAN_SECMELI):
    return Question(
        number=1, question=question, answer=answer, question_type=qtype,
        kazanim_kod=kod, difficulty=Difficulty.ORTA,
        solution_steps="Açıklama: doğru cevabın gerekçesi.",
    )


# (grade, kazanım, soru, cevap) — BİLİMSEL HATA içeriyor → critic reddetmeli.
BAD = [
    (6, "FB.6.1.1", "Hücre duvarı ile ilgili aşağıdakilerden hangisi doğrudur? "
        "A) Yalnızca bitki hücrelerinde bulunur B) Hayvan hücrelerinde de bulunur "
        "C) DNA içerir D) Enerji üretir", "A"),  # hücre duvarı sadece bitkide DEĞİL
    (6, "FB.6.5.1", "Bir astronot Ay'a gittiğinde kütlesi için ne söylenebilir? "
        "A) Azalır B) Artar C) Değişmez D) Sıfır olur", "A"),  # kütle değişmez
    (5, "FB.5.4.1", "Buzun erimesi ne tür bir değişimdir? "
        "A) Kimyasal değişim B) Fiziksel değişim C) Yanma D) Paslanma", "A"),  # fiziksel
    (8, "FB.8.4.1", "Isı ve sıcaklık ile ilgili hangisi doğrudur? "
        "A) Isı ve sıcaklık aynı şeydir B) Isı enerjidir, sıcaklık ölçülen değerdir "
        "C) Sıcaklık joule ile ölçülür D) Isı °C ile ölçülür", "A"),  # ısı≠sıcaklık
]

# (grade, kazanım, soru, cevap) — BİLİMSEL OLARAK DOĞRU → critic geçirmeli.
GOOD = [
    (6, "FB.6.1.1", "Hücre duvarı hangi hücrelerde bulunur? "
        "A) Yalnız hayvan B) Bitki, mantar ve bakteri C) Yalnız insan D) Hiçbiri", "B"),
    (6, "FB.6.5.1", "Bir cismin Ay'daki ağırlığı Dünya'dakinden azdır. Nedeni nedir? "
        "A) Kütlesi azalır B) Ay'ın çekim kuvveti daha küçüktür C) Havasızlık "
        "D) Sıcaklık farkı", "B"),
    (5, "FB.5.4.1", "Aşağıdakilerden hangisi kimyasal değişimdir? "
        "A) Buzun erimesi B) Şekerin suda çözünmesi C) Kâğıdın yanması "
        "D) Camın kırılması", "C"),
]


def main() -> None:
    critic = GeminiCritic(system_prompt=FEN_CRITIC)

    def run(cases, label):
        caught = 0
        for grade, kod, q, ans in cases:
            question = _q(grade, kod, q, ans)
            kzs = [{"kod": kod, "metin": kod}]
            ctx = _collect_critic_context(SubjectId.FEN, grade, kzs)
            verdicts = critic.evaluate([question], kzs, Difficulty.ORTA, context=ctx)
            v = verdicts[0] if verdicts else None
            is_valid = v.is_valid if v else True  # fail-open → geçer
            # BAD: is_valid=False beklenir; GOOD: is_valid=True beklenir
            expected_invalid = label == "BAD"
            ok = (not is_valid) if expected_invalid else is_valid
            caught += 1 if ok else 0
            mark = "✓" if ok else "✗"
            print(f"  {mark} [{label}] g{grade} valid={is_valid} conf={getattr(v,'confidence',None)} "
                  f"issues={getattr(v,'issues',[])} | {q[:55]}")
        return caught

    print("=== BAD (reddedilmeli) ===")
    bad_ok = run(BAD, "BAD")
    print("=== GOOD (geçmeli) ===")
    good_ok = run(GOOD, "GOOD")
    print(f"\nSONUÇ: BAD yakalama {bad_ok}/{len(BAD)} | GOOD koruma {good_ok}/{len(GOOD)}")


if __name__ == "__main__":
    main()
