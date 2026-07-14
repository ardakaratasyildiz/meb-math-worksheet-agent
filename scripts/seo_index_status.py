"""SEO index-coverage takibi — Search Console URL Inspection API.

north-star = organik oturum/hafta. Bunu kıpırdatan tek şey sayfaların GERÇEKTEN
indekslenmesi. Bu script sitemap'teki (veya verilen) URL'lerin coverage durumunu
çeker ve 3 kovaya böler, böylece Request-Indexing + backlink çabasının işe yarayıp
yaramadığını haftalık ölçebiliriz:

  INDEXED               → "Submitted and indexed" (iş bitti)
  CRAWLED_NOT_INDEXED   → tarandı, indekslenmedi (otorite eşiği → backlink + nudge)
  UNKNOWN               → hiç taranmadı (keşif → iç link + Request Indexing)

Kurulum (bir kez):
  pip install google-api-python-client google-auth
Çalıştırma (tüm sitemap — YAVAŞ, URL Inspection ~1-2 sn/URL, günlük ~2000 kota):
  PYTHONIOENCODING=utf-8 python scripts/seo_index_status.py
Sadece head-term + hub'lar (hızlı, önerilen düzenli kontrol):
  PYTHONIOENCODING=utf-8 python scripts/seo_index_status.py --hubs
Belirli sayı kadar örnekle:
  PYTHONIOENCODING=utf-8 python scripts/seo_index_status.py --limit 40

Yapılandırma (env, opsiyonel):
  GA_SA_PATH  (vars: secrets/ga-sa.json)
  SC_SITE     (vars: sc-domain:soruatolyesi.com)
  SITE_URL    (vars: https://soruatolyesi.com)
"""
from __future__ import annotations

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parent.parent
KEY = os.environ.get("GA_SA_PATH", str(ROOT / "secrets" / "ga-sa.json"))
SC_SITE = os.environ.get("SC_SITE", "sc-domain:soruatolyesi.com")
SITE_URL = os.environ.get("SITE_URL", "https://soruatolyesi.com")


def _svc():
    from googleapiclient.discovery import build
    from google.oauth2 import service_account

    creds = service_account.Credentials.from_service_account_file(
        KEY, scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
    )
    return build("searchconsole", "v1", credentials=creds, cache_discovery=False)


def hub_urls() -> list[str]:
    """Head-term hub'lar — en yüksek arama değeri, düzenli izlenmeli."""
    urls = [f"{SITE_URL}/", f"{SITE_URL}/calismalar", f"{SITE_URL}/lgs-matematik"]
    urls += [f"{SITE_URL}/{g}-sinif-matematik" for g in range(1, 8)]
    return urls


def sitemap_urls(limit: int | None = None) -> list[str]:
    """Canlı sitemap.xml'den URL'leri çek (sunucudan; kod codegen'e bağımlı değil)."""
    import urllib.request

    req = urllib.request.Request(f"{SITE_URL}/sitemap.xml", headers={"User-Agent": "seo-index-status"})
    with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310
        xml = r.read().decode("utf-8")
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [loc.text.strip() for loc in ET.fromstring(xml).findall(".//sm:loc", ns) if loc.text]
    return urls[:limit] if limit else urls


def coverage(svc, url: str) -> str:
    res = (
        svc.urlInspection()
        .index()
        .inspect(body={"inspectionUrl": url, "siteUrl": SC_SITE})
        .execute()
    )
    return (
        res.get("inspectionResult", {})
        .get("indexStatusResult", {})
        .get("coverageState", "?")
    )


def bucket_of(cov: str) -> str:
    low = cov.lower()
    if "unknown" in low:
        return "UNKNOWN"
    if "not indexed" in low:
        return "CRAWLED_NOT_INDEXED"
    if "indexed" in low:
        return "INDEXED"
    return "OTHER"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hubs", action="store_true", help="sadece head-term hub'ları incele")
    ap.add_argument("--limit", type=int, default=None, help="sitemap'ten en fazla N URL")
    args = ap.parse_args()

    if not Path(KEY).exists():
        print(f"HATA: service account anahtarı yok: {KEY}")
        return 1

    urls = hub_urls() if args.hubs else sitemap_urls(args.limit)
    print(f"SC site: {SC_SITE} · {len(urls)} URL inceleniyor "
          f"({'hub' if args.hubs else 'sitemap'})...\n")

    svc = _svc()
    buckets: dict[str, list[tuple[str, str]]] = {
        "INDEXED": [], "CRAWLED_NOT_INDEXED": [], "UNKNOWN": [], "OTHER": []
    }
    for url in urls:
        try:
            cov = coverage(svc, url)
        except Exception as exc:  # noqa: BLE001
            cov = f"ERR {type(exc).__name__}"
        buckets[bucket_of(cov)].append((url, cov))

    total = len(urls)
    idx = len(buckets["INDEXED"])
    print("=" * 64)
    print(f"ÖZET: {idx}/{total} indeksli "
          f"({100*idx/total:.0f}%) · "
          f"{len(buckets['CRAWLED_NOT_INDEXED'])} crawled-not-indexed · "
          f"{len(buckets['UNKNOWN'])} unknown")
    print("=" * 64)
    # En değerli önce: crawled-not-indexed (nudge'a yakın) → unknown (keşif) → indexed
    for b in ["CRAWLED_NOT_INDEXED", "UNKNOWN", "OTHER", "INDEXED"]:
        rows = buckets[b]
        if not rows:
            continue
        print(f"\n### {b} ({len(rows)})")
        for url, cov in rows:
            print(f"  {url}   [{cov}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
