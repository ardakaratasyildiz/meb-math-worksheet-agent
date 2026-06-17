"""Çözülebilir quiz endpoint'leri (öğrenme döngüsü — Adım 1).

POST /api/quizzes      → çözülebilir quiz üret (yalnız 4 otomatik-puanlanabilir
                         tip), yapısal alanları doğrula, kaydet → CEVAPSIZ döndür.
GET  /api/quizzes/{id} → çözmek için getir (CEVAPSIZ, owner-only).

Anti-kopya: cevaplar (answer/solution_steps/correct_index/blanks/correct_bool)
istemciye HİÇ gönderilmez; sunucuda kalır, Adım 2 /attempt puanlamasında kullanılır.

Mevcut /api/worksheets akışından tamamen ayrıdır; PDF üretimi etkilenmez.
"""
from __future__ import annotations

import logging
import random
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, Request

from app.data.curriculum import get_topic
from app.models.enums import Difficulty, QuestionType
from app.models.schemas import (
    AttemptResult,
    CreateQuizRequest,
    CreateShareResponse,
    Question,
    QuizPublic,
    QuizQuestionPublic,
    SubmitAttemptRequest,
)
from app.security import limiter, rate_limit_string, require_api_key
from app.services.agent import AgentError, GeminiAgent
from app.services.grading import grade_quiz
from app.services.quiz_store import QUIZ_STORE
from app.services.structured import derive_structured_fields, validate_structured

logger = logging.getLogger(__name__)

router = APIRouter()

# Adım 0'da desteklenen 4 çözülebilir tip — üretim dağıtımına allowed_types olarak
# geçer. Eşleştirme/sıralama sonraki dilime bırakıldı.
_SOLVABLE_TYPES = [
    QuestionType.COKTAN_SECMELI,
    QuestionType.DOGRU_YANLIS,
    QuestionType.BOSLUK_DOLDURMA,
    QuestionType.SALT_ISLEM,
]


@lru_cache(maxsize=1)
def _agent() -> GeminiAgent:
    return GeminiAgent()


def _resolve_solvable_types(
    requested: list[QuestionType] | None,
) -> list[QuestionType]:
    """İstenen tipleri çözülebilir havuza indir. None → 4 tip. Filtre sonrası boş
    olabilir (çağıran 400 döner)."""
    if not requested:
        return list(_SOLVABLE_TYPES)
    solvable = set(_SOLVABLE_TYPES)
    return [t for t in requested if t in solvable]


def _split_buckets(total: int) -> dict[Difficulty, int]:
    """Karışık/progresyon için zorluk dağılımı (kolay 30 / orta 40 / zor 30).
    Toplam < 5'te anlamlı bölünmez → tek seviye (orta)."""
    if total < 5:
        return {Difficulty.ORTA: total}
    kolay = max(1, total * 3 // 10)
    zor = max(1, total * 3 // 10)
    orta = total - kolay - zor
    if orta < 1:
        return {Difficulty.ORTA: total}
    return {Difficulty.KOLAY: kolay, Difficulty.ORTA: orta, Difficulty.ZOR: zor}


def _generate_solvable(req: CreateQuizRequest) -> tuple[list[Question], str]:
    """Çözülebilir mod üretim: seçili tipler + zorluk modu; derive+validate'den
    geçenler kalır. Dönüş: (geçerli sorular [1..n numaralı], konu adı)."""
    topic = get_topic(req.grade, req.topic_id)
    if topic is None:
        raise HTTPException(
            status_code=404,
            detail=f"{req.grade}. sınıfta '{req.topic_id}' konusu bulunmuyor.",
        )
    allowed = _resolve_solvable_types(req.question_types)
    if not allowed:
        raise HTTPException(
            status_code=400,
            detail="Seçilen tipler çözülebilir değil; en az bir çözülebilir tip seçin.",
        )

    def _gen(agent: GeminiAgent, diff: Difficulty, count: int) -> list[Question]:
        return agent.generate(
            grade=req.grade,
            topic_id=req.topic_id,
            kazanim_kod=req.kazanim_kod,
            difficulty=diff,
            question_count=count,
            tenant_id=req.tenant_id,
            allowed_types=allowed,
        )

    raw: list[Question] = []
    if req.difficulty_mode == "single":
        try:
            raw = _gen(_agent(), req.difficulty, req.question_count)
        except AgentError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
    else:
        # Karışık/progresyon: kolay/orta/zor bucket'ları paralel üret (latency).
        buckets = _split_buckets(req.question_count)
        seq = [d for d in (Difficulty.KOLAY, Difficulty.ORTA, Difficulty.ZOR)
               if buckets.get(d, 0) > 0]

        def _gen_bucket(diff: Difficulty):
            # İzole agent → paylaşılan trace/durum yarışı olmaz.
            try:
                return diff, _gen(GeminiAgent(), diff, buckets[diff]), None
            except Exception as exc:  # noqa: BLE001
                logger.warning("Quiz bucket başarısız (diff=%s): %s", diff.value, exc)
                return diff, [], str(exc)

        results: dict[Difficulty, list[Question]] = {}
        with ThreadPoolExecutor(max_workers=len(seq)) as ex:
            for diff, qs, _err in ex.map(_gen_bucket, seq):
                results[diff] = qs
        # progressive: kolay→zor sırasında topla.
        for diff in seq:
            raw.extend(results.get(diff, []))
        if req.difficulty_mode == "mixed":
            random.shuffle(raw)

    valid: list[Question] = []
    for q in raw:
        enriched = derive_structured_fields(q)
        ok, issues = validate_structured(enriched)
        if ok:
            valid.append(enriched)
        else:
            logger.info(
                "Çözülebilir-dışı soru elendi (tip=%s): %s",
                q.question_type.value, issues,
            )
    # Numaraları sıkı tut (eleme sonrası boşluk kalmasın).
    valid = [q.model_copy(update={"number": i + 1}) for i, q in enumerate(valid)]
    return valid, topic["name"]


def _to_public(
    *,
    quiz_id: str,
    title: str,
    grade: int,
    topic_id: str,
    difficulty: Difficulty,
    created_at: str,
    questions: list[Question],
) -> QuizPublic:
    """Cevaplı Question listesini CEVAPSIZ QuizPublic'e dönüştürür (anti-kopya).

    Çoktan seçmelide `options` (şıklar — cevap değil) gönderilir; boşluk
    doldurmada yalnız `blank_count` (kaç giriş). Diğer her şey soyulur.
    """
    pub: list[QuizQuestionPublic] = []
    for q in questions:
        is_mcq = q.question_type == QuestionType.COKTAN_SECMELI
        is_blank = q.question_type == QuestionType.BOSLUK_DOLDURMA
        pub.append(
            QuizQuestionPublic(
                number=q.number,
                question=q.question,
                question_type=q.question_type,
                kazanim_kod=q.kazanim_kod,
                options=q.options if is_mcq else None,
                blank_count=(len(q.blanks) if (is_blank and q.blanks) else None),
            )
        )
    return QuizPublic(
        id=quiz_id,
        title=title,
        grade=grade,
        topic_id=topic_id,
        difficulty=difficulty,
        question_count=len(pub),
        questions=pub,
        created_at=created_at,
    )


@router.post("", response_model=QuizPublic)
@limiter.limit(rate_limit_string())
def create_quiz(
    request: Request,
    req: CreateQuizRequest,
    _api_key: str = Depends(require_api_key),
) -> QuizPublic:
    """Çözülebilir quiz üret + kaydet → CEVAPSIZ döndür. LLM çağrısı (rate limitli)."""
    questions, topic_name = _generate_solvable(req)
    if not questions:
        # Üretilenlerin hiçbiri yapısal doğrulamadan geçmedi (nadir) → tekrar deneyin.
        raise HTTPException(
            status_code=502,
            detail="Çözülebilir soru üretilemedi; lütfen tekrar deneyin.",
        )
    title = f"{req.grade}. Sınıf - {topic_name} Quiz"
    record = QUIZ_STORE.create(
        owner_tenant_id=req.tenant_id,
        title=title,
        grade=req.grade,
        topic_id=req.topic_id,
        difficulty=req.difficulty.value,
        questions=[q.model_dump() for q in questions],
    )
    logger.info(
        "quiz oluşturuldu: tenant=%s id=%s soru=%d",
        req.tenant_id, record["id"], len(questions),
    )
    return _to_public(
        quiz_id=record["id"],
        title=title,
        grade=req.grade,
        topic_id=req.topic_id,
        difficulty=req.difficulty,
        created_at=record["created_at"],
        questions=questions,
    )


@router.get("/{quiz_id}", response_model=QuizPublic)
def get_quiz(
    quiz_id: str,
    tenant_id: str,
    _api_key: str = Depends(require_api_key),
) -> QuizPublic:
    """Quiz'i çözmek için getir — CEVAPSIZ, yalnız sahibi (tenant_id) erişir."""
    record = QUIZ_STORE.get(quiz_id, tenant_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Quiz bulunamadı.")
    questions = [Question(**q) for q in record["questions"]]
    return _to_public(
        quiz_id=record["id"],
        title=record["title"],
        grade=record["grade"],
        topic_id=record["topic_id"],
        difficulty=Difficulty(record["difficulty"]),
        created_at=record["created_at"],
        questions=questions,
    )


@router.post("/{quiz_id}/attempt", response_model=AttemptResult)
def submit_attempt(
    quiz_id: str,
    req: SubmitAttemptRequest,
    _api_key: str = Depends(require_api_key),
) -> AttemptResult:
    """Cevapları gönder → sunucuda LLM'siz puanla → sonuç + kazanım kırılımı.

    Puanlama sunucuda yapılır (cevaplar istemcide yok). Sonuçta doğru cevap +
    çözüm açığa çıkar (çözüm sonrası geri bildirim). Deneme + mastery kaydedilir.
    """
    record = QUIZ_STORE.get(quiz_id, req.tenant_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Quiz bulunamadı.")
    stored = [Question(**q) for q in record["questions"]]

    results, score, total, per_kazanim = grade_quiz(stored, req.answers)
    per_kazanim_dicts = [k.model_dump() for k in per_kazanim]

    attempt = QUIZ_STORE.record_attempt(
        quiz_id=quiz_id,
        solver_tenant_id=req.tenant_id,
        answers=[a.model_dump() for a in req.answers],
        score=score,
        total=total,
        duration_seconds=req.duration_seconds,
        per_kazanim=per_kazanim_dicts,
        # Snapshot: geçmiş, quiz FIFO-trim'lense bile self-contained kalsın.
        quiz_snapshot={
            "title": record["title"],
            "grade": record["grade"],
            "topic_id": record["topic_id"],
            "difficulty": record["difficulty"],
            "questions": [q.model_dump() for q in stored],
        },
    )
    # Mastery güncelle — best-effort, puanlama sonucu kullanıcıya yine döner.
    try:
        QUIZ_STORE.update_mastery(req.tenant_id, per_kazanim_dicts)
    except Exception as exc:  # noqa: BLE001
        logger.warning("mastery güncelleme hatası (tenant=%s): %s", req.tenant_id, exc)

    logger.info(
        "attempt: tenant=%s quiz=%s skor=%d/%d",
        req.tenant_id, quiz_id, score, total,
    )
    return AttemptResult(
        attempt_id=attempt["id"],
        quiz_id=quiz_id,
        score=score,
        total=total,
        duration_seconds=req.duration_seconds,
        per_kazanim=per_kazanim,
        results=results,
        completed_at=attempt["completed_at"],
    )


@router.post("/{quiz_id}/share", response_model=CreateShareResponse)
def share_quiz(
    quiz_id: str,
    tenant_id: str,
    _api_key: str = Depends(require_api_key),
) -> CreateShareResponse:
    """Quiz için link paylaşımı oluştur (idempotent) — yalnız sahibi.

    Dönen share_url görecedir (/q/{code}); frontend origin'i ekler.
    """
    res = QUIZ_STORE.create_share(quiz_id=quiz_id, owner_tenant_id=tenant_id)
    if res is None:
        raise HTTPException(status_code=404, detail="Quiz bulunamadı.")
    return CreateShareResponse(
        share_code=res["share_code"],
        share_url=f"/q/{res['share_code']}",
    )
