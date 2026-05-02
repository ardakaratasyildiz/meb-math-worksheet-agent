from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.enums import Difficulty, EducationLevel, QuestionType


class GradeInfo(BaseModel):
    id: int
    name: str
    level: EducationLevel


class GradesResponse(BaseModel):
    grades: list[GradeInfo]


class KazanimInfo(BaseModel):
    kod: str
    metin: str


class TopicInfo(BaseModel):
    id: str
    name: str
    description: str
    kazanim_count: int


class TopicsResponse(BaseModel):
    grade: int
    topics: list[TopicInfo]


class KazanimlarResponse(BaseModel):
    grade: int
    topic_id: str
    topic_name: str
    kazanimlar: list[KazanimInfo]


class GenerateWorksheetRequest(BaseModel):
    grade: int = Field(..., ge=1, le=7, description="Sınıf (1-7)")
    topic_id: str = Field(..., description="Konu kimliği (curriculum.py)")
    kazanim_kod: str | None = Field(
        None,
        description="Opsiyonel: belirli bir kazanım kodu. Boşsa konunun kazanımları arasından otomatik dağılım yapılır.",
    )
    difficulty: Difficulty = Difficulty.ORTA
    question_count: int = Field(10, ge=1, le=20, description="Üretilecek soru sayısı")
    tenant_id: str | None = Field(
        None,
        description="Opsiyonel: kullanıcı/sınıf/kurum izolasyonu. Boş bırakılırsa "
        "ortak history kullanılır. Aynı tenant_id'yi tekrar veren istemci kümülatif "
        "varyasyon kazanır.",
        max_length=64,
    )

    @field_validator("topic_id")
    @classmethod
    def _strip_topic(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("tenant_id")
    @classmethod
    def _normalize_tenant(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None


class Question(BaseModel):
    number: int
    question: str
    answer: str
    solution_steps: str
    kazanim_kod: str
    question_type: QuestionType


class AnswerKeyEntry(BaseModel):
    number: int
    answer: str


class GenerationTrace(BaseModel):
    """Üretim sürecinin gözlemlenebilirlik verisi.

    Hangi few-shot kaynağı kullanıldı, kaç tekrar atıldı, kaç critic reddetti,
    retrieval ne kadar emin — kalite regresyonlarını yakalamak için.
    """

    few_shot_source: str  # "rag" | "static"
    few_shot_count: int
    textbook_count: int
    retrieval_avg_distance: float | None = None
    model_used: str
    temperature: float  # initial (jitter sonrası)
    final_temperature: float | None = None  # retry'da boost olduysa son değer
    seed: int
    retry_rounds: int
    dedup_rejected_string: int = 0
    dedup_rejected_semantic: int = 0
    critic_rejected: int = 0
    requested_count: int
    delivered_count: int


class WorksheetMetadata(BaseModel):
    generated_at: datetime
    model: str
    curriculum: str = "MEB"
    trace: GenerationTrace | None = None


class Worksheet(BaseModel):
    title: str
    grade: int
    topic: str
    difficulty: Difficulty
    question_count: int
    questions: list[Question]
    answer_key: list[AnswerKeyEntry]


class GenerateWorksheetResponse(BaseModel):
    worksheet: Worksheet
    metadata: WorksheetMetadata


class ErrorResponse(BaseModel):
    detail: str
