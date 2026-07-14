"""Google Indexing API ile yarı-otomatik crawl/index bildirimi.

NE İŞE YARAR (dürüst çerçeve):
  Indexing API resmî olarak yalnız JobPosting/BroadcastEvent tiplerini destekler.
  Genel sayfalarda Google indekslemeyi görmezden gelebilir — AMA tipik olarak bir
  CRAWL tetikler. Bizim darboğazımız "unknown" (hiç taranmamış) sayfalar; API'nin en
  değerli olduğu yer burası (keşfi zorlar). "Crawled-not-indexed"de etkisi sınırlı
  (Google zaten gördü → asıl çözüm backlink/otorite). Bkz docs/SEO_INDEXING_PLAYBOOK.md.

ÖNCE KURULUM (bir kez, kullanıcı tarafı):
  1. GCP Console → proje gen-lang-client-0770878935 → "Indexing API"yi ETKİNLEŞTİR.
     https://console.cloud.google.com/apis/library/indexing.googleapis.com
  2. Search Console → soruatolyesi.com → Ayarlar → Kullanıcılar ve izinler →
     Kullanıcı ekle: metrics-reader@gen-lang-client-0770878935.iam.gserviceaccount.com
     rol = "Sahip" (Owner). Indexing API SADECE site sahiplerini kabul eder.
  (Kurulum eksikse script PERMISSION_DENIED / API not enabled hatası verir — normal.)

ÇALIŞTIRMA:
  # Ne gönderileceğini göster, GÖNDERME (önce bununla dene):
  PYTHONIOENCODING=utf-8 python scripts/seo_request_indexing.py --dry-run
  # Gerçek gönderim (varsayılan: unknown + crawled-not-indexed, en fazla 180/gün):
  PYTHONIOENCODING=utf-8 python scripts/seo_request_indexing.py
  # Sadece keşif (unknown) sayfaları, en fazla 50:
  PYTHONIOENCODING=utf-8 python scripts/seo_request_indexing.py --only-unknown --limit 50

Kota: Indexing API varsayılan 200 istek/gün. Script tavanı 180 (güvenlik payı).
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

from seo_index_status import (  # noqa: E402  (aynı klasör)
    KEY,
    SC_SITE,
    _svc,
    bucket_of,
    coverage,
    hub_urls,
    sitemap_urls,
)

DAILY_CAP = 180
INDEXING_SCOPE = "https://www.googleapis.com/auth/indexing"


def indexing_service():
    """Indexing servisi + OAuth token'ı HEMEN al.

    Arka plan koşumlarında oauth2.googleapis.com bazen yavaş sınıflandırmadan SONRA
    (ilk publish'te token alınırken) çözülemiyor. Token'ı burada, script başında
    (oauth2 erişilebilirken) zorla alıp cache'liyoruz; publish döngüsü onu kullanır.
    """
    import google.auth.transport.requests
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds = service_account.Credentials.from_service_account_file(
        KEY, scopes=[INDEXING_SCOPE]
    )
    creds.refresh(google.auth.transport.requests.Request())  # token'ı şimdi al
    return build("indexing", "v3", credentials=creds, cache_discovery=False)


def classify(urls: list[str]) -> dict[str, list[str]]:
    """Her URL'nin coverage kovasını çek (SC URL Inspection, readonly)."""
    svc = _svc()
    out: dict[str, list[str]] = {"UNKNOWN": [], "CRAWLED_NOT_INDEXED": [], "INDEXED": [], "OTHER": []}
    for u in urls:
        try:
            out[bucket_of(coverage(svc, u))].append(u)
        except Exception:  # noqa: BLE001
            out["OTHER"].append(u)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="gönderme, sadece listeyi göster")
    ap.add_argument("--only-unknown", action="store_true", help="sadece 'unknown' (keşif) sayfaları")
    ap.add_argument("--hubs", action="store_true", help="aday havuzu = head-term hub'lar (yoksa sitemap)")
    ap.add_argument("--limit", type=int, default=DAILY_CAP, help=f"en fazla N URL (tavan {DAILY_CAP})")
    args = ap.parse_args()

    if not Path(KEY).exists():
        print(f"HATA: service account anahtarı yok: {KEY}")
        return 1
    limit = min(args.limit, DAILY_CAP)

    # Indexing token'ını ÖNCE al (yavaş sınıflandırmadan evvel — arka plan DNS fix).
    svc = None
    if not args.dry_run:
        svc = indexing_service()
        print("Indexing API token alındı.")

    pool = hub_urls() if args.hubs else sitemap_urls()
    print(f"{len(pool)} aday coverage için inceleniyor (SC URL Inspection)...")
    buckets = classify(pool)
    wanted = list(buckets["UNKNOWN"])
    if not args.only_unknown:
        wanted += buckets["CRAWLED_NOT_INDEXED"]
    targets = wanted[:limit]

    print(f"\nHedef: {len(targets)} URL "
          f"(unknown {len(buckets['UNKNOWN'])}, "
          f"crawled-not-indexed {len(buckets['CRAWLED_NOT_INDEXED'])}, "
          f"indexed {len(buckets['INDEXED'])} atlandı)")
    if args.dry_run:
        print("\n[DRY-RUN] Gönderilecek URL'ler:")
        for u in targets:
            print(f"  {u}")
        print("\nGerçek gönderim için --dry-run olmadan çalıştır.")
        return 0

    ok = err = 0
    for i, url in enumerate(targets, 1):
        try:
            svc.urlNotifications().publish(
                body={"url": url, "type": "URL_UPDATED"}
            ).execute()
            ok += 1
            print(f"  [{i}/{len(targets)}] OK   {url}")
        except Exception as exc:  # noqa: BLE001
            err += 1
            print(f"  [{i}/{len(targets)}] HATA {type(exc).__name__}: {str(exc)[:120]}")
            if "PERMISSION_DENIED" in str(exc) or "has not been used" in str(exc) or "disabled" in str(exc):
                print("\n[!] Kurulum eksik görünüyor. Docstring'deki 2 adımı yap:\n"
                      "    (1) Indexing API'yi GCP'de etkinleştir\n"
                      "    (2) service account'u SC'de 'Sahip' olarak ekle")
                break
        time.sleep(0.2)  # nazik ol
    print(f"\nBitti: {ok} gönderildi, {err} hata.")
    return 0 if err == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
