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

from fastapi import APIRouter, Depends, HTTPException, Request

from app.data.curriculum import get_topic
from app.data.units import find_unit_by_kazanim, get_unit, resolve_legacy_topic
from app.models.enums import Difficulty, QuestionType, SubjectId
from app.models.schemas import (
    AttemptResult,
    CreateQuizRequest,
    CreateShareResponse,
    Question,
    QuizPublic,
    QuizQuestionPublic,
    QuizReviewResponse,
    RegeneratedQuestionResponse,
    SubmitAttemptRequest,
)
from app.security import limiter, rate_limit_string, require_api_key
from app.services import entitlements
from app.services.agent import (
    AgentError,
    GeminiAgent,
    model_and_thinking_for,
)
from app.services.clerk_auth import require_tenant, verified_tenant_id
from app.services.grading import grade_quiz
from app.services.quiz_store import QUIZ_STORE
from app.services.structured import derive_structured_fields, validate_structured
from app.services.usage_ledger import STATUS_FAILED as LEDGER_FAILED
from app.services.usage_ledger import STATUS_OK as LEDGER_OK
from app.services.usage_ledger import USAGE_LEDGER

logger = logging.getLogger(__name__)

router = APIRouter()


def _record_gen_cost(
    traces: list,
    *,
    tenant_id: str | None,
    grade: int,
    topic: str,
    question_count: int,
    status: str = LEDGER_OK,
) -> None:
    """Quiz üretiminin Gemini maliyetini deftere yazar (worksheet akışıyla aynı kaynak).

    quiz üretimi de (create + regenerate) gerçek Gemini token'ı yakar ama önceden
    hiç kaydedilmiyordu → admin cost dashboard gerçek harcamayı olduğundan düşük
    gösteriyordu. `traces` = agent.build_last_trace() çıktıları (tek mod: 1;
    paralel zorluk bucket'ları: N). Best-effort — kayıt hatası akışı bozmaz.

    question_count kotayı etkiler (entitlements.check_quota, cache_hit=0 satırların
    question_count'unu sayar). Yeniden-üretim (regenerate) net-yeni üretim değil →
    çağıran question_count=0 geçerek kotayı şişirmez, yalnız maliyeti kaydeder.
    """
    if not traces:
        return
    prompt_tokens = sum(getattr(t, "prompt_tokens", 0) for t in traces)
    completion_tokens = sum(getattr(t, "completion_tokens", 0) for t in traces)
    cost_usd = sum(getattr(t, "estimated_cost_usd", 0.0) for t in traces)
    model = next((t.model_used for t in traces if getattr(t, "model_used", None)), "unknown")
    cache_hit = all(getattr(t, "cache_hit", False) for t in traces)
    USAGE_LEDGER.record(
        tenant_id=tenant_id,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=cost_usd,
        grade=grade,
        topic=topic,
        question_count=question_count,
        cache_hit=cache_hit,
        status=status,
    )

# Adım 0'da desteklenen 4 çözülebilir tip — üretim dağıtımına allowed_types olarak
# geçer. Eşleştirme/sıralama sonraki dilime bırakıldı.
_SOLVABLE_TYPES = [
    QuestionType.COKTAN_SECMELI,
    QuestionType.DOGRU_YANLIS,
    QuestionType.BOSLUK_DOLDURMA,
    # SALT_ISLEM (sayısal) → SOZEL_PROBLEM (açık uçlu): serbest cevap, ÖZ-DEĞERLENDİRME
    # ile puanlanır (öğrenci cevabı görür, kendini işaretler). Eski salt_islem quizleri
    # yine puanlanır (grading'de branch korunur).
    QuestionType.SOZEL_PROBLEM,
]


def _agent_for_model(model: str, thinking_budget: int | None = None) -> GeminiAgent:
    """İSTEK BAŞINA yeni agent. (Eskiden `@lru_cache` ile model başına TEKİLDİ.)

    Bkz. app/routers/worksheets.py::_agent_for_model — üretim izleri (maliyet,
    model, token, cache_hit) agent ÖRNEĞİNDE tutuluyor ve üretimden sonra
    `build_last_trace()` ile okunuyor; paylaşılan örnek eşzamanlı isteklerde bu
    izleri karıştırıp maliyeti yanlış tenant'a yazıyordu. Kurulum maliyeti
    ihmal edilebilir (ağ I/O yok)."""
    return GeminiAgent(model=model, thinking_budget=thinking_budget)


def _resolve_solvable_types(
    requested: list[QuestionType] | None,
    subject: SubjectId | None = None,
) -> list[QuestionType]:
    """İstenen tipleri çözülebilir havuza indir. None → 4 tip. Filtre sonrası boş
    olabilir (çağıran 400 döner).

    `subject` verilirse DERS uyumu da uygulanır (2026-08-24): çözülebilir havuzda
    `sozel_problem` (matematik sözel problemi) var ve istemciler soru-tipi gruplarını
    matematiğe göre sabit gönderiyordu → Türkçe quiz'inde matematik sorusu çıkıyordu.
    Ders süzgecinden hiçbir tip geçmezse dersin ÇÖZÜLEBİLİR varsayılanına düşülür
    (istek reddedilmez; kullanıcı yine quiz alır, ama doğru dersten).

    DİKKAT — iki farklı durum, iki farklı sonuç (CI regresyonu 2026-08-24):
      * Kullanıcı GEÇERLİ ama çözülebilir OLMAYAN bir tip seçtiyse (ör. matematikte
        yalnız `salt_islem`) sonuç BOŞTUR → router 400 döner ve kullanıcıya "bu
        tipler çözülemez" der. Bu sözleşme korunur.
      * İstek ders-farkında OLMAYAN bir istemciden geliyorsa (matematik grupları
        Türkçe'ye gönderilmiş) kısıt tümden bırakılır → dersin varsayılanı. Burada
        kullanıcıyı hataya düşürmek yanlış olur, çünkü seçimi arayüzde yaptı.
    """
    from app.subjects import filter_types_for_subject, supported_types

    # Dersin destekleyip AYNI ZAMANDA çözülebilir olan tipleri (varsayılan havuz).
    subject_solvable = [
        t for t in _SOLVABLE_TYPES
        if subject is None or t in supported_types(subject)
    ] or list(_SOLVABLE_TYPES)
    if not requested:
        return subject_solvable
    if subject is not None:
        kept, dropped = filter_types_for_subject(subject, requested)
        if dropped:
            if kept is None:  # ders-farkında olmayan istek → kısıt yok
                return subject_solvable
            requested = kept
    return [t for t in requested if t in subject_solvable]


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


def _generate_solvable(req: CreateQuizRequest) -> tuple[list[Question], str, list]:
    """Çözülebilir mod üretim: seçili tipler + zorluk modu; derive+validate'den
    geçenler kalır. Dönüş: (geçerli sorular [1..n numaralı], görünen ad, trace'ler).

    trace'ler = üretimde kullanılan agent'ların build_last_trace() çıktısı (Gemini
    maliyet defterine yazmak için); tek modda 1, paralel zorluk bucket'larında N."""
    from app.models.enums import SubjectId
    from app.subjects import get_content_module, subject_enabled
    # ── Non-math ders (fen/ingilizce/…) — feature flag + ünite ────────────────
    if req.subject != SubjectId.MATEMATIK:
        if not subject_enabled(req.subject):
            raise HTTPException(
                status_code=403,
                detail=f"'{req.subject.value}' dersi henüz yayında değil (kalite kapısı).",
            )
        content = get_content_module(req.subject)
        if content is None:
            raise HTTPException(status_code=400, detail=f"Desteklenmeyen ders: {req.subject.value}")
        if not req.unit_id:
            raise HTTPException(status_code=400, detail=f"'{req.subject.value}' ünite bazlıdır: unit_id zorunlu.")
        _u = content.get_unit(req.grade, req.unit_id)
        if _u is None:
            raise HTTPException(
                status_code=404,
                detail=f"{req.grade}. sınıf '{req.subject.value}'de '{req.unit_id}' ünitesi bulunmuyor.",
            )
        display_name = _u["name"]
    # Yeni seçim akışı: MEB ünite (tema). Şema unit_id XOR topic_id garantiler.
    elif req.unit_id:
        unit = get_unit(req.grade, req.unit_id)
        if unit is None:
            raise HTTPException(
                status_code=404,
                detail=f"{req.grade}. sınıfta '{req.unit_id}' ünitesi bulunmuyor.",
            )
        display_name = unit["name"]
    else:
        topic = get_topic(req.grade, req.topic_id)
        if topic is None:
            raise HTTPException(
                status_code=404,
                detail=f"{req.grade}. sınıfta '{req.topic_id}' konusu bulunmuyor.",
            )
        display_name = topic["name"]
    allowed = _resolve_solvable_types(req.question_types, req.subject)
    if not allowed:
        raise HTTPException(
            status_code=400,
            detail="Seçilen tipler çözülebilir değil; en az bir çözülebilir tip seçin.",
        )

    # Model + thinking POLİTİKAYLA (grade + geometri + zorluk + gerçek premium);
    # her bucket kendi zorluğuna göre model seçer (premium 5-7 zor→3.5).
    _is_premium = entitlements.is_premium_for_model(req.tenant_id)

    def _agent_for_diff(diff: Difficulty) -> GeminiAgent:
        model, tb = model_and_thinking_for(
            req.grade, subject=req.subject, topic_id=req.topic_id,
            unit_id=req.unit_id, difficulty=diff, is_premium=_is_premium,
        )
        # Her çağrı İZOLE agent (trace state yarışı — bkz. _agent_for_model).
        return _agent_for_model(model, tb)

    def _gen(agent: GeminiAgent, diff: Difficulty, count: int) -> list[Question]:
        return agent.generate(
            grade=req.grade,
            topic_id=req.topic_id,
            kazanim_kod=req.kazanim_kod,
            difficulty=diff,
            question_count=count,
            tenant_id=req.tenant_id,
            allowed_types=allowed,
            # yeni_nesil quiz'e de bağlandı: premium full, ücretsiz teaser (tek bucket).
            yeni_nesil=entitlements.yeni_nesil_for_bucket(req.tenant_id, diff),
            unit_id=req.unit_id,
            subject=req.subject,
        )

    raw: list[Question] = []
    traces: list = []  # Gemini maliyet defteri için (build_last_trace çıktıları).
    if req.difficulty_mode == "single":
        single_agent = _agent_for_diff(req.difficulty)
        try:
            raw = _gen(single_agent, req.difficulty, req.question_count)
        except AgentError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        traces.append(single_agent.build_last_trace())
    else:
        # Karışık/progresyon: kolay/orta/zor bucket'ları paralel üret (latency).
        buckets = _split_buckets(req.question_count)
        seq = [d for d in (Difficulty.KOLAY, Difficulty.ORTA, Difficulty.ZOR)
               if buckets.get(d, 0) > 0]

        def _gen_bucket(diff: Difficulty):
            # İzole (fresh) agent → paylaşılan trace/durum yarışı olmaz; modeli
            # kendi zorluğuna göre seçer (premium 5-7 zor→3.5).
            local_agent = _agent_for_diff(diff)
            try:
                qs = _gen(local_agent, diff, buckets[diff])
                return diff, qs, local_agent.build_last_trace(), None
            except Exception as exc:  # noqa: BLE001
                logger.warning("Quiz bucket başarısız (diff=%s): %s", diff.value, exc)
                return diff, [], None, str(exc)

        results: dict[Difficulty, list[Question]] = {}
        with ThreadPoolExecutor(max_workers=len(seq)) as ex:
            for diff, qs, tr, _err in ex.map(_gen_bucket, seq):
                results[diff] = qs
                if tr is not None:
                    traces.append(tr)
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
    return valid, display_name, traces


def _to_public(
    *,
    quiz_id: str,
    title: str,
    grade: int,
    topic_id: str,
    difficulty: Difficulty,
    created_at: str,
    questions: list[Question],
    answer_mode: str = "quiz",
) -> QuizPublic:
    """Cevaplı Question listesini CEVAPSIZ QuizPublic'e dönüştürür (anti-kopya).

    Çoktan seçmelide `options` (şıklar — cevap değil) gönderilir; boşluk
    doldurmada yalnız `blank_count` (kaç giriş). Diğer her şey soyulur.

    answer_mode="worksheet" (sınıf worksheet ödevi): açık uçlu/yapılandırılmamış tipler
    self-eval yerine metin-eşleştirmeyle puanlanır → cevap HİÇ açığa çıkarılmaz
    (reveal_answer=None); frontend metin kutusu gösterir. "quiz" (varsayılan, Çöz&Geliş)
    açık uçluda cevabı öz-değerlendirme için açar.
    """
    pub: list[QuizQuestionPublic] = []
    for q in questions:
        is_mcq = q.question_type == QuestionType.COKTAN_SECMELI
        is_blank = q.question_type == QuestionType.BOSLUK_DOLDURMA
        # Açık uçlu (öz-değerlendirme): otomatik puanlanamaz → cevap istemciye AÇILIR
        # (öğrenci "cevabı gör" deyip kendini işaretler). Diğer tiplerde cevap gizli.
        # worksheet modunda self-eval yok → hiçbir cevap açılmaz (kopya önleme korunur).
        is_open = q.question_type == QuestionType.SOZEL_PROBLEM
        reveal = q.answer if (is_open and answer_mode == "quiz") else None
        pub.append(
            QuizQuestionPublic(
                number=q.number,
                question=q.question,
                question_type=q.question_type,
                kazanim_kod=q.kazanim_kod,
                options=q.options if is_mcq else None,
                blank_count=(len(q.blanks) if (is_blank and q.blanks) else None),
                reveal_answer=reveal,
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
        answer_mode=answer_mode,
    )


@router.post("", response_model=QuizPublic)
@limiter.limit(rate_limit_string())
def create_quiz(
    request: Request,
    req: CreateQuizRequest,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> QuizPublic:
    """Çözülebilir quiz üret + kaydet → CEVAPSIZ döndür. LLM çağrısı (rate limitli)."""
    # Kota birimi = 1 çalışma kağıdı. Dönüş: ek paket kredisi düşüldü mü → quiz
    # teslim edilemezse iade edilir (kredi kapıda düşülmek zorunda, ama alınmayan
    # quiz'in parası kullanıcıda kalmalı — bkz. entitlements.refund_topup).
    topup_charged = entitlements.enforce_quota(verified)
    # Sahiplik client-supplied tenant'a DEĞİL, doğrulanmış kimliğe bağlanır (IDOR/spoof).
    req.tenant_id = require_tenant(verified, req.tenant_id)
    try:
        questions, topic_name, traces = _generate_solvable(req)
    except Exception:
        if topup_charged:
            entitlements.refund_topup(verified)
        raise
    # Gemini maliyet defteri — quiz üretimi de gerçek token yakar (worksheet ile
    # aynı kaynak). question_count teslim edilen soru = quota tüketimi.
    # Boş sonuç = para harcandı, quiz teslim EDİLMEDİ → 'failed'. Bu satır zaten
    # yazılıyordu (kayıt 502'den ÖNCE) ama 'ok' sayıldığı için hem "teslim edilen
    # üretim" sayımını şişiriyor hem de kağıt-bazlı kotadan bir kağıt yiyordu.
    _record_gen_cost(
        traces,
        tenant_id=req.tenant_id,
        grade=req.grade,
        topic=topic_name,
        question_count=len(questions),
        status=LEDGER_OK if questions else LEDGER_FAILED,
    )
    if not questions:
        # Üretilenlerin hiçbiri yapısal doğrulamadan geçmedi (nadir) → tekrar deneyin.
        if topup_charged:
            entitlements.refund_topup(verified)
        raise HTTPException(
            status_code=502,
            detail="Çözülebilir soru üretilemedi; lütfen tekrar deneyin.",
        )
    title = f"{req.grade}. Sınıf - {topic_name} Quiz"
    # topic_id kaydı: ünite akışında legacy topic'e köprüle (downstream string bekler).
    store_topic_id = req.topic_id or resolve_legacy_topic(
        req.grade, req.unit_id, req.kazanim_kod
    ) or "dogal_sayilar"
    record = QUIZ_STORE.create(
        owner_tenant_id=req.tenant_id,
        title=title,
        grade=req.grade,
        topic_id=store_topic_id,
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
        topic_id=store_topic_id,
        difficulty=req.difficulty,
        created_at=record["created_at"],
        questions=questions,
    )


@router.get("/{quiz_id}", response_model=QuizPublic)
def get_quiz(
    quiz_id: str,
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> QuizPublic:
    """Quiz'i çözmek için getir — CEVAPSIZ, yalnız sahibi (tenant_id) erişir."""
    tenant_id = require_tenant(verified, tenant_id)
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


@router.get("/{quiz_id}/review", response_model=QuizReviewResponse)
def review_quiz(
    quiz_id: str,
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> QuizReviewResponse:
    """Quiz'i sahibine CEVAPLI getir — öğretmen atamadan önce soruları inceler.

    Kopya önleme sahibe uygulanmaz (kendi ürettiği içerik). Yalnız quiz'in sahibi
    (tenant_id) erişir; başkası 404 alır → başka öğretmenin/öğrencinin quiz'i sızmaz.
    """
    tenant_id = require_tenant(verified, tenant_id)
    record = QUIZ_STORE.get(quiz_id, tenant_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Quiz bulunamadı.")
    questions = [Question(**q) for q in record["questions"]]
    return QuizReviewResponse(
        id=record["id"],
        title=record["title"],
        grade=record["grade"],
        topic_id=record["topic_id"],
        difficulty=Difficulty(record["difficulty"]),
        question_count=len(questions),
        questions=questions,
        created_at=record["created_at"],
    )


def _regenerate_one_question(
    *, grade: int, kazanim_kod: str, question_type: QuestionType,
    difficulty: Difficulty, fallback_topic_id: str, tenant_id: str,
) -> Question | None:
    """Tek soruyu aynı kazanım + tip + zorlukta yeniden üretir (LLM). Ders kazanım
    kodundan çözülür; ünite bulunamazsa quiz'in kayıtlı topic_id'sine düşer. Yapısal
    doğrulamadan geçen ilk soruyu döndürür; hiçbiri geçmezse None."""
    from app.models.enums import SubjectId
    from app.services.subject_resolve import resolve_kazanim
    from app.subjects import get_content_module, subject_enabled

    subject, _, _ = resolve_kazanim(kazanim_kod)
    # Ders-tip kapısı: eski/bozuk kayıtta soru matematik tipinde etiketli olabilir;
    # aynı tipte yeniden üretmek Türkçe quiz'ine yine matematik sorusu koyardı.
    # Derse uygun DEĞİLSE dersin çözülebilir varsayılanına düşülür.
    if question_type not in set(_resolve_solvable_types(None, subject)):
        question_type = _resolve_solvable_types(None, subject)[0]
    topic_id: str | None = None
    unit_id: str | None = None
    if subject != SubjectId.MATEMATIK:
        if not subject_enabled(subject):
            raise HTTPException(
                status_code=403,
                detail=f"'{subject.value}' dersi henüz yayında değil (kalite kapısı).",
            )
        content = get_content_module(subject)
        found = content.find_unit_by_kazanim(kazanim_kod) if content else None
        if found is None:
            raise HTTPException(
                status_code=400,
                detail=f"'{kazanim_kod}' kodu '{subject.value}' müfredatında bulunamadı.",
            )
        unit_id = found[1]["unit_id"]
    else:
        found = find_unit_by_kazanim(kazanim_kod)
        if found is not None:
            unit_id = found[1]["unit_id"]
        else:
            topic_id = fallback_topic_id  # legacy M.* / topic-bazlı quiz
    _model, _tb = model_and_thinking_for(
        grade, subject=subject, topic_id=topic_id, unit_id=unit_id,
        difficulty=difficulty, is_premium=entitlements.is_premium_for_model(tenant_id),
    )
    agent = _agent_for_model(_model, _tb)
    try:
        raw = agent.generate(
            grade=grade,
            topic_id=topic_id,
            kazanim_kod=kazanim_kod,
            difficulty=difficulty,
            question_count=1,
            tenant_id=tenant_id,
            allowed_types=[question_type],
            yeni_nesil=entitlements.yeni_nesil_for_bucket(tenant_id, difficulty),
            unit_id=unit_id,
            subject=subject,
        )
    except AgentError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    # Maliyet defteri: yeniden-üretim de token yakar. question_count=0 → net-yeni
    # üretim değil (mevcut soruyu değiştirir), kotayı şişirmesin; ama gerçek maliyet
    # (thinking token dahil) dashboard'a yansısın.
    _record_gen_cost(
        [agent.build_last_trace()],
        tenant_id=tenant_id,
        grade=grade,
        topic="quiz-regenerate",
        question_count=0,
    )
    for q in raw:
        enriched = derive_structured_fields(q)
        ok, _issues = validate_structured(enriched)
        if ok:
            return enriched
    return None


@router.post(
    "/{quiz_id}/questions/{number}/regenerate",
    response_model=RegeneratedQuestionResponse,
)
@limiter.limit(rate_limit_string())
def regenerate_quiz_question(
    request: Request,
    quiz_id: str,
    number: int,
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> RegeneratedQuestionResponse:
    """Sahibin quiz'inde `number` numaralı soruyu yeniden üretir + kalıcı kılar.

    Öğretmen beğenmediği soruyu tek tık değiştirir. LLM çağrısı (rate limitli).
    Yalnız quiz sahibi; sonuç CEVAPLI döner (sahip görünümü)."""
    tenant_id = require_tenant(verified, tenant_id)
    record = QUIZ_STORE.get(quiz_id, tenant_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Quiz bulunamadı.")
    target = next(
        (Question(**q) for q in record["questions"] if q.get("number") == number),
        None,
    )
    if target is None:
        raise HTTPException(status_code=404, detail="Soru bulunamadı.")
    new_q = _regenerate_one_question(
        grade=record["grade"],
        kazanim_kod=target.kazanim_kod,
        question_type=target.question_type,
        difficulty=Difficulty(record["difficulty"]),
        fallback_topic_id=record["topic_id"],
        tenant_id=tenant_id,
    )
    if new_q is None:
        raise HTTPException(
            status_code=502, detail="Yeni soru üretilemedi; lütfen tekrar deneyin."
        )
    new_q = new_q.model_copy(update={"number": number})
    if not QUIZ_STORE.replace_question(
        quiz_id, tenant_id, number, new_q.model_dump()
    ):
        raise HTTPException(status_code=404, detail="Soru güncellenemedi.")
    logger.info(
        "quiz sorusu yenilendi: tenant=%s quiz=%s no=%d", tenant_id, quiz_id, number
    )
    return RegeneratedQuestionResponse(question=new_q)


@router.post("/{quiz_id}/attempt", response_model=AttemptResult)
def submit_attempt(
    quiz_id: str,
    req: SubmitAttemptRequest,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> AttemptResult:
    """Cevapları gönder → sunucuda LLM'siz puanla → sonuç + kazanım kırılımı.

    Puanlama sunucuda yapılır (cevaplar istemcide yok). Sonuçta doğru cevap +
    çözüm açığa çıkar (çözüm sonrası geri bildirim). Deneme + mastery kaydedilir.
    """
    req.tenant_id = require_tenant(verified, req.tenant_id)
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
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> CreateShareResponse:
    """Quiz için link paylaşımı oluştur (idempotent) — yalnız sahibi.

    Dönen share_url görecedir (/q/{code}); frontend origin'i ekler.
    """
    tenant_id = require_tenant(verified, tenant_id)
    res = QUIZ_STORE.create_share(quiz_id=quiz_id, owner_tenant_id=tenant_id)
    if res is None:
        raise HTTPException(status_code=404, detail="Quiz bulunamadı.")
    return CreateShareResponse(
        share_code=res["share_code"],
        share_url=f"/q/{res['share_code']}",
    )
