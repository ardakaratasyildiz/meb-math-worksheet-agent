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

# Kayıt durumu. 'failed' = PARA HARCANDI ama kağıt teslim EDİLMEDİ.
# ÖLÇÜLDÜ (2026-07-29): defter yalnız BAŞARI yolunda yazıldığı için faturanın
# %25-40'ı hiçbir yere düşmüyordu — 26 Tem'de ₺22,5, 28 Tem'de ₺10,9. Canlıda
# birebir görüldü: 23,6 sn süren, tam bedeli ödenmiş bir 502 defterde YOK.
STATUS_OK = "ok"
STATUS_FAILED = "failed"


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
                created_at REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'ok'
            )
            """
        )
        self._migrate_schema()
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_ul_created ON usage_ledger(created_at DESC)"
        )
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_ul_tenant ON usage_ledger(tenant_id, created_at DESC)"
        )
        self._db.commit()

    def _migrate_schema(self) -> None:
        """`status` kolonunu mevcut tablolara ekler — idempotent, BEST-EFFORT.

        Migrasyon öncesi satırların hepsi başarılı üretimdir (defter yalnız başarı
        yolunda yazılıyordu) → DEFAULT 'ok' doğru geçmişi verir.
        """
        assert self._db is not None
        try:
            cols = {r[1] for r in self._db.execute("PRAGMA table_info(usage_ledger)")}
        except Exception as exc:  # noqa: BLE001 — okunamazsa migrasyonu atla
            logger.warning("Defter şeması okunamadı: %s", exc)
            return
        if "status" in cols:
            return
        try:
            self._db.execute(
                "ALTER TABLE usage_ledger ADD COLUMN status TEXT NOT NULL DEFAULT 'ok'"
            )
        except Exception as exc:  # noqa: BLE001 — idempotent: kolon zaten olabilir
            logger.debug("Defter `status` kolonu eklenemedi/zaten var: %s", exc)

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
        status: str = STATUS_OK,
    ) -> None:
        """Bir üretimin maliyetini kaydeder. Anonim → tenant_id='anon'. Best-effort.

        status: 'ok' → teslim edilen kağıt · 'failed' → PARA HARCANDI ama kağıt
            teslim EDİLMEDİ (üretim çöktü / sonuç boş geldi / istek düştü).
            'failed' satırlar KOTADAN SAYILMAZ (bkz. questions_used_since,
            worksheets_used_since) — kullanıcı almadığı kağıdın kotasını ödemez.
        """
        try:
            with self._lock:
                self._db.execute(
                    "INSERT INTO usage_ledger (id, tenant_id, model, prompt_tokens, "
                    "completion_tokens, cost_usd, grade, topic, question_count, cache_hit, "
                    "created_at, status) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
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
                        status if status in (STATUS_OK, STATUS_FAILED) else STATUS_OK,
                    ),
                )
                self._db.commit()
        except Exception as exc:  # noqa: BLE001 — maliyet kaydı üretimi bozmasın
            logger.warning("usage_ledger kayıt başarısız (yutuldu): %s", exc)

    def questions_used_since(self, tenant_id: str | None, since_ts: float) -> int:
        """Bir tenant'ın `since_ts`'ten beri ürettiği soru sayısı (cache-hit HARİÇ).

        Kota enforcement için (entitlements.check_quota). Cache-hit üretimler kotadan
        düşmez (fiyat sayfasındaki söz). Anonim (tenant yok) → 0. Fail-open: hata
        halinde 0 döner (üretimi bloklamaz).

        `status='failed'` satırlar da SAYILMAZ: kullanıcı teslim edilmeyen kağıdın
        kotasını ödemez (maliyeti biz üstleniriz, görünürlük için deftere yazılır).
        """
        if not tenant_id:
            return 0
        try:
            with self._lock:
                row = self._db.execute(
                    "SELECT COALESCE(SUM(question_count),0) FROM usage_ledger "
                    "WHERE tenant_id=? AND cache_hit=0 AND status=? AND created_at>=?",
                    (tenant_id, STATUS_OK, since_ts),
                ).fetchone()
            return int(row[0] or 0)
        except Exception as exc:  # noqa: BLE001 — kota sayımı üretimi bozmasın
            logger.warning("usage_ledger kota sayımı başarısız (yutuldu): %s", exc)
            return 0

    def worksheets_used_since(self, tenant_ids, since_ts: float) -> int:
        """Bir/birden çok tenant'ın `since_ts`'ten beri ürettiği ÇALIŞMA KAĞIDI sayısı
        (cache-hit HARİÇ). Kota birimi = kağıt (soru değil): her generate() bir satır =
        bir kağıt. **Aile paylaşımlı havuzu** için tenant LİSTESİ alır (veli + bağlı
        çocuklar TEK havuzdan çeker). Tek tenant str de kabul eder. Fail-open → 0.

        `status='failed'` satırlar SAYILMAZ — teslim edilmeyen kağıt kotadan düşmez.

        `question_count=0` satırlar da SAYILMAZ. ÖLÇÜLDÜ (2026-07-29): quiz
        "yeniden üret" akışı (`quizzes.py::_record_gen_cost(question_count=0)`)
        maliyeti kaydetmek için satır atıyor ve koddaki yorum "kotayı şişirmez"
        diyor — ama o yorum kota SORU bazlıyken doğruydu. Kota KAĞIT bazlıya
        (COUNT(*)) geçtiğinde bu satırlar sessizce tam bir kağıt yemeye başladı.
        Teslim edilen kağıt her zaman ≥1 soru taşır → eşik güvenli.
        """
        if isinstance(tenant_ids, str):
            tenant_ids = [tenant_ids]
        ids = [t for t in (tenant_ids or []) if t]
        if not ids:
            return 0
        try:
            placeholders = ",".join("?" * len(ids))
            with self._lock:
                row = self._db.execute(
                    f"SELECT COUNT(*) FROM usage_ledger "
                    f"WHERE tenant_id IN ({placeholders}) AND cache_hit=0 "
                    f"AND status=? AND question_count>0 AND created_at>=?",
                    (*ids, STATUS_OK, since_ts),
                ).fetchone()
            return int(row[0] or 0)
        except Exception as exc:  # noqa: BLE001 — kağıt sayımı üretimi bozmasın
            logger.warning("usage_ledger kağıt sayımı başarısız (yutuldu): %s", exc)
            return 0

    def recent(self, limit: int = 100, since_ts: float | None = None) -> list[dict]:
        """Son N üretim — HER SATIR ayrı (agregasyon değil): kağıt-bazında maliyet
        detayı. "Hangi üretim (sınıf/konu) hangi modelle ne kadar harcadı" için.

        Not: karışık-zorluk kağıtta buckets farklı model kullanabilir; `model` alanı
        birincil (ilk) bucket'ı gösterir, `cost_usd` ise TÜM bucket'ların toplamıdır.
        """
        limit = max(1, min(500, limit))
        where = ""
        params: list = []
        if since_ts is not None:
            where = "WHERE created_at >= ?"
            params.append(since_ts)
        params.append(limit)
        try:
            with self._lock:
                rows = self._db.execute(
                    f"SELECT id, tenant_id, model, prompt_tokens, completion_tokens, "
                    f"cost_usd, grade, topic, question_count, cache_hit, created_at, status "
                    f"FROM usage_ledger {where} ORDER BY created_at DESC LIMIT ?",
                    tuple(params),
                ).fetchall()
        except Exception as exc:  # noqa: BLE001
            logger.warning("usage_ledger recent başarısız: %s", exc)
            return []
        return [
            {
                "id": r[0],
                "tenant_id": r[1],
                "model": r[2],
                "prompt_tokens": int(r[3] or 0),
                "completion_tokens": int(r[4] or 0),
                "cost_usd": round(float(r[5] or 0.0), 6),
                "grade": r[6],
                "topic": r[7],
                "question_count": int(r[8] or 0),
                "cache_hit": bool(r[9]),
                "created_at": r[10],
                "status": r[11] or STATUS_OK,
            }
            for r in rows
        ]

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
                    f"COALESCE(SUM(completion_tokens),0), COALESCE(SUM(cache_hit),0), "
                    # Teslim edilmemiş (boşa giden) harcama AYRI gösterilir: toplam
                    # maliyete dahildir ama "kaç kağıt ürettik" sayımına DEĞİL.
                    f"COALESCE(SUM(CASE WHEN status='{STATUS_FAILED}' THEN cost_usd END),0), "
                    f"COALESCE(SUM(CASE WHEN status='{STATUS_FAILED}' THEN 1 END),0) "
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

        cnt, cost, pt, ct, ch, failed_cost, failed_cnt = total_row
        return {
            "total": {
                "generations": int(cnt or 0),
                "cost_usd": round(float(cost or 0.0), 6),
                "prompt_tokens": int(pt or 0),
                "completion_tokens": int(ct or 0),
                "cache_hits": int(ch or 0),
                # Boşa giden harcama: para ödendi, kağıt teslim edilmedi.
                "failed_generations": int(failed_cnt or 0),
                "failed_cost_usd": round(float(failed_cost or 0.0), 6),
                "delivered_generations": int(cnt or 0) - int(failed_cnt or 0),
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
