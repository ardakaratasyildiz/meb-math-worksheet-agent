import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.enums import Difficulty, EducationLevel, QuestionType


DifficultyMode = Literal["single", "mixed", "progressive"]


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
    # Sprint 12-A toggle paketi (2026-05-19) — kullanıcı UI'dan tipini, zorluk
    # modunu ve cevap anahtarı dahil edip etmemeyi seçebilir.
    question_types: list[QuestionType] | None = Field(
        None,
        description="Opsiyonel: yalnızca bu tiplerden üretim yapılır. None → mevcut "
        "tip dağılımı (DIFFICULTY_DISTRIBUTIONS) kullanılır. Boş liste 400 ile reddedilir.",
    )
    difficulty_mode: DifficultyMode = Field(
        "single",
        description="single = sadece `difficulty` alanı kullanılır (mevcut). "
        "mixed = kolay+orta+zor karışık dağıtım (4/4/2). "
        "progressive = aynı dağılım ama soru sırası kolay→orta→zor.",
    )
    include_answer_key: bool = Field(
        True,
        description="PDF çıktısında 'Cevap Anahtarı' tablosu basılsın mı? "
        "False = sınav modu (sadece sorular).",
    )
    include_solutions: bool = Field(
        True,
        description="PDF çıktısında 'Çözüm Adımları' sayfası basılsın mı? "
        "False = öğrenci kağıdı (cevap anahtarı dahil olsa bile çözüm yok).",
    )

    @field_validator("question_types")
    @classmethod
    def _validate_types(cls, v: list[QuestionType] | None) -> list[QuestionType] | None:
        if v is None:
            return None
        if not v:
            raise ValueError("question_types boş liste olamaz; None bırakın veya en az 1 tip seçin.")
        # Tekrarları kaldır, sırayı koru
        seen: set[QuestionType] = set()
        out: list[QuestionType] = []
        for t in v:
            if t not in seen:
                seen.add(t)
                out.append(t)
        return out

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "grade": 5,
                    "topic_id": "cebir",
                    "kazanim_kod": "M.5.5.1",
                    "difficulty": "orta",
                    "question_count": 10,
                    "tenant_id": "ogretmen-42",
                },
                {
                    "grade": 3,
                    "topic_id": "dogal_sayilar",
                    "difficulty": "kolay",
                    "question_count": 5,
                },
            ]
        }
    }

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


class SolutionStep(BaseModel):
    step_no: int = Field(..., description="Adım sırası (1'den başlar)")
    description: str = Field(..., description="Adımın kısa açıklaması")
    computation: str | None = Field(
        None,
        description="O adıma karşılık gelen aritmetik ifade (ör. '3 + 4 = 7'). Sözel adımda boş.",
    )


_STEP_LEAD_RE = re.compile(
    r"""
    \A                                     # sadece string başında
    (?:
        (\d+)[\.\)]                        # "1." veya "1)"
      | (?:adım|step)\s*(\d+)\s*[:\.\-]?   # "Adım 1:" / "Step 2 -"
      | [•∙]                                # gerçek bullet karakterleri (- DEĞİL)
    )
    \s*
    """,
    flags=re.IGNORECASE | re.VERBOSE,
)
_INLINE_COMPUTATION_RE = re.compile(r"[\d\(\)\+\-\*\/\^\=\.\,\s]{4,}")


def parse_solution_steps(text: str) -> list[SolutionStep]:
    """Düz metin çözümü adım listesine çevirir. Numaralı/maddeli pattern'leri yakalar.

    Yakalama olmazsa tek adım olarak döner (description=text). Frontend bu listeyi
    güvenle render edebilir; her adımın opsiyonel computation alanı ayrı renderlanabilir.
    """
    if not text or not text.strip():
        return []
    raw = text.replace("\r\n", "\n").strip()
    # Önce satır bölme; sonra her satırda "1." pattern'i için kes
    parts: list[str] = []
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Aynı satırda multiple "1.", "2." varsa böl
        sub = re.split(r"(?<=[\.\?\!])\s+(?=\d+[\.\)])", line)
        parts.extend(s.strip() for s in sub if s.strip())
    if not parts:
        parts = [raw]

    steps: list[SolutionStep] = []
    for i, p in enumerate(parts, start=1):
        clean = _STEP_LEAD_RE.sub("", p, count=1).strip()
        if not clean:
            continue
        # Computation: en uzun aritmetik substring (>=4 char, içinde digit ve operatör)
        comp = None
        candidates = _INLINE_COMPUTATION_RE.findall(clean)
        for cand in sorted(candidates, key=len, reverse=True):
            cand_strip = cand.strip()
            if (
                any(c.isdigit() for c in cand_strip)
                and any(c in "+-*/=^" for c in cand_strip)
                and len(cand_strip) >= 4
            ):
                comp = cand_strip
                break
        steps.append(SolutionStep(step_no=i, description=clean, computation=comp))
    return steps


class Question(BaseModel):
    number: int
    question: str
    answer: str
    solution_steps: str | list[SolutionStep] = Field(
        ...,
        description="Düz metin çözüm (eski format) ya da yapılandırılmış adım listesi.",
    )
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
    provider: str = "gemini"  # "gemini" | "anthropic" — son başarılı çağrının kaynağı
    temperature: float  # initial (jitter sonrası)
    final_temperature: float | None = None  # retry'da boost olduysa son değer
    seed: int
    retry_rounds: int
    dedup_rejected_string: int = 0
    dedup_rejected_semantic: int = 0
    math_verifier_rejected: int = 0
    critic_rejected: int = 0
    requested_count: int
    delivered_count: int
    cache_hit: bool = False  # True ise LLM çağrısı yapılmadı, cached set döndü
    # Cost metering (Sprint 6) — tüm LLM çağrılarının (üretim + retry + critic)
    # token toplamları + tahmini USD maliyet. cache_hit=True ise hepsi 0.
    prompt_tokens: int = 0
    completion_tokens: int = 0
    estimated_cost_usd: float = 0.0


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
