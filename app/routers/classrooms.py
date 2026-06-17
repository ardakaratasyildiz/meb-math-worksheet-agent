"""Sınıf endpoint'leri (Faz 3.5 — Sınıf modeli, PR 1).

POST /api/classrooms        → sınıf oluştur (öğretmen) → katılma kodu döner
POST /api/classrooms/join   → öğrenci katılma koduyla sınıfa katılır
GET  /api/classrooms        → kullanıcının sınıfları (sahip + katılınan)
GET  /api/classrooms/{id}   → sınıf detayı (sahip: kod + üyeler; üye: ad + sayı)

Ödev atama + sonuç panosu PR 2/PR 3'te eklenir. LLM çağrısı yok → rate limit yok,
yalnız API key auth (mevcut güven modeli: tenant_id istemciden, doğrulanmadan).
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import (
    ClassroomDetail,
    ClassroomMember,
    ClassroomsResponse,
    ClassroomSummary,
    CreateClassroomRequest,
    JoinClassroomRequest,
    JoinClassroomResponse,
)
from app.security import require_api_key
from app.services.classroom_store import CLASSROOM_STORE

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=ClassroomDetail)
def create_classroom(
    req: CreateClassroomRequest,
    _api_key: str = Depends(require_api_key),
) -> ClassroomDetail:
    """Yeni sınıf oluştur (sahip = öğretmen). Katılma kodu döner."""
    rec = CLASSROOM_STORE.create_classroom(owner_tenant_id=req.tenant_id, name=req.name)
    logger.info("sınıf oluşturuldu: owner=%s id=%s", req.tenant_id, rec["id"])
    detail = CLASSROOM_STORE.get_classroom(rec["id"], req.tenant_id)
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
def join_classroom(
    req: JoinClassroomRequest,
    _api_key: str = Depends(require_api_key),
) -> JoinClassroomResponse:
    """Öğrenci katılma koduyla sınıfa katılır (üye Clerk hesabı şart)."""
    res = CLASSROOM_STORE.join_classroom(
        code=req.code,
        student_tenant_id=req.tenant_id,
        display_name=req.display_name,
    )
    if res is None:
        raise HTTPException(status_code=404, detail="Geçersiz katılma kodu.")
    logger.info("sınıfa katılım: student=%s classroom=%s", req.tenant_id, res["classroom_id"])
    return JoinClassroomResponse(**res)


@router.get("", response_model=ClassroomsResponse)
def list_classrooms(
    tenant_id: str,
    _api_key: str = Depends(require_api_key),
) -> ClassroomsResponse:
    """Kullanıcının sınıfları: sahip olunanlar (teaching) + katılınanlar (enrolled)."""
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
    _api_key: str = Depends(require_api_key),
) -> ClassroomDetail:
    """Sınıf detayı — yalnız sahip veya üye erişir (yoksa 404)."""
    detail = CLASSROOM_STORE.get_classroom(classroom_id, tenant_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Sınıf bulunamadı.")
    return ClassroomDetail(
        id=detail["id"],
        name=detail["name"],
        is_owner=detail["is_owner"],
        member_count=detail["member_count"],
        created_at=detail["created_at"],
        join_code=detail["join_code"],
        members=[ClassroomMember(**m) for m in detail["members"]],
    )
