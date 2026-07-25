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

# Şık işaretleyici: metin içinde "A)" "A." "a)" biçimleri. MEB ortaokul TÜM
# derslerde 4 şık (A-D) → A-E DEĞİL A-D (5. şık üretilirse Bug: yanlış say/render).
# `(?<![A-Za-z0-9])`: kelime-içi harfi (ör. "e-mail", "art") şık sanmamak için.
_MCQ_OPTION_RE = re.compile(
    # Şık HARFİ A-D (4 şık); sınır lookahead'i A-E → olası kaçak "E)" şıkkı D'nin
    # metnine karışmaz (E) içeriği yutulur, ayrı şık olmaz). 4-şık'ı agent zorlar.
    r"(?<![A-Za-z0-9])([A-Da-d])\s*[\)\.]\s*(.+?)"
    r"(?=(?:(?<![A-Za-z0-9])[A-Ea-e]\s*[\)\.])|$)",
    flags=re.DOTALL,
)
# Beşinci şık (E) tespiti — üretimde 4-şık zorunluluğunu denetlemek için (agent).
_MCQ_FIFTH_OPTION_RE = re.compile(r"(?<![A-Za-z0-9])[Ee]\s*[\)\.]")


def _answer_letter(answer: str) -> str | None:
    """Cevaptan şık harfini (A-D) sağlamca çıkar: 'B', 'B)', 'B) art', 'B.',
    'Cevap: C', ya da sonda '... doğru cevap D'. Bulamazsa None."""
    a = (answer or "").strip()
    if not a:
        return None
    # Baştan: "B", "B)", "B) art", "B.", "Cevap: C"
    m = re.match(r"(?:cevap\s*[:\-]?\s*)?([A-Da-d])\s*(?:[\)\.\-:]|$|\s)", a, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    # Sondan: "... cevap B"
    m = re.search(r"\b([A-Da-d])\b\s*[\)\.]?\s*$", a, re.IGNORECASE)
    return m.group(1).upper() if m else None

_TRUE_TOKENS = {"doğru", "dogru", "d", "true", "evet", "✓", "t"}
_FALSE_TOKENS = {"yanlış", "yanlis", "y", "false", "hayır", "hayir", "✗", "x", "f"}


def count_blanks(text: str) -> int:
    """Metindeki boşluk yer-tutucu sayısı (____ / … / boş parantez)."""
    if not text:
        return 0
    return len(_BLANK_RE.findall(text))


# ── Fallback parser'lar ──────────────────────────────────────────────────────

def _parse_mcq(question: str, answer: str) -> tuple[list[str] | None, int | None]:
    """Çoktan seçmeli metninden şıkları (A-D sırasında) + doğru indeksi çıkarır.

    Şıklar `question` metnine gömülü ("A) .. B) .. C) .. D) ..") ve GÖSTERİLEN
    sıra budur → doğru indeks bu sıraya göre hesaplanır (grading index-tabanlı).
    """
    pairs = _MCQ_OPTION_RE.findall(question or "")
    if len(pairs) < 2:
        return None, None
    # Harf sırasına göre diz (A,B,C,D), metni temizle.
    pairs_sorted = sorted(pairs, key=lambda p: p[0].upper())
    letters = [p[0].upper() for p in pairs_sorted]
    options = [re.sub(r"\s+", " ", p[1]).strip().rstrip(",;") for p in pairs_sorted]

    idx: int | None = None
    # 1) Cevaptan şık harfi ("B", "B)", "B) art" → B) → indeks.
    letter = _answer_letter(answer)
    if letter and letter in letters:
        idx = letters.index(letter)
    # 2) Harf yoksa/uymuyorsa: cevap metni bir şıkla (harf öneki soyulmuş) eşleşiyor mu?
    if idx is None:
        ans_norm = re.sub(r"\s+", " ", (answer or "")).strip().lower()
        # Cevabın başındaki şık önekini de soy ("b) art" → "art") ve karşılaştır.
        ans_stripped = re.sub(r"^\s*[A-Da-d]\s*[\)\.\-:]\s*", "", ans_norm)
        for i, opt in enumerate(options):
            ol = opt.lower()
            if ol == ans_norm or ol == ans_stripped:
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


# ── Atıf bütünlüğü (WS-5.27) ─────────────────────────────────────────────────
# Soru bir öğeye ("öncüller", "görsel/şekil/grafik", "tablo") atıf yapıp o öğeyi
# İÇERMİYORSA cevaplanamaz → üretimde elenir (top-up doldurur). Yanlış-eleme maliyeti
# düşük (yeniden üretilir) ama SİSTEMATİK yanlış-eleme (periyodik/çarpım tablosu gibi
# kavramlar) yield'i düşürür → bilinen kavramlar dışlanır.

# "hangileri" + Roman-set cevap kalıbı: "I ve II", "I, II ve III" (yalnız bitişik
# Roman'lar; "I. Dünya Savaşı ve II. Meşrutiyet" gibi araya isim girenler eşleşmez).
_ROMAN_ANSWER_RE = re.compile(r"\b(?:I|II|III|IV|V)\b\s*(?:,|ve|-)\s*\b(?:I|II|III|IV|V)\b")
# Gerçek numaralı/Roman öğe listesi — SATIR-İÇİ de olabilir ("I. Ocak II. Mart").
# Roman öğe işaretçileri (kelime-içi harfi saymamak için sınır guard'ı).
_ROMAN_ITEM_RE = re.compile(r"(?<![A-Za-zÇĞİÖŞÜçğıöşü])(I{1,3}|IV|V)\s*[.\)]")
_NUM_ITEM_RE = re.compile(r"(?<!\d)([1-9])\s*[.\)]\s")


def _has_enum_items(text: str) -> bool:
    """Metinde en az iki ardışık numaralı/Roman öğe var mı (I. II. / 1. 2.)?"""
    romans = set(_ROMAN_ITEM_RE.findall(text))
    if "I" in romans and "II" in romans:
        return True
    nums = set(_NUM_ITEM_RE.findall(text))
    return "1" in nums and "2" in nums
# Görsel atfı — Türkçe ünsüz yumuşaması/ünlü düşmesi için yaygın çekimli biçimler
# AÇIKÇA sayılır (yanlış-eleme riskini düşürür). "bu/aşağıdaki ŞEKİLDE" ZARFI dahil
# DEĞİL (şekle/şekildeki gibi net isim kullanımları dahil).
_VISUAL_REF_RE = re.compile(
    r"\b(?:"
    r"görsel(?:e|de|deki|i|den)?|"
    r"grafi(?:ğe|kte|ğinde|ği|kten)|"
    r"şema(?:ya|da|daki|yı|dan)?|"
    r"harita(?:ya|da|daki|yı|dan)?|"
    r"diyagram(?:a|da|daki|ı|dan)?|"
    r"şekle|şekildeki|şekilden|şekli"
    r")\b",
    re.IGNORECASE,
)
# Demonstratif + çıplak görsel-ismi ("yukarıdaki grafik", "verilen şema"). "şekil"
# burada YOK — "aşağıdaki şekilde" zarfıyla karışmasın (şekil biçimleri üstte açık).
_VISUAL_DEMO_RE = re.compile(
    r"(?:yukar\w+|aşağ\w+|verilen|yanda\w*)\s+(?:[^.?!\n]{0,30}?)?"
    r"(?:görsel|grafik|şema|harita|diyagram)\b",
    re.IGNORECASE,
)
# Tablo atfı ("tabloya göre", "yukarıdaki tablo"); "periyodik/çarpım tablosu" KAVRAM → dışla.
_TABLE_REF_RE = re.compile(
    r"tablo\w*\s+göre|(?:yukar\w+|aşağ\w+|verilen)\s+(?:[^.?!\n]{0,30}?)?tablo\w*",
    re.IGNORECASE,
)
_TABLE_EXCLUDE_RE = re.compile(r"periyodik\s+tablo|çarp[ıi]m\s+tablo", re.IGNORECASE)
# Markdown tablo: en az bir "| ... |" satırı.
_MD_TABLE_RE = re.compile(r"\|[^\n|]*\|")


def reference_integrity_issue(question: str) -> str | None:
    """Soru bir öğeye ("öncül", "görsel/grafik", "tablo") atıf yapıp o öğeyi
    İÇERMİYORSA neden döner (cevaplanamaz → elenmeli). Emin değilse None."""
    if not question:
        return None
    low = question.lower()
    has_visual = ("<svg" in low) or ("{{chart" in low)

    # 1) Öncül / Roman-set "hangileri" → numaralı/Roman öğe listesi olmalı.
    refers_premise = ("öncül" in low) or bool(_ROMAN_ANSWER_RE.search(question))
    if refers_premise and not _has_enum_items(question):
        return "öncül/numaralı-liste atfı var ama öğeler metinde yok"

    # 2) Görsel atfı → <svg> veya {{chart}} olmalı.
    if not has_visual and (
        _VISUAL_REF_RE.search(question) or _VISUAL_DEMO_RE.search(question)
    ):
        return "görsel/grafik/şema atfı var ama görsel yok"

    # 3) Tablo atfı → markdown tablo olmalı (periyodik/çarpım tablosu hariç).
    if (
        _TABLE_REF_RE.search(question)
        and not _TABLE_EXCLUDE_RE.search(question)
        and not _MD_TABLE_RE.search(question)
        and not has_visual
    ):
        return "tablo atfı var ama tablo yok"

    return None


# Eşleştirme sağ-kolon harf şıkları (iki-liste formatı: "a. …" / "a) …" / "A) …").
_LETTER_OPT_RE = re.compile(r"(?:^|\n)\s*[a-eA-E][.)]\s")


def structured_content_issue(question_type: QuestionType, question: str) -> str | None:
    """Eşleştirme/sıralama sorusu GÖVDESİNDE gerekli öğe/şık içeriğini taşımıyorsa
    (model yalnız yönergeyi üretmiş; öğeler/şıklar ne metinde ne yapısal alanda var →
    cevaplanamaz) neden döner. WS: 4.sınıf sosyal PDF'inde "…eşleştiriniz." /
    "…sıralayınız." yönergeleri boş gövdeyle yayınlanıyordu.

    - eşleştirme: GFM tablo VEYA (numaralı öğe listesi + harf şık listesi) olmalı.
    - sıralama: sıralanacak numaralı/Roman öğe listesi (≥2) olmalı.
    """
    if not question:
        return None
    if question_type == QuestionType.ESLESTIRME:
        has_table = bool(_MD_TABLE_RE.search(question))
        has_pairs = _has_enum_items(question) and bool(_LETTER_OPT_RE.search(question))
        if not (has_table or has_pairs):
            return "eşleştirme öğe/şık listesi yok (yalnız yönerge → cevaplanamaz)"
    elif question_type == QuestionType.SIRALAMA:
        if not _has_enum_items(question):
            return "sıralama öğe listesi yok (yalnız yönerge → cevaplanamaz)"
    return None


def derive_structured_fields(q: Question) -> Question:
    """LLM yapısal alan üretmediyse metinden en-iyi-çaba doldurur.

    Zaten dolu alanlara dokunmaz (LLM'in ürettiği sağlam değer korunur). Çözülebilir
    olmayan tipte / çıkaramadığında soruyu değiştirmeden döner.
    """
    t = q.question_type
    updates: dict[str, object] = {}

    if t == QuestionType.COKTAN_SECMELI:
        # Şıklar metne gömülü ve kullanıcıya GÖSTERİLEN sıra bu → metinden çıkarılan
        # şıklar + indeks OTORİTER (LLM'in options/correct_index'i güvenilmez: sıra
        # kayması / şık-harfi uyumsuzluğu Bug B'ye yol açıyordu). Metinden çıkarılamazsa
        # (nadir) LLM alanlarına düş.
        options, idx = _parse_mcq(q.question, q.answer)
        if options is not None:
            updates["options"] = options
            updates["correct_index"] = idx  # idx None ise validate_structured düşürür
        elif q.options is None and q.correct_index is None:
            pass  # ne metinden ne LLM'den şık var → validate karar verir
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
