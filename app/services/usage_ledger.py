"""Gemini kullanım/maliyet defteri — HER üretim için bir satır (anonim dahil).

worksheet_history yalnızca giriş yapan kullanıcının kağıdını saklar; anonim
üretimlerin maliyeti hiçbir yerde tutulmuyordu. Bu defter üretim başına
gerçek Gemini maliyetini (üretim + retry + top-up + critic + embedding) kalıcı
kaydeder → "kim ne kadar harcadı" ve toplam fatura tahmini için kaynak.

SQLite/Turso (`history.sqlite3` ile aynı dosya). Singleton: `USAGE_LEDGER`.
Kayıt best-effort'tur: hata üretim akışını ASLA bozmaz (yutulur).
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

ANON_TENANT = "anon"


class UsageLedger:
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
            CREATE TABLE IF NOT EXISTS usage_ledger (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                model TEXT,
                prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0,
                cost_usd REAL DEFAULT 0,
                grade INTEGER,
                topic TEXT,
                question_count INTEGER DEFAULT 0,
                cache_hit INTEGER DEFAULT 0,
                created_at REAL NOT NULL
            )
            """
        )
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_ul_created ON usage_ledger(created_at DESC)"
        )
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_ul_tenant ON usage_ledger(tenant_id, created_at DESC)"
        )
        self._db.commit()

    def record(
        self,
        *,
        tenant_id: str | None,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
        grade: int | None = None,
        topic: str | None = None,
        question_count: int = 0,
        cache_hit: bool = False,
    ) -> None:
        """Bir üretimin maliyetini kaydeder. Anonim → tenant_id='anon'. Best-effort."""
        try:
            with self._lock:
                self._db.execute(
                    "INSERT INTO usage_ledger (id, tenant_id, model, prompt_tokens, "
                    "completion_tokens, cost_usd, grade, topic, question_count, cache_hit, created_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        uuid.uuid4().hex,
                        tenant_id or ANON_TENANT,
                        model or "unknown",
                        int(prompt_tokens or 0),
                        int(completion_tokens or 0),
                        float(cost_usd or 0.0),
                        grade,
                        topic,
                        int(question_count or 0),
                        1 if cache_hit else 0,
                        time.time(),
                    ),
                )
                self._db.commit()
        except Exception as exc:  # noqa: BLE001 — maliyet kaydı üretimi bozmasın
            logger.warning("usage_ledger kayıt başarısız (yutuldu): %s", exc)

    def summary(self, since_ts: float | None = None, until_ts: float | None = None) -> dict:
        """Dönem için agregasyon: toplam + tenant/model/gün kırılımı.

        since_ts/until_ts unix saniye (None → sınırsız).
        """
        where = "WHERE 1=1"
        params: list = []
        if since_ts is not None:
            where += " AND created_at >= ?"
            params.append(since_ts)
        if until_ts is not None:
            where += " AND created_at < ?"
            params.append(until_ts)
        try:
            with self._lock:
                total_row = self._db.execute(
                    f"SELECT COUNT(*), COALESCE(SUM(cost_usd),0), COALESCE(SUM(prompt_tokens),0), "
                    f"COALESCE(SUM(completion_tokens),0), COALESCE(SUM(cache_hit),0) "
                    f"FROM usage_ledger {where}",
                    tuple(params),
                ).fetchone()
                by_tenant = self._db.execute(
                    f"SELECT tenant_id, COUNT(*) AS n, COALESCE(SUM(cost_usd),0) AS c, "
                    f"COALESCE(SUM(prompt_tokens),0), COALESCE(SUM(completion_tokens),0) "
                    f"FROM usage_ledger {where} GROUP BY tenant_id ORDER BY c DESC LIMIT 200",
                    tuple(params),
                ).fetchall()
                by_model = self._db.execute(
                    f"SELECT model, COUNT(*) AS n, COALESCE(SUM(cost_usd),0) AS c "
                    f"FROM usage_ledger {where} GROUP BY model ORDER BY c DESC",
                    tuple(params),
                ).fetchall()
                by_day = self._db.execute(
                    f"SELECT date(created_at,'unixepoch') AS d, COUNT(*) AS n, "
                    f"COALESCE(SUM(cost_usd),0) AS c FROM usage_ledger {where} "
                    f"GROUP BY d ORDER BY d DESC LIMIT 60",
                    tuple(params),
                ).fetchall()
        except Exception as exc:  # noqa: BLE001
            logger.warning("usage_ledger özet başarısız: %s", exc)
            return {"total": {}, "by_tenant": [], "by_model": [], "by_day": []}

        cnt, cost, pt, ct, ch = total_row
        return {
            "total": {
                "generations": int(cnt or 0),
                "cost_usd": round(float(cost or 0.0), 6),
                "prompt_tokens": int(pt or 0),
                "completion_tokens": int(ct or 0),
                "cache_hits": int(ch or 0),
            },
            "by_tenant": [
                {
                    "tenant_id": t,
                    "generations": int(n),
                    "cost_usd": round(float(c), 6),
                    "prompt_tokens": int(p),
                    "completion_tokens": int(o),
                }
                for (t, n, c, p, o) in by_tenant
            ],
            "by_model": [
                {"model": m, "generations": int(n), "cost_usd": round(float(c), 6)}
                for (m, n, c) in by_model
            ],
            "by_day": [
                {"day": d, "generations": int(n), "cost_usd": round(float(c), 6)}
                for (d, n, c) in by_day
            ],
        }


USAGE_LEDGER = UsageLedger()
