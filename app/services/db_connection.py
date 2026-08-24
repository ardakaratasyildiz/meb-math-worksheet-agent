"""SQLite veya Turso (libSQL) bağlantı fabrikası.

Env-var driven:
    TURSO_DATABASE_URL set → Turso embedded replica modu (lokal SQLite cache +
        her commit'te otomatik remote sync). Restart'a dayanıklı.
    Değilse → klasik sqlite3 bağlantısı (lokal dev).

Kullanım: `from app.services.db_connection import connect`
yerine `sqlite3.connect(path, check_same_thread=False)` koyulur.
Cevap olarak gelen connection object sqlite3.Connection ile API-uyumlu —
mevcut execute/commit/fetchall çağrıları aynen çalışır.

BAYAT OTURUM (Hrana stream) DAYANIKLILIĞI — 2026-08-24 canlı arıza
------------------------------------------------------------------
Prod'da giriş yapmış kullanıcılar bir noktadan sonra HİÇ soru üretemez oldu; log:

    File "app/services/billing_store.py", line 122, in get
      row = self._db.execute("SELECT ... FROM subscriptions WHERE tenant_id = ?")
    File "app/services/db_connection.py", line 40, in execute
      return self._conn.execute(*args, **kwargs)
    ValueError: Hrana: `api error: `status=404 Not Found,
                body={"error":"stream not found: 37caba41:3062c21"}``

Hrana, libSQL'in HTTP protokolü; sunucu tarafında her bağlantı bir "stream"
(oturum) tutar ve bir süre sessiz kalan stream'i ÇÖPE ATAR. İstemci elindeki
baton'la o stream'i tekrar kullanmaya çalışınca 404 "stream not found" gelir.

Kritik nokta: bağlantı nesneleri modül seviyesinde TEKİL ve süresiz yaşıyor
(BILLING_STORE, QUIZ_STORE, USAGE_LEDGER, WORKSHEET_HISTORY, SPARE_POOL...).
Stream bir kez öldüğünde o bağlantı bir daha ASLA kendine gelmiyor → process
yeniden başlayana kadar HER istek 500. Kullanıcının tarifi birebir buydu:
"normalde çalışıyordu, sonradan bozuldu". Anonim istekler bu depolara
girmediği (ya da hataları yuttukları) için çalışmaya devam ediyordu; hata da
bu yüzden "mobil bozuk" gibi görünüyordu.

Çözüm: bayat-oturum hatası TANINIR, bağlantı YENİDEN KURULUR ve işlem BİR KEZ
tekrarlanır (`_SyncOnCommit._run`). Tekrar güvenli: 404 stream düzeyindedir,
yani ifade sunucuya hiç ulaşmamıştır (yarım yazma yok). Aynı anda birçok
thread aynı bayat bağlantıya çarpabileceği için yenileme bir kilit + nesil
(generation) sayacıyla korunur — yalnız ilk gelen yeniler, diğerleri onun
kurduğu bağlantıyı kullanır.
"""
from __future__ import annotations

import logging
import os
import sqlite3
import threading

logger = logging.getLogger(__name__)


def is_turso_enabled() -> bool:
    return bool(os.environ.get("TURSO_DATABASE_URL", "").strip())


# Bayat oturum imzaları — Hrana/libSQL sunucu tarafı oturumu düşürdüğünde gelir.
# Sadece BUNLARDA yeniden bağlanılır; gerçek SQL hataları (syntax, constraint)
# aynen yukarı fırlar, yoksa hatalı sorgu iki kez koşar ve teşhis kaybolur.
_STALE_SESSION_MARKERS = (
    "stream not found",
    "stream expired",
    "stream is closed",
    "invalid baton",
    "baton not found",
)


def _is_stale_session(exc: BaseException) -> bool:
    msg = str(exc).lower()
    if any(m in msg for m in _STALE_SESSION_MARKERS):
        return True
    # Hrana katmanından gelen 404/409: oturum/baton kaybı (mesaj metni sürümle
    # değişebiliyor, bu yüzden ikinci bir ağ daha atılıyor).
    return "hrana" in msg and ("404" in msg or "409" in msg)


class _SyncOnCommit:
    """libsql Connection wrapper — commit() sonrası otomatik sync + bayat oturum onarımı.

    Reads lokal replica'dan (hızlı). Writes önce lokale, commit sonrası
    Turso'ya push edilir. Sync hatası uygulamayı durdurmaz, log yazar.
    Bayat Hrana oturumunda bağlantı yenilenip işlem bir kez tekrarlanır
    (bkz. modül docstring'i).
    """

    def __init__(self, conn, factory=None) -> None:
        self._conn = conn
        self._factory = factory  # None → yenileme yapılamaz (eski davranış)
        self._lock = threading.Lock()
        self._generation = 0

    def __getattr__(self, name):
        return getattr(self._conn, name)

    # ── Bayat oturum onarımı ────────────────────────────────────────────────
    def _reconnect(self, seen_generation: int) -> bool:
        """Bağlantıyı yeniler. Başka bir thread zaten yenilediyse hiçbir şey yapmaz."""
        if self._factory is None:
            return False
        with self._lock:
            if seen_generation != self._generation:
                return True  # yarışı başkası kazandı, yeni bağlantı hazır
            try:
                new_conn = self._factory()
            except Exception as exc:  # noqa: BLE001 — yenileme başarısız
                logger.error("Turso bağlantısı yenilenemedi: %s", exc)
                return False
            old_conn, self._conn = self._conn, new_conn
            self._generation += 1
            try:
                old_conn.close()
            except Exception as exc:  # noqa: BLE001 — ölü bağlantı, kapanmasa da olur
                logger.debug("Bayat bağlantı kapatılamadı (yutuldu): %s", exc)
            logger.warning(
                "Turso bağlantısı yenilendi (bayat Hrana oturumu, nesil=%d).",
                self._generation,
            )
            return True

    def _run(self, op, *args, **kwargs):
        """`op(conn, *args)` — bayat oturumda bağlantıyı yenileyip BİR KEZ tekrarlar."""
        seen = self._generation
        try:
            return op(self._conn, *args, **kwargs)
        except Exception as exc:  # noqa: BLE001 — bayat mı, gerçek hata mı?
            if not _is_stale_session(exc):
                raise
            logger.warning("Turso oturumu bayatlamış (%s) — yenilenip tekrar deneniyor.", exc)
            if not self._reconnect(seen):
                raise
            return op(self._conn, *args, **kwargs)

    # ── sqlite3.Connection uyumlu yüz ───────────────────────────────────────
    def execute(self, *args, **kwargs):
        return self._run(lambda c, *a, **k: c.execute(*a, **k), *args, **kwargs)

    def commit(self) -> None:
        self._run(lambda c: c.commit())
        try:
            self._run(lambda c: c.sync())
        except Exception as exc:  # noqa: BLE001
            logger.warning("Turso sync başarısız (commit sonrası): %s", exc)

    def close(self) -> None:
        try:
            self._run(lambda c: c.sync())
        except Exception as exc:  # noqa: BLE001
            logger.warning("Turso final sync başarısız (close): %s", exc)
        self._conn.close()


def connect(local_path: str):
    """Lokal SQLite path'i alır, ortama göre uygun connection döner."""
    if is_turso_enabled():
        url = os.environ["TURSO_DATABASE_URL"].strip()
        token = os.environ.get("TURSO_AUTH_TOKEN", "").strip()
        try:
            import libsql_experimental as libsql  # type: ignore

            def _new_raw_conn(initial: bool = False):
                """Ham libsql bağlantısı + best-effort sync (yenilemede de kullanılır)."""
                conn = libsql.connect(local_path, sync_url=url, auth_token=token)
                try:
                    conn.sync()
                    if initial:
                        logger.info(
                            "Turso bağlantısı kuruldu, initial sync OK (local=%s)",
                            local_path,
                        )
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Sync başarısız (replica boş/eski başlar): %s", exc
                    )
                return conn

            # factory = bayat oturumda yeniden kurulum yolu (bkz. _SyncOnCommit).
            return _SyncOnCommit(_new_raw_conn(initial=True), factory=_new_raw_conn)
        except ImportError:
            logger.warning(
                "libsql-experimental kurulu değil — TURSO_* env'leri set ama "
                "paket yok. Lokal SQLite'a düşülüyor."
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Turso bağlantısı kurulamadı, lokal SQLite fallback: %s", exc
            )

    return sqlite3.connect(local_path, check_same_thread=False)
