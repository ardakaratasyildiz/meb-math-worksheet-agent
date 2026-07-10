from fastapi import APIRouter, HTTPException

from app.config import settings
from app.data.curriculum import (
    GRADE_LEVELS,
    get_grades,
    get_topic,
    get_topics_for_grade,
)
from app.data.units import get_unit, get_units_for_grade
from app.models.enums import SubjectId
from app.models.schemas import (
    GradeInfo,
    GradesResponse,
    KazanimInfo,
    KazanimlarResponse,
    TopicInfo,
    TopicsResponse,
    UnitInfo,
    UnitKazanimlarResponse,
    UnitsResponse,
)

router = APIRouter()


def _require_fen_enabled() -> None:
    """Fen curriculum'u yalnız flag açıkken servis edilir (üretimle tutarlı kapı)."""
    if not settings.fen_enabled:
        raise HTTPException(
            status_code=403,
            detail="Fen Bilimleri henüz yayında değil (kalite kapısı).",
        )


@router.get("/grades", response_model=GradesResponse)
def list_grades(subject: SubjectId = SubjectId.MATEMATIK) -> GradesResponse:
    if subject == SubjectId.FEN:
        _require_fen_enabled()
        from app.subjects.fen import FEN_CURRICULUM
        return GradesResponse(grades=[
            GradeInfo(id=g, name=f"{g}. Sınıf", level=GRADE_LEVELS[g])
            for g in sorted(FEN_CURRICULUM)
        ])
    return GradesResponse(grades=get_grades())


@router.get("/grades/{grade_id}/topics", response_model=TopicsResponse)
def list_topics(grade_id: int) -> TopicsResponse:
    if grade_id < 1 or grade_id > 8:
        raise HTTPException(status_code=400, detail="grade_id 1-8 arasında olmalı")
    topics = get_topics_for_grade(grade_id)
    return TopicsResponse(
        grade=grade_id,
        topics=[
            TopicInfo(
                id=t["topic_id"],
                name=t["name"],
                description=t["description"],
                kazanim_count=len(t["kazanimlar"]),
            )
            for t in topics
        ],
    )


@router.get(
    "/grades/{grade_id}/topics/{topic_id}/kazanimlar",
    response_model=KazanimlarResponse,
)
def list_kazanimlar(grade_id: int, topic_id: str) -> KazanimlarResponse:
    if grade_id < 1 or grade_id > 8:
        raise HTTPException(status_code=400, detail="grade_id 1-8 arasında olmalı")
    topic = get_topic(grade_id, topic_id)
    if topic is None:
        raise HTTPException(
            status_code=404,
            detail=f"{grade_id}. sınıfta '{topic_id}' konusu bulunmuyor",
        )
    return KazanimlarResponse(
        grade=grade_id,
        topic_id=topic["topic_id"],
        topic_name=topic["name"],
        kazanimlar=[KazanimInfo(**k) for k in topic["kazanimlar"]],
    )


# ── MEB TYMM ünite (tema) uçları — yeni seçim akışı ─────────────────────────


@router.get("/grades/{grade_id}/units", response_model=UnitsResponse)
def list_units(
    grade_id: int, subject: SubjectId = SubjectId.MATEMATIK
) -> UnitsResponse:
    if grade_id < 1 or grade_id > 8:
        raise HTTPException(status_code=400, detail="grade_id 1-8 arasında olmalı")
    if subject == SubjectId.FEN:
        _require_fen_enabled()
        from app.subjects.fen import get_units_for_grade as fen_units
        units = fen_units(grade_id)
    else:
        units = get_units_for_grade(grade_id)
    return UnitsResponse(
        grade=grade_id,
        units=[
            UnitInfo(
                unit_id=u["unit_id"],
                name=u["name"],
                no=u["no"],
                kazanim_count=len(u["kazanimlar"]),
            )
            for u in units
        ],
    )


@router.get(
    "/grades/{grade_id}/units/{unit_id}/kazanimlar",
    response_model=UnitKazanimlarResponse,
)
def list_unit_kazanimlar(
    grade_id: int, unit_id: str, subject: SubjectId = SubjectId.MATEMATIK
) -> UnitKazanimlarResponse:
    if grade_id < 1 or grade_id > 8:
        raise HTTPException(status_code=400, detail="grade_id 1-8 arasında olmalı")
    if subject == SubjectId.FEN:
        _require_fen_enabled()
        from app.subjects.fen import get_unit as fen_get_unit
        unit = fen_get_unit(grade_id, unit_id)
    else:
        unit = get_unit(grade_id, unit_id)
    if unit is None:
        raise HTTPException(
            status_code=404,
            detail=f"{grade_id}. sınıfta '{unit_id}' ünitesi bulunmuyor",
        )
    return UnitKazanimlarResponse(
        grade=grade_id,
        unit_id=unit["unit_id"],
        unit_name=unit["name"],
        kazanimlar=[
            KazanimInfo(kod=k["kod"], metin=k["metin"]) for k in unit["kazanimlar"]
        ],
    )
