"""Generation cache durumu — özet rapor.

Çalıştırma:
    PYTHONIOENCODING=utf-8 python scripts/cache_report.py

Çıktı:
    - Toplam cached set sayısı
    - Distinct cache key sayısı
    - Process içi hit/miss sayaçları (ayrı süreçte 0 görünür — sadece aynı
      Python process'inde anlamlı)
    - En çok set'e sahip top 10 key (sıcak noktalar)
    - En eski / en yeni set zaman damgaları
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from app.services.llm_cache import GENERATION_CACHE  # noqa: E402


def main() -> None:
    db_path = settings.history_db_path
    if not Path(db_path).exists():
        print(f"DB yok: {db_path}")
        sys.exit(0)

    conn = sqlite3.connect(db_path)
    try:
        # Tablo var mı?
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='generation_cache'"
        ).fetchone()
        if row is None:
            print("generation_cache tablosu henüz oluşmadı. Cache hiç kullanılmamış.")
            sys.exit(0)

        total = conn.execute(
            "SELECT COUNT(*) FROM generation_cache"
        ).fetchone()[0]
        distinct = conn.execute(
            "SELECT COUNT(DISTINCT cache_key) FROM generation_cache"
        ).fetchone()[0]
        oldest, newest = conn.execute(
            "SELECT MIN(created_at), MAX(created_at) FROM generation_cache"
        ).fetchone()

        print("=== Generation Cache Raporu ===")
        print(f"DB: {db_path}")
        print(f"Toplam cached set:    {total}")
        print(f"Distinct cache key:   {distinct}")
        if oldest is not None and newest is not None:
            o = datetime.fromtimestamp(oldest, tz=timezone.utc).isoformat()
            n = datetime.fromtimestamp(newest, tz=timezone.utc).isoformat()
            print(f"En eski set:          {o}")
            print(f"En yeni set:          {n}")
        stats = GENERATION_CACHE.stats()
        print(f"Process hit/miss:     {stats['hits']} / {stats['misses']}")

        if total > 0:
            print("\nTop 10 sıcak key (en çok set'e sahip):")
            hot = conn.execute(
                "SELECT cache_key, COUNT(*) AS n FROM generation_cache "
                "GROUP BY cache_key ORDER BY n DESC LIMIT 10"
            ).fetchall()
            for k, n in hot:
                print(f"  {n:3d}  {k}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
