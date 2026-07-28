import asyncio
import json
import logging
from datetime import datetime, timezone
from functools import lru_cache
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import ValidationError

from app.config import settings
from app.data.curriculum import get_topic
from app.data.units import find_unit_by_kazanim, get_unit
from app.models.enums import TopicId
from app.models.schemas import (
    AnswerKeyEntry,
    GenerateWorksheetRequest,
    GenerateWorksheetResponse,
    RegenerateQuestionRequest,
    RenderRequest,
    Worksheet,
    WorksheetMetadata,
)
from app.security import limiter, rate_limit_string, require_api_key
from app.services import entitlements
from app.services.agent import (
    AgentError,
    GeminiAgent,
    model_and_thinking_for,
)
from app.services.clerk_auth import require_tenant, verified_tenant_id
from app.services.pdf_renderer import render_worksheet_pdf
from app.services.usage_ledger import USAGE_LEDGER
from app.services.worksheet_history import WORKSHEET_HISTORY

router = APIRouter()
logger = logging.getLogger(__name__)


@lru_cache(maxsize=16)
def _agent_for_model(model: str, thinking_budget: int | None = None) -> GeminiAgent:
    """Model başına tekil (cache'li) agent. Model seçimi sınıfa göre yapılır
    (model_for_grade); premium/yeni_nesil model değil prompt+dağılımı etkiler.
    thinking_budget sınıf bandına göre gelir (cache anahtarına dahil).
    DİKKAT: paralel bucket modunda paylaşılan agent kullanılamaz (trace state
    yarışı) — orada her bucket kendi izole GeminiAgent'ını oluşturur."""
    return GeminiAgent(model=model, thinking_budget=thinking_budget)


def _validate_request(req: GenerateWorksheetRequest) -> None:
    from app.models.enums import SubjectId
    from app.subjects import get_content_module, subject_enabled
    # ── Non-math ders (fen/ingilizce/…) — feature flag + ünite bazlı müfredat ──
    if req.subject != SubjectId.MATEMATIK:
        if not subject_enabled(req.subject):
            raise HTTPException(
                status_code=403,
                detail=f"'{req.subject.value}' dersi henüz yayında değil (kalite kapısı).",
            )
        content = get_content_module(req.subject)
        if content is None:
            raise HTTPException(
                status_code=400, detail=f"Desteklenmeyen ders: {req.subject.value}"
            )
        if not req.unit_id:
            raise HTTPException(
                status_code=400,
                detail=f"'{req.subject.value}' üretimi ünite bazlıdır: unit_id zorunlu.",
            )
        unit = content.get_unit(req.grade, req.unit_id)
        if unit is None:
            raise HTTPException(
                status_code=400,
                detail=f"{req.grade}. sınıf '{req.subject.value}'de '{req.unit_id}' ünitesi bulunmuyor.",
            )
        if req.kazanim_kod is not None and not any(
            k["kod"] == req.kazanim_kod for k in unit["kazanimlar"]
        ):
            raise HTTPException(
                status_code=400,
                detail=f"'{req.kazanim_kod}' kodu '{req.unit_id}' ünitesinde bulunamadı.",
            )
        return
    # Yeni seçim akışı: MEB ünite (tema). Şema unit_id XOR topic_id garantiler.
    if req.unit_id:
        unit = get_unit(req.grade, req.unit_id)
        if unit is None:
            raise HTTPException(
                status_code=400,
                detail=f"{req.grade}. sınıfta '{req.unit_id}' ünitesi müfredatta yok.",
            )
        if req.kazanim_kod is not None and not any(
            k["kod"] == req.kazanim_kod for k in unit["kazanimlar"]
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"'{req.kazanim_kod}' kodu {req.grade}. sınıf '{req.unit_id}' "
                    "ünitesinde bulunamadı."
                ),
            )
        return
    # Eski akış (geriye-uyum): topic_id.
    valid_topic_ids = {t.value for t in TopicId}
    if req.topic_id not in valid_topic_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Geçersiz topic_id '{req.topic_id}'. Geçerliler: {sorted(valid_topic_ids)}",
        )
    topic = get_topic(req.grade, req.topic_id)
    if topic is None:
        raise HTTPException(
            status_code=400,
            detail=f"{req.grade}. sınıfta '{req.topic_id}' konusu müfredatta yok.",
        )
    if req.kazanim_kod is not None:
        if not any(k["kod"] == req.kazanim_kod for k in topic["kazanimlar"]):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"'{req.kazanim_kod}' kodu {req.grade}. sınıf '{req.topic_id}' "
                    "konusunda bulunamadı."
                ),
            )


def _split_difficulty_buckets(total: int) -> dict["Difficulty", int]:
    """Karışık/progresyon modu için zorluk dağılımı.

    Hedef oran: kolay 30%, orta 40%, zor 30%. Toplam < 5 için anlamlı bölüm
    çıkmayacağından tek seviye fallback verilir.
    """
    from app.models.enums import Difficulty
    if total < 5:
        return {Difficulty.ORTA: total}
    kolay = max(1, total * 3 // 10)
    zor = max(1, total * 3 // 10)
    orta = total - kolay - zor
    if orta < 1:
        return {Difficulty.ORTA: total}
    return {Difficulty.KOLAY: kolay, Difficulty.ORTA: orta, Difficulty.ZOR: zor}


def _merge_traces(traces: list):
    """Paralel bucket trace'lerini tek metadata trace'ine birleştirir.

    Token/maliyet/eleme sayaçları toplanır; model/sağlayıcı/few-shot kaynağı gibi
    temsilî alanlar ilk başarılı bucket'tan alınır. Boşsa None.
    """
    if not traces:
        return None
    if len(traces) == 1:
        return traces[0]
    base = traces[0]
    return base.model_copy(update={
        "prompt_tokens": sum(t.prompt_tokens for t in traces),
        "completion_tokens": sum(t.completion_tokens for t in traces),
        "estimated_cost_usd": sum(t.estimated_cost_usd for t in traces),
        "math_verifier_rejected": sum(t.math_verifier_rejected for t in traces),
        "critic_rejected": sum(t.critic_rejected for t in traces),
        "dedup_rejected_string": sum(t.dedup_rejected_string for t in traces),
        "dedup_rejected_semantic": sum(t.dedup_rejected_semantic for t in traces),
        "retry_rounds": sum(t.retry_rounds for t in traces),
        "requested_count": sum(t.requested_count for t in traces),
        "delivered_count": sum(t.delivered_count for t in traces),
        # cache_hit yalnız TÜM bucket'lar cache'ten geldiyse true. Aksi halde en
        # az bir bucket üretildi (yavaş) → "cache hit" demek yanıltıcı olur.
        "cache_hit": all(t.cache_hit for t in traces),
        # Depo isabeti (Faz 2, §3b, docs/COST_QUALITY_V2_PLAN.md) — her bucket
        # kendi pool_key'inden BAĞIMSIZ çeker; toplam olmadan mixed/progressive
        # (üretimin en yaygın modu) için depo tasarrufu ÖLÇÜLEMEZ.
        "pool_hit_count": sum(t.pool_hit_count for t in traces),
        # Pool-first'in ESKİ havuz satırlarını denetleyip elediği sayaçlar —
        # `math_verifier_rejected`/`critic_rejected`'tan AYRI tutulur (Küçük 1,
        # Opus denetimi): aksi halde mixed modda "kalite düştü" ile "havuz
        # temizliği" ayırt edilemezdi.
        "pool_math_rejected": sum(t.pool_math_rejected for t in traces),
        "pool_critic_rejected": sum(t.pool_critic_rejected for t in traces),
    })


def _build_worksheet(req: GenerateWorksheetRequest) -> tuple[Worksheet, WorksheetMetadata]:
    """Ortak üretim mantığı: hem JSON hem PDF endpoint'leri kullanır.

    Sprint 12-A toggle paketi (2026-05-19):
        difficulty_mode = "single"     → tek difficulty ile mevcut akış
        difficulty_mode = "mixed"      → kolay/orta/zor 3 ayrı agent.generate;
                                         birleştirilip rastgele karıştırılır.
        difficulty_mode = "progressive"→ aynı 3 batch; kolay → orta → zor sırası.
        question_types verilirse agent.generate'e allowed_types geçer.
    """
    from app.models.enums import Difficulty as _Diff
    from app.models.enums import SubjectId
    from app.subjects import get_content_module
    _validate_request(req)
    # Görünen ad: ders/akışa göre tema/konu adı (başlık/geçmiş/defter).
    if req.subject != SubjectId.MATEMATIK:
        _u = get_content_module(req.subject).get_unit(req.grade, req.unit_id)
        assert _u is not None  # _validate_request doğruladı
        display_name = _u["name"]
    elif req.unit_id:
        _unit = get_unit(req.grade, req.unit_id)
        assert _unit is not None
        display_name = _unit["name"]
    else:
        topic = get_topic(req.grade, req.topic_id)
        assert topic is not None
        display_name = topic["name"]

    # "Yeni nesil" gizli kalite kaldıracı: karar SUNUCUDA, premium yetkiye göre
    # verilir (client bir bayrak gönderemez). Ücretsiz → normal, premium → yeni nesil.
    # Model + thinking seçimi POLİTİKAYLA: grade + geometri teması + zorluk + GERÇEK
    # premium (is_premium_for_model — premium_all dark-launch değil). Zorluğa bağlı
    # olduğu için her bucket kendi (model, thinking)'ini alır (premium 5-7 zor→3.5).
    _is_premium = entitlements.is_premium_for_model(req.tenant_id)

    def _agent_for_diff(diff: _Diff, *, fresh: bool = False) -> GeminiAgent:
        model, tb = model_and_thinking_for(
            req.grade, subject=req.subject, topic_id=req.topic_id,
            unit_id=req.unit_id, difficulty=diff, is_premium=_is_premium,
        )
        # Paralel bucket'larda paylaşılan (lru_cache) agent trace state yarışı
        # yaratır → izole (fresh) instance. Tek modda cache'li yeterli.
        return GeminiAgent(model=model, thinking_budget=tb) if fresh else _agent_for_model(model, tb)

    def _gen(agent: GeminiAgent, diff: _Diff, count: int) -> list:
        return agent.generate(
            grade=req.grade,
            topic_id=req.topic_id,
            kazanim_kod=req.kazanim_kod,
            difficulty=diff,
            question_count=count,
            tenant_id=req.tenant_id,
            allowed_types=req.question_types,
            # yeni_nesil bucket-bazlı: premium full, ücretsiz teaser (tek bucket).
            yeni_nesil=entitlements.yeni_nesil_for_bucket(req.tenant_id, diff),
            unit_id=req.unit_id,
            subject=req.subject,
        )

    if req.difficulty_mode == "single":
        agent = _agent_for_diff(req.difficulty)
        try:
            questions = _gen(agent, req.difficulty, req.question_count)
        except AgentError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        trace_for_meta = agent.build_last_trace()
        worksheet_difficulty = req.difficulty
    else:
        # Mixed/progressive: kolay/orta/zor bucket'ları. Her bucket bağımsız bir
        # agent.generate (~3-5 LLM call). Bucket-başına hata yakalanır: en az 1
        # bucket başarılıysa kısmi sonuç döner (tüm istek çökmez).
        #
        # LATENCY (#1): bucket'lar paralel koşar (settings.parallel_difficulty_
        # buckets). Ardışık 3 bucket ~3× süre alıyordu; paralelde ~1× (en yavaş
        # bucket). Bağımsızlar — her biri farklı difficulty → farklı history_key,
        # dedup karışmaz; GENERATION_HISTORY/CACHE lock-serialized (thread-safe).
        # Paralelde her bucket KENDİ GeminiAgent'ıyla çalışır → paylaşılan trace
        # state (_last_*) yarışı olmaz. 429 burst'ü artık transient-retry/backoff
        # ile toparlandığından eski time.sleep(1.5) yumuşatması gereksiz.
        buckets = _split_difficulty_buckets(req.question_count)
        bucket_seq = [d for d in (_Diff.KOLAY, _Diff.ORTA, _Diff.ZOR)
                      if buckets.get(d, 0) > 0]

        def _gen_bucket(diff: "_Diff"):
            """Tek bucket üretir; modeli/thinking'i KENDİ zorluğuna göre seçer
            (premium 5-7 zor→3.5). Paralel modda izole (fresh) agent."""
            local_agent = _agent_for_diff(
                diff, fresh=settings.parallel_difficulty_buckets
            )
            try:
                qs = _gen(local_agent, diff, buckets[diff])
                return diff, qs, local_agent.build_last_trace(), None
            except Exception as exc:  # noqa: BLE001
                # AgentError + paralelliğin getirdiği embedding/429 gibi hatalar:
                # bir bucket'ın hatası tüm kağıdı çökertmesin — kısmi sonuçla
                # devam et (en az 1 bucket başarılıysa worksheet üretilir).
                logger.warning(
                    "Bucket başarısız (diff=%s, n=%s): %s — kısmi sonuçla devam.",
                    diff.value, buckets[diff], exc,
                )
                return diff, [], None, f"{diff.value}: {type(exc).__name__}: {exc}"

        results: dict = {}
        if settings.parallel_difficulty_buckets and len(bucket_seq) > 1:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=len(bucket_seq)) as ex:
                for diff, qs, tr, err in ex.map(_gen_bucket, bucket_seq):
                    results[diff] = (qs, tr, err)
        else:
            for diff in bucket_seq:
                d, qs, tr, err = _gen_bucket(diff)
                results[d] = (qs, tr, err)

        # bucket_seq sırasında topla (progressive: kolay→orta→zor korunur).
        collected: list = []
        bucket_errors: list[str] = []
        bucket_traces: list = []
        for diff in bucket_seq:
            qs, tr, err = results[diff]
            collected.extend(qs)
            if tr is not None:
                bucket_traces.append(tr)
            if err:
                bucket_errors.append(err)

        if not collected:
            # Hiçbir bucket başarılı olmadı — gerçek hata.
            detail = "Üretim başarısız (tüm zorluk grupları hata verdi). "
            if bucket_errors:
                detail += "Sebep: " + " | ".join(bucket_errors[:3])
            raise HTTPException(status_code=502, detail=detail)

        if req.difficulty_mode == "mixed":
            import random as _random
            _random.shuffle(collected)
        # progressive ise zaten kolay→orta→zor sırasında toplandı.
        from app.models.schemas import Question as _Q
        questions = [
            q.model_copy(update={"number": i + 1}) if isinstance(q, _Q) else q
            for i, q in enumerate(collected)
        ]
        trace_for_meta = _merge_traces(bucket_traces)
        worksheet_difficulty = req.difficulty

    if not questions:
        raise HTTPException(
            status_code=502,
            detail="Üretim sonucu boş geldi; lütfen tekrar deneyin.",
        )

    title = f"{req.grade}. Sınıf - {display_name} Çalışma Kağıdı"
    worksheet = Worksheet(
        title=title,
        grade=req.grade,
        topic=display_name,
        difficulty=worksheet_difficulty,
        question_count=len(questions),
        questions=questions,
        answer_key=[
            AnswerKeyEntry(number=q.number, answer=q.answer) for q in questions
        ],
    )
    # NOT: `agent` YALNIZ single modda bağlanır; mixed/progressive'de bucket'lar
    # kendi (local_agent) örnekleriyle çalışır. Burada `agent.last_model_used`
    # okumak mixed/progressive'de UnboundLocalError → HTTP 500 veriyordu: üretim
    # (3 bucket × LLM çağrısı) TAMAMEN yapılıp para harcandıktan SONRA istek
    # çöküyordu. Model adını trace'ten al (her iki modda dolu).
    metadata = WorksheetMetadata(
        generated_at=datetime.now(tz=timezone.utc),
        model=(trace_for_meta.model_used if trace_for_meta is not None else "unknown"),
        trace=trace_for_meta,
    )

    # Gemini maliyet defteri — HER üretim için (ANONİM DAHİL). Gerçek Gemini
    # harcamasını (üretim+retry+top-up+critic+embedding) tenant/anon bazında kalıcı
    # kaydeder → admin cost dashboard'un kaynağı. Best-effort, üretimi bozmaz.
    if trace_for_meta is not None:
        USAGE_LEDGER.record(
            tenant_id=req.tenant_id,
            model=trace_for_meta.model_used,
            prompt_tokens=trace_for_meta.prompt_tokens,
            completion_tokens=trace_for_meta.completion_tokens,
            cost_usd=trace_for_meta.estimated_cost_usd,
            grade=req.grade,
            topic=display_name,
            question_count=worksheet.question_count,
            cache_hit=bool(getattr(trace_for_meta, "cache_hit", False)),
        )

    # Kullanıcı (tenant) bazlı geçmiş kaydı — yalnızca giriş yapmış kullanıcı
    # için (tenant_id Clerk userId'sidir). Best-effort: kayıt hatası üretimi
    # bozmaz. Gözlemlenebilirlik: her üretim için tek satır log düşülür.
    if settings.enable_worksheet_history:
        if req.tenant_id:
            try:
                item = WORKSHEET_HISTORY.add(
                    tenant_id=req.tenant_id,
                    request={
                        "grade": req.grade,
                        "unit_id": req.unit_id,
                        "topic_id": req.topic_id,
                        "kazanim_kod": req.kazanim_kod,
                        "difficulty": worksheet_difficulty.value,
                        "question_count": worksheet.question_count,
                    },
                    response={
                        "worksheet": worksheet.model_dump(mode="json"),
                        "metadata": metadata.model_dump(mode="json"),
                    },
                )
                logger.info(
                    "worksheet_history KAYDEDİLDİ: tenant=%s id=%s",
                    req.tenant_id, item["id"] if item else "?",
                )
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "worksheet_history KAYIT HATASI: tenant=%s — %s",
                    req.tenant_id, exc, exc_info=True,
                )
        else:
            logger.warning(
                "worksheet_history ATLANDI: istekte tenant_id yok "
                "(frontend Clerk userId göndermemiş — giriş/oturum sorunu)."
            )

    return worksheet, metadata


@router.post("/generate", response_model=GenerateWorksheetResponse)
@limiter.limit(rate_limit_string())
def generate_worksheet(
    request: Request,
    req: GenerateWorksheetRequest,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> GenerateWorksheetResponse:
    entitlements.enforce_quota(verified)  # kota birimi = 1 çalışma kağıdı (soru sayısı değil)
    worksheet, metadata = _build_worksheet(req)
    return GenerateWorksheetResponse(worksheet=worksheet, metadata=metadata)


# Türkçe karakterleri ASCII karşılıklarına çevirir; başlığa benzer şekilde
# frontend/lib'de de aynı haritalama var (PDF dosya adı tutarlılığı için).
_TURKISH_TRANSLIT = str.maketrans({
    "ş": "s", "Ş": "S",
    "ı": "i", "İ": "I",
    "ğ": "g", "Ğ": "G",
    "ç": "c", "Ç": "C",
    "ö": "o", "Ö": "O",
    "ü": "u", "Ü": "U",
})


def _build_pdf_filename(worksheet: Worksheet) -> str:
    title_ascii = worksheet.title.translate(_TURKISH_TRANSLIT)
    cleaned = "".join(
        c if c.isalnum() or c in " -_" else " " for c in title_ascii
    )
    parts = [p for p in cleaned.split() if p]
    slug = "_".join(parts) if parts else "Calisma_Kagidi"
    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    return f"SoruAtolyesi_{slug}_{today}.pdf"


def _pdf_response(
    worksheet: Worksheet,
    include_answer_key: bool = True,
    include_solutions: bool = True,
    brand_name: str | None = None,
    brand_subtitle: str | None = None,
    brand_logo: str | None = None,
) -> Response:
    pdf_bytes = render_worksheet_pdf(
        worksheet,
        include_answer_key=include_answer_key,
        include_solutions=include_solutions,
        brand_name=brand_name,
        brand_subtitle=brand_subtitle,
        brand_logo=brand_logo,
    )
    filename = _build_pdf_filename(worksheet)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.post("/generate.pdf")
@limiter.limit(rate_limit_string())
def generate_worksheet_pdf(
    request: Request,
    req: GenerateWorksheetRequest,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> Response:
    """Üretim + PDF render tek call'da. Rate limit + auth uygulanır (LLM çağrısı yapar)."""
    entitlements.enforce_quota(verified)  # kota birimi = 1 çalışma kağıdı (soru sayısı değil)
    worksheet, _ = _build_worksheet(req)
    return _pdf_response(
        worksheet,
        include_answer_key=req.include_answer_key,
        include_solutions=req.include_solutions,
    )


# ---- Kullanıcı bazlı geçmiş (Sprint 13) --------------------------------------
# Cihazlar arası kalıcı geçmiş: kullanıcının ürettiği kağıtlar tenant_id
# (Clerk userId) ile saklanır. LLM çağrısı yok → rate limit yok, sadece auth.


@router.get("/history")
def get_worksheet_history(
    tenant_id: str,
    limit: int = 50,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> dict:
    """Kullanıcının ürettiği çalışma kağıtları — en yeni önce.

    `tenant_id` zorunlu query parametresidir (frontend Clerk userId'sini geçer),
    ancak kimlik doğrulanmış Clerk oturumundan türetilir (spoof/IDOR koruması).
    Dönen her öğe frontend'in `HistoryItem` yapısındadır.
    """
    tenant_id = require_tenant(verified, tenant_id)
    return {"items": WORKSHEET_HISTORY.list(tenant_id, limit=limit)}


@router.delete("/history/{item_id}", status_code=204)
def delete_worksheet_history(
    item_id: str,
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> None:
    """Tek bir geçmiş kaydını siler. tenant_id doğrulanmış kimlikten türetilir
    → başkasının kaydı silinemez (IDOR koruması)."""
    tenant_id = require_tenant(verified, tenant_id)
    WORKSHEET_HISTORY.delete(tenant_id, item_id)


@router.delete("/history", status_code=204)
def clear_worksheet_history(
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> None:
    """Kullanıcının tüm geçmişini siler (tenant_id doğrulanmış kimlikten)."""
    tenant_id = require_tenant(verified, tenant_id)
    WORKSHEET_HISTORY.clear(tenant_id)


# /render.pdf gövde tavanı: brand_logo base64 (birkaç yüz KB) + ≤60 soru (her biri
# ≤50KB) rahat sığar; multi-MB DoS payload'ları erken (parse öncesi) reddedilir.
_MAX_RENDER_BODY_BYTES = 8 * 1024 * 1024  # 8 MB


@router.post("/render.pdf")
# LLM çağrısı YOK ama CPU/bellek-yoğun (ReportLab + svglib + matplotlib) ve girdi
# tümüyle client'tan → throttle şart (cost-DoS değil, kaynak-DoS). LLM uçlarından
# daha cömert: PDF indirme meşru olarak arka arkaya yapılır.
@limiter.limit("30/minute;200/hour")
async def render_existing_worksheet(
    request: Request,
    _api_key: str = Depends(require_api_key),
) -> Response:
    """Önceden üretilmiş bir worksheet JSON'unu PDF'e çevirir.

    LLM çağrısı YAPMAZ. White-label: brand_name + brand_subtitle + brand_logo
    (opsiyonel) PDF üst bilgisine basılır. Girdi sınırlıdır (gövde ≤8MB, ≤60 soru)
    ve uç throttle'lıdır (kaynak-DoS koruması).

    Geriye uyumlu: YENİ format gövdede {worksheet, brand_logo, ...} (logo base64
    query'ye sığmaz); ESKİ format gövde=Worksheet + marka/toggle query'de. Deploy
    sırasında eski frontend yeni backend'e (veya tersi) çarparsa PDF kırılmasın.
    """
    # Gövde boyutu tavanı — parse'tan ÖNCE Content-Length ile erken reddet
    # (devasa payload'ı belleğe hiç almadan). Başlık yoksa json() yine de
    # Pydantic sınırlarına (≤60 soru, alan max_length) takılır.
    _clen = request.headers.get("content-length")
    if _clen is not None:
        try:
            if int(_clen) > _MAX_RENDER_BODY_BYTES:
                raise HTTPException(status_code=413, detail="İstek gövdesi çok büyük.")
        except ValueError:
            pass  # bozuk başlık → normal akışa bırak
    try:
        body = await request.json()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Geçersiz JSON gövde.") from exc

    # Modeller ELLE kurulur (gövde parse dallanması) → Pydantic ValidationError
    # otomatik 422'ye çevrilmez, aksi halde 500 olur. Girdi sınırı ihlali (≤60 soru,
    # alan max_length) burada temiz 422 döner — hem DoS kapısı hem net hata.
    try:
        if isinstance(body, dict) and "worksheet" in body:
            # Yeni format — gövde-model.
            req = RenderRequest(**body)
            return _pdf_response(
                req.worksheet,
                include_answer_key=req.include_answer_key,
                include_solutions=req.include_solutions,
                brand_name=req.brand_name,
                brand_subtitle=req.brand_subtitle,
                brand_logo=req.brand_logo,
            )

        # Eski format — gövde doğrudan Worksheet, marka/toggle query parametrelerinde.
        qp = request.query_params
        return _pdf_response(
            Worksheet(**body),
            include_answer_key=qp.get("include_answer_key") != "false",
            include_solutions=qp.get("include_solutions") != "false",
            brand_name=qp.get("brand_name"),
            brand_subtitle=qp.get("brand_subtitle"),
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail="Geçersiz veya sınır aşan worksheet (max 60 soru).",
        ) from exc


# ---- Tek soru yeniden üretimi ("Soruyu Değiştir") ---------------------------


def _resolve_topic_id(grade: int, kazanim_kod: str) -> str | None:
    """grade + kazanim_kod'tan topic_id'yi müfredattan çözer.

    Her kazanım kodu tek bir (grade, topic)'e aittir → frontend topic_id
    göndermez, soruyu tutarlı şekilde aynı konuda yeniden üretiriz.
    """
    from app.data.curriculum import CURRICULUM
    for topic_id, topic in CURRICULUM.get(grade, {}).items():
        if any(k["kod"] == kazanim_kod for k in topic["kazanimlar"]):
            return topic_id
    return None


@router.post("/regenerate-question")
@limiter.limit(rate_limit_string())
def regenerate_question(
    request: Request,
    req: RegenerateQuestionRequest,
    _api_key: str = Depends(require_api_key),
) -> dict:
    """Tek bir soruyu, aynı kazanım + tip + zorlukta yeniden üretir.

    Tüm kağıdı baştan üretmek yerine kullanıcı beğenmediği soruyu tek tek
    değiştirebilir. LLM çağrısı yapar → rate limit + auth uygulanır. Yeni soru
    tenant geçmişine göre dedup'lanır (mevcut sorulardan farklı gelir).
    """
    from app.models.enums import SubjectId
    from app.subjects import get_content_module, subject_enabled
    topic_id: str | None = None
    unit_id: str | None = None
    if req.subject != SubjectId.MATEMATIK:
        if not subject_enabled(req.subject):
            raise HTTPException(
                status_code=403,
                detail=f"'{req.subject.value}' dersi henüz yayında değil (kalite kapısı).",
            )
        content = get_content_module(req.subject)
        if content is None:
            raise HTTPException(
                status_code=400, detail=f"Desteklenmeyen ders: {req.subject.value}"
            )
        found = content.find_unit_by_kazanim(req.kazanim_kod)
        if found is None:
            raise HTTPException(
                status_code=400,
                detail=f"'{req.kazanim_kod}' kodu '{req.subject.value}' müfredatında bulunamadı.",
            )
        unit_id = found[1]["unit_id"]
    else:
        # Önce eski müfredat (M.*); bulunamazsa yeni MEB ünitesi (MAT.*) → unit yolu.
        topic_id = _resolve_topic_id(req.grade, req.kazanim_kod)
        if topic_id is None:
            found = find_unit_by_kazanim(req.kazanim_kod)
            if found is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"'{req.kazanim_kod}' kodu {req.grade}. sınıf müfredatında bulunamadı.",
                )
            _, unit = found
            unit_id = unit["unit_id"]
    agent = _agent_for_model(model_for_grade(req.grade))
    try:
        questions = agent.generate(
            grade=req.grade,
            topic_id=topic_id,
            kazanim_kod=req.kazanim_kod,
            difficulty=req.difficulty,
            question_count=1,
            tenant_id=req.tenant_id,
            allowed_types=[req.question_type],
            unit_id=unit_id,
            subject=req.subject,
        )
    except AgentError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if not questions:
        raise HTTPException(
            status_code=502,
            detail="Yeni soru üretilemedi; lütfen tekrar deneyin.",
        )
    return {"question": questions[0].model_dump(mode="json")}


# ---- SSE streaming endpoint (Sprint 7) ----------------------------------
# Pragmatik MVP: agent.generate hâlâ blocking (Gemini batch response).
# Endpoint blocking üretim sonrası her soruyu ayrı SSE event olarak yollar →
# frontend EventSource canlı akış hissi verir, perceived latency düşer.
# Gerçek token-by-token streaming Sprint 7.5'te (Gemini streaming API + agent
# refactor) eklenecek.


async def _stream_worksheet_events(
    req: GenerateWorksheetRequest,
) -> AsyncIterator[str]:
    """SSE event akışı üretir. Format:
        event: meta        — başlangıç (request echo)
        event: question    — her soru
        event: complete    — final worksheet + metadata
        event: error       — hata
        : keepalive        — üretim sürerken periyodik ping (SSE yorumu)
    """

    def sse(event: str, data: dict | str) -> str:
        body = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
        return f"event: {event}\ndata: {body}\n\n"

    # Hand-off başlangıç event'i — frontend "bağlantı kuruldu" olarak gösterir
    yield sse("meta", {
        "grade": req.grade,
        "unit_id": req.unit_id,
        "topic_id": req.topic_id,
        "kazanim_kod": req.kazanim_kod,
        "difficulty": req.difficulty.value if hasattr(req.difficulty, "value") else req.difficulty,
        "question_count": req.question_count,
    })

    # _build_worksheet ~30-90 sn sürebilir; bu süre boyunca tek bir byte bile
    # akmazsa araya giren proxy (Render/Nginx) veya tarayıcı bağlantıyı idle
    # sanıp koparır → kullanıcı "hata" görür ama backend üretimi bitirip geçmişe
    # yazar. Üretimi ayrı task'ta çalıştırıp BİTENE KADAR her HEARTBEAT_SECONDS'ta
    # bir SSE yorumu (": keepalive") akıtıyoruz: byte aktığı için bağlantı canlı
    # kalır, yorum satırı olduğu için istemci onu yok sayar (event tetiklemez).
    HEARTBEAT_SECONDS = 10.0
    gen_task = asyncio.ensure_future(asyncio.to_thread(_build_worksheet, req))
    while not gen_task.done():
        # wait timeout'ta task'ı İPTAL ETMEZ; sadece beklemeyi bırakır → güvenli.
        await asyncio.wait({gen_task}, timeout=HEARTBEAT_SECONDS)
        if not gen_task.done():
            yield ": keepalive\n\n"

    try:
        worksheet, metadata = gen_task.result()
    except HTTPException as exc:
        yield sse("error", {"detail": exc.detail, "status": exc.status_code})
        return
    except Exception as exc:  # noqa: BLE001
        yield sse("error", {"detail": str(exc)[:500], "status": 500})
        return

    # Her soru ayrı event — frontend skeleton'ları teker teker doldurur.
    for q in worksheet.questions:
        yield sse("question", q.model_dump(mode="json"))
        await asyncio.sleep(0.05)  # küçük gecikme → akış hissi

    yield sse(
        "complete",
        {
            "worksheet": worksheet.model_dump(mode="json"),
            "metadata": metadata.model_dump(mode="json"),
        },
    )


@router.post("/generate.stream")
@limiter.limit(rate_limit_string())
def generate_worksheet_stream(
    request: Request,
    req: GenerateWorksheetRequest,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> StreamingResponse:
    """SSE streaming üretim. Frontend EventSource ile bağlanır."""
    # Kota kapısı stream BAŞLAMADAN uygulanır (aşımda 402, akış hiç açılmaz).
    entitlements.enforce_quota(verified)  # kota birimi = 1 çalışma kağıdı (soru sayısı değil)
    return StreamingResponse(
        _stream_worksheet_events(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",  # Render/Nginx proxy buffer'ını kapat
        },
    )
