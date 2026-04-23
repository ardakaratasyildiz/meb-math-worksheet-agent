"""Soru tipi dağılımı + in-batch tekrar önleme."""
import re
import unicodedata
from typing import Iterable

from app.models.enums import Difficulty, QuestionType

DIFFICULTY_DISTRIBUTIONS: dict[Difficulty, list[tuple[QuestionType, float]]] = {
    Difficulty.KOLAY: [
        (QuestionType.ISLEM, 0.50),
        (QuestionType.KAVRAM_SORUSU, 0.25),
        (QuestionType.SOZEL_PROBLEM, 0.15),
        (QuestionType.GUNLUK_HAYAT, 0.10),
    ],
    Difficulty.ORTA: [
        (QuestionType.ISLEM, 0.30),
        (QuestionType.SOZEL_PROBLEM, 0.30),
        (QuestionType.KAVRAM_SORUSU, 0.15),
        (QuestionType.AKIL_YURUTME, 0.10),
        (QuestionType.GUNLUK_HAYAT, 0.10),
        (QuestionType.MODELLEME, 0.05),
    ],
    Difficulty.ZOR: [
        (QuestionType.AKIL_YURUTME, 0.35),
        (QuestionType.SOZEL_PROBLEM, 0.30),
        (QuestionType.MODELLEME, 0.15),
        (QuestionType.ISLEM, 0.10),
        (QuestionType.GUNLUK_HAYAT, 0.10),
    ],
}


def distribute_question_types(
    total: int, difficulty: Difficulty
) -> dict[QuestionType, int]:
    """Toplam soruyu zorluk profiline göre soru tiplerine paylaştırır.

    Yuvarlama hatalarını telafi etmek için en yüksek paylı tipe ekleme/çıkarma yapılır.
    """
    weights = DIFFICULTY_DISTRIBUTIONS[difficulty]
    raw = [(qt, total * w) for qt, w in weights]
    counts: dict[QuestionType, int] = {qt: int(v) for qt, v in raw}
    assigned = sum(counts.values())
    diff = total - assigned
    if diff != 0:
        sorted_types = [qt for qt, _ in sorted(weights, key=lambda x: -x[1])]
        i = 0
        while diff != 0 and i < 100:
            qt = sorted_types[i % len(sorted_types)]
            if diff > 0:
                counts[qt] += 1
                diff -= 1
            else:
                if counts[qt] > 0:
                    counts[qt] -= 1
                    diff += 1
            i += 1
    return {qt: c for qt, c in counts.items() if c > 0}


_NUM_RE = re.compile(r"\d+([.,]\d+)?")
_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\wçğıöşüÇĞİÖŞÜ\s]")


def normalize_question(text: str) -> str:
    """Sorunun yapısal hash'i için normalize edilmiş hâli.

    Sayıları `<N>` ile, noktalama+fazla boşluğu temizler, küçük harfe çevirir.
    """
    t = text.lower().strip()
    t = unicodedata.normalize("NFKC", t)
    t = _NUM_RE.sub("<N>", t)
    t = _PUNCT_RE.sub(" ", t)
    t = _WS_RE.sub(" ", t).strip()
    return t


_TURKISH_STOPWORDS = {
    # Bağlaç / edat / yaygın dolgu
    "bir", "ve", "ile", "veya", "de", "da", "ki", "bu", "şu", "o",
    "için", "ise", "her", "tüm", "tane", "adet", "kadar", "daha", "en",
    "az", "çok", "olmak", "var", "yoktur", "vardır", "sonra", "önce", "ardından",
    "aynı", "farklı", "hem", "ya", "ama", "fakat", "değil", "gibi", "göre",
    # Soru ek/kelimeleri
    "kaç", "kaçtır", "kaçtan", "kaçta", "kaçı", "kaçını", "kaça",
    "nedir", "midir", "mıdır", "mıdır", "mudur", "müdür", "olan", "olur",
    "hangi", "hangileridir", "neden",
    # Çok kullanılan tanımlayıcı / işlev
    "sayı", "sayıda", "sayısı", "sayısının", "sayının", "sayıyı", "sayıya",
    "toplam", "toplamı", "toplamını", "toplamda", "fark", "farkı",
    "işlem", "işlemin", "işlemi", "işlemini", "sonuç", "sonucu", "sonucunu",
    "eşit", "eşittir", "büyük", "küçük", "katı", "katını", "fazla", "fazlası", "eksik", "eksiği",
    # Genel fiil kökleri (ayıklama için çoğu -mış, -di biçiminde takılı; 4 harf filtresi ilk eleği)
    "yapar", "yapın", "yazınız", "çözünüz", "bulunuz", "hesaplayınız", "hesapla",
    "veriniz", "verilir", "verilen", "verilerek", "veriliyor",
    # Sayı kelimeleri
    "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz",
    "on", "yüz", "bin", "milyon",
    # Zaman
    "sabah", "akşam", "gün", "günde", "saat", "saatte", "dakika", "dakikada",
    # Genel durum
    "durumda", "kısım", "kısmı", "kalan", "kalır", "kalmış", "kalmıştır",
    "yenir", "yenilen", "yenildi", "yenildiyse",
    "olduğu", "oldu", "olur", "olduğunda",
    "sürer", "sürmüş", "sürmüştür", "süredir", "içerisinde", "içinde",
    "oku", "okundu", "okuma", "okunmuş", "okunmamış", "okunmamıştır",
    "yapıldı", "yapılmış", "yapılmıştır", "yapılan",
    "alır", "alındı", "alınmış", "alınmıştır", "aldı",
    "satıldı", "satılır", "satılmış",
    "koyuldu", "koyulmuş", "konuldu",
    "sürdü", "sürmek", "sürüldü",
    "sini", "sinin", "nin", "nın", "nun", "nün",
}

_PROPER_NAMES = {
    "ali", "ayşe", "ahmet", "burak", "mehmet", "fatma", "veli",
    "ahmed", "ayșe", "ahmet'in", "ali'nin",
}


def extract_context_tokens(text: str) -> set[str]:
    """Bağlam dışlama listesi için anlamlı isimleri/nesneleri çıkarır.

    Basit yaklaşım: isim/nesne adı olabilecek 4+ harfli kelimeler (stopword olmayan).
    """
    t = text.lower()
    t = _PUNCT_RE.sub(" ", t)
    tokens = set()
    for w in t.split():
        w = w.strip("'\"")
        if len(w) < 4:
            continue
        if w in _TURKISH_STOPWORDS:
            continue
        if w.isdigit():
            continue
        tokens.add(w)
    return tokens


class BatchDeduplicator:
    """Bir batch içinde aynı sorunun tekrar etmesini engelleyen yardımcı.

    `prime()` ile önceden üretilmiş normalize sorular (history) yüklenir;
    bu sorular yeni üretimde de "görülmüş" sayılır.
    """

    def __init__(self) -> None:
        self._seen: set[str] = set()
        self._contexts: set[str] = set()
        self._primed_count = 0

    def prime(self, normalized_questions: Iterable[str]) -> None:
        """History'den gelen normalize soruları duplikat kontrolüne dahil eder."""
        before = len(self._seen)
        self._seen.update(normalized_questions)
        self._primed_count += len(self._seen) - before

    def is_duplicate(self, question: str) -> bool:
        return normalize_question(question) in self._seen

    def add(self, question: str) -> None:
        self._seen.add(normalize_question(question))
        self._contexts.update(extract_context_tokens(question))

    @property
    def context_exclusions(self) -> list[str]:
        return sorted(self._contexts)

    @property
    def primed_count(self) -> int:
        return self._primed_count
