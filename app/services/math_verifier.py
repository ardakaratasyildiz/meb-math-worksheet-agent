"""Deterministic math verifier — SymPy ile aritmetik doğruluk kontrolü.

Yalnızca SALT_ISLEM ve ISLEM tipindeki sorularda uygulanır (sözel problemde
ifade çıkarmak güvenilmez). Soru metninden ifadeyi regex ile yakalar, cevabı
parse eder, SymPy ile değerlendirir. Tutarsızlık varsa MathVerdict(is_valid=False).

Fail-open: ifade veya cevap parse edilemezse skip → critic LLM judge devreye girer.
Critic'ten ucuz ve deterministik; ona kadar gelmeden hatayı yakalamak hedef.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from fractions import Fraction

import sympy
from sympy import Rational, sympify, SympifyError

from app.models.enums import QuestionType
from app.models.schemas import Question

logger = logging.getLogger(__name__)


# Verifier'ın güvenle ele alabileceği soru tipleri.
_VERIFIABLE_TYPES = {QuestionType.SALT_ISLEM, QuestionType.ISLEM}


@dataclass
class MathVerdict:
    question_index: int
    is_verifiable: bool  # tip + parse edilebilirlik
    is_valid: bool
    expected: str | None = None
    actual: str | None = None
    reason: str | None = None


# Türkçe sayı ifadelerini SymPy formatına çeviren temel pre-processor'lar
_TURKISH_DECIMAL_RE = re.compile(r"(?<=\d),(?=\d)")  # "3,14" → "3.14"
_MIXED_FRACTION_RE = re.compile(
    r"(\d+)\s*tam\s*(\d+)\s*[/⁄]\s*(\d+)",  # "3 tam 1/4"
    flags=re.IGNORECASE,
)
_PLAIN_FRACTION_RE = re.compile(r"(\d+)\s*[/⁄]\s*(\d+)")  # "1/4"
_POWER_RE = re.compile(r"(\d+)\s*[\^²³]\s*(\d+)?")  # "3^2", "5²"


# Karakter eşlemeleri — Türkçe matematik notasyonu → ASCII
_SUPERSCRIPT_MAP = str.maketrans({
    "²": "^2", "³": "^3", "⁴": "^4", "⁵": "^5",
    "⁶": "^6", "⁷": "^7", "⁸": "^8", "⁹": "^9", "⁰": "^0", "¹": "^1",
    "×": "*", "·": "*", "÷": "/", "−": "-", "–": "-", "—": "-",
})


def _normalize_number_text(text: str) -> str:
    """Türkçe sayı ifadelerini SymPy'ın anlayabileceği formata getirir."""
    if not text:
        return text
    text = text.translate(_SUPERSCRIPT_MAP)
    # Karışık kesirler: "3 tam 1/4" → "(3 + 1/4)"
    text = _MIXED_FRACTION_RE.sub(r"(\1 + \2/\3)", text)
    # Türkçe ondalık: "3,14" → "3.14" (sadece sayı içinde virgül)
    text = _TURKISH_DECIMAL_RE.sub(".", text)
    return text.strip()


def _parse_answer(answer: str) -> sympy.Expr | None:
    """Cevabı SymPy ifadesine çevirir. Başarısızsa None."""
    if not answer:
        return None
    text = _normalize_number_text(answer)
    # Sadece ilk anlamlı token'ı al — örn. "55 elma" → "55"
    # Önce karışık kesir parantez içine alındı, sonraki sözcüğü kes.
    # Yaklaşım: ilk regex match'i kullan
    m = re.match(
        r"^\s*\(?\s*-?\s*\d+(?:\s*[+\-*/]\s*\d+(?:/\d+)?)*\s*\)?",
        text,
    )
    candidate = m.group(0) if m else text
    try:
        return sympify(candidate, rational=True)
    except (SympifyError, SyntaxError, TypeError, ValueError):
        return None


def _extract_expression(question_text: str) -> str | None:
    """Soru metninden hesaplanabilir ifadeyi çıkarmaya çalışır.

    Strateji: '=' veya '?' işaretine kadar olan kısımdaki en uzun aritmetik
    ifade dizisini bul. Sözel problem ise None döner (parse başarısız).
    """
    if not question_text:
        return None
    text = _normalize_number_text(question_text)

    # "= ?" veya "= kaçtır" öncesine bak
    cut = re.split(r"=\s*\??|kaç(?:tır)?\??", text, maxsplit=1)[0]
    # Aritmetik karakterler dışındakileri at, ama parantez/operatör tut
    # Önce sözel ipuçları varsa pas geç
    # Sözel ipuçları: harf grupları (kazanım metinleri Türkçe sözel)
    # Eğer cut içinde belirgin operatör + sayı yoğunluğu yoksa skip
    expr_chars = re.findall(r"[\d\.\+\-\*\/\(\)\^\s]+", cut)
    if not expr_chars:
        return None
    longest = max(expr_chars, key=lambda s: sum(c.isdigit() for c in s))
    longest = longest.strip()
    # En az 1 operatör + 2 sayı içermeli
    if not re.search(r"[\+\-\*\/\^]", longest):
        return None
    if len(re.findall(r"\d+", longest)) < 2:
        return None
    return longest


def _evaluate(expr_text: str) -> sympy.Expr | None:
    try:
        return sympify(expr_text, rational=True)
    except (SympifyError, SyntaxError, TypeError, ValueError, ZeroDivisionError):
        return None


def _equal_enough(expected: sympy.Expr, actual: sympy.Expr) -> bool:
    """İki SymPy ifadesi sayısal olarak eşit mi?"""
    try:
        diff = sympy.simplify(expected - actual)
        if diff == 0:
            return True
        # Float karşılaştırma fallback
        return abs(float(expected) - float(actual)) < 1e-9
    except (TypeError, ValueError):
        return False


# Sayısal cevap parse'ı — ondalık + kesir + basit aritmetik. `_parse_answer`'dan
# farkı: ondalık (0.5 / 0,5) destekler. Etkileşimli puanlama virgül-ondalığı sık
# gördüğü için ayrı tutuldu (verify_question'ın davranışı değişmesin diye).
_NUMERIC_TOKEN_RE = re.compile(
    r"^\s*\(?\s*-?\s*\d+(?:[.,]\d+)?"
    r"(?:\s*[+\-*/^]\s*-?\d+(?:[.,]\d+)?(?:\s*/\s*\d+)?)*\s*\)?"
)


def _parse_numeric_answer(answer: str) -> sympy.Expr | None:
    """Cevabı ondalık/kesir destekli SymPy ifadesine çevirir. Başarısızsa None.

    Yalnız baştaki sayısal token alınır ("12 elma" → 12). Sözel cevap ("yedi")
    None döner — sympify harf dizisini sessizce Symbol'e çevirdiği için sonucta
    serbest sembol kalırsa reddedilir (aksi halde "yedi" ≡ "yedi" yanlış pozitif).
    """
    if not answer:
        return None
    text = _normalize_number_text(answer)  # Türkçe ondalık virgül → nokta, vs.
    m = _NUMERIC_TOKEN_RE.match(text)
    if not m:
        return None
    candidate = m.group(0).strip()
    if not candidate or not any(c.isdigit() for c in candidate):
        return None
    try:
        expr = sympify(candidate, rational=True)
    except (SympifyError, SyntaxError, TypeError, ValueError, ZeroDivisionError):
        return None
    # Saf sayı olmalı — içinde değişken kalmışsa (ör. "2x") sayısal değildir.
    if getattr(expr, "free_symbols", set()):
        return None
    return expr


def numeric_equivalent(expected: str, actual: str) -> bool | None:
    """İki sayısal cevap metni denk mi? (etkileşimli çözme puanlaması için)

    Türkçe notasyonu (virgül-ondalık, karışık kesir, üst simge) normalize edip
    SymPy ile karşılaştırır → "1/2" ≡ "0,5" ≡ "0.5", "3 tam 1/4" ≡ "13/4".

    Dönüş:
      True  → denk
      False → parse edildi ama denk değil
      None  → en az biri sayısal olarak parse edilemedi (bilinmiyor / kapsam dışı)
    """
    e = _parse_numeric_answer(expected)
    a = _parse_numeric_answer(actual)
    if e is None or a is None:
        return None
    return _equal_enough(e, a)


def verify_question(question: Question, index: int = 0) -> MathVerdict:
    """Tek bir soruyu doğrula. Verifier kapsamı dışındaysa is_verifiable=False."""
    if question.question_type not in _VERIFIABLE_TYPES:
        return MathVerdict(question_index=index, is_verifiable=False, is_valid=True)

    expr_text = _extract_expression(question.question)
    if expr_text is None:
        return MathVerdict(question_index=index, is_verifiable=False, is_valid=True,
                           reason="ifade çıkarılamadı")

    expected = _evaluate(expr_text)
    actual = _parse_answer(question.answer)

    if expected is None:
        return MathVerdict(question_index=index, is_verifiable=False, is_valid=True,
                           reason="ifade SymPy ile değerlendirilemedi")
    if actual is None:
        return MathVerdict(question_index=index, is_verifiable=False, is_valid=True,
                           reason="cevap parse edilemedi")

    is_valid = _equal_enough(expected, actual)
    return MathVerdict(
        question_index=index,
        is_verifiable=True,
        is_valid=is_valid,
        expected=str(expected),
        actual=str(actual),
        reason=None if is_valid else f"beklenen {expected}, verilen {actual}",
    )


def verify_batch(questions: list[Question]) -> list[MathVerdict]:
    return [verify_question(q, i) for i, q in enumerate(questions)]
