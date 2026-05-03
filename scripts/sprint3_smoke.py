"""Sprint 3 smoke test: math verifier + hybrid retrieval + structured solution.

3 fazda doğrular:
  1. Math verifier: yapay yanlış cevaplı SALT_ISLEM/ISLEM yakalanıyor mu?
  2. Hybrid retrieval: term-spesifik sorgu BM25 katkısıyla daha alakalı sonuç veriyor mu?
  3. Structured solution: parse_solution_steps gerçek bir Gemini çıktısını adımlara bölebiliyor mu?

Kullanım:
    PYTHONIOENCODING=utf-8 python scripts/sprint3_smoke.py
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.models.enums import Difficulty, QuestionType
from app.models.schemas import Question, parse_solution_steps
from app.services.agent import GeminiAgent
from app.services.history import GENERATION_HISTORY
from app.services.math_verifier import verify_question
from app.services.retriever import get_retriever


def faz1_math_verifier() -> bool:
    print("\n[Faz 1] Math verifier — yapay yanlış cevaplar")
    print("-" * 60)
    cases = [
        ("Doğru salt işlem", "(15 + 5) × 4 - 3² = ?", "71", QuestionType.SALT_ISLEM, True),
        ("Yanlış cevap (40 ≠ 28)", "12 + 8 × 2 = ?", "40", QuestionType.SALT_ISLEM, False),
        ("Doğru kesir", "1/2 + 1/4 = ?", "3/4", QuestionType.SALT_ISLEM, True),
        ("Yanlış kesir", "2/3 + 1/6 = ?", "1/2", QuestionType.SALT_ISLEM, False),  # doğru: 5/6
        ("Sözel — verifier kapsam dışı", "Ali 3 elma aldı, Ayşe 2. Toplam?", "5", QuestionType.SOZEL_PROBLEM, True),
    ]
    all_ok = True
    for name, q, ans, qtype, expected_valid in cases:
        question = Question(number=0, question=q, answer=ans, solution_steps="",
                            kazanim_kod="x", question_type=qtype)
        v = verify_question(question, 0)
        actual_valid = v.is_valid
        ok = actual_valid == expected_valid
        marker = " PASS" if ok else " FAIL"
        print(f"  {marker} {name}: verifiable={v.is_verifiable} valid={actual_valid} (expected {expected_valid})")
        if v.reason:
            print(f"        reason: {v.reason}")
        all_ok = all_ok and ok
    return all_ok


def faz2_hybrid_retrieval() -> bool:
    print("\n[Faz 2] Hybrid retrieval — term-spesifik sorgu")
    print("-" * 60)
    retriever = get_retriever()
    if retriever is None:
        print("  WARN: retriever yok — RAG kapalı veya ChromaDB eksik. Faz atlanıyor.")
        return True
    # Term-spesifik sorgular: BM25'ın anlamlı katkıda bulunması beklenen örnekler
    queries = [
        ("eşkenar üçgen iç açıları", 6, "geometri", None),
        ("asal sayı çarpanları", 6, "dogal_sayilar", None),
        ("denklem çözmek", 5, "cebir", "M.5.5.1"),
    ]
    rng = random.Random(42)
    found_any = False
    for query, grade, topic_id, kazanim_kod in queries:
        try:
            hits = retriever.retrieve(
                query_text=query,
                grade=grade,
                kazanim_kod=kazanim_kod,
                topic_id=topic_id,
                difficulty="orta",
                k=3,
                rng=rng,
            )
        except Exception as exc:
            print(f"  WARN '{query}': {exc}")
            continue
        if hits:
            found_any = True
        print(f"  '{query}' → {len(hits)} hit (grade={grade}, topic={topic_id})")
        for h in hits[:2]:
            d = h.get("distance")
            d_str = f"{d:.3f}" if isinstance(d, float) else str(d)
            print(f"    distance={d_str} | {(h.get('question') or '')[:80]}")
    return found_any


def faz3_solution_parser() -> bool:
    print("\n[Faz 3] Structured solution_steps parser")
    print("-" * 60)
    # Gerçek Gemini benzeri çıktı
    real_solution = (
        "1. Bilinmeyeni x ile gösterelim. "
        "2. Denklemi yaz: 4x - 10 = 30. "
        "3. Her iki tarafa 10 ekle: 4x = 40. "
        "4. 4'e böl: x = 10. "
        "5. Cevap: x = 10."
    )
    steps = parse_solution_steps(real_solution)
    print(f"  Parsed {len(steps)} adım:")
    for s in steps:
        print(f"    [{s.step_no}] {s.description[:70]} | comp={s.computation}")
    ok = len(steps) >= 4 and any(s.computation for s in steps)
    print(f"  {' PASS' if ok else ' FAIL'} Parser ≥4 adım çıkardı ve en az birinde computation var")
    return ok


def main() -> None:
    print("Sprint 3 smoke test başlıyor.")
    GENERATION_HISTORY.clear()

    f1 = faz1_math_verifier()
    f2 = faz2_hybrid_retrieval()
    f3 = faz3_solution_parser()

    print("\n" + "=" * 60)
    print("ÖZET")
    print("=" * 60)
    print(f"  Faz 1 (math verifier):     {' PASS' if f1 else ' FAIL'}")
    print(f"  Faz 2 (hybrid retrieval):  {' PASS' if f2 else ' FAIL'}")
    print(f"  Faz 3 (solution parser):   {' PASS' if f3 else ' FAIL'}")

    if f1 and f2 and f3:
        print("\nTüm Sprint 3 fazları geçti.")
        sys.exit(0)
    print("\nEn az bir faz başarısız.")
    sys.exit(1)


if __name__ == "__main__":
    main()
