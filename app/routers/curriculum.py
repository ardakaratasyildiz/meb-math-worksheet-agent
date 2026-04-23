from fastapi import APIRouter, HTTPException

from app.data.curriculum import (
    get_grades,
    get_topic,
    get_topics_for_grade,
)
from app.models.schemas import (
    GradesResponse,
    KazanimInfo,
    KazanimlarResponse,
    TopicInfo,
    TopicsResponse,
)

router = APIRouter()


@router.get("/grades", response_model=GradesResponse)
def list_grades() -> GradesResponse:
    return GradesResponse(grades=get_grades())


@router.get("/grades/{grade_id}/topics", response_model=TopicsResponse)
def list_topics(grade_id: int) -> TopicsResponse:
    if grade_id < 1 or grade_id > 7:
        raise HTTPException(status_code=400, detail="grade_id 1-7 arasında olmalı")
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
    if grade_id < 1 or grade_id > 7:
        raise HTTPException(status_code=400, detail="grade_id 1-7 arasında olmalı")
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
