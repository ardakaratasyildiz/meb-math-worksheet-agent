"""Geçmiş deneme gözden geçirmesi (quiz geçmişi — PR1).

Saklanan deneme (kullanıcının cevapları) + quiz snapshot'ından (sorular + doğru
cevaplar) bir AttemptDetail üretir: her soru için doğru/yanlış, doğru cevap, çözüm
ve KULLANICININ verdiği cevap. Puanlama mantığı YENİDEN YAZILMAZ — grade_quiz reuse.

Saf/deterministik, LLM/DB yok → birim test edilebilir.
"""
from __future__ import annotations

from app.models.enums import QuestionType
from app.models.schemas import (
    AttemptDetail,
    AttemptReviewItem,
    Question,
    SubmittedAnswer,
)
from app.services.grading import grade_quiz


def build_attempt_detail(
    *,
    attempt_id: str,
    quiz_id: str,
    meta: dict,
    questions: list[Question],
    submitted: list[SubmittedAnswer],
    duration_seconds: int | None,
    completed_at: str,
    open_ended_text_match: bool = False,
) -> AttemptDetail:
    """Deneme + quiz snapshot → tam gözden geçirme.

    meta: {title, grade, topic_id, difficulty}. questions: snapshot'taki cevaplı
    Question listesi. submitted: kullanıcının SubmittedAnswer listesi.

    open_ended_text_match: worksheet ödevi denemesinde True — açık uçlu/yapılandırılmamış
    tipler metin-eşleştirmeyle puanlanır (çözümdeki puanlamayla tutarlı olsun). Quiz/öğrenci
    geçmişinde False (varsayılan davranış korunur).
    """
    results, score, total, per_kazanim = grade_quiz(
        questions, submitted, open_ended_text_match=open_ended_text_match
    )
    by_number = {a.number: a for a in submitted}

    review: list[AttemptReviewItem] = []
    for q, r in zip(questions, results):
        is_mcq = q.question_type == QuestionType.COKTAN_SECMELI
        review.append(
            AttemptReviewItem(
                number=q.number,
                question=q.question,
                question_type=q.question_type,
                kazanim_kod=q.kazanim_kod,
                options=q.options if is_mcq else None,
                is_correct=r.is_correct,
                correct_answer=r.correct_answer,
                correct_index=r.correct_index if is_mcq else None,
                solution_steps=r.solution_steps,
                submitted=by_number.get(q.number),
            )
        )

    return AttemptDetail(
        attempt_id=attempt_id,
        quiz_id=quiz_id,
        title=meta.get("title", "Quiz"),
        grade=meta.get("grade"),
        topic_id=meta.get("topic_id", ""),
        difficulty=meta.get("difficulty", "orta"),
        score=score,
        total=total,
        duration_seconds=duration_seconds,
        completed_at=completed_at,
        per_kazanim=per_kazanim,
        review=review,
        has_detail=True,
    )
