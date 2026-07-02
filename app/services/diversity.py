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
    # Format tipleri (coktan_secmeli, dogru_yanlis, bosluk_doldurma, eslestirme,
    # siralama) Bloom seviyesine göre yerleştirildi; her tip yalnızca pedagojik
    # olarak anlamlı olduğu zorluklarda varsayılan karışıma girer:
    #   - dogru_yanlis  → hatırlama/anlama: KOLAY (asıl), ORTA (ikincil). ZOR yok.
    #   - bosluk_doldurma → hatırlama/uygulama: KOLAY + ORTA. ZOR yok.
    #   - eslestirme    → anlama: KOLAY + ORTA. ZOR yok.
    #   - siralama      → anlama/analiz: ORTA + ZOR. KOLAY yok.
    #   - coktan_secmeli → her seviye (LGS hazırlığı).
    # Sözel/işlem çekirdek her zaman baskın (%67-78). Kullanıcı UI'dan bir tipi
    # açıkça seçtiğinde profilde yoksa bile distribute_question_types() taban
    # (floor) ağırlık verir → seçilen tip yine de üretilir.
    Difficulty.KOLAY: [
        # Çekirdek (toplam 0.67) — kazanım pekiştirme ağırlıklı.
        (QuestionType.ISLEM, 0.30),
        (QuestionType.KAVRAM_SORUSU, 0.18),
        (QuestionType.SOZEL_PROBLEM, 0.10),
        (QuestionType.GUNLUK_HAYAT, 0.09),
        # Format (toplam 0.33) — kolay seviyede pekiştirmeye en uygun tipler.
        (QuestionType.COKTAN_SECMELI, 0.11),
        (QuestionType.DOGRU_YANLIS, 0.09),
        (QuestionType.BOSLUK_DOLDURMA, 0.08),
        (QuestionType.ESLESTIRME, 0.05),
    ],
    Difficulty.ORTA: [
        # Çekirdek (toplam 0.72) — sözel problem + işlem ağırlıklı.
        (QuestionType.SOZEL_PROBLEM, 0.22),
        (QuestionType.ISLEM, 0.19),
        (QuestionType.KAVRAM_SORUSU, 0.10),
        (QuestionType.AKIL_YURUTME, 0.09),
        (QuestionType.GUNLUK_HAYAT, 0.07),
        (QuestionType.MODELLEME, 0.05),
        # Format (toplam 0.28) — çoktan seçmeli (LGS) baskın, beş tip de mevcut.
        (QuestionType.COKTAN_SECMELI, 0.12),
        (QuestionType.BOSLUK_DOLDURMA, 0.07),
        (QuestionType.DOGRU_YANLIS, 0.04),
        (QuestionType.ESLESTIRME, 0.03),
        (QuestionType.SIRALAMA, 0.02),
    ],
    Difficulty.ZOR: [
        # Çekirdek (toplam 0.78) — akıl yürütme + çok adımlı sözel ağırlıklı.
        (QuestionType.AKIL_YURUTME, 0.28),
        (QuestionType.SOZEL_PROBLEM, 0.24),
        (QuestionType.MODELLEME, 0.13),
        (QuestionType.ISLEM, 0.08),
        (QuestionType.GUNLUK_HAYAT, 0.05),
        # Format (toplam 0.22) — çoktan seçmeli (LGS son aşama) + sıralama
        # (analiz/karşılaştırma). Doğru/yanlış ve eşleştirme zor seviyede
        # yüzeysel kaldığından varsayılan karışıma alınmadı.
        (QuestionType.COKTAN_SECMELI, 0.15),
        (QuestionType.SIRALAMA, 0.07),
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

# "Yeni nesil / beceri temelli" dağıtım — zorluktan BAĞIMSIZ eksen. Uzun bağlam +
# yorumlama gerektiren tipler baskın; salt_islem / dogru_yanlis / eslestirme gibi
# kısa-format tipler dışarıda bırakılır (yeni nesil ruhuna aykırı). Aritmetik zorluğu
# yine "Zorluk Kalibrasyonu" belirler; bu profil sadece SORU KARAKTERİNİ değiştirir.
YENI_NESIL_DISTRIBUTION: list[tuple[QuestionType, float]] = [
    (QuestionType.GUNLUK_HAYAT, 0.28),
    (QuestionType.SOZEL_PROBLEM, 0.24),
    (QuestionType.AKIL_YURUTME, 0.16),
    (QuestionType.MODELLEME, 0.12),
    (QuestionType.COKTAN_SECMELI, 0.12),
    (QuestionType.GRAFIK_OKUMA, 0.04),
    (QuestionType.TABLO_SORUSU, 0.04),
]


def distribute_question_types(
    total: int,
    difficulty: Difficulty,
    topic_id: str | None = None,
    allowed_types: set[QuestionType] | None = None,
    yeni_nesil: bool = False,
) -> dict[QuestionType, int]:
    """Toplam soruyu zorluk profiline göre soru tiplerine paylaştırır.

    `topic_id` verilirse topic'e özel görsel/yapısal tipler (TABLO_SORUSU,
    GRAFIK_OKUMA, GORSEL_GEOMETRI, ORUNTU_SEKIL, SALT_ISLEM) belirli bir paya
    sahip olur; geri kalan pay zorluk profili üzerinden dağıtılır.

    `allowed_types` verilirse SADECE bu tipler arası dağıtım yapılır; zorluk
    profilinde ağırlığı olmayan ama istenen tipler taban (floor) ağırlık alır →
    seçilen her tip mutlaka temsil edilir. None (default) → tüm tipler geçerli.

    Yuvarlama: en büyük kalan (Hamilton) yöntemi kullanılır — düşük paylı tipler
    `int()` kırpması yüzünden sistematik olarak elenmez.
    """
    if yeni_nesil:
        # HARMAN (blend): normal zorluk dağılımı ile yeni nesil dağılımını 50/50
        # ortalar → aynı kağıtta hem hızlı pratik (islem/salt_islem) hem senaryo/
        # beceri soruları bir arada. (Tam senaryo değil; kullanıcı "karıştır" istedi.)
        _normal: dict[QuestionType, float] = {}
        for qt, w in DIFFICULTY_DISTRIBUTIONS[difficulty]:
            _normal[qt] = _normal.get(qt, 0.0) + w
        _yeni: dict[QuestionType, float] = {}
        for qt, w in YENI_NESIL_DISTRIBUTION:
            _yeni[qt] = _yeni.get(qt, 0.0) + w
        base = [
            (qt, 0.5 * _normal.get(qt, 0.0) + 0.5 * _yeni.get(qt, 0.0))
            for qt in (set(_normal) | set(_yeni))
        ]
    else:
        base = DIFFICULTY_DISTRIBUTIONS[difficulty]
    # Harman modda salt_islem KALIR (pratik kısmı); topic bias'a dokunma.
    visual_bias = dict(TOPIC_VISUAL_BIAS.get(topic_id or "", {}))
    if yeni_nesil and visual_bias:
        # Yeni nesil modda ŞEKİLLİ soru payını artır (kullanıcı "şekilli + bağlamsal"
        # istedi). Yalnızca gerçek figür tipleri boost edilir; salt_islem (kuru işlem) değil.
        _figure = {QuestionType.GORSEL_GEOMETRI, QuestionType.GRAFIK_OKUMA,
                   QuestionType.TABLO_SORUSU, QuestionType.ORUNTU_SEKIL}
        visual_bias = {
            qt: (w * 1.5 if qt in _figure else w) for qt, w in visual_bias.items()
        }

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

    # Kullanıcı tip filtresi — yalnızca izin verilen tipler arası dağıtım yapılır.
    # ÖNEMLİ: Bir tip kullanıcı tarafından açıkça istendiği hâlde seçilen zorluk
    # profilinde (DIFFICULTY_DISTRIBUTIONS) ağırlığa sahip değilse (örn. ORTA
    # zorlukta `bosluk_doldurma`), eski kod onu sessizce eler ve hiç üretmezdi.
    # Artık profilde bulunmayan ama istenen her tipe taban (floor) ağırlık verilir
    # → kullanıcının seçtiği her tip mutlaka temsil edilir.
    if allowed_types is not None:
        weight_map: dict[QuestionType, float] = {}
        for qt, w in weights:
            weight_map[qt] = weight_map.get(qt, 0.0) + w
        present = {qt: weight_map[qt] for qt in allowed_types if qt in weight_map}
        # Profilde olmayan istenen tipler için taban ağırlık: eşleşen ağırlıkların
        # ortalaması (hiç eşleşme yoksa düz 1.0 → tümü eşit dağılır).
        floor = (sum(present.values()) / len(present)) if present else 1.0
        filtered = [
            (qt, present.get(qt, floor))
            for qt in sorted(allowed_types, key=lambda t: t.value)
        ]
        total_w = sum(w for _, w in filtered)
        weights = [(qt, w / total_w) for qt, w in filtered]

    # Ağırlıkları tipe göre birleştir (base + visual bias aynı tipi iki kez
    # listeleyebilir) ve toplamı 1.0'a normalize et.
    weight_by_type: dict[QuestionType, float] = {}
    for qt, w in weights:
        if w > 0:
            weight_by_type[qt] = weight_by_type.get(qt, 0.0) + w
    total_w = sum(weight_by_type.values())
    if total_w <= 0:
        return {}
    weight_by_type = {qt: w / total_w for qt, w in weight_by_type.items()}

    # En büyük kalan (Hamilton) yöntemi: önce taban (floor) atanır, artan
    # kontenjanlar en büyük ondalık kalana sahip tiplere verilir. Eski "artığı
    # en yüksek ağırlıklı tipe ekle" yaklaşımı, düşük ağırlıklı tipleri (örn.
    # bosluk_doldurma 0.07 → 10 soruda 0.7) her seferinde 0'a düşürüyordu.
    exact = {qt: total * w for qt, w in weight_by_type.items()}
    counts: dict[QuestionType, int] = {qt: int(v) for qt, v in exact.items()}
    diff = total - sum(counts.values())
    if diff > 0:
        order = sorted(
            weight_by_type,
            key=lambda qt: (exact[qt] - counts[qt], weight_by_type[qt], qt.value),
            reverse=True,
        )
        for qt in order[:diff]:
            counts[qt] += 1
    elif diff < 0:
        # Float hassasiyeti nedeniyle nadiren fazla atanırsa en küçük ağırlıklı
        # tiplerden geri al.
        order = sorted(weight_by_type, key=lambda qt: (weight_by_type[qt], qt.value))
        i = 0
        while diff < 0 and i < 1000:
            qt = order[i % len(order)]
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
