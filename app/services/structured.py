"""Yapısal cevap katmanı — etkileşimli (site içi) çözme + LLM'siz otomatik puanlama.

Adım 0 (kapsam: en basit 4 çözülebilir tip):
  - coktan_secmeli  → options + correct_index
  - dogru_yanlis    → correct_bool
  - bosluk_doldurma → blanks (sıralı)
  - salt_islem      → ek alan yok; `answer` + SymPy ile puanlanır

İki sorumluluk:
  1. derive_structured_fields — LLM yapısal alanları üretmediyse mevcut metinden
     "en iyi çaba" ile çıkarır (fallback). Üretim hattı bu alanları doğrudan
     üretirse (Adım 1, sağlam yol) bu parser devreye girmez.
  2. validate_structured — yapısal tutarlılık denetimi (critic). Yanlış işaretli
     doğru cevap felakettir → puanlanabilir hale gelmeden önce burada elenir.

Saf/deterministik, LLM çağırmaz. Mevcut üretim/PDF akışını ETKİLEMEZ; yalnız
çözme modunda çağrılır.
"""
from __future__ import annotations

import re

from app.models.enums import QuestionType
from app.models.schemas import Question
from app.services.math_verifier import numeric_equivalent

# Adım 0'da desteklenen çözülebilir tipler (en basit 4). Eşleştirme/sıralama sonra.
SOLVABLE_TYPES: set[QuestionType] = {
    QuestionType.COKTAN_SECMELI,
    QuestionType.DOGRU_YANLIS,
    QuestionType.BOSLUK_DOLDURMA,
    QuestionType.SALT_ISLEM,
}

# Metindeki boşluk yer tutucuları: 2+ alt çizgi, "…"/"...", boş parantez/köşeli.
_BLANK_RE = re.compile(r"_{2,}|…+|\.{3,}|\(\s*\)|\[\s*\]")

# Şık işaretleyici: satır/metin içinde "A)" "A." "A-" "a)" biçimleri.
_MCQ_OPTION_RE = re.compile(
    r"([A-Ea-e])\s*[\)\.\-]\s*(.+?)(?=(?:[A-Ea-e]\s*[\)\.\-]\s)|$)",
    flags=re.DOTALL,
)
# Cevap tek harfse (şık harfi) yakala: "A", "B)", "Cevap: D".
_MCQ_ANSWER_LETTER_RE = re.compile(r"(?:cevap\s*[:\-]?\s*)?\b([A-Ea-e])\b\s*[\)\.]?\s*$",
                                   flags=re.IGNORECASE)

_TRUE_TOKENS = {"doğru", "dogru", "d", "true", "evet", "✓", "t"}
_FALSE_TOKENS = {"yanlış", "yanlis", "y", "false", "hayır", "hayir", "✗", "x", "f"}


def count_blanks(text: str) -> int:
    """Metindeki boşluk yer-tutucu sayısı (____ / … / boş parantez)."""
    if not text:
        return 0
    return len(_BLANK_RE.findall(text))


# ── Fallback parser'lar ──────────────────────────────────────────────────────

def _parse_mcq(question: str, answer: str) -> tuple[list[str] | None, int | None]:
    """Çoktan seçmeli metninden şıkları + doğru indeksi çıkarmaya çalışır."""
    pairs = _MCQ_OPTION_RE.findall(question or "")
    if len(pairs) < 2:
        return None, None
    # Harf sırasına göre diz (A,B,C,D…), metni temizle.
    pairs_sorted = sorted(pairs, key=lambda p: p[0].upper())
    letters = [p[0].upper() for p in pairs_sorted]
    options = [re.sub(r"\s+", " ", p[1]).strip().rstrip(",;") for p in pairs_sorted]

    idx: int | None = None
    ans = (answer or "").strip()
    m = _MCQ_ANSWER_LETTER_RE.search(ans)
    if m:
        letter = m.group(1).upper()
        if letter in letters:
            idx = letters.index(letter)
    if idx is None:
        # Cevap metni bir şıkla birebir eşleşiyor mu?
        ans_norm = re.sub(r"\s+", " ", ans).strip().lower()
        for i, opt in enumerate(options):
            if opt.lower() == ans_norm:
                idx = i
                break
    return options, idx


def _parse_bool(answer: str) -> bool | None:
    """'Doğru'/'Yanlış' (ve yaygın varyasyonları) → bool."""
    tok = (answer or "").strip().lower().strip(".")
    if tok in _TRUE_TOKENS:
        return True
    if tok in _FALSE_TOKENS:
        return False
    return None


def _parse_blanks(answer: str) -> list[str]:
    """Boşluk cevaplarını sıralı listeye böler.

    Öncelik: satır sonu / ';' / '|' ayıracı → çoklu boşluk. Yoksa numaralı
    ('1) .. 2) ..') dene. Hâlâ tek parça ise virgül-ile-ayrılmış say; o da yoksa
    tek elemanlı liste (tek boşluk).
    """
    raw = (answer or "").strip()
    if not raw:
        return []
    # Belirgin ayıraçlar
    for sep in ("\n", ";", "|"):
        if sep in raw:
            return [s.strip() for s in raw.split(sep) if s.strip()]
    # Numaralı liste: "1) x 2) y" veya "1. x 2. y"
    numbered = re.findall(r"\d+\s*[\)\.]\s*([^0-9].*?)(?=\s*\d+\s*[\)\.]|$)", raw)
    if len(numbered) >= 2:
        return [s.strip().rstrip(",;") for s in numbered if s.strip()]
    # Virgülle ayrılmış birden çok kısa cevap
    if "," in raw:
        parts = [s.strip() for s in raw.split(",") if s.strip()]
        if len(parts) >= 2:
            return parts
    return [raw]


def derive_structured_fields(q: Question) -> Question:
    """LLM yapısal alan üretmediyse metinden en-iyi-çaba doldurur.

    Zaten dolu alanlara dokunmaz (LLM'in ürettiği sağlam değer korunur). Çözülebilir
    olmayan tipte / çıkaramadığında soruyu değiştirmeden döner.
    """
    t = q.question_type
    updates: dict[str, object] = {}

    if t == QuestionType.COKTAN_SECMELI and (q.options is None or q.correct_index is None):
        options, idx = _parse_mcq(q.question, q.answer)
        if q.options is None and options is not None:
            updates["options"] = options
        if q.correct_index is None and idx is not None:
            updates["correct_index"] = idx
    elif t == QuestionType.DOGRU_YANLIS and q.correct_bool is None:
        b = _parse_bool(q.answer)
        if b is not None:
            updates["correct_bool"] = b
    elif t == QuestionType.BOSLUK_DOLDURMA and q.blanks is None:
        blanks = _parse_blanks(q.answer)
        if blanks:
            updates["blanks"] = blanks

    return q.model_copy(update=updates) if updates else q


# ── Critic: yapısal tutarlılık denetimi ──────────────────────────────────────

def validate_structured(q: Question) -> tuple[bool, list[str]]:
    """Sorunun yapısal alanları otomatik puanlama için tutarlı mı?

    Dönüş: (geçerli_mi, sorunlar). Çözülebilir tip değilse her zaman (True, []).
    Çağıran (Adım 1 üretim) geçersizleri çözülebilir havuzdan eler.
    """
    t = q.question_type
    issues: list[str] = []

    if t == QuestionType.COKTAN_SECMELI:
        if not q.options or len(q.options) < 2:
            issues.append("en az 2 şık gerekli")
        else:
            if any(not (o or "").strip() for o in q.options):
                issues.append("boş şık var")
            if len({(o or "").strip().lower() for o in q.options}) != len(q.options):
                issues.append("tekrarlayan şık var")
            if q.correct_index is None or not (0 <= q.correct_index < len(q.options)):
                issues.append("correct_index şık aralığında değil")

    elif t == QuestionType.DOGRU_YANLIS:
        if q.correct_bool is None:
            issues.append("correct_bool belirsiz (Doğru/Yanlış çözülemedi)")

    elif t == QuestionType.BOSLUK_DOLDURMA:
        if not q.blanks or any(not (b or "").strip() for b in q.blanks):
            issues.append("boşluk cevap(lar)ı eksik")
        else:
            n = count_blanks(q.question)
            # Metinde belirgin boşluk işareti varsa sayı eşleşmeli; hiç yoksa
            # tolere et (tek boşluk varsayımı — bazı sorular "..." kullanmaz).
            if n and n != len(q.blanks):
                issues.append(
                    f"boşluk sayısı uyuşmuyor (metin {n}, cevap {len(q.blanks)})"
                )

    elif t == QuestionType.SALT_ISLEM:
        # Sayısal cevap SymPy ile parse edilebilmeli — puanlamanın önkoşulu.
        if numeric_equivalent(q.answer, q.answer) is not True:
            issues.append("sayısal cevap SymPy ile parse edilemiyor")

    else:
        # Çözülebilir tip değil → yapısal denetim uygulanmaz.
        return True, []

    return (not issues), issues
