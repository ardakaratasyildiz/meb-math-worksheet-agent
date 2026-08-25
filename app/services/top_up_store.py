"""Ek kağıt paketi (top-up) kredi defteri — abonelik üstü tüketilebilir kağıt hakkı.

MONETIZATION_PLAN §2 (2026-07-24): abone aylık kotayı bitirince ay-sonunu beklemeden
ek kağıt paketi satın alır (+25 / +75). Tüketilebilir IAP (RevenueCat consumable),
**30 günlük** kullanım süresi. Abonelik kotası aylık sıfırlanır; ek paket kendi süresi
içinde geçerli. Tüketim sırası (entitlements): önce abonelik kotası, sonra ek kredi —
"en erken biten önce" (israfı önle) → bu store `consume()`'da expires_at ASC uygular.

Aile: krediler HAVUZ SAHİBİNE (ödeyen veli) eklenir; aile aynı krediyi paylaşır
(entitlements _billing_owner sahibi belirler → balance/consume owner üzerinde).

Thread-safe (Lock + db_connection), history.sqlite3 paylaşımlı. Singleton: TOP_UP_STORE.
Best-effort: sayım/tüketim hatası üretimi bozmaz (fail-open → 0).
"""
from __future__ import annotations

import logging
import threading
import time
import uuid
from pathlib import Path

from app.config import settings
from app.services.db_connection import connect as db_connect

logger = logging.getLogger(__name__)


class TopUpStore:
    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path or settings.history_db_path
        self._lock = threading.Lock()
        self._db = None
        self._init_db()

    def _init_db(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db = db_connect(self._db_path)
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS top_up_credits (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                amount INTEGER NOT NULL,
                remaining INTEGER NOT NULL,
                purchased_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                provider_ref TEXT
            )
            """
        )
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_topup_tenant "
            "ON top_up_credits(tenant_id, expires_at)"
        )
        self._db.commit()

    def add(
        self,
        tenant_id: str,
        amount: int,
        *,
        days: int | None = None,
        provider_ref: str | None = None,
    ) -> bool:
        """Tenant'a `amount` kağıtlık ek kredi ekler (30g — settings.topup_expiry_days).

        provider_ref: RevenueCat transaction id → idempotency (aynı işlem iki kez
        gelirse tekrar eklemez). Best-effort; başarı bool döner.
        """
        if not tenant_id or amount <= 0:
            return False
        days = days if days is not None else settings.topup_expiry_days
        now = time.time()
        try:
            with self._lock:
                assert self._db is not None
                if provider_ref:  # idempotency — aynı satın alma tekrar teslim edilirse atla
                    dup = self._db.execute(
                        "SELECT 1 FROM top_up_credits WHERE provider_ref = ?",
                        (provider_ref,),
                    ).fetchone()
                    if dup:
                        return False
                self._db.execute(
                    "INSERT INTO top_up_credits "
                    "(id, tenant_id, amount, remaining, purchased_at, expires_at, provider_ref) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (uuid.uuid4().hex, tenant_id, int(amount), int(amount),
                     now, now + days * 86400, provider_ref),
                )
                self._db.commit()
            return True
        except Exception as exc:  # noqa: BLE001 — kredi ekleme akışı bozmasın
            logger.warning("top_up add başarısız (yutuldu): %s", exc)
            return False

    def balance(self, tenant_id: str, now: float | None = None) -> int:
        """Süresi geçmemiş toplam kalan ek-kredi (kağıt). Fail-open → 0."""
        if not tenant_id:
            return 0
        now = now if now is not None else time.time()
        try:
            with self._lock:
                assert self._db is not None
                row = self._db.execute(
                    "SELECT COALESCE(SUM(remaining),0) FROM top_up_credits "
                    "WHERE tenant_id=? AND expires_at>? AND remaining>0",
                    (tenant_id, now),
                ).fetchone()
            return int(row[0] or 0)
        except Exception as exc:  # noqa: BLE001
            logger.warning("top_up balance başarısız (yutuldu): %s", exc)
            return 0

    def consume(self, tenant_id: str, n: int = 1, now: float | None = None) -> int:
        """`n` kağıtlık krediyi EN ERKEN BİTEN paketten başlayarak düşer (israfı önle).
        Gerçekte düşülen miktarı döner (yetersizse < n). Best-effort → 0.
        """
        if not tenant_id or n <= 0:
            return 0
        now = now if now is not None else time.time()
        consumed = 0
        try:
            with self._lock:
                assert self._db is not None
                rows = self._db.execute(
                    "SELECT id, remaining FROM top_up_credits "
                    "WHERE tenant_id=? AND expires_at>? AND remaining>0 "
                    "ORDER BY expires_at ASC",
                    (tenant_id, now),
                ).fetchall()
                for cid, rem in rows:
                    if consumed >= n:
                        break
                    take = min(int(rem), n - consumed)
                    self._db.execute(
                        "UPDATE top_up_credits SET remaining = remaining - ? WHERE id = ?",
                        (take, cid),
                    )
                    consumed += take
                self._db.commit()
        except Exception as exc:  # noqa: BLE001 — tüketim üretimi bozmasın
            logger.warning("top_up consume başarısız (yutuldu): %s", exc)
        return consumed


    def refund(self, tenant_id: str, n: int = 1, now: float | None = None) -> int:
        """`consume()` ile düşülen `n` kağıtlık krediyi GERİ VERİR. İade edileni döner.

        NEDEN (2026-08-24 denetimi): kredi üretimden ÖNCE düşülüyor
        (`entitlements.enforce_quota`), üretim 502 verdiğinde ise geri verilmiyordu →
        ödeyen kullanıcı almadığı kağıdın kredisini kaybediyordu. Plan kotasında bu
        durum düşünülmüştü (`usage_ledger` status='failed' satırları saymaz), ek
        pakette düşünülmemişti.

        Kredi HAVADAN YARATILMAZ: her satır `amount`'unu aşamaz (cap). İade
        `consume()` ile AYNI sırada (expires_at ASC) yapılır → "en erken biten önce
        kullanılır" politikası korunur ve iade edilen kredi yine ilk harcanacak
        olandır. Süresi GEÇMİŞ pakete iade edilmez (zaten kullanılamaz).
        Best-effort: hata akışı bozmaz.
        """
        if not tenant_id or n <= 0:
            return 0
        now = now if now is not None else time.time()
        refunded = 0
        try:
            with self._lock:
                assert self._db is not None
                rows = self._db.execute(
                    "SELECT id, amount, remaining FROM top_up_credits "
                    "WHERE tenant_id=? AND expires_at>? AND remaining < amount "
                    "ORDER BY expires_at ASC",
                    (tenant_id, now),
                ).fetchall()
                for cid, amount, rem in rows:
                    if refunded >= n:
                        break
                    give = min(int(amount) - int(rem), n - refunded)
                    if give <= 0:
                        continue
                    self._db.execute(
                        "UPDATE top_up_credits SET remaining = remaining + ? WHERE id = ?",
                        (give, cid),
                    )
                    refunded += give
                self._db.commit()
        except Exception as exc:  # noqa: BLE001 — iade akışı bozmasın
            logger.warning("top_up refund başarısız (yutuldu): %s", exc)
        if refunded:
            logger.info(
                "Ek paket kredisi iade edildi (teslim edilmeyen üretim): tenant=%s n=%d",
                tenant_id, refunded,
            )
        return refunded


TOP_UP_STORE = TopUpStore()
