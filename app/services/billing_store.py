"""Abonelik durumu deposu (source of truth) — billing (iyzico) ön koşulu.

docs/IYZICO_ENTEGRASYON_PLANI.md §4. İki tablo:
  - subscriptions: tenant başına abonelik durumu (kaynak-of-truth; webhook + callback
    ile senkronlanır). `entitlements` yalnız buna bakar, client bayrağına asla.
  - billing_events: webhook idempotency + audit (iyzico retry'larına dayanıklılık).

Model (MONETIZATION_PLAN §2, 2026-07-16): free (satırsız) · trial (trialing) ·
pro · pro-plus (active/past_due). SQLite/Turso (`history.sqlite3` ile aynı dosya;
diğer store'larla aynı desen — Turso set ise otomatik kalıcı replica).

iyzico entegrasyonu HENÜZ yok; bu depo saf DB primitifleridir (checkout/webhook
sonraki PR'da bu API'yi kullanır). Tüm zamanlar ISO-8601 UTC string.
"""
from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.services.db_connection import connect as db_connect

logger = logging.getLogger(__name__)

# Abonelik durumları (iyzico + trial akışı)
STATUS_TRIALING = "trialing"
STATUS_ACTIVE = "active"
STATUS_PAST_DUE = "past_due"   # ödeme başarısız — dunning grace (period_end'e kadar erişim)
STATUS_CANCELED = "canceled"
STATUS_EXPIRED = "expired"

# Bir aboneliğin hâlâ erişim VERDİĞİ durumlar (period_end/trial_end kontrolüyle birlikte)
_ENTITLING_STATUSES = {STATUS_TRIALING, STATUS_ACTIVE, STATUS_PAST_DUE}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        # naive → UTC varsay (eski/dış kayıt toleransı)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


class BillingStore:
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
            CREATE TABLE IF NOT EXISTS subscriptions (
                tenant_id            TEXT PRIMARY KEY,
                plan_code            TEXT NOT NULL,
                status               TEXT NOT NULL,
                provider             TEXT NOT NULL DEFAULT 'iyzico',
                provider_ref         TEXT,
                customer_ref         TEXT,
                trial_end            TEXT,
                current_period_end   TEXT,
                cancel_at_period_end INTEGER DEFAULT 0,
                created_at           TEXT NOT NULL,
                updated_at           TEXT NOT NULL
            )
            """
        )
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS billing_events (
                event_id     TEXT PRIMARY KEY,
                event_type   TEXT NOT NULL,
                tenant_id    TEXT,
                payload_json TEXT NOT NULL,
                received_at  TEXT NOT NULL,
                processed    INTEGER DEFAULT 0
            )
            """
        )
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_sub_status ON subscriptions(status)"
        )
        self._db.commit()

    # ── Subscriptions ────────────────────────────────────────────────────────

    @staticmethod
    def _row_to_dict(row) -> dict | None:
        if row is None:
            return None
        cols = (
            "tenant_id", "plan_code", "status", "provider", "provider_ref",
            "customer_ref", "trial_end", "current_period_end",
            "cancel_at_period_end", "created_at", "updated_at",
        )
        d = dict(zip(cols, row))
        d["cancel_at_period_end"] = bool(d["cancel_at_period_end"])
        return d

    def get(self, tenant_id: str) -> dict | None:
        """Ham abonelik satırı (durumdan bağımsız). Yoksa None."""
        if not tenant_id:
            return None
        with self._lock:
            row = self._db.execute(
                "SELECT tenant_id, plan_code, status, provider, provider_ref, "
                "customer_ref, trial_end, current_period_end, cancel_at_period_end, "
                "created_at, updated_at FROM subscriptions WHERE tenant_id = ?",
                (tenant_id,),
            ).fetchone()
        return self._row_to_dict(row)

    def get_active(self, tenant_id: str) -> dict | None:
        """Erişim VEREN abonelik (aksi halde None) — entitlements'ın baktığı tek yer.

        - trialing: trial_end > now
        - active/past_due: current_period_end > now (past_due = dunning grace)
        Süresi geçmiş/iptal/expired → None.
        """
        sub = self.get(tenant_id)
        if sub is None or sub["status"] not in _ENTITLING_STATUSES:
            return None
        now = _now()
        if sub["status"] == STATUS_TRIALING:
            end = _parse_iso(sub.get("trial_end"))
            return sub if (end and end > now) else None
        end = _parse_iso(sub.get("current_period_end"))
        return sub if (end and end > now) else None

    def upsert(
        self,
        *,
        tenant_id: str,
        plan_code: str,
        status: str,
        provider: str = "iyzico",
        provider_ref: str | None = None,
        customer_ref: str | None = None,
        trial_end: str | None = None,
        current_period_end: str | None = None,
        cancel_at_period_end: bool = False,
    ) -> dict:
        """Abonelik satırını ekle/güncelle (tenant_id PK). created_at korunur."""
        now = _now_iso()
        with self._lock:
            existing = self._db.execute(
                "SELECT created_at FROM subscriptions WHERE tenant_id = ?",
                (tenant_id,),
            ).fetchone()
            created_at = existing[0] if existing else now
            self._db.execute(
                """
                INSERT INTO subscriptions (
                    tenant_id, plan_code, status, provider, provider_ref, customer_ref,
                    trial_end, current_period_end, cancel_at_period_end, created_at, updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(tenant_id) DO UPDATE SET
                    plan_code=excluded.plan_code,
                    status=excluded.status,
                    provider=excluded.provider,
                    provider_ref=excluded.provider_ref,
                    customer_ref=excluded.customer_ref,
                    trial_end=excluded.trial_end,
                    current_period_end=excluded.current_period_end,
                    cancel_at_period_end=excluded.cancel_at_period_end,
                    updated_at=excluded.updated_at
                """,
                (
                    tenant_id, plan_code, status, provider, provider_ref, customer_ref,
                    trial_end, current_period_end, 1 if cancel_at_period_end else 0,
                    created_at, now,
                ),
            )
            self._db.commit()
        return self.get(tenant_id)  # type: ignore[return-value]

    def start_trial(self, tenant_id: str, *, days: int | None = None) -> dict | None:
        """İlk giriş/onboarding'te 7g kartsız reverse trial başlatır (iyzico çağrısı YOK).

        Zaten bir satır varsa (trial kullanılmış / aktif abone) DOKUNMAZ → None döner.
        """
        if self.get(tenant_id) is not None:
            return None
        from datetime import timedelta

        d = days if days is not None else settings.trial_days
        trial_end = (_now() + timedelta(days=d)).isoformat()
        return self.upsert(
            tenant_id=tenant_id,
            plan_code="trial",
            status=STATUS_TRIALING,
            trial_end=trial_end,
        )

    def set_cancel_at_period_end(self, tenant_id: str, value: bool = True) -> None:
        """Dönem sonu iptal işaretle (erişim period_end'e kadar sürer)."""
        with self._lock:
            self._db.execute(
                "UPDATE subscriptions SET cancel_at_period_end=?, updated_at=? "
                "WHERE tenant_id=?",
                (1 if value else 0, _now_iso(), tenant_id),
            )
            self._db.commit()

    # ── Billing events (webhook idempotency + audit) ─────────────────────────

    def record_event(
        self,
        *,
        event_id: str,
        event_type: str,
        payload: dict | str,
        tenant_id: str | None = None,
    ) -> bool:
        """Webhook olayını kaydeder. Daha önce işlendiyse (event_id PK) False → no-op.

        True = yeni olay (işlenmeli); False = tekrar (idempotent atla). iyzico retry
        güvenliği: aynı event_id iki kez gelirse ikinci INSERT çakışır → False.
        """
        payload_json = payload if isinstance(payload, str) else json.dumps(
            payload, ensure_ascii=False
        )
        try:
            with self._lock:
                self._db.execute(
                    "INSERT INTO billing_events (event_id, event_type, tenant_id, "
                    "payload_json, received_at, processed) VALUES (?,?,?,?,?,0)",
                    (event_id, event_type, tenant_id, payload_json, _now_iso()),
                )
                self._db.commit()
            return True
        except Exception as exc:  # noqa: BLE001 — UNIQUE çakışması = tekrar (beklenen)
            logger.info("billing_event tekrar/atlandı (%s): %s", event_id, exc)
            return False

    def mark_event_processed(self, event_id: str) -> None:
        with self._lock:
            self._db.execute(
                "UPDATE billing_events SET processed=1 WHERE event_id=?",
                (event_id,),
            )
            self._db.commit()

    def is_event_processed(self, event_id: str) -> bool:
        with self._lock:
            row = self._db.execute(
                "SELECT processed FROM billing_events WHERE event_id=?",
                (event_id,),
            ).fetchone()
        return bool(row and row[0])


BILLING_STORE = BillingStore()
