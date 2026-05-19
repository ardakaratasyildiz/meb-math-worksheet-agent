"""Soru tipi dağılımı + in-batch tekrar önleme."""
from __future__ import annotations

import logging
import math
import re
import unicodedata
from typing import Iterable, Sequence

from app.models.enums import Difficulty, QuestionType

logger = logging.getLogger(__name__)

DIFFICULTY_DISTRIBUTIONS: dict[Difficulty, list[tuple[QuestionType, float]]] = {
    # Sprint 12-A: Bloom alt seviyelerini ve LGS hazırlığı destekleyen format
    # tipleri (coktan_secmeli, dogru_yanlis, bosluk_doldurma, eslestirme,
    # siralama) zorluk bazında karıştırıldı. Sözel/işlem çekirdek korunur.
    Difficulty.KOLAY: [
        (QuestionType.ISLEM, 0.35),
        (QuestionType.KAVRAM_SORUSU, 0.20),
        (QuestionType.SOZEL_PROBLEM, 0.10),
        (QuestionType.GUNLUK_HAYAT, 0.10),
        # Yeni format tipleri — kolay seviyede en yüksek pay (kavram pekiştirme).
        (QuestionType.COKTAN_SECMELI, 0.10),
        (QuestionType.DOGRU_YANLIS, 0.10),
        (QuestionType.BOSLUK_DOLDURMA, 0.05),
    ],
    Difficulty.ORTA: [
        (QuestionType.ISLEM, 0.25),
        (QuestionType.SOZEL_PROBLEM, 0.25),
        (QuestionType.KAVRAM_SORUSU, 0.12),
        (QuestionType.AKIL_YURUTME, 0.08),
        (QuestionType.GUNLUK_HAYAT, 0.08),
        (QuestionType.MODELLEME, 0.05),
        # Format tipleri — orta seviyede çoktan seçmeli (LGS) baskın.
        (QuestionType.COKTAN_SECMELI, 0.10),
        (QuestionType.ESLESTIRME, 0.04),
        (QuestionType.SIRALAMA, 0.03),
    ],
    Difficulty.ZOR: [
        (QuestionType.AKIL_YURUTME, 0.30),
        (QuestionType.SOZEL_PROBLEM, 0.25),
        (QuestionType.MODELLEME, 0.12),
        (QuestionType.ISLEM, 0.08),
        (QuestionType.GUNLUK_HAYAT, 0.05),
        # Zor seviyede çoktan seçmeli (LGS son aşama) + sıralama (karşılaştırma).
        (QuestionType.COKTAN_SECMELI, 0.15),
        (QuestionType.SIRALAMA, 0.05),
    ],
}

# Topic'e özel görsel/yapısal tip ağırlıkları. Toplamları 0.7'yi geçemez —
# sözel çekirdek dağılım her zaman korunur, üstüne bu tipler bindirilir.
TOPIC_VISUAL_BIAS: dict[str, dict[QuestionType, float]] = {
    "veri_isleme": {
        QuestionType.TABLO_SORUSU: 0.30,
        QuestionType.GRAFIK_OKUMA: 0.25,
    },
    "olasilik": {
        QuestionType.TABLO_SORUSU: 0.20,
    },
    "geometri": {
        QuestionType.GORSEL_GEOMETRI: 0.35,
    },
    "cebir": {
        QuestionType.ORUNTU_SEKIL: 0.15,
        QuestionType.SALT_ISLEM: 0.10,
    },
    "dogal_sayilar": {
        QuestionType.SALT_ISLEM: 0.15,
    },
    "kesirler": {
        QuestionType.SALT_ISLEM: 0.20,
    },
    "olcme": {
        QuestionType.SALT_ISLEM: 0.10,
    },
}

_MAX_VISUAL_SHARE = 0.65  # bias toplamı bu üst sınırla kırpılır


def distribute_question_types(
    total: int,
    difficulty: Difficulty,
    topic_id: str | None = None,
    allowed_types: set[QuestionType] | None = None,
) -> dict[QuestionType, int]:
    """Toplam soruyu zorluk profiline göre soru tiplerine paylaştırır.

    `topic_id` verilirse topic'e özel görsel/yapısal tipler (TABLO_SORUSU,
    GRAFIK_OKUMA, GORSEL_GEOMETRI, ORUNTU_SEKIL, SALT_ISLEM) belirli bir paya
    sahip olur; geri kalan pay zorluk profili üzerinden dağıtılır.

    `allowed_types` verilirse SADECE bu tipler arası dağıtım yapılır; diğer
    tipler ağırlık 0 alır. Kullanıcı UI'dan tip filtresi uyguladığında. None
    (default) → tüm tipler geçerli.

    Yuvarlama hatalarını telafi etmek için en yüksek paylı tipe ekleme/çıkarma yapılır.
    """
    base = DIFFICULTY_DISTRIBUTIONS[difficulty]
    visual_bias = TOPIC_VISUAL_BIAS.get(topic_id or "", {})

    if visual_bias:
        visual_share = min(sum(visual_bias.values()), _MAX_VISUAL_SHARE)
        # Bias üst sınırı aşıyorsa orantılı kırp
        if sum(visual_bias.values()) > _MAX_VISUAL_SHARE:
            scale_v = _MAX_VISUAL_SHARE / sum(visual_bias.values())
            visual_bias = {qt: w * scale_v for qt, w in visual_bias.items()}
            visual_share = _MAX_VISUAL_SHARE
        scale_b = 1.0 - visual_share
        weights: list[tuple[QuestionType, float]] = [
            (qt, w * scale_b) for qt, w in base
        ]
        weights.extend(visual_bias.items())
    else:
        weights = list(base)

    # Kullanıcı tip filtresi — izin verilmeyen tiplerin ağırlığını 0 yap.
    # Ardından kalan ağırlıkları renormalize et (toplam 1.0). Filtre sonrası
    # boş kalırsa fail-safe: ISLEM tipi default olarak verilir.
    if allowed_types is not None:
        filtered = [(qt, w) for qt, w in weights if qt in allowed_types]
        total_w = sum(w for _, w in filtered)
        if total_w <= 0:
            # Allowed tiplerden hiçbiri base/visual'da yoksa direkt eşit dağıt.
            n = len(allowed_types) or 1
            filtered = [(qt, 1.0 / n) for qt in allowed_types]
        else:
            filtered = [(qt, w / total_w) for qt, w in filtered]
        weights = filtered

    raw = [(qt, total * w) for qt, w in weights]
    counts: dict[QuestionType, int] = {}
    for qt, v in raw:
        counts[qt] = counts.get(qt, 0) + int(v)
    assigned = sum(counts.values())
    diff = total - assigned
    if diff != 0:
        sorted_types = [qt for qt, _ in sorted(weights, key=lambda x: -x[1])]
        # Aynı QT iki kez gelmesin (visual + base aynı tip olabilir teorik olarak)
        seen: set[QuestionType] = set()
        unique_sorted: list[QuestionType] = []
        for qt in sorted_types:
            if qt not in seen:
                seen.add(qt)
                unique_sorted.append(qt)
        i = 0
        while diff != 0 and i < 200:
            qt = unique_sorted[i % len(unique_sorted)]
            if diff > 0:
                counts[qt] = counts.get(qt, 0) + 1
                diff -= 1
            else:
                if counts.get(qt, 0) > 0:
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
        self._rejected = 0

    def prime(self, normalized_questions: Iterable[str]) -> None:
        """History'den gelen normalize soruları duplikat kontrolüne dahil eder."""
        before = len(self._seen)
        self._seen.update(normalized_questions)
        self._primed_count += len(self._seen) - before

    def is_duplicate(self, question: str) -> bool:
        dup = normalize_question(question) in self._seen
        if dup:
            self._rejected += 1
        return dup

    def add(self, question: str) -> None:
        self._seen.add(normalize_question(question))
        self._contexts.update(extract_context_tokens(question))

    @property
    def context_exclusions(self) -> list[str]:
        return sorted(self._contexts)

    @property
    def primed_count(self) -> int:
        return self._primed_count

    @property
    def rejected_count(self) -> int:
        return self._rejected


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b):
        dot += x * y
        norm_a += x * x
        norm_b += y * y
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))


class SemanticDeduplicator:
    """Embedding tabanlı tekrar önleme.

    `prime()` ile geçmiş sorulara ait embedding'ler yüklenir; `is_duplicate(emb)`
    yeni gelen embedding'i mevcut havuzla cosine similarity üstünden karşılaştırır.
    Threshold üstündeki herhangi bir eşleşme tekrar olarak işaretlenir.

    Embedding üretimi pahalı olduğundan bu sınıf embedding'leri kendi üretmez —
    çağıran taraf (agent) batch embed eder ve bu sınıfı besler.
    """

    def __init__(self, threshold: float = 0.88) -> None:
        self.threshold = threshold
        self._embeddings: list[list[float]] = []
        self._primed_count = 0
        self._rejected = 0

    def prime(self, embeddings: Iterable[Sequence[float]]) -> None:
        before = len(self._embeddings)
        for emb in embeddings:
            if emb:
                self._embeddings.append(list(emb))
        self._primed_count += len(self._embeddings) - before

    def is_duplicate(self, embedding: Sequence[float]) -> tuple[bool, float]:
        """En yüksek similarity'i ve duplicate olup olmadığını döner."""
        if not embedding or not self._embeddings:
            return False, 0.0
        max_sim = 0.0
        for existing in self._embeddings:
            sim = _cosine_similarity(embedding, existing)
            if sim > max_sim:
                max_sim = sim
            if max_sim >= self.threshold:
                return True, max_sim
        return False, max_sim

    def add(self, embedding: Sequence[float]) -> None:
        if embedding:
            self._embeddings.append(list(embedding))

    def record_rejection(self) -> None:
        self._rejected += 1

    @property
    def primed_count(self) -> int:
        return self._primed_count

    @property
    def rejected_count(self) -> int:
        return self._rejected

    @property
    def size(self) -> int:
        return len(self._embeddings)
