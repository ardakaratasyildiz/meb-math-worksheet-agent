"""Kullanıcı (öğrenci) ilerleme endpoint'leri (öğrenme döngüsü — Adım 3).

GET /api/me/progress → kazanım-bazlı ustalık + genel özet + zayıf kazanımlar.
LLM çağrısı yok (saf sayım) → rate limit yok, yalnız auth.
"""
from __future__ import annotations

import time
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from app.models.schemas import (
    AttemptDetail,
    AttemptHistoryItem,
    AttemptHistoryResponse,
    EmailPrefsResponse,
    EntitlementsResponse,
    GamificationResponse,
    MyAssignmentItem,
    MyAssignmentsResponse,
    MyQuizItem,
    MyQuizzesResponse,
    ProgressResponse,
    QuotaInfo,
    SetEmailPrefsRequest,
    Question,
    ShareResultItem,
    ShareResultsResponse,
    SharesResponse,
    ChildItem,
    ChildrenResponse,
    LinkChildRequest,
    ParentCodeRequest,
    ParentCodeResponse,
    ShareSummary,
    StudyPlanResponse,
    SubmittedAnswer,
    TeachingOverviewItem,
    TeachingOverviewResponse,
)
from pydantic import BaseModel

from app.security import limiter, require_api_key
from app.services import clerk_roles, entitlements
from app.services.billing_store import BILLING_STORE
from app.services.clerk_auth import (
    require_verified_tenant_id,
    resolve_tenant_id,
    verified_tenant_id,
)
from app.services.attempt_review import build_attempt_detail
from app.services.classroom_store import CLASSROOM_STORE
from app.services.email_prefs_store import EMAIL_PREFS
from app.services.gamification import build_gamification
from app.services.parent_link_store import PARENT_LINK_STORE
from app.services.progress import build_daily_trend, build_progress
from app.services.quiz_store import QUIZ_STORE
from app.services.study_plan import build_study_plan
from app.services.study_plan_store import STUDY_PLAN_STORE

_IST = timezone(timedelta(hours=3))

router = APIRouter()


def _require_tenant(verified: str | None, supplied: str | None) -> str:
    """Doğrulanmış kimliği tercih et; yoksa (auth kapalıyken) supplied'a düş.

    Clerk doğrulaması AÇIKKEN ve doğrulanmış kimlik yoksa → 401 (client-supplied
    tenant_id'ye GÜVENİLMEZ; spoof koruması). Doğrulama KAPALIYKEN supplied aynen
    kullanılır → bugünkü davranış korunur (additive/kademeli açılış).
    """
    tid = resolve_tenant_id(verified, supplied)
    if not tid:
        raise HTTPException(status_code=401, detail="Kimlik doğrulanamadı.")
    return tid


# ── Rol onboarding (mobil RoleGate — publicMetadata.role TEK SEFER set eder) ──

class SetRoleRequest(BaseModel):
    role: str  # "student" | "teacher" | "parent"


@router.post("/role")
def set_my_role(
    req: SetRoleRequest,
    tenant_id: str = Depends(require_verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> dict:
    """Onboarding'de kullanıcının rolünü Clerk publicMetadata'ya TEK SEFER yazar.

    Doğrulanmış oturum ŞART (kendi rolünü set eder; spoof yok). Zaten rol atanmışsa
    değiştirmez, mevcut rolü döner. Frontend `/api/role` deseninin mobil karşılığı.
    """
    try:
        role = clerk_roles.set_user_role(tenant_id, req.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Geçersiz rol.")
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {"role": role}


# ── Entitlements (mobil paywall + özellik kapıları) ──────────────────────────

@router.get("/entitlements", response_model=EntitlementsResponse)
def get_my_entitlements(
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> EntitlementsResponse:
    """Kullanıcının efektif planı + kotası + abonelik durumu.

    Kaynak-of-truth billing_store (iyzico + RevenueCat ortak); karar entitlements'ta.
    Mobil bunu GÖSTERİM için okur (gating yine sunucuda enforce edilir). Doğrulanmış
    oturum gerekir (client-supplied tenant'a güvenilmez).
    """
    tid = _require_tenant(verified, tenant_id)
    plan = entitlements.plan_of(tid)
    q = entitlements.check_quota(tid)
    sub = BILLING_STORE.get(tid)
    return EntitlementsResponse(
        plan=plan,
        is_premium=(plan != entitlements.PLAN_FREE),
        status=sub["status"] if sub else None,
        trial_end=sub.get("trial_end") if sub else None,
        current_period_end=sub.get("current_period_end") if sub else None,
        cancel_at_period_end=bool(sub["cancel_at_period_end"]) if sub else False,
        quota=QuotaInfo(limit=q["limit"], used=q["used"], remaining=q["remaining"]),
    )


@router.get("/progress", response_model=ProgressResponse)
def get_progress(
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> ProgressResponse:
    """Kullanıcının kazanım ustalığı + zayıf konuları + genel özeti."""
    tenant_id = _require_tenant(verified, tenant_id)
    mastery_rows = QUIZ_STORE.get_mastery(tenant_id)
    quizzes_solved = QUIZ_STORE.count_attempts(tenant_id)
    recent = QUIZ_STORE.recent_attempts(tenant_id, limit=10)
    resp = build_progress(mastery_rows, quizzes_solved, recent)
    # 30 günlük gün-bazlı trend (Türkiye günü).
    since = time.time() - 30 * 86400
    today = datetime.now(_IST).date()
    resp.daily_trend = build_daily_trend(
        QUIZ_STORE.attempts_since(tenant_id, since), today
    )
    return resp


def _iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


@router.get("/study-plan", response_model=StudyPlanResponse)
def get_study_plan(
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> StudyPlanResponse:
    """Kayıtlı haftalık programı döner (varsa). LLM çağrısı YOK → hızlı. Kayıt yoksa
    boş döner (created_at=""), frontend 'oluştur' CTA'sı gösterir."""
    tenant_id = _require_tenant(verified, tenant_id)
    saved = STUDY_PLAN_STORE.get(tenant_id)
    if saved is None:
        return StudyPlanResponse(summary="", days=[], created_at="")
    plan_json, created = saved
    resp = StudyPlanResponse.model_validate_json(plan_json)
    resp.created_at = _iso(created)
    return resp


@router.post("/study-plan", response_model=StudyPlanResponse)
def create_study_plan(
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> StudyPlanResponse:
    """Haftalık programı (yeniden) üretir, KAYDEDER ve döner (LLM çağrısı içerir).
    Zayıf konu yoksa tekrar+karışık haftası; hiç veri yoksa teşvik mesajı."""
    tenant_id = _require_tenant(verified, tenant_id)
    mastery_rows = QUIZ_STORE.get_mastery(tenant_id)
    quizzes_solved = QUIZ_STORE.count_attempts(tenant_id)
    progress = build_progress(mastery_rows, quizzes_solved, [])
    plan = build_study_plan(progress)
    created = STUDY_PLAN_STORE.save(tenant_id, plan.model_dump_json())
    plan.created_at = _iso(created)
    return plan


# ── Veli ↔ öğrenci bağı (WS-6b) ──────────────────────────────────────────────


@router.post("/parent-code", response_model=ParentCodeResponse)
def get_parent_code(
    req: ParentCodeRequest,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> ParentCodeResponse:
    """Öğrencinin veli takip kodu (yoksa üretilir, kalıcı). Veli bu kodla bağlanır."""
    tenant_id = _require_tenant(verified, req.tenant_id)
    return ParentCodeResponse(code=PARENT_LINK_STORE.get_or_create_code(tenant_id))


@router.post("/link-child")
# Veli kodu brute-force koruması: kod uzayı 30^6, kimlik başına dakikada 10 /
# saatte 60 deneme ile sınırlanır (kod tahminiyle çocuk ilerlemesine erişim yüzeyi).
@limiter.limit("10/minute;60/hour")
def link_child(
    request: Request,
    req: LinkChildRequest,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> dict:
    """Veli, öğrencinin kodunu girerek bağlanır. Geçersiz/kendi kodu → 404."""
    tenant_id = _require_tenant(verified, req.tenant_id)
    student = PARENT_LINK_STORE.link(tenant_id, req.code, req.child_label)
    if student is None:
        raise HTTPException(status_code=404, detail="Kod geçersiz veya kendi kodun.")
    return {"student_id": student, "ok": True}


@router.get("/children", response_model=ChildrenResponse)
def list_children(
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> ChildrenResponse:
    """Velinin bağlı olduğu öğrenciler."""
    tenant_id = _require_tenant(verified, tenant_id)
    return ChildrenResponse(
        items=[ChildItem(**c) for c in PARENT_LINK_STORE.list_children(tenant_id)]
    )


@router.get("/children/{student_id}/progress", response_model=ProgressResponse)
def get_child_progress(
    student_id: str,
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> ProgressResponse:
    """Velinin, bağlı olduğu öğrencinin ilerlemesi (SALT-OKUNUR). Bağlı değilse 403."""
    tenant_id = _require_tenant(verified, tenant_id)
    if not PARENT_LINK_STORE.is_linked(tenant_id, student_id):
        raise HTTPException(status_code=403, detail="Bu öğrenciye bağlı değilsin.")
    mastery_rows = QUIZ_STORE.get_mastery(student_id)
    quizzes_solved = QUIZ_STORE.count_attempts(student_id)
    recent = QUIZ_STORE.recent_attempts(student_id, limit=10)
    resp = build_progress(mastery_rows, quizzes_solved, recent)
    since = time.time() - 30 * 86400
    today = datetime.now(_IST).date()
    resp.daily_trend = build_daily_trend(
        QUIZ_STORE.attempts_since(student_id, since), today
    )
    return resp


@router.get("/gamification", response_model=GamificationResponse)
def get_gamification(
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> GamificationResponse:
    """XP / seviye / seri. Rozetler frontend'de mastery'den türetilir."""
    tenant_id = _require_tenant(verified, tenant_id)
    mastery_rows = QUIZ_STORE.get_mastery(tenant_id)
    total_correct = sum(int(m.get("correct", 0)) for m in mastery_rows)
    quizzes_solved = QUIZ_STORE.count_attempts(tenant_id)
    active_dates = [
        date.fromisoformat(s)
        for s in QUIZ_STORE.distinct_attempt_dates(tenant_id)
    ]
    today = datetime.now(_IST).date()
    return build_gamification(total_correct, quizzes_solved, active_dates, today)


@router.get("/attempts", response_model=AttemptHistoryResponse)
def list_attempts(
    tenant_id: str,
    limit: int = 50,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> AttemptHistoryResponse:
    """Kullanıcının geçmiş çözüm denemeleri — en yeni önce."""
    tenant_id = _require_tenant(verified, tenant_id)
    rows = QUIZ_STORE.list_attempts(tenant_id, limit=limit)
    return AttemptHistoryResponse(
        items=[AttemptHistoryItem(**r) for r in rows]
    )


@router.get("/attempts/{attempt_id}", response_model=AttemptDetail)
def get_attempt_detail(
    attempt_id: str,
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> AttemptDetail:
    """Geçmiş bir denemenin tam gözden geçirmesi (soru + doğru cevap + senin cevabın)."""
    tenant_id = _require_tenant(verified, tenant_id)
    rec = QUIZ_STORE.get_attempt(attempt_id, tenant_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Deneme bulunamadı.")
    snapshot = rec.get("snapshot")
    if not snapshot:
        # Eski/snapshot'sız kayıt + quiz de silinmiş → yalnız skor özeti.
        return AttemptDetail(
            attempt_id=rec["attempt_id"],
            quiz_id=rec["quiz_id"],
            title="Quiz",
            grade=None,
            topic_id="",
            difficulty="orta",
            score=rec["score"],
            total=rec["total"],
            duration_seconds=rec.get("duration_seconds"),
            completed_at=rec["completed_at"],
            has_detail=False,
        )
    questions = [Question(**q) for q in snapshot.get("questions", [])]
    submitted = [SubmittedAnswer(**a) for a in rec.get("answers", [])]
    return build_attempt_detail(
        attempt_id=rec["attempt_id"],
        quiz_id=rec["quiz_id"],
        meta=snapshot,
        questions=questions,
        submitted=submitted,
        duration_seconds=rec.get("duration_seconds"),
        completed_at=rec["completed_at"],
    )


# ── Paylaşım sonuç panosu (Faz 3 PR A) ───────────────────────────────────────


@router.get("/shares", response_model=SharesResponse)
def list_my_shares(
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> SharesResponse:
    """Kullanıcının oluşturduğu aktif paylaşımlar + çözülme sayısı + ort. skor."""
    tenant_id = _require_tenant(verified, tenant_id)
    rows = QUIZ_STORE.list_shares(tenant_id)
    return SharesResponse(items=[ShareSummary(**r) for r in rows])


@router.get("/shares/{share_id}/results", response_model=ShareResultsResponse)
def get_share_results(
    share_id: str,
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> ShareResultsResponse:
    """Bir paylaşımın sonuç panosu — kim çözdü, kaç doğru, ne sürede (sahip-only)."""
    tenant_id = _require_tenant(verified, tenant_id)
    data = QUIZ_STORE.share_results(share_id, tenant_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Paylaşım bulunamadı.")
    return ShareResultsResponse(
        title=data["title"],
        question_count=data["question_count"],
        items=[ShareResultItem(**i) for i in data["items"]],
    )


# ── Sınıf / Ödev (Faz 3.5 PR 2) ──────────────────────────────────────────────


@router.get("/quizzes", response_model=MyQuizzesResponse)
def list_my_quizzes(
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> MyQuizzesResponse:
    """Kullanıcının ürettiği quiz'ler (hafif meta) — ödev atamak için seçim listesi."""
    tenant_id = _require_tenant(verified, tenant_id)
    rows = QUIZ_STORE.list(tenant_id)
    return MyQuizzesResponse(items=[MyQuizItem(**r) for r in rows])


@router.get("/assignments", response_model=MyAssignmentsResponse)
def list_my_assignments(
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> MyAssignmentsResponse:
    """Öğrencinin katıldığı sınıflardaki ödevler + çözüldü durumu/skor ('Ödevlerim')."""
    tenant_id = _require_tenant(verified, tenant_id)
    rows = CLASSROOM_STORE.list_my_assignments(tenant_id)
    return MyAssignmentsResponse(items=[MyAssignmentItem(**r) for r in rows])


@router.get("/teaching-results", response_model=TeachingOverviewResponse)
def teaching_results(
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> TeachingOverviewResponse:
    """Öğretmenin TÜM sınıflarındaki ödevler + çözülme özeti ('Ödev Sonuçları' panosu).

    Yalnız çağıranın SAHİBİ olduğu sınıfların ödevlerini döndürür (owner-scoped by
    query). Detay (kim/kaç puan) /api/assignments/{id}/results ile çekilir."""
    tenant_id = _require_tenant(verified, tenant_id)
    rows = CLASSROOM_STORE.owner_assignment_overview(tenant_id)
    return TeachingOverviewResponse(items=[TeachingOverviewItem(**r) for r in rows])


# ── E-posta tercihleri (KVKK opt-in — Track 2) ───────────────────────────────


@router.get("/email-prefs", response_model=EmailPrefsResponse)
def get_email_prefs(
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> EmailPrefsResponse:
    """Kullanıcının e-posta tercihi. Hiç ayarlamadıysa is_set=false (onay kartı gösterilir)."""
    tenant_id = _require_tenant(verified, tenant_id)
    pref = EMAIL_PREFS.get(tenant_id)
    if pref is None:
        return EmailPrefsResponse(is_set=False)
    return EmailPrefsResponse(
        is_set=True,
        newsletter_optin=pref["newsletter_optin"],
        email=pref["email"],
    )


@router.post("/email-prefs", response_model=EmailPrefsResponse)
def set_email_prefs(
    req: SetEmailPrefsRequest,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> EmailPrefsResponse:
    """E-posta tercihini kaydet (bülten + hatırlatma izni). E-posta sonraki gönderim için saklanır."""
    tenant_id = _require_tenant(verified, req.tenant_id)
    EMAIL_PREFS.set(
        tenant_id=tenant_id,
        email=req.email,
        newsletter_optin=req.newsletter_optin,
    )
    return EmailPrefsResponse(
        is_set=True,
        newsletter_optin=req.newsletter_optin,
        email=req.email,
    )
