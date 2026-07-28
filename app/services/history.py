"""Üretim geçmişi cache'i — aynı isteği tekrarladığında varyasyon için.

(tenant_id, grade, topic_id, kazanim_kod, difficulty) anahtarıyla son N üretilmiş
sorunun normalize hali + bağlam kelimeleri + opsiyonel embedding'i tutulur.

Persistence (settings.enable_history_persist):
    True  → SQLite'a yazar. BAŞLANGIÇTA HİÇBİR SATIR YÜKLENMEZ (MUST-FIX 1,
            2026-07-28) — her anahtar İLK erişildiğinde DB'den tembel yüklenir
            (bkz. `_get_bucket_locked`, `_get_seen_set_locked`). Restart sonrası
            kayıp olmaz, ama açılış artık tablo büyüklüğünden bağımsızdır.
    False → Sadece bellek; eski davranış.

Tenant izolasyonu HistoryKey'in ilk elemanı (str). Default "__shared__"
geriye uyumluluk için; istemci farklı tenant_id verirse cache ayrılır.
"""
from __future__ import annotations

import logging
import sqlite3
import struct
import threading
from collections import deque
from pathlib import Path
from typing import Iterable, Sequence

from app.config import settings
from app.services.db_connection import connect as db_connect

logger = logging.getLogger(__name__)


HistoryKey = tuple[str, int, str, str, str]
"""(tenant_id, grade, topic_id, kazanim_kod, difficulty)"""

DEFAULT_TENANT = "__shared__"


def _key_to_str(key: HistoryKey) -> str:
    return "|".join(str(p) for p in key)


def _pack_embedding(emb: Sequence[float] | None) -> bytes | None:
    if not emb:
        return None
    return struct.pack(f"{len(emb)}f", *emb)


def _unpack_embedding(blob: bytes | None) -> list[float] | None:
    if not blob:
        return None
    n = len(blob) // 4
    return list(struct.unpack(f"{n}f", blob))


class _Entry:
    __slots__ = ("normalized_question", "contexts", "embedding")

    def __init__(
        self,
        normalized_question: str,
        contexts: Iterable[str],
        embedding: Sequence[float] | None = None,
    ) -> None:
        self.normalized_question = normalized_question
        self.contexts = tuple(contexts)
        self.embedding = list(embedding) if embedding else None


class GenerationHistory:
    # RAM sızıntı freni (küçük 3, denetim 2026-07-28): `_cache`/`_seen_sets`
    # anahtar başına process ömrü boyunca büyür (kullanıcı×sınıf×ünite×kazanım×
    # zorluk ile çarpılır). Bu tavan aşılınca insertion-order'daki EN ESKİ
    # anahtar atılır — kayıp yok, ihtiyaç olunca DB'den yeniden tembel yüklenir.
    _MAX_CACHED_KEYS = 500

    def __init__(
        self,
        capacity_per_key: int = 30,
        persist: bool | None = None,
        db_path: str | None = None,
    ) -> None:
        self._capacity = capacity_per_key
        # ÖNEMLİ (MUST-FIX 1, denetim 2026-07-28): eskiden `__init__` burada
        # `_load_from_db()` çağırıp TÜM `history` tablosunu (embedding BLOB'ları
        # dahil) çekip bu deque'lere dolduruyordu. Tavansız modda (§3a) DB artık
        # capacity'e kırpılmadığından (bkz. `record()`), bu eager yükleme her
        # açılışta (Render cold-start) tabloyla birlikte BÜYÜYEN bir ağ/RAM
        # maliyeti doğururdu (Turso = ağ; embedding blob'u ~2.7KB/satır).
        # Fix: `_cache` de `_seen_sets` gibi ANAHTAR BAŞINA TEMBEL yüklenir
        # (bkz. `_get_bucket_locked`) — açılışta HİÇBİR sorgu atılmaz, yalnız
        # gerçekten erişilen anahtar, yalnız `capacity_per_key` kadar satırla
        # yüklenir. Window-function tabanlı tek-sorgu eager yükleme (ROW_NUMBER
        # OVER PARTITION BY) alternatifi değerlendirildi ve lokal sqlite3'te
        # ÇALIŞTIĞI doğrulandı, ama prod'daki libsql (Turso) yolunda bu ortamda
        # DERLENEMEDİĞİ için (Rust toolchain yok) fiilen doğrulanamadı — o riski
        # almak yerine zaten kanıtlı olan tembel-yükleme deseni (`_get_seen_set_locked`
        # ile aynı) tercih edildi: SQL diyalektinden bağımsız, basit `WHERE key=?`.
        self._cache: dict[HistoryKey, deque[_Entry]] = {}
        # Kalıcı görülmüş-set (Soru deposu Faz 1, §3a): `_cache` (deque, sınırlı —
        # context_exclusions/seen_embeddings için hâlâ kullanılır) yerine
        # `seen_questions()` için anahtar başına TAVANSIZ set. Process ömrü
        # boyunca cache'lenir (anahtar başına tek DB sorgusu — bkz. `_get_seen_set_locked`).
        self._seen_sets: dict[HistoryKey, set[str]] = {}
        self._lock = threading.Lock()
        self._persist = settings.enable_history_persist if persist is None else persist
        self._db_path = db_path or settings.history_db_path
        self._db: sqlite3.Connection | None = None
        # Denetim 2026-07-28 (persist-kapalı tahliye kaybı fix'i): persist
        # kapalıyken/DB yokken tahliye devre dışı bırakıldığında kullanıcıya
        # bir kez uyarı basmak için — sessizce her seferinde basılmasın.
        self._evict_disabled_warned = False
        if self._persist:
            self._init_db()
            # DİKKAT: eager `_load_from_db()` KASITLI OLARAK çağrılmıyor —
            # yukarıdaki not. Tüm okuma/yazma yolları artık `_get_bucket_locked`/
            # `_get_seen_set_locked` üzerinden anahtar-bazlı tembel yükleme yapar.

    def _init_db(self) -> None:
        try:
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
            self._db = db_connect(self._db_path)
            self._db.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL,
                    normalized_question TEXT NOT NULL,
                    contexts TEXT NOT NULL,
                    embedding BLOB,
                    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
                )
                """
            )
            self._db.execute(
                "CREATE INDEX IF NOT EXISTS idx_history_key ON history(key, id)"
            )
            self._db.commit()
        except sqlite3.Error as exc:
            logger.warning("History DB init başarısız, persistence devre dışı: %s", exc)
            self._persist = False
            self._db = None

    def _evict_oldest_if_needed(self, mapping: dict, new_key: HistoryKey) -> None:
        """`mapping`'e `new_key` eklendikten SONRA çağrılır (küçük 3, denetim
        2026-07-28) — `_MAX_CACHED_KEYS` aşılırsa insertion-order'daki EN ESKİ
        anahtarı atar. `new_key`'in kendisi hiçbir zaman atılmaz (az önce
        eklendi, en yeni odur).

        ÖNEMLİ (2. denetim, 2026-07-28 — persist-kapalı kayıp fix'i): tahliye
        YALNIZ `self._persist and self._db is not None` iken uygulanır. Persist
        kapalıyken (ya da `_init_db()` bir DB arızasından sonra `self._persist`'i
        False'a düşürdüğünde) bellek TEK kaynaktır — atılan anahtar DB'den
        YENİDEN YÜKLENEMEZ, boş olarak yeniden oluşur. Bu, o kullanıcının daha
        önce gördüğü soruyu bir daha "hiç görülmemiş" saymak demektir — tam da
        Faz 1'in düzelttiği regresyonun aynısı, sessizce geri gelirdi. Bu yüzden
        persist kapalıyken tahliye YAPILMAZ (mapping'e dokunulmaz); anahtar
        sayısı sınırsız büyüyebilir ama bu zaten arızalı/degrade bir mod —
        kaybetmek büyümekten kötü. İlk aşımda BİR KEZ `logger.warning` basılır.

        ÇAĞRI SÖZLEŞMESİ: `self._lock` tutulurken çağrılır.
        """
        if len(mapping) <= self._MAX_CACHED_KEYS:
            return
        if not (self._persist and self._db is not None):
            if not self._evict_disabled_warned:
                logger.warning(
                    "Persist kapalı/DB yok → görülmüş-set/deque tahliyesi devre "
                    "dışı (anahtar sayısı %d, tavan %d) — bellek anahtar "
                    "sayısıyla büyüyor. Tahliye edip kaybetmek yerine büyümeyi "
                    "seçtik: bu modda atılan anahtar DB'den yeniden yüklenemez.",
                    len(mapping), self._MAX_CACHED_KEYS,
                )
                self._evict_disabled_warned = True
            return
        oldest = next(iter(mapping))
        if oldest != new_key:
            del mapping[oldest]

    def _get_bucket_locked(self, key: HistoryKey) -> "deque[_Entry]":
        """Anahtarın SINIRLI (capacity_per_key) bellek deque'ini döner (lazy-load).

        ÇAĞRI SÖZLEŞMESİ: `self._lock` tutulurken çağrılır (kilitlemeyi kendisi
        yapmaz) — `_get_seen_set_locked` ile aynı desen. İlk çağrıda persist
        açıksa DB'den yalnız bu anahtarın SON `capacity_per_key` satırı çekilir
        (`ORDER BY id DESC LIMIT capacity`), sonra deque'e ESKİDEN-YENİYE sırayla
        eklenir (mevcut `context_exclusions`'ın `reversed(entries)` semantiği —
        en yeniden en eskiye — korunsun diye).

        ÖDÜN (bkz. MUST-FIX 1, denetim 2026-07-28): bu, kilit tutulurken bir DB
        sorgusu atar — `_get_seen_set_locked` ile AYNI ödün. Mixed modda 3
        bucket paralel thread ilk dokunuşta serileşebilir; anahtar başına BİR
        KEZ olduğundan (sonraki her çağrı bu process-ömrü cache'ten döner) kabul
        edilebilir kabul edildi.
        """
        bucket = self._cache.get(key)
        if bucket is not None:
            return bucket
        bucket = deque(maxlen=self._capacity)
        if self._persist and self._db is not None:
            try:
                rows = self._db.execute(
                    "SELECT normalized_question, contexts, embedding FROM history "
                    "WHERE key = ? ORDER BY id DESC LIMIT ?",
                    (_key_to_str(key), self._capacity),
                ).fetchall()
                for nq, ctx_str, emb_blob in reversed(rows):
                    contexts = ctx_str.split("\x1f") if ctx_str else []
                    emb = _unpack_embedding(emb_blob)
                    bucket.append(_Entry(nq, contexts, emb))
            except Exception as exc:  # noqa: BLE001 — best-effort, boş bucket ile devam
                logger.warning("Bellek deque'i yüklenemedi (key=%s): %s", key, exc)
        self._cache[key] = bucket
        self._evict_oldest_if_needed(self._cache, key)
        return bucket

    @staticmethod
    def _parse_key(key_str: str) -> HistoryKey | None:
        parts = key_str.split("|")
        if len(parts) != 5:
            return None
        try:
            return (parts[0], int(parts[1]), parts[2], parts[3], parts[4])
        except ValueError:
            return None

    def record(
        self,
        key: HistoryKey,
        normalized_question: str,
        contexts: Iterable[str],
        embedding: Sequence[float] | None = None,
    ) -> None:
        contexts_list = list(contexts)
        entry = _Entry(normalized_question, contexts_list, embedding)
        with self._lock:
            # `_get_bucket_locked`: bu anahtara bu process'te İLK dokunuş ise
            # (deque henüz `_cache`'te yok) DB'den son `capacity` satırı tembel
            # yükler, sonra yeni girdiyi ekler — eski satırlar kaybolmaz.
            bucket = self._get_bucket_locked(key)
            bucket.append(entry)
            if settings.history_seen_unbounded:
                self._get_seen_set_locked(key).add(normalized_question)
        if self._persist and self._db is not None:
            try:
                key_str = _key_to_str(key)
                self._db.execute(
                    "INSERT INTO history (key, normalized_question, contexts, embedding) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        key_str,
                        normalized_question,
                        "\x1f".join(contexts_list),
                        _pack_embedding(embedding),
                    ),
                )
                # Capacity-aşımı: en eski kayıtları sil — YALNIZ bayrak kapalıyken.
                # ÖNEMLİ (§3a): bu DELETE aslında DB'yi de `capacity_per_key`'e
                # kırpıyordu — `seen_questions()` yalnız bellek deque'ine değil,
                # DB'nin kendisine de bağlı olarak sınırlıydı. Tavansız modda bu
                # satır ATLANIR: `history` tablosu anahtar başına TÜM kayıtları
                # kalıcı tutar (yeni migrasyon gerekmez, aynı tablo) →
                # `_get_seen_set_locked` DB'den doğru/tam sonuç okuyabilir.
                # Bellek deque'i (`self._cache`) zaten `maxlen=capacity` ile
                # sınırlı olduğundan context_exclusions/seen_embeddings davranışı
                # DEĞİŞMEZ — yalnız DB'nin büyüklüğü artık capacity'e kilitli değil.
                if not settings.history_seen_unbounded:
                    self._db.execute(
                        "DELETE FROM history WHERE key = ? AND id NOT IN ("
                        "SELECT id FROM history WHERE key = ? ORDER BY id DESC LIMIT ?"
                        ")",
                        (key_str, key_str, self._capacity),
                    )
                self._db.commit()
            except sqlite3.Error as exc:
                logger.warning("History DB write başarısız (kayıp olmayacak, RAM güncellendi): %s", exc)

    def seen_embeddings(self, key: HistoryKey) -> list[list[float]]:
        with self._lock:
            bucket = self._get_bucket_locked(key)
            return [e.embedding for e in bucket if e.embedding]

    def _get_seen_set_locked(self, key: HistoryKey) -> set[str]:
        """Anahtarın TAVANSIZ görülmüş-setini döner (lazy-load + cache).

        ÇAĞRI SÖZLEŞMESİ: `self._lock` tutulurken çağrılır (kilitlemeyi kendisi
        yapmaz). İlk çağrıda persist açıksa DB'den `SELECT ... WHERE key = ?`
        ile tek sorgu yapılır (idx_history_key kullanır) ve process ömrü boyunca
        cache'lenir — sonraki her `record()`/`seen_questions()` çağrısı DB'ye
        gitmez (Turso'da ağ round-trip'i anahtar başına BİR kez).

        ÖDÜN (küçük 4, denetim 2026-07-28): bu, `self._lock` tutulurken bir DB
        sorgusu (ağ, Turso'da) atar. Mixed modda 3 zorluk bucket'ı PARALEL
        thread'te koştuğundan, bu anahtara İLK dokunuş anında üç thread aynı
        kilitte sıraya girip serileşebilir. Kabul edilen ödün: anahtar başına
        yalnız BİR KEZ olur (sonraki her çağrı cache'ten, kilitsiz döner) —
        "neden kilit altında ağ çağrısı var" diye şaşırma, bilinçli bir tercih.
        """
        cached = self._seen_sets.get(key)
        if cached is not None:
            return cached
        seen: set[str] = set()
        if self._persist and self._db is not None:
            try:
                rows = self._db.execute(
                    "SELECT normalized_question FROM history WHERE key = ?",
                    (_key_to_str(key),),
                ).fetchall()
                seen.update(r[0] for r in rows if r and r[0])
            except Exception as exc:  # noqa: BLE001 — best-effort, boş sette devam
                logger.warning(
                    "Kalıcı görülmüş-set yüklenemedi (key=%s): %s", key, exc
                )
        else:
            # Persist kapalı → tek kaynak bellekteki (sınırlı) deque.
            bucket = self._get_bucket_locked(key)
            if bucket:
                seen.update(e.normalized_question for e in bucket)
        self._seen_sets[key] = seen
        self._evict_oldest_if_needed(self._seen_sets, key)
        return seen

    def seen_questions(self, key: HistoryKey) -> set[str]:
        """Anahtarın gördüğü TÜM soruların normalize metni.

        settings.history_seen_unbounded=True (varsayılan) → tavansız: 30'luk
        deque pencerenin ÖTESİNDEKİ eski sorular da dışlanır (bkz. §3a — eskiden
        3. kağıtta 1. kağıdın soruları "hiç görülmemiş" sayılıp tekrar
        gelebiliyordu). False → eski davranış (yalnız bellek deque'i, sınırlı).
        """
        if settings.history_seen_unbounded:
            with self._lock:
                return set(self._get_seen_set_locked(key))
        with self._lock:
            bucket = self._get_bucket_locked(key)
            return {e.normalized_question for e in bucket}

    def context_exclusions(self, key: HistoryKey, max_contexts: int = 15) -> list[str]:
        with self._lock:
            bucket = self._get_bucket_locked(key)
            entries = list(bucket)
        all_ctx: set[str] = set()
        for e in reversed(entries):
            all_ctx.update(e.contexts)
            if len(all_ctx) >= max_contexts:
                break
        return sorted(all_ctx)[:max_contexts]

    def size(self, key: HistoryKey) -> int:
        with self._lock:
            bucket = self._get_bucket_locked(key)
            return len(bucket)

    def clear(self, key: HistoryKey | None = None) -> None:
        """key None ise tüm cache'i temizler."""
        with self._lock:
            if key is None:
                self._cache.clear()
                self._seen_sets.clear()
            else:
                self._cache.pop(key, None)
                self._seen_sets.pop(key, None)
        if self._persist and self._db is not None:
            try:
                if key is None:
                    self._db.execute("DELETE FROM history")
                else:
                    self._db.execute("DELETE FROM history WHERE key = ?", (_key_to_str(key),))
                self._db.commit()
            except sqlite3.Error as exc:
                logger.warning("History DB clear başarısız: %s", exc)


GENERATION_HISTORY = GenerationHistory()
