"""Bayat Turso/Hrana oturumu — bağlantı yenilenir, işlem tekrarlanır.

Pytest gerektirmez — `python tests/test_turso_stale_stream.py`. Ağ çağrısı yok
(libsql taklit edilir).

CANLI ARIZA (2026-08-24): giriş yapmış kullanıcılar bir noktadan sonra HİÇ soru
üretemez oldu, her istek 500. Log:

    File "app/services/billing_store.py", line 122, in get
      row = self._db.execute("SELECT ... FROM subscriptions WHERE tenant_id = ?")
    ValueError: Hrana: `api error: `status=404 Not Found,
                body={"error":"stream not found: 37caba41:3062c21"}``

Hrana sunucusu sessiz kalan oturumu (stream) çöpe atıyor; bağlantı nesneleri
modül seviyesinde TEKİL ve süresiz yaşadığı için o bağlantı bir daha kendine
gelmiyordu → process restart'a kadar kalıcı 500. Kullanıcının tarifi birebir:
"normalde çalışıyordu, sonradan bozuldu".
"""
from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("GEMINI_API_KEY", "fake-key-for-tests")

from app.services.db_connection import (  # noqa: E402
    _is_stale_session,
    _SyncOnCommit,
)

_failures: list[str] = []

STALE_MSG = (
    'Hrana: `api error: `status=404 Not Found, '
    'body={"error":"stream not found: 37caba41:3062c21"}``'
)


def check(cond: bool, msg: str) -> None:
    if cond:
        print(f"  ok   {msg}")
    else:
        _failures.append(msg)
        print(f"  FAIL {msg}")


class _FakeConn:
    """Tek kullanımlık libsql taklidi. `stale=True` ise her çağrıda bayat hata verir."""

    def __init__(self, name: str, stale: bool = False) -> None:
        self.name = name
        self.stale = stale
        self.calls: list[str] = []
        self.closed = False

    def _maybe_boom(self, what: str) -> None:
        self.calls.append(what)
        if self.stale:
            raise ValueError(STALE_MSG)

    def execute(self, sql, *params):
        self._maybe_boom(f"execute:{sql}")
        return f"rows-from-{self.name}"

    def commit(self):
        self._maybe_boom("commit")

    def sync(self):
        self._maybe_boom("sync")

    def close(self):
        self.closed = True


def test_stale_detection() -> None:
    print("\n[1] bayat oturum imzası tanınıyor")
    check(_is_stale_session(ValueError(STALE_MSG)), "canlıdaki tam mesaj → bayat")
    check(_is_stale_session(RuntimeError("Hrana: stream expired")), "stream expired → bayat")
    check(
        not _is_stale_session(ValueError("no such column: plan_code")),
        "gerçek SQL hatası bayat SAYILMAZ (tekrar edilmez, teşhis kaybolmaz)",
    )
    check(
        not _is_stale_session(ValueError("UNIQUE constraint failed")),
        "constraint hatası bayat SAYILMAZ",
    )


def test_execute_recovers_after_stale_session() -> None:
    print("\n[2] bayat oturumda bağlantı yenilenir ve execute tekrarlanır")
    dead = _FakeConn("dead", stale=True)
    fresh = _FakeConn("fresh")
    wrapper = _SyncOnCommit(dead, factory=lambda: fresh)
    try:
        result = wrapper.execute("SELECT 1 FROM subscriptions WHERE tenant_id = ?", ("u",))
        check(result == "rows-from-fresh", "sorgu YENİ bağlantıda başarıyla koştu")
    except Exception as exc:  # noqa: BLE001
        check(False, f"execute hâlâ patlıyor: {type(exc).__name__}: {exc}")
    check(dead.closed, "ölü bağlantı kapatıldı")
    # İkinci çağrı doğrudan yeni bağlantıya gider (kalıcı onarım).
    fresh.calls.clear()
    wrapper.execute("SELECT 2")
    check(len(fresh.calls) == 1, "sonraki çağrılar doğrudan yeni bağlantıya gidiyor")


def test_real_sql_error_is_not_retried() -> None:
    print("\n[3] gerçek SQL hatası yukarı fırlar (iki kez koşmaz)")

    class _Boom(_FakeConn):
        def execute(self, sql, *params):
            self.calls.append(sql)
            raise ValueError("no such table: subscriptions")

    conn = _Boom("boom")
    calls_to_factory = []
    wrapper = _SyncOnCommit(conn, factory=lambda: calls_to_factory.append(1))
    try:
        wrapper.execute("SELECT 1")
        check(False, "hata yutuldu (olmamalı)")
    except ValueError as exc:
        check("no such table" in str(exc), "asıl hata korunmuş")
    check(len(conn.calls) == 1, "sorgu YALNIZ BİR KEZ koştu")
    check(not calls_to_factory, "yeniden bağlanma denenmedi")


def test_commit_recovers_and_still_syncs() -> None:
    print("\n[4] commit de onarılır; sync hatası akışı bozmaz")
    dead = _FakeConn("dead", stale=True)
    fresh = _FakeConn("fresh")
    wrapper = _SyncOnCommit(dead, factory=lambda: fresh)
    try:
        wrapper.commit()
        check(True, "commit bayat oturumdan sonra başarılı")
    except Exception as exc:  # noqa: BLE001
        check(False, f"commit patladı: {type(exc).__name__}: {exc}")
    check("commit" in fresh.calls and "sync" in fresh.calls, "commit + sync yeni bağlantıda")


def test_single_reconnect_under_concurrency() -> None:
    print("\n[5] paralel bucket'larda TEK yenileme olur (nesil sayacı)")
    dead = _FakeConn("dead", stale=True)
    created: list[_FakeConn] = []
    lock = threading.Lock()

    def factory():
        with lock:
            c = _FakeConn(f"fresh-{len(created)}")
            created.append(c)
            return c

    wrapper = _SyncOnCommit(dead, factory=factory)
    errors: list[str] = []

    def worker():
        try:
            wrapper.execute("SELECT 1")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{type(exc).__name__}: {exc}")

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    check(not errors, f"8 eşzamanlı sorgu da başarılı (hata: {errors[:1]})")
    check(len(created) == 1, f"yalnız 1 yeni bağlantı kuruldu (kurulan: {len(created)})")


def main() -> int:
    for fn in (
        test_stale_detection,
        test_execute_recovers_after_stale_session,
        test_real_sql_error_is_not_retried,
        test_commit_recovers_and_still_syncs,
        test_single_reconnect_under_concurrency,
    ):
        fn()
    print()
    if _failures:
        print(f"FAILED: {len(_failures)} assert düştü")
        return 1
    print("PASSED: bayat Hrana oturumu kendini onarıyor")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
