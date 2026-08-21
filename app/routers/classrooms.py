"""Sınıf endpoint'leri (Faz 3.5 — Sınıf modeli, PR 1).

POST /api/classrooms        → sınıf oluştur (öğretmen) → katılma kodu döner
POST /api/classrooms/join   → öğrenci katılma koduyla sınıfa katılır
GET  /api/classrooms        → kullanıcının sınıfları (sahip + katılınan)
GET  /api/classrooms/{id}   → sınıf detayı (sahip: kod + üyeler; üye: ad + sayı)

Ödev atama + sonuç panosu PR 2/PR 3'te eklenir. LLM çağrısı yok → rate limit yok,
yalnız API key auth (mevcut güven modeli: tenant_id istemciden, doğrulanmadan).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from app.models.schemas import (
    AssignmentCreatedResponse,
    AssignmentSummary,
    AssignPdfRequest,
    AssignQuizRequest,
    ClassroomDetail,
    ClassroomMember,
    ClassroomsResponse,
    ClassroomSummary,
    CreateClassroomRequest,
    JoinClassroomRequest,
    JoinClassroomResponse,
)
from app.security import limiter, require_api_key
from app.services import entitlements
from app.services.classroom_store import CLASSROOM_STORE
from app.services.clerk_auth import require_tenant, verified_tenant_id
from app.services.clerk_roles import enforce_role
from app.services.quiz_store import QUIZ_STORE

logger = logging.getLogger(__name__)

router = APIRouter()

_TR = timezone(timedelta(hours=3))


def _due_epoch(due_date: str | None) -> float | None:
    """'YYYY-MM-DD' → gün sonu (TR) epoch. Geçersiz/boş → None."""
    if not due_date:
        return None
    try:
        d = datetime.strptime(due_date.strip(), "%Y-%m-%d")
    except ValueError:
        return None
    return d.replace(hour=23, minute=59, second=59, tzinfo=_TR).timestamp()


@router.post("", response_model=ClassroomDetail)
def create_classroom(
    req: CreateClassroomRequest,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> ClassroomDetail:
    """Yeni sınıf oluştur (sahip = öğretmen). Katılma kodu döner."""
    tenant_id = require_tenant(verified, req.tenant_id)
    enforce_role(tenant_id, {"teacher", "admin"})  # sınıf açma öğretmene özel
    # Plan sınırı — "Çoklu sınıf yönetimi" Pro+ ayrıcalığı. Sınır OLUŞTURMA anında
    # uygulanır: mevcut sınıflar geriye dönük kırılmaz, yalnız yenisi engellenir.
    limit = entitlements.classroom_limit(entitlements.plan_of(tenant_id))
    owned = len(CLASSROOM_STORE.list_owned(tenant_id))
    if owned >= limit:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "classroom_limit_reached",
                "message": (
                    f"Planında {limit} sınıf açabilirsin. Daha fazla sınıf yönetmek "
                    "için Pro+'a geçebilirsin."
                ),
                "limit": limit,
                "owned": owned,
            },
        )
    rec = CLASSROOM_STORE.create_classroom(owner_tenant_id=tenant_id, name=req.name)
    logger.info("sınıf oluşturuldu: owner=%s id=%s", tenant_id, rec["id"])
    detail = CLASSROOM_STORE.get_classroom(rec["id"], tenant_id)
    assert detail is not None  # az önce oluşturuldu
    return ClassroomDetail(
        id=detail["id"],
        name=detail["name"],
        is_owner=detail["is_owner"],
        member_count=detail["member_count"],
        created_at=detail["created_at"],
        join_code=detail["join_code"],
        members=[ClassroomMember(**m) for m in detail["members"]],
    )


@router.post("/join", response_model=JoinClassroomResponse)
# Katılma kodu brute-force koruması: kod uzayı 30^6, kimlik başına dakikada 10 /
# saatte 60 deneme ile sınırlanır (LLM'siz ama enumerasyon yüzeyi). Kimlik
# doğrulanmış tenant / IP (bkz. security._identifier).
@limiter.limit("10/minute;60/hour")
def join_classroom(
    request: Request,
    req: JoinClassroomRequest,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> JoinClassroomResponse:
    """Öğrenci katılma koduyla sınıfa katılır (üye Clerk hesabı şart)."""
    tenant_id = require_tenant(verified, req.tenant_id)
    enforce_role(tenant_id, {"student", "admin"})  # sınıfa katılma öğrenciye özel
    res = CLASSROOM_STORE.join_classroom(
        code=req.code,
        student_tenant_id=tenant_id,
        display_name=req.display_name,
    )
    if res is None:
        raise HTTPException(status_code=404, detail="Geçersiz katılma kodu.")
    logger.info("sınıfa katılım: student=%s classroom=%s", tenant_id, res["classroom_id"])
    return JoinClassroomResponse(**res)


@router.get("", response_model=ClassroomsResponse)
def list_classrooms(
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> ClassroomsResponse:
    """Kullanıcının sınıfları: sahip olunanlar (teaching) + katılınanlar (enrolled)."""
    tenant_id = require_tenant(verified, tenant_id)
    teaching = CLASSROOM_STORE.list_owned(tenant_id)
    enrolled = CLASSROOM_STORE.list_joined(tenant_id)
    return ClassroomsResponse(
        teaching=[ClassroomSummary(**c) for c in teaching],
        enrolled=[ClassroomSummary(**c) for c in enrolled],
    )


@router.get("/{classroom_id}", response_model=ClassroomDetail)
def get_classroom(
    classroom_id: str,
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> ClassroomDetail:
    """Sınıf detayı — yalnız sahip veya üye erişir (yoksa 404)."""
    tenant_id = require_tenant(verified, tenant_id)
    detail = CLASSROOM_STORE.get_classroom(classroom_id, tenant_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Sınıf bulunamadı.")
    assignments = CLASSROOM_STORE.list_assignments(classroom_id)
    return ClassroomDetail(
        id=detail["id"],
        name=detail["name"],
        is_owner=detail["is_owner"],
        member_count=detail["member_count"],
        created_at=detail["created_at"],
        join_code=detail["join_code"],
        members=[ClassroomMember(**m) for m in detail["members"]],
        assignments=[AssignmentSummary(**a) for a in assignments],
    )


@router.delete("/{classroom_id}")
def delete_classroom(
    classroom_id: str,
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> dict:
    """Sınıfı sil — yalnız sahibi (öğretmen/admin). Üyeler + ödevler cascade silinir."""
    tenant_id = require_tenant(verified, tenant_id)
    enforce_role(tenant_id, {"teacher", "admin"})
    ok = CLASSROOM_STORE.delete_classroom(classroom_id, tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Sınıf bulunamadı veya sahibi değilsin.")
    logger.info("sınıf silindi: owner=%s id=%s", tenant_id, classroom_id)
    return {"ok": True}


@router.post("/{classroom_id}/leave")
def leave_classroom_endpoint(
    classroom_id: str,
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> dict:
    """Öğrenci sınıftan ayrılır (üyeliğini siler). Sahip ayrılamaz (sınıfı silmeli)."""
    tenant_id = require_tenant(verified, tenant_id)
    enforce_role(tenant_id, {"student", "admin"})
    ok = CLASSROOM_STORE.leave_classroom(classroom_id, tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Bu sınıfın üyesi değilsin.")
    logger.info("sınıftan ayrıldı: student=%s classroom=%s", tenant_id, classroom_id)
    return {"ok": True}


@router.delete("/{classroom_id}/members/{student_tenant_id}")
def remove_member_endpoint(
    classroom_id: str,
    student_tenant_id: str,
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> dict:
    """Öğretmen bir öğrenciyi sınıftan çıkarır (kick) — yalnız sınıf sahibi."""
    tenant_id = require_tenant(verified, tenant_id)
    enforce_role(tenant_id, {"teacher", "admin"})
    ok = CLASSROOM_STORE.remove_member(classroom_id, student_tenant_id, tenant_id)
    if not ok:
        raise HTTPException(
            status_code=404, detail="Öğrenci bulunamadı veya sınıfın sahibi değilsin."
        )
    logger.info(
        "öğrenci çıkarıldı: owner=%s classroom=%s student=%s",
        tenant_id, classroom_id, student_tenant_id,
    )
    return {"ok": True}


@router.delete("/{classroom_id}/assignments/{assignment_id}")
def delete_assignment_endpoint(
    classroom_id: str,
    assignment_id: str,
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> dict:
    """Ödevi sil — yalnız sınıf sahibi (öğretmen/admin). Denemeler tarihsel olarak kalır."""
    tenant_id = require_tenant(verified, tenant_id)
    enforce_role(tenant_id, {"teacher", "admin"})
    ok = CLASSROOM_STORE.delete_assignment(assignment_id, tenant_id)
    if not ok:
        raise HTTPException(
            status_code=404, detail="Ödev bulunamadı veya sınıfın sahibi değilsin."
        )
    logger.info(
        "ödev silindi: owner=%s classroom=%s assignment=%s",
        tenant_id, classroom_id, assignment_id,
    )
    return {"ok": True}


@router.post("/{classroom_id}/assignments", response_model=AssignmentCreatedResponse)
def assign_quiz(
    classroom_id: str,
    req: AssignQuizRequest,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> AssignmentCreatedResponse:
    """Sınıfa quiz'i ödev olarak ata — yalnız sınıf sahibi + kendi quiz'i."""
    tenant_id = require_tenant(verified, req.tenant_id)
    quiz = QUIZ_STORE.get(req.quiz_id, tenant_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz bulunamadı (senin quiz'in olmalı).")
    res = CLASSROOM_STORE.create_assignment(
        classroom_id=classroom_id,
        owner_tenant_id=tenant_id,
        quiz_id=req.quiz_id,
        title=quiz["title"],
        due_at=_due_epoch(req.due_date),
    )
    if res is None:
        raise HTTPException(status_code=403, detail="Bu sınıfın sahibi değilsin.")
    logger.info("ödev atandı: classroom=%s quiz=%s", classroom_id, req.quiz_id)
    return AssignmentCreatedResponse(**res)


@router.post("/{classroom_id}/assignments/pdf", response_model=AssignmentCreatedResponse)
def assign_pdf(
    classroom_id: str,
    req: AssignPdfRequest,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> AssignmentCreatedResponse:
    """Sınıfa PDF (çalışma kağıdı) ödevi ata — öğrenci indirir, site içi çözüm yok."""
    tenant_id = require_tenant(verified, req.tenant_id)
    res = CLASSROOM_STORE.create_assignment(
        classroom_id=classroom_id,
        owner_tenant_id=tenant_id,
        quiz_id="",
        title=req.worksheet.title,
        due_at=_due_epoch(req.due_date),
        assignment_type="pdf",
        worksheet_json=json.dumps(req.worksheet.model_dump(mode="json"), ensure_ascii=False),
    )
    if res is None:
        raise HTTPException(status_code=403, detail="Bu sınıfın sahibi değilsin.")
    logger.info("pdf ödev atandı: classroom=%s", classroom_id)
    return AssignmentCreatedResponse(**res)
