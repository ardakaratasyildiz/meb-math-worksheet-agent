"""Kalıcı görülmüş-set testleri (Soru deposu Faz 1, §3a — docs/COST_QUALITY_V2_PLAN.md).

Bulgu: `history.py` `seen_questions()` eskiden yalnız `deque(maxlen=capacity_per_key)`
penceresine bakıyordu. Veritabanı her soruyu saklıyor olsa da (kalıcı geçmiş), aynı
üniteden 3. kağıt üretildiğinde 1. kağıdın soruları pencereden düşmüş oluyor ve
"hiç görülmemiş" sayılıp TEKRAR servis edilebiliyordu.

Fix: `settings.history_seen_unbounded` (varsayılan True) açıkken `seen_questions()`
anahtar başına TÜM geçmişi (DB'den tembel yüklenmiş `set[str]`) döner. BUNUNLA
BİRLİKTE `context_exclusions()` ve `seen_embeddings()` BİLİNÇLİ OLARAK sınırlı
kalır — bunlar prompt'a giriyor (context_exclusions) ya da pairwise embedding
karşılaştırması yapıyor (seen_embeddings); tavansızlaştırmak maliyeti/CPU'yu
arttırırdı. Bu test dosyası bu ayrımın regresyona uğramamasını kilitler.
"""
import tempfile
from pathlib import Path

import pytest

from app.config import settings
from app.services.history import DEFAULT_TENANT, GenerationHistory

KEY = (DEFAULT_TENANT, 5, "dogal_sayilar", "MAT.5.1.1.1", "orta")

# Test hızlı olsun diye küçük bir pencere (gerçek varsayılan 30) — pencerenin
# ÖTESİNE geçmek için birkaç kayıt yeterli olsun.
CAPACITY = 5
OVER_CAPACITY = 12


@pytest.fixture()
def history():
    with tempfile.TemporaryDirectory() as d:
        h = GenerationHistory(
            capacity_per_key=CAPACITY,
            persist=True,
            db_path=str(Path(d) / "history.sqlite3"),
        )
        try:
            yield h
        finally:
            # Windows: tempdir silinebilsin diye SQLite bağlantısını kapat.
            if h._db is not None:
                h._db.close()


def _fill(h: GenerationHistory, n: int) -> None:
    for i in range(n):
        h.record(
            KEY,
            f"normalize edilmis soru metni <N> varyant {i}",
            [f"ctx{i}"],
            embedding=[float(i), float(i + 1), float(i + 2)],
        )


def test_seen_questions_unbounded_beyond_capacity(history, monkeypatch):
    """30 (burada CAPACITY=5)'dan fazla kayıt olunca `seen_questions` HEPSİNİ
    döndürmeli — deque penceresi (bugünkü/eski davranış) değil."""
    monkeypatch.setattr(settings, "history_seen_unbounded", True)
    _fill(history, OVER_CAPACITY)
    seen = history.seen_questions(KEY)
    assert len(seen) == OVER_CAPACITY, (
        "tavansız görülmüş-set TÜM geçmişi kapsamalı, yalnız pencereyi değil"
    )


def test_context_exclusions_still_bounded(history, monkeypatch):
    """context_exclusions PROMPT'a giriyor → sınırlı kalmalı (maliyet frenidir)."""
    monkeypatch.setattr(settings, "history_seen_unbounded", True)
    _fill(history, OVER_CAPACITY)
    ctx = history.context_exclusions(KEY, max_contexts=100)
    assert len(ctx) <= CAPACITY, (
        "context_exclusions tavansızlaşırsa prompt token'ı şişer — bu regresyondur"
    )


def test_seen_embeddings_still_bounded(history, monkeypatch):
    """seen_embeddings pairwise semantic dedup'ta kullanılıyor → sınırlı kalmalı."""
    monkeypatch.setattr(settings, "history_seen_unbounded", True)
    _fill(history, OVER_CAPACITY)
    embs = history.seen_embeddings(KEY)
    assert len(embs) <= CAPACITY, (
        "seen_embeddings tavansızlaşırsa RAM/CPU maliyeti patlar — bu regresyondur"
    )


def test_flag_false_restores_old_windowed_behavior(history, monkeypatch):
    """`history_seen_unbounded=False` → redeploy'suz geri alma: eski 30'luk (burada
    5'lik) pencere davranışına dönmeli."""
    monkeypatch.setattr(settings, "history_seen_unbounded", False)
    _fill(history, OVER_CAPACITY)
    seen = history.seen_questions(KEY)
    assert len(seen) == CAPACITY, "bayrak kapalıyken eski pencereli davranış geçerli olmalı"


class _RowCountingConn:
    """`execute()` çağrılarını gerçek bağlantıya yönlendirir, dönen satırın
    `fetchall()` boyutunu kaydeder.

    MUST-FIX 1 (denetim 2026-07-28) için: yalnız `len(deque)`'e bakmak YETMEZ —
    deque zaten `maxlen` ile kırpar, sorgunun KENDİSİNİN sınırlı veri çektiğini
    (ağdan/DB'den GERÇEKTEN kaç satır geldiğini) ölçmek gerekir.
    """

    def __init__(self, real):
        self._real = real
        self.last_fetch_row_count: int | None = None

    def execute(self, sql, params=()):
        cur = self._real.execute(sql, params)
        return _RowCountingCursor(cur, self)

    def commit(self) -> None:
        self._real.commit()


class _RowCountingCursor:
    def __init__(self, cur, parent: _RowCountingConn) -> None:
        self._cur = cur
        self._parent = parent

    def fetchall(self):
        rows = self._cur.fetchall()
        self._parent.last_fetch_row_count = len(rows)
        return rows

    def fetchone(self):
        return self._cur.fetchone()


def test_no_eager_load_and_bucket_query_is_row_bounded(monkeypatch):
    """MUST-FIX 1 (denetim 2026-07-28): eskiden `_load_from_db()` açılışta TÜM
    `history` tablosunu (bu anahtarın satır sayısından bağımsız, embedding
    BLOB'ları dahil) çekiyordu — tavansız modda tablo artık capacity'e
    kırpılmadığından bu, açılışı (Render cold-start) zamanla yavaşlatıp OOM
    riski doğururdu. Bu test İKİ şeyi ayrı ayrı doğrular:

      1) Yeni bir `GenerationHistory` örneği açılışta HİÇBİR anahtarı önceden
         yüklemez (`_cache` boş kalır) — eager yükleme tamamen kaldırıldı.
      2) Bir anahtara İLK erişimde DB'den GERÇEKTEN çekilen satır sayısı
         `capacity_per_key` ile sınırlı (sorgunun `fetchall()` sonucu sayılarak
         ölçülür), tablo o anahtar için 200 satır barındırsa bile.
    """
    monkeypatch.setattr(settings, "history_seen_unbounded", True)
    with tempfile.TemporaryDirectory() as d:
        db_path = str(Path(d) / "history.sqlite3")
        LOTS = 200
        h1 = GenerationHistory(capacity_per_key=CAPACITY, persist=True, db_path=db_path)
        _fill(h1, LOTS)
        if h1._db is not None:
            h1._db.close()

        h2 = GenerationHistory(capacity_per_key=CAPACITY, persist=True, db_path=db_path)
        try:
            # (1) Açılışta hiçbir anahtar önceden yüklenmemiş olmalı.
            assert h2._cache == {}, (
                "eager yükleme geri geldi — açılışta hiçbir sorgu atılmamalı"
            )

            # (2) Gerçek bağlantıyı satır-sayan bir sarmalayıcıyla değiştirip bu
            # anahtara İLK erişimi tetikle.
            counting = _RowCountingConn(h2._db)
            h2._db = counting
            ctx = h2.context_exclusions(KEY, max_contexts=1000)

            assert counting.last_fetch_row_count is not None
            assert counting.last_fetch_row_count <= CAPACITY, (
                f"DB'den çekilen satır sayısı ({counting.last_fetch_row_count}) "
                f"capacity_per_key'i ({CAPACITY}) aşıyor — sorgu artık tam "
                "tabloyu çekiyor, LIMIT kaybolmuş olabilir"
            )
            assert len(ctx) <= CAPACITY
        finally:
            # Sarmalayıcı yerine gerçek bağlantıyı kapat.
            real = getattr(h2._db, "_real", h2._db)
            if real is not None:
                real.close()


def test_lazy_load_from_db_survives_restart(monkeypatch):
    """Persist açıkken process yeniden başlasa (yeni GenerationHistory örneği,
    boş `_seen_sets` cache'i) bile tavansız set DB'den doğru yüklenmeli —
    yalnız süreç belleğine güvenmiyor."""
    monkeypatch.setattr(settings, "history_seen_unbounded", True)
    with tempfile.TemporaryDirectory() as d:
        db_path = str(Path(d) / "history.sqlite3")
        h1 = GenerationHistory(capacity_per_key=CAPACITY, persist=True, db_path=db_path)
        _fill(h1, OVER_CAPACITY)
        if h1._db is not None:
            h1._db.close()

        h2 = GenerationHistory(capacity_per_key=CAPACITY, persist=True, db_path=db_path)
        try:
            seen = h2.seen_questions(KEY)
            assert len(seen) == OVER_CAPACITY, "restart sonrası DB'den tembel yükleme çalışmalı"
        finally:
            if h2._db is not None:
                h2._db.close()


def test_seen_sets_evict_oldest_key_beyond_max_cached_keys(history, monkeypatch):
    """Küçük 3 (denetim 2026-07-28): `_seen_sets` anahtar başına process ömrü
    boyunca tutulur — kullanıcı×sınıf×ünite×kazanım×zorluk ile çarpıldığından
    uzun ömürlü süreçte tavansız büyürdü. `_MAX_CACHED_KEYS` aşılınca EN ESKİ
    anahtar (insertion-order) atılmalı, en yeniler kalmalı. Kayıp yok: atılan
    anahtar bir sonraki erişimde DB'den yeniden yüklenir (bkz. diğer testler)."""
    monkeypatch.setattr(type(history), "_MAX_CACHED_KEYS", 3)
    monkeypatch.setattr(settings, "history_seen_unbounded", True)

    keys = [
        (DEFAULT_TENANT, 5, f"unite{i}", "MAT.5.1.1.1", "orta") for i in range(5)
    ]
    for k in keys:
        history.record(k, "soru metni <N>", ["ctx"], embedding=None)

    assert len(history._seen_sets) <= 3, "tavan aşılmamalı"
    # En eski 2 anahtar (keys[0], keys[1]) atılmış olmalı; en yeni 3'ü kalmalı.
    assert keys[0] not in history._seen_sets
    assert keys[1] not in history._seen_sets
    assert keys[4] in history._seen_sets, "en yeni anahtar kalmalı"
    # Atılan anahtar hâlâ doğru cevaplıyor (DB'den yeniden yüklenir, kayıp yok).
    assert history.seen_questions(keys[0]) == {"soru metni <N>"}


def test_persist_false_disables_eviction_no_data_loss(monkeypatch):
    """2. denetim (2026-07-28) — MUST-FIX: `persist=False` iken bellek TEK
    kaynaktır; atılan anahtar DB'den yeniden yüklenemez → eski tahliye mantığı
    o kullanıcının daha önce gördüğü soruyu sessizce "hiç görülmemiş" sayardı
    (Faz 1'in düzelttiği regresyonun aynısı geri gelirdi). Bu durumda tahliye
    YAPILMAMALI: tavan aşılsa bile HİÇBİR anahtar atılmamalı, en eski anahtarın
    `seen_questions()`'ı hâlâ dolu olmalı."""
    monkeypatch.setattr(settings, "history_seen_unbounded", True)
    h = GenerationHistory(capacity_per_key=CAPACITY, persist=False)
    monkeypatch.setattr(type(h), "_MAX_CACHED_KEYS", 3)

    keys = [
        (DEFAULT_TENANT, 5, f"unite{i}", "MAT.5.1.1.1", "orta") for i in range(5)
    ]
    for k in keys:
        h.record(k, "soru metni <N>", ["ctx"], embedding=None)

    # Tavan (3) aşıldı (5 anahtar) ama persist kapalı → HİÇBİR anahtar atılmamalı.
    assert len(h._seen_sets) == 5, "persist kapalıyken tahliye YAPILMAMALI (veri kaybı)"
    for k in keys:
        assert k in h._seen_sets
    # En eski anahtarın verisi hâlâ tam — "daha önce görülen soru tekrar
    # görülmemiş sayılmadı" garantisi bozulmamış.
    assert h.seen_questions(keys[0]) == {"soru metni <N>"}

    # Bir kez uyarı basıldığını doğrula (sessiz kalmasın).
    assert h._evict_disabled_warned is True


def test_persist_true_eviction_still_works_after_fix(monkeypatch):
    """Regresyon kilidi: persist=True/DB var olan (normal) yolda tahliye hâlâ
    çalışmalı — bu fix yalnız persist=False dalını değiştirdi."""
    monkeypatch.setattr(settings, "history_seen_unbounded", True)
    with tempfile.TemporaryDirectory() as d:
        h = GenerationHistory(
            capacity_per_key=CAPACITY, persist=True,
            db_path=str(Path(d) / "history.sqlite3"),
        )
        monkeypatch.setattr(type(h), "_MAX_CACHED_KEYS", 3)
        try:
            keys = [
                (DEFAULT_TENANT, 5, f"unite{i}", "MAT.5.1.1.1", "orta")
                for i in range(5)
            ]
            for k in keys:
                h.record(k, "soru metni <N>", ["ctx"], embedding=None)

            assert len(h._seen_sets) <= 3, "persist açıkken tavan hâlâ uygulanmalı"
            assert keys[0] not in h._seen_sets
            assert h._evict_disabled_warned is False
        finally:
            if h._db is not None:
                h._db.close()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
