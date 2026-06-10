import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.enums import Difficulty, EducationLevel, QuestionType


DifficultyMode = Literal["single", "mixed", "progressive"]


# --- LaTeX kontrol-karakteri onarımı ------------------------------------------
# LLM'ler structured-output (JSON) üretirken tek-ters-bölülü bir LaTeX komutu
# (\frac, \times, \right, \beta, \neq ...) yazar; ters bölüden sonraki harf
# geçerli bir JSON escape harfiyse (f r t b n) JSON çözümleyici bu ikiliyi
# sessizce bir kontrol karakterine dönüştürür:
#   \frac  -> \x0c + "rac"      \right -> \x0d + "ight"
#   \times -> \x09 + "imes"     \beta  -> \x08 + "eta"     \neq -> \x0a + "eq"
# (\div \leq \sqrt \cdot bozulmaz: 2. harf escape harfi olmadığından
# constrained-decoding modeli \\ yazmaya zorlanır.) Bu fonksiyon onu geri alır.

_MATH_SPAN_RE = re.compile(r"\$\$?[^$]+?\$\$?")
_CTRL_BACKSLASH = {
    "\x08": "\\b", "\x09": "\\t", "\x0a": "\\n", "\x0c": "\\f", "\x0d": "\\r",
}


def repair_latex_control_chars(text: str) -> str:
    """JSON escape'i yüzünden kontrol karakterine dönüşmüş LaTeX komutlarını onarır."""
    if not text or not any(c in text for c in "\x08\x09\x0a\x0c\x0d"):
        return text
    # \x0c (form feed = \f) ve \x08 (backspace = \b): çalışma kağıdı metninde
    # asla meşru olarak bulunmaz → koşulsuz onar.
    text = text.replace("\x0c", "\\f").replace("\x08", "\\b")
    # \x09 (tab = \t) ve \x0d (CR = \r): ardından ASCII harf geliyorsa bozulmuş
    # \times/\theta/\right/\rho... komutudur (gerçek tab/CR'yi harf izlemez).
    text = re.sub(
        r"[\x09\x0d](?=[A-Za-z])",
        lambda m: _CTRL_BACKSLASH[m.group(0)],
        text,
    )
    # \x0a (newline = \n): gerçek satır sonları yaygın olduğundan yalnızca
    # $...$ / $$...$$ matematik blokları içinde onarılır (orada satır sonu olmaz).
    if "\x0a" in text:
        text = _MATH_SPAN_RE.sub(
            lambda m: m.group(0).replace("\x0a", "\\n"),
            text,
        )
    return text


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


class RegenerateQuestionRequest(BaseModel):
    """Tek bir soruyu yeniden üretme isteği ("Soruyu Değiştir").

    topic_id sunucuda (grade, kazanim_kod)'tan çözülür → frontend göndermez.
    Yeni soru aynı kazanım + aynı tip + worksheet zorluğunda üretilir.
    """
    grade: int = Field(..., ge=1, le=12)
    kazanim_kod: str = Field(..., min_length=1)
    difficulty: Difficulty = Difficulty.ORTA
    question_type: QuestionType
    tenant_id: str | None = None

    @field_validator("tenant_id")
    @classmethod
    def _norm_tenant(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return v.strip() or None


class SolutionStep(BaseModel):
    step_no: int = Field(..., description="Adım sırası (1'den başlar)")
    description: str = Field(..., description="Adımın kısa açıklaması")
    computation: str | None = Field(
        None,
        description="O adıma karşılık gelen aritmetik ifade (ör. '3 + 4 = 7'). Sözel adımda boş.",
    )

    @field_validator("description", "computation")
    @classmethod
    def _repair_latex(cls, v: str | None) -> str | None:
        return repair_latex_control_chars(v) if isinstance(v, str) else v


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

    # ── Yapısal cevap alanları (Adım 0 — etkileşimli çözme) ───────────────────
    # Yalnız "çözülebilir" tiplerde dolar; açık-uçlu/PDF akışında None kalır.
    # Eski kod ve PDF render bu alanları YOK SAYAR → tam geriye uyumlu. Sayısal
    # (salt_islem) tip ek alan istemez: `answer` + SymPy ile puanlanır.
    options: list[str] | None = Field(
        None,
        description="Çoktan seçmeli şıkları (A,B,C,D… sırasıyla). Yalnız coktan_secmeli.",
    )
    correct_index: int | None = Field(
        None,
        description="Çoktan seçmeli doğru şıkkın 0-tabanlı indeksi.",
    )
    blanks: list[str] | None = Field(
        None,
        description="Boşluk doldurma: metindeki boşlukların sıralı doğru cevapları.",
    )
    correct_bool: bool | None = Field(
        None,
        description="Doğru/Yanlış sorusunda doğru önerme mi (True=Doğru, False=Yanlış).",
    )

    # JSON escape kaynaklı LaTeX bozulmasını her Question oluşturulurken onar —
    # taze üretim, generation cache okuması ve /render.pdf girdileri dahil.
    @field_validator("question", "answer")
    @classmethod
    def _repair_latex(cls, v: str) -> str:
        return repair_latex_control_chars(v)

    @field_validator("solution_steps")
    @classmethod
    def _repair_solution_steps(
        cls, v: "str | list[SolutionStep]"
    ) -> "str | list[SolutionStep]":
        # list[SolutionStep] dalı zaten SolutionStep validator'ında onarıldı.
        return repair_latex_control_chars(v) if isinstance(v, str) else v

    @field_validator("options", "blanks")
    @classmethod
    def _repair_list(cls, v: list[str] | None) -> list[str] | None:
        # Yapısal metin alanları da LaTeX bozulmasından korunur (şık/boşluk
        # cevabı matematik içerebilir).
        if v is None:
            return v
        return [repair_latex_control_chars(x) if isinstance(x, str) else x for x in v]


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


# ── Çözülebilir quiz (öğrenme döngüsü, Adım 1) ───────────────────────────────
# Mevcut worksheet akışından AYRI: yalnız otomatik-puanlanabilir tipler, site
# içinde çözülür, cevaplar istemciye SIZMAZ (anti-kopya).


class CreateQuizRequest(BaseModel):
    """Çözülebilir quiz üretim isteği (POST /api/quizzes).

    GenerateWorksheetRequest'in çekirdek alt kümesi; PDF/markalama/zorluk-modu
    yok. tenant_id ZORUNLU — quiz kişiseldir (giriş gerekli).
    """

    grade: int = Field(..., ge=1, le=7)
    topic_id: str = Field(..., description="Konu kimliği (curriculum.py)")
    kazanim_kod: str | None = Field(
        None, description="Opsiyonel: belirli kazanım. Boşsa konu geneli."
    )
    difficulty: Difficulty = Difficulty.ORTA
    question_count: int = Field(10, ge=1, le=20)
    tenant_id: str = Field(..., min_length=1, max_length=64)

    @field_validator("topic_id")
    @classmethod
    def _strip_topic(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("tenant_id")
    @classmethod
    def _strip_tenant(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("tenant_id boş olamaz (quiz kişiseldir).")
        return v


class QuizQuestionPublic(BaseModel):
    """Çözme için soru — CEVAPSIZ. answer/solution_steps/correct_index/blanks/
    correct_bool kasıtlı olarak yoktur (kopya önleme). options = çoktan seçmeli
    şıkları (cevap değil); blank_count = boşluk doldurmada kaç giriş gerektiği."""

    number: int
    question: str
    question_type: QuestionType
    kazanim_kod: str
    options: list[str] | None = None
    blank_count: int | None = None


class QuizPublic(BaseModel):
    """Çözülebilir quiz — cevapsız soru listesi + meta."""

    id: str
    title: str
    grade: int
    topic_id: str
    difficulty: Difficulty
    question_count: int
    questions: list[QuizQuestionPublic]
    created_at: str
