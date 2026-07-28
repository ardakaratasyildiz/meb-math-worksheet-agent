"""Üretim sonucu önbelleği — aynı (grade, topic, kazanım, difficulty, count)
istekleri için cached soru seti döndürür, LLM çağrısını atlar.

Tasarım:
    - SQLite tablosu (`generation_cache`), aynı history.sqlite3 dosyasında.
    - Key: cache_key = "g{grade}|{topic_id}|{kazanim_kod}|{difficulty}|q{count}"
    - Her key için en fazla `max_per_key` cached set saklanır (FIFO).
    - get() önce key ile filter, sonra exclude_questions overlap'i 0 olan ilk
      set'i döndürür (kullanıcının history'sinde olan sorular tekrar gelmesin).
    - put() yeni set ekler, max aşılırsa en eski silinir.

Semantic fallback (yakın kazanım/zorluk için cache hit) Sprint 7+'da değerlendirilecek;
şu anki sürüm exact-match — basit, deterministik, embedding gerekmez.
"""
from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from pathlib import Path
from typing import Iterable, NamedTuple

from app.config import settings
from app.models.schemas import Question
from app.services.db_connection import connect as db_connect

logger = logging.getLogger(__name__)


def _cache_key(
    grade: int,
    topic_id: str,
    kazanim_kod: str | None,
    difficulty: str,
    question_count: int,
    allowed_types=None,
    yeni_nesil: bool = False,
) -> str:
    # allowed_types (kullanıcının seçtiği soru tipi filtresi) anahtara dahil
    # edilir — aksi halde filtre seçen kullanıcıya filtresiz bir cached set
    # (veya tersi) dönebilirdi. None/boş → "all".
    if allowed_types:
        types = "+".join(sorted(getattr(t, "value", str(t)) for t in allowed_types))
    else:
        types = "all"
    # yeni_nesil (premium: farklı model + prompt + görsel-ağırlıklı dağılım)
    # anahtara dahildir — premium ve normal setler farklı karakterde olduğundan
    # ayrı havuzlarda tutulur; premium isteyen kullanıcıya normal set (veya tersi)
    # dönmesin. Normal mod SONEK EKLEMEZ → eski cache kayıtları geçerli kalır.
    suffix = "|premium" if yeni_nesil else ""
    return (
        f"g{grade}|{topic_id}|{kazanim_kod or '__AUTO__'}|{difficulty}"
        f"|q{question_count}|t{types}{suffix}"
    )


class GenerationCache:
    """Thread-safe SQLite tabanlı cache. Singleton kullanım önerilir (`GENERATION_CACHE`)."""

    def __init__(
        self,
        db_path: str | None = None,
        max_per_key: int = 10,
    ) -> None:
        self._db_path = db_path or settings.history_db_path
        self._max_per_key = max_per_key
        self._lock = threading.Lock()
        self._db = None
        self._hits = 0
        self._misses = 0
        self._init_db()

    def _init_db(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db = db_connect(self._db_path)
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS generation_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT NOT NULL,
                questions_json TEXT NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_cache_key_created "
            "ON generation_cache(cache_key, created_at DESC)"
        )
        self._db.commit()

    def get(
        self,
        grade: int,
        topic_id: str,
        kazanim_kod: str | None,
        difficulty: str,
        question_count: int,
        exclude_questions: Iterable[str] = (),
        allowed_types=None,
        yeni_nesil: bool = False,
    ) -> list[Question] | None:
        """Cached set döndürür ya da None.

        exclude_questions: kullanıcının history'sinde olan normalize edilmiş sorular.
        Bir cached set'in herhangi bir sorusu bu kümede ise o set atlanır;
        kalan set yoksa miss.

        allowed_types: kullanıcının soru tipi filtresi — cache anahtarına dahildir.
        yeni_nesil: premium mod — cache anahtarına dahildir (ayrı havuz).
        """
        from app.services.diversity import normalize_question

        excl = set(exclude_questions)
        key = _cache_key(
            grade, topic_id, kazanim_kod, difficulty, question_count,
            allowed_types, yeni_nesil,
        )
        with self._lock:
            assert self._db is not None
            rows = self._db.execute(
                "SELECT questions_json FROM generation_cache WHERE cache_key = ? "
                "ORDER BY created_at DESC LIMIT ?",
                (key, self._max_per_key),
            ).fetchall()

        if not rows:
            self._misses += 1
            return None

        # Rastgele bir set seç ki çeşitlilik korunsun (zaman damgasıyla sıralı geldiler)
        import random
        random.shuffle(rows)

        for (questions_json,) in rows:
            try:
                data = json.loads(questions_json)
                questions = [Question.model_validate(q) for q in data]
            except (json.JSONDecodeError, ValueError) as exc:
                logger.warning("Cache satırı parse edilemedi (%s): %s", key, exc)
                continue
            if excl:
                has_overlap = any(
                    normalize_question(q.question) in excl for q in questions
                )
                if has_overlap:
                    continue
            self._hits += 1
            logger.info("Cache HIT: %s (%d soru)", key, len(questions))
            return questions

        # Tüm cached set'ler history'de var
        self._misses += 1
        logger.info("Cache MISS (history overlap): %s", key)
        return None

    def put(
        self,
        grade: int,
        topic_id: str,
        kazanim_kod: str | None,
        difficulty: str,
        question_count: int,
        questions: list[Question],
        allowed_types=None,
        yeni_nesil: bool = False,
    ) -> None:
        """Yeni set ekler. Aynı key için max_per_key aşıldıysa en eski silinir."""
        if not questions:
            return
        key = _cache_key(
            grade, topic_id, kazanim_kod, difficulty, question_count,
            allowed_types, yeni_nesil,
        )
        # Pydantic mode="json" → datetime/enum'ları string'e çevirir.
        payload = json.dumps(
            [q.model_dump(mode="json") for q in questions],
            ensure_ascii=False,
        )
        now = time.time()
        with self._lock:
            assert self._db is not None
            self._db.execute(
                "INSERT INTO generation_cache (cache_key, questions_json, created_at) "
                "VALUES (?, ?, ?)",
                (key, payload, now),
            )
            # Trim: bu key için fazla satırları sil.
            self._db.execute(
                """
                DELETE FROM generation_cache
                WHERE cache_key = ?
                  AND id NOT IN (
                    SELECT id FROM generation_cache
                    WHERE cache_key = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                  )
                """,
                (key, key, self._max_per_key),
            )
            self._db.commit()
        logger.info("Cache PUT: %s (%d soru)", key, len(questions))

    def stats(self) -> dict[str, int]:
        with self._lock:
            assert self._db is not None
            total = self._db.execute(
                "SELECT COUNT(*) FROM generation_cache"
            ).fetchone()[0]
            distinct = self._db.execute(
                "SELECT COUNT(DISTINCT cache_key) FROM generation_cache"
            ).fetchone()[0]
        return {
            "hits": self._hits,
            "misses": self._misses,
            "total_entries": int(total),
            "distinct_keys": int(distinct),
        }

    def clear(self) -> None:
        """Test ve admin amaçlı toplu temizlik."""
        with self._lock:
            assert self._db is not None
            self._db.execute("DELETE FROM generation_cache")
            self._db.commit()
            self._hits = 0
            self._misses = 0


GENERATION_CACHE = GenerationCache(max_per_key=settings.generation_cache_max_per_key)


# ---------------------------------------------------------------------------
# Yedek soru havuzu (spare pool)
# ---------------------------------------------------------------------------


def _pool_key(
    grade: int,
    topic_id: str,
    kazanim_kod: str | None,
    difficulty: str,
    allowed_types=None,
    yeni_nesil: bool = False,
) -> str:
    """Havuz anahtarı — `_cache_key`'in soru SAYISI olmayan hâli.

    `generation_cache` anahtarı `q{count}` taşır: 10 soruluk bir set 20 soruluk
    isteğe hizmet edemez (isabet oranı düşük). Havuz soru-bazlı olduğundan sayı
    anahtarda yer ALMAZ → her istek havuzdan istediği kadar çekebilir.
    """
    if allowed_types:
        types = "+".join(sorted(getattr(t, "value", str(t)) for t in allowed_types))
    else:
        types = "all"
    suffix = "|premium" if yeni_nesil else ""
    return (
        f"g{grade}|{topic_id}|{kazanim_kod or '__AUTO__'}|{difficulty}"
        f"|t{types}{suffix}"
    )


class PoolItem(NamedTuple):
    """`take_for_serving()` sonucu — Faz 2 tembel damga (§3c) için soru + damga durumu.

    `critic_pass`:
        1    → satır zaten damgalı ("bedava damga" ya da önceki tembel damga).
               Çağıran taraf bu soruyu math_verifier/critic'ten HİÇ geçirmeden
               doğrudan servis eder (marjinal maliyet ~0 — Faz 2'nin asıl kazancı).
        None → hiç denetlenmemiş. Çağıran taraf BİR KEZ critic'ten geçirir, sonucu
               `SpareQuestionPool.stamp()` ile satıra yazar (geçtiyse 1, reddettiyse 0).

    `critic_pass = 0` olan satırlar `take()`/`take_for_serving()` tarafından ASLA
    döndürülmez (SQL WHERE'de elenir) — bu yüzden bu alan hiçbir zaman 0 olmaz.
    """

    question: Question
    critic_pass: int | None


class SpareQuestionPool:
    """Fazla üretilmiş soruların soru-BAZLI envanteri.

    NEDEN: `generation_overshoot_ratio` (1.8) hedefin ~2 katı soru ürettiriyor —
    eleme payını tek çağrıda karşılamak için (latency). Eleme az olduğunda fazla
    sorular `questions[:question_count]` ile KIRPILIP ATILIYORDU: ölçümde 20
    soruluk sosyal kağıdı için 36 soru üretilip 12'si çöpe gitti (~%40 çıktı
    token'ı). Burada fazlalar saklanır ve SONRAKİ isteklerde LLM çağrısı yerine
    buradan karşılanır → overshoot israf olmaktan çıkıp STOK olur.

    NOT: havuza yazılan sorular `_process_batch` + dedup'tan geçmiştir ama
    math_verifier/critic'ten GEÇMEMİŞ olabilir (kırpma bu filtrelerden önce
    oluyor). Bu yüzden havuzdan çekilen sorular çağıran tarafta filtrelerden
    yeniden geçirilir — critic ucuz (flash-lite, gruplu), üretim pahalı.

    FAZ 2 (docs/COST_QUALITY_V2_PLAN.md §3b/§3c): havuz artık BİRİNCİL servis
    yolu (`enable_pool_first_serving`) — `agent.py::generate()` LLM'e gitmeden
    ÖNCE burayı dener. `critic_pass=1` damgalı satırlar filtrelerden hiç
    geçirilmeden servis edilir (`take_for_serving`/`stamp`, marjinal maliyet
    ~0). Bu yüzden `add_many`'nin trim'i `used_count`'a göre DEĞİL damga
    durumuna göre korur (bkz. add_many) — aksi halde en çok servis edilen
    (== en çok damgalanan) satırlar ilk silinir, ödenen damga hep çöpe giderdi.
    """

    def __init__(self, db_path: str | None = None, max_per_key: int = 300) -> None:
        self._db_path = db_path or settings.history_db_path
        self._max_per_key = max_per_key
        self._lock = threading.Lock()
        self._db = None
        self._served = 0
        self._stored = 0
        self._init_db()

    # Faz 1 şema genişletmesi (§3d, docs/COST_QUALITY_V2_PLAN.md) — sorgulanabilir
    # alanlar + kalıcı kimlik (question_id) + damga alanları. `pool_key` bugün bir
    # string ve bu alanları İÇİNE GÖMÜYOR (sorgulanamıyor); kolonlar bunları
    # ayrıştırır. (kolon adı, SQL tipi) — sıra ADD COLUMN sırasıyla eşleşir.
    _SCHEMA_MIGRATIONS: list[tuple[str, str]] = [
        ("question_id", "TEXT"),
        ("subject", "TEXT"),
        ("grade", "INTEGER"),
        ("unit_id", "TEXT"),
        ("kazanim_kod", "TEXT"),
        ("question_type", "TEXT"),
        ("difficulty", "TEXT"),
        ("critic_pass", "INTEGER"),
        ("critic_confidence", "REAL"),
        ("verified_at", "REAL"),
        ("verifier_model", "TEXT"),
        ("quality_score", "REAL"),
        ("flagged_count", "INTEGER DEFAULT 0"),
        ("source", "TEXT"),
    ]

    def _init_db(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db = db_connect(self._db_path)
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS spare_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pool_key TEXT NOT NULL,
                norm_question TEXT NOT NULL,
                question_json TEXT NOT NULL,
                used_count INTEGER DEFAULT 0,
                created_at REAL NOT NULL
            )
            """
        )
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_spare_key "
            "ON spare_questions(pool_key, used_count, created_at)"
        )
        # Aynı sorunun havuzda iki kez durmasını engelle.
        self._db.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_spare_unique "
            "ON spare_questions(pool_key, norm_question)"
        )
        self._db.commit()
        # Şema genişletmesi BEST-EFFORT: prod'da dolu bir tablo üzerinde çalışır
        # (Turso) — migrasyon hatası havuzun temel add_many/take işlevini ASLA
        # düşürmemeli (sınıfın genel "istisna fırlatmaz" sözleşmesiyle aynı).
        try:
            self._migrate_schema()
        except Exception as exc:  # noqa: BLE001 — migrasyon havuzu düşürmesin
            logger.warning("Havuz şema migrasyonu başarısız (yutuldu): %s", exc)

    def _migrate_schema(self) -> None:
        """`spare_questions`'ı Faz 1 kolonlarıyla genişletir — idempotent, BEST-EFFORT.

        Adımlar (her biri ayrı ayrı try/except ile korunur, biri başarısız olsa
        diğerleri denenir):
          1) PRAGMA table_info ile hangi kolonların zaten var olduğu bulunur;
             yalnız EKSİK olanlar `ALTER TABLE ... ADD COLUMN` ile eklenir
             (dolu tabloda mevcut satırlar bozulmaz, yeni kolonlar NULL/default
             ile başlar).
          2) Migrasyon öncesi yazılmış satırların `question_id`'si NULL'dır;
             `norm_question`'dan tek seferlik best-effort backfill yapılır.
             Bu adım her `_init_db()` çağrısında tekrar çalışır ama yalnız HÂLÂ
             NULL olan satırları işler → doğal olarak idempotent (ikinci
             çağrıda işlenecek satır kalmaz).
          3) Yeni sorgulanabilir alanlar için indeksler.
        """
        assert self._db is not None
        existing_cols: set[str] = set()
        try:
            rows = self._db.execute("PRAGMA table_info(spare_questions)").fetchall()
            existing_cols = {r[1] for r in rows}
        except Exception as exc:  # noqa: BLE001 — okunamazsa migrasyonu atla
            logger.warning("Havuz şeması okunamadı (PRAGMA table_info): %s", exc)
            return

        for col, coltype in self._SCHEMA_MIGRATIONS:
            if col in existing_cols:
                continue
            try:
                self._db.execute(
                    f"ALTER TABLE spare_questions ADD COLUMN {col} {coltype}"
                )
            except Exception as exc:  # noqa: BLE001 — idempotent: kolon zaten olabilir
                logger.debug("Havuz kolonu eklenemedi/zaten var (%s): %s", col, exc)
        try:
            self._db.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Havuz şema migrasyonu commit edilemedi: %s", exc)

        # Tek seferlik backfill: question_id'si olmayan eski satırları doldur.
        try:
            stale = self._db.execute(
                "SELECT id, norm_question FROM spare_questions WHERE question_id IS NULL"
            ).fetchall()
            if stale:
                for row_id, norm_q in stale:
                    try:
                        qid = hashlib.sha1((norm_q or "").encode("utf-8")).hexdigest()[:16]
                        self._db.execute(
                            "UPDATE spare_questions SET question_id = ? WHERE id = ?",
                            (qid, row_id),
                        )
                    except Exception as exc:  # noqa: BLE001
                        logger.warning(
                            "question_id backfill atlandı (id=%s): %s", row_id, exc
                        )
                self._db.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("question_id backfill sorgusu başarısız: %s", exc)

        # Sorgulanabilir alanlar için indeksler (soru-bazlı kimlik + filtre alanları).
        try:
            self._db.execute(
                "CREATE INDEX IF NOT EXISTS idx_spare_question_id "
                "ON spare_questions(question_id)"
            )
            self._db.execute(
                "CREATE INDEX IF NOT EXISTS idx_spare_subject_grade_kazanim "
                "ON spare_questions(subject, grade, kazanim_kod)"
            )
            self._db.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Havuz yeni indeksleri oluşturulamadı: %s", exc)

    def add_many(
        self,
        key: str,
        questions: list[Question],
        *,
        subject: str | None = None,
        grade: int | None = None,
        unit_id: str | None = None,
        difficulty: str | None = None,
        source: str | None = None,
        critic_pass: int | None = None,
        critic_confidence: float | None = None,
        verifier_model: str | None = None,
    ) -> int:
        """Fazla soruları havuza yazar. Tekrarlar sessizce atlanır. Eklenen sayı döner.

        BEST-EFFORT: hiçbir koşulda istisna FIRLATMAZ. Havuz bir optimizasyondur;
        prod'da Turso'ya yazar ve mixed modda 3 bucket paralel koşar — bir DB
        hatası üretimi düşürmemeli (bucket'ın `except Exception`'ı hazır soruları
        çöpe atardı).

        Yeni parametreler (Faz 1, §3d) hepsi OPSİYONEL — mevcut çağrılar
        (`add_many(key, questions)`) hiçbir davranış değişikliği olmadan çalışır.
        `subject`/`grade`/`unit_id`/`difficulty` çağrı-bazlı (bir batch'in tamamı
        için ortak); `kazanim_kod`/`question_type` her `Question`'ın kendi
        alanından okunur (bir batch farklı kazanımlar içerebilir).
        `critic_pass`/`verifier_model` — "bedava damga" (§3c): bu sorular ZATEN
        critic'ten geçtiyse (ör. teslim edilen sorular) burada damgalanır, aksi
        halde NULL kalır (Faz 2'de ilk servis anında tembel damgalanacak).

        FAZ 2 NOTU (denetim 2026-07-28): `INSERT OR IGNORE` — havuzdan çekilip
        `_apply_post_filters`'tan GEÇEREK tekrar buraya yazılan bir soru
        (`(pool_key, norm_question)` UNIQUE index'e çarpar) sessizce YOK
        SAYILIR; satırın mevcut damgası (ör. NULL) GÜNCELLENMEZ. Yani havuz
        kökenli bir satır bir kez damgasız girdiyse damgasız kalabilir. Faz 2'nin
        tembel damgası bunu bir `UPDATE ... SET critic_pass=... WHERE
        pool_key=? AND norm_question=?` ile ayrıca yazmalı — `INSERT OR IGNORE`
        buna yetmez.
        """
        if not questions:
            return 0
        from app.services.diversity import normalize_question

        now = time.time()
        verified_at = now if critic_pass is not None else None
        added = 0
        try:
            with self._lock:
                assert self._db is not None
                for q in questions:
                    try:
                        norm_q = normalize_question(q.question)
                        question_id = hashlib.sha1(
                            norm_q.encode("utf-8")
                        ).hexdigest()[:16]
                        q_type = getattr(q, "question_type", None)
                        self._db.execute(
                            "INSERT OR IGNORE INTO spare_questions "
                            "(pool_key, norm_question, question_json, used_count, "
                            "created_at, question_id, subject, grade, unit_id, "
                            "kazanim_kod, question_type, difficulty, critic_pass, "
                            "critic_confidence, verified_at, verifier_model, source) "
                            "VALUES (?,?,?,0,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            (
                                key,
                                norm_q,
                                json.dumps(q.model_dump(mode="json"), ensure_ascii=False),
                                now,
                                question_id,
                                subject,
                                grade,
                                unit_id,
                                getattr(q, "kazanim_kod", None),
                                getattr(q_type, "value", q_type),
                                difficulty,
                                critic_pass,
                                critic_confidence,
                                verified_at,
                                verifier_model,
                                source,
                            ),
                        )
                        added += 1
                    except Exception as exc:  # noqa: BLE001 — havuz üretimi bozmasın
                        logger.warning("Havuz satır yazımı atlandı: %s", exc)
                # Trim (MUST-FIX, Opus denetimi 2026-07-28): ESKİDEN `used_count ASC`
                # ile sıralanıyordu — yani EN AZ kullanılan tutulur, EN ÇOK
                # kullanılan silinirdi. Faz 1'de zararsızdı (havuz yalnız yedekti,
                # used_count neredeyse artmıyordu). Faz 2'de servis used_count'u
                # artırıyor → politika TERSİNE dönüyordu: en çok servis edilen
                # (== en çok damgalanıp bedava hâle gelen, `critic_pass=1`) satırlar
                # SİLİNİYOR, yerine damgasız (`critic_pass IS NULL`, her serviste
                # yine critic ödeyecek) yeni satırlar tutuluyordu — ödediğimiz
                # damga bir sonraki trim'de çöpe gidiyordu, "depo isabetinin
                # marjinal maliyeti ~0" hedefi hiç gerçekleşmiyordu.
                # FIX: `used_count` DEĞER sinyali değil bir adalet/çeşitlilik
                # sinyalidir (`_select_rows`'ta hâlâ kullanılır) — trim'in KORUMA
                # sıralamasında YOK. Önce damgalı (`critic_pass=1`, bedava envanter)
                # korunur, sonra en YENİ damgasız (`critic_pass IS NULL`, henüz
                # denetlenmemiş ama potansiyel), en ÖNCE silinenler `critic_pass=0`
                # (critic'in reddettiği — bir "mezar taşı", tekrar üretilirse
                # `add_many`'nin INSERT OR IGNORE'u zaten bir daha eklemez/damgasını
                # bozmaz, silinmesi bilgi kaybı değil).
                self._db.execute(
                    """
                    DELETE FROM spare_questions
                    WHERE pool_key = ?
                      AND id NOT IN (
                        SELECT id FROM spare_questions
                        WHERE pool_key = ?
                        ORDER BY
                          CASE WHEN critic_pass = 1 THEN 0
                               WHEN critic_pass IS NULL THEN 1
                               ELSE 2 END ASC,
                          created_at DESC
                        LIMIT ?
                      )
                    """,
                    (key, key, self._max_per_key),
                )
                self._db.commit()
        except Exception as exc:  # noqa: BLE001 — trim/commit/lock hatası da yutulur
            logger.warning("Havuz yazımı başarısız (yutuldu): %s", exc)
            return added
        self._stored += added
        logger.info("Havuz PUT: %s (+%d soru, source=%s)", key, added, source)
        return added

    def _select_rows(
        self,
        key: str,
        count: int,
        exclude_norms: Iterable[str],
        question_type: str | None = None,
    ) -> list[tuple[int, str, str, int | None]]:
        """Ortak satır seçimi — `take()` ve `take_for_serving()` bunu paylaşır.

        Faz 2 (§3c, docs/COST_QUALITY_V2_PLAN.md):
          - WHERE `critic_pass IS NULL OR critic_pass = 1` → REDDEDİLMİŞ
            (`critic_pass = 0`) satırlar asla dönmez; bir kez critic reddettiyse
            o soru bir daha hiçbir isteğe servis edilmez.
          - ORDER BY önce `critic_pass = 1` (bedava, zaten damgalı), sonra NULL
            (denetlenecek) — bedava (LLM'siz) sorular ÖNCE tükensin diye.
            İkincil sıralama eskisiyle AYNI: `used_count ASC` (az kullanılan
            öncelenir) + `created_at DESC` (tekrarlarda çeşitlilik). NOT: bu
            `used_count` kullanımı yalnız BURADA (adalet/çeşitlilik sinyali —
            "hep aynı ilk soru gelmesin") — `add_many`'nin trim'inde ARTIK
            kullanılmıyor (bkz. add_many, Opus denetimi MUST-FIX).
          - `question_type` verilirse (Faz 2 SHOULD-FIX — tip-farkında pool-first,
            `app/services/agent.py::generate()`) yalnız o tipten satırlar döner;
            None ise (varsayılan, eski davranış) tüm tipler.

        LIMIT (Küçük 2, Opus denetimi): eskiden `count + len(excl) + 20` idi —
        `exclude_norms` artık TAVANSIZ olabildiğinden (§3a, `seen_questions()`)
        ağır kullanıcıda `len(excl)` büyüyüp sorgu çok satır çekebilirdi. Dışlama
        zaten Python tarafında (`norm_q in excl`) yapıldığından SQL LIMIT'i
        `exclude_norms` büyüklüğüne bağlamaya gerek yok — `count`'a görece küçük
        sabit bir tavanla (`_max_per_key`'i aşmayacak şekilde) sınırlanır.

        Dönen tuple: (id, norm_question, question_json, critic_pass).
        BEST-EFFORT: DB hatasında boş liste döner, istisna fırlatmaz.
        """
        excl = set(exclude_norms)
        sql_limit = min(count * 4 + 50, self._max_per_key)
        params: list = [key]
        type_clause = ""
        if question_type is not None:
            type_clause = " AND question_type = ?"
            params.append(question_type)
        params.append(sql_limit)
        try:
            with self._lock:
                assert self._db is not None
                rows = self._db.execute(
                    "SELECT id, norm_question, question_json, critic_pass "
                    "FROM spare_questions "
                    "WHERE pool_key = ? AND (critic_pass IS NULL OR critic_pass = 1)"
                    f"{type_clause} "
                    "ORDER BY CASE WHEN critic_pass = 1 THEN 0 ELSE 1 END ASC, "
                    "used_count ASC, created_at DESC LIMIT ?",
                    params,
                ).fetchall()
        except Exception as exc:  # noqa: BLE001 — BEST-EFFORT (bkz. add_many)
            logger.warning("Havuz okuması başarısız (yutuldu): %s", exc)
            return []
        picked: list[tuple[int, str, str, int | None]] = []
        for row_id, norm_q, payload, critic_pass in rows:
            if len(picked) >= count:
                break
            if norm_q in excl:
                continue
            picked.append((row_id, norm_q, payload, critic_pass))
        return picked

    def _bump_used_count(self, row_ids: list[int]) -> None:
        """`take()`/`take_for_serving()` ortak sayaç güncellemesi — kritik değil,
        hata BEST-EFFORT yutulur (bkz. add_many docstring)."""
        if not row_ids:
            return
        try:
            with self._lock:
                assert self._db is not None
                self._db.execute(
                    "UPDATE spare_questions SET used_count = used_count + 1 "
                    f"WHERE id IN ({','.join('?' * len(row_ids))})",
                    row_ids,
                )
                self._db.commit()
        except Exception as exc:  # noqa: BLE001 — sayaç güncellemesi kritik değil
            logger.warning("Havuz used_count güncellenemedi (yutuldu): %s", exc)
            return
        self._served += len(row_ids)

    def take(
        self,
        key: str,
        count: int,
        exclude_norms: Iterable[str] = (),
        question_type: str | None = None,
    ) -> list[Question]:
        """En az kullanılmış `count` soruyu döndürür (silmez, used_count++).

        Soru silinmez: farklı kullanıcılara tekrar servis edilmesi İSTENEN
        davranıştır (yeniden kullanım = maliyet düşüşü). Aynı kullanıcıya tekrar
        gitmesini `exclude_norms` (tenant history) engeller. `critic_pass = 0`
        (critic'in reddettiği) satırlar asla dönmez (bkz. `_select_rows`).
        `question_type` opsiyonel — verilirse yalnız o tipten soru döner (Faz 2
        SHOULD-FIX, tip-farkında pool-first).
        """
        if count <= 0:
            return []
        rows = self._select_rows(key, count, exclude_norms, question_type=question_type)
        picked: list[Question] = []
        picked_ids: list[int] = []
        for row_id, _norm_q, payload, _critic_pass in rows:
            try:
                picked.append(Question.model_validate(json.loads(payload)))
                picked_ids.append(row_id)
            except (json.JSONDecodeError, ValueError) as exc:
                logger.warning("Havuz satırı parse edilemedi: %s", exc)
        if picked_ids:
            self._bump_used_count(picked_ids)
            logger.info("Havuz HIT: %s (%d soru)", key, len(picked_ids))
        return picked

    def take_for_serving(
        self,
        key: str,
        count: int,
        exclude_norms: Iterable[str] = (),
        question_type: str | None = None,
    ) -> list[PoolItem]:
        """`take()` ile AYNI seçim/sıralama, ama her satırın `critic_pass` durumunu
        da döner (Faz 2, §3c — pool-first serving). Çağıran taraf (agent.py):

          - `critic_pass == 1` olanları filtrelerden geçirmeden doğrudan servis eder.
          - `critic_pass is None` olanları BİR KEZ math_verifier/critic'ten geçirir,
            sonucu `stamp()` ile bu satıra yazar.

        `question_type` opsiyonel — verilirse yalnız o tipten soru döner (Faz 2
        SHOULD-FIX, §3b: `agent.py` hedef tip dağılımına göre tip-bazlı çeker,
        aksi halde depo tipi tesadüfe bırakıp kağıdı tek tipe düşürebilirdi).

        `take()` gibi used_count'u artırır (aynı satır iki kez sayılmasın diye
        bir SONRAKİ çağrıda öne çıkmaz) — BEST-EFFORT, istisna fırlatmaz.
        """
        if count <= 0:
            return []
        rows = self._select_rows(key, count, exclude_norms, question_type=question_type)
        items: list[PoolItem] = []
        picked_ids: list[int] = []
        for row_id, _norm_q, payload, critic_pass in rows:
            try:
                q = Question.model_validate(json.loads(payload))
            except (json.JSONDecodeError, ValueError) as exc:
                logger.warning("Havuz satırı parse edilemedi: %s", exc)
                continue
            items.append(PoolItem(question=q, critic_pass=critic_pass))
            picked_ids.append(row_id)
        if picked_ids:
            self._bump_used_count(picked_ids)
            logger.info("Havuz HIT (serving): %s (%d soru)", key, len(picked_ids))
        return items

    def stamp(
        self,
        key: str,
        norm_questions: Iterable[str],
        *,
        critic_pass: int,
        critic_confidence: float | None = None,
        verifier_model: str | None = None,
    ) -> int:
        """Tembel damga (§3c) — `take_for_serving()` ile çekilip İLK KEZ (bu istekte)
        denetlenen satırları UPDATE eder.

        NEDEN AYRI BİR METOT: `add_many`'nin `INSERT OR IGNORE`'u zaten var olan
        bir satıra (aynı `pool_key` + `norm_question`) çarptığında satırı sessizce
        YOK SAYAR — mevcut damga (ör. NULL) GÜNCELLENMEZ (bkz. add_many docstring,
        "FAZ 2 NOTU"). Tembel damganın gerçekten işe yaraması için bu bir `UPDATE`
        olmalı.

        `critic_pass=1` → bir SONRAKİ `take()`/`take_for_serving()` bu satırı
        filtrelerden geçirmeden servis eder (marjinal maliyet ~0).
        `critic_pass=0` → satır `_select_rows`'un WHERE'inde daimi olarak elenir
        (bir daha ASLA servis edilmez — critic'in reddi kalıcıdır).

        FAIL-CLOSED SORUMLULUĞU ÇAĞIRANDA: bu metot kendisi "verdict gerçek mi
        fail-open mi" ayrımını YAPMAZ — çağıran (agent.py) yalnız critic GERÇEK
        bir verdict ürettiğinde bu metodu çağırmalı (critic fail-open olduysa
        hiç çağırmayıp satırı NULL bırakmalı). BEST-EFFORT: istisna fırlatmaz.
        """
        norms = list(dict.fromkeys(norm_questions))  # sırayı koru, tekrarları at
        if not norms:
            return 0
        now = time.time()
        try:
            with self._lock:
                assert self._db is not None
                placeholders = ",".join("?" * len(norms))
                self._db.execute(
                    "UPDATE spare_questions SET critic_pass = ?, "
                    "critic_confidence = ?, verified_at = ?, verifier_model = ? "
                    f"WHERE pool_key = ? AND norm_question IN ({placeholders})",
                    (critic_pass, critic_confidence, now, verifier_model, key, *norms),
                )
                self._db.commit()
        except Exception as exc:  # noqa: BLE001 — BEST-EFFORT (bkz. add_many)
            logger.warning("Havuz damgalama başarısız (yutuldu): %s", exc)
            return 0
        logger.info(
            "Havuz DAMGA: %s (%d soru, critic_pass=%s)", key, len(norms), critic_pass
        )
        return len(norms)

    def stats(self) -> dict[str, int]:
        with self._lock:
            assert self._db is not None
            total = self._db.execute("SELECT COUNT(*) FROM spare_questions").fetchone()[0]
            keys = self._db.execute(
                "SELECT COUNT(DISTINCT pool_key) FROM spare_questions"
            ).fetchone()[0]
        return {
            "served": self._served,
            "stored": self._stored,
            "total_entries": int(total),
            "distinct_keys": int(keys),
        }

    def clear(self) -> None:
        with self._lock:
            assert self._db is not None
            self._db.execute("DELETE FROM spare_questions")
            self._db.commit()
            self._served = 0
            self._stored = 0


SPARE_POOL = SpareQuestionPool(max_per_key=settings.spare_pool_max_per_key)
