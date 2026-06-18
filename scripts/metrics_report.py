"""North-star metrik raporu — GA4 Data API + Search Console (ops/GA4 otomasyonu).

Konsola tıklamadan, service account ile metrikleri çeker:
  GA4   → aktif kullanıcı (7g/28g), kanal bazlı oturum (organik), kilit event'ler
          (cta_generate_click, generate_page_view, quiz_share_create/open/attempt/signup)
  SC    → son 28g tıklama/gösterim + 8. sınıf (/calismalar/8-sinif*) sayfalarının durumu

Kurulum (bir kez):
  pip install google-analytics-data google-api-python-client google-auth
Çalıştırma:
  PYTHONIOENCODING=utf-8 python scripts/metrics_report.py

Yapılandırma (env, hepsi opsiyonel — varsayılanlar gömülü):
  GA_SA_PATH   (vars: secrets/ga-sa.json)
  GA4_PROPERTY (vars: 538957291)
  SC_SITE      (vars: sc-domain:soruatolyesi.com)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parent.parent
KEY = os.environ.get("GA_SA_PATH", str(ROOT / "secrets" / "ga-sa.json"))
GA4_PROPERTY = os.environ.get("GA4_PROPERTY", "538957291")
SC_SITE = os.environ.get("SC_SITE", "sc-domain:soruatolyesi.com")

# İzlediğimiz kilit funnel event'leri — koddaki gerçek track() adlarıyla eşleşir
# (frontend grep ile doğrulandı, 2026-06-18).
KEY_EVENTS = [
    # Üretim funnel'ı
    "cta_generate_click",
    "generate_page_view",
    "worksheet_generate_start",
    "worksheet_generate_success",
    "worksheet_generate_error",
    "pdf_download",
    "download_signup_gate",
    "question_regenerate",
    # Paylaşım (viral) funnel'ı
    "quiz_share_create",
    "quiz_share_open",
    "quiz_share_attempt",
    "quiz_share_signup",
]


def _hr(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def ga4_report() -> None:
    _hr("GA4 — Aktif kullanıcı + kanal + event'ler")
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        DateRange,
        Dimension,
        Metric,
        RunReportRequest,
    )
    from google.oauth2 import service_account

    creds = service_account.Credentials.from_service_account_file(
        KEY, scopes=["https://www.googleapis.com/auth/analytics.readonly"]
    )
    client = BetaAnalyticsDataClient(credentials=creds)
    prop = f"properties/{GA4_PROPERTY}"

    # 1) Aktif kullanıcı + oturum (7 ve 28 gün)
    # Çoklu date-range verilince GA4 otomatik bir 'dateRange' dimension'ı ekler;
    # onu DIMENSIONS'a yazmıyoruz (API hata verir), satırlarda hazır gelir.
    r = client.run_report(
        RunReportRequest(
            property=prop,
            date_ranges=[
                DateRange(start_date="7daysAgo", end_date="today", name="7g"),
                DateRange(start_date="28daysAgo", end_date="today", name="28g"),
            ],
            metrics=[Metric(name="activeUsers"), Metric(name="sessions")],
        )
    )
    print("Aktif kullanıcı / oturum:")
    for row in r.rows:
        rng = row.dimension_values[0].value if row.dimension_values else "?"
        au = row.metric_values[0].value
        se = row.metric_values[1].value
        print(f"  {rng:4} → aktif kullanıcı: {au:>6}  | oturum: {se:>6}")

    # 2) Kanal bazlı oturum (organik trafik) — son 28g
    r2 = client.run_report(
        RunReportRequest(
            property=prop,
            date_ranges=[DateRange(start_date="28daysAgo", end_date="today")],
            dimensions=[Dimension(name="sessionDefaultChannelGroup")],
            metrics=[Metric(name="sessions")],
        )
    )
    print("\nKanal bazlı oturum (28g):")
    for row in sorted(r2.rows, key=lambda x: -int(x.metric_values[0].value or 0)):
        print(f"  {row.dimension_values[0].value:24} {row.metric_values[0].value:>6}")

    # 3) Kilit funnel event'leri — son 28g
    r3 = client.run_report(
        RunReportRequest(
            property=prop,
            date_ranges=[DateRange(start_date="28daysAgo", end_date="today")],
            dimensions=[Dimension(name="eventName")],
            metrics=[Metric(name="eventCount")],
        )
    )
    counts = {row.dimension_values[0].value: row.metric_values[0].value for row in r3.rows}
    print("\nKilit funnel event'leri (28g):")
    for ev in KEY_EVENTS:
        print(f"  {ev:24} {counts.get(ev, '0'):>6}")


def sc_report() -> None:
    _hr("Search Console — tıklama/gösterim + 8. sınıf sayfaları")
    from googleapiclient.discovery import build
    from google.oauth2 import service_account

    creds = service_account.Credentials.from_service_account_file(
        KEY, scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
    )
    svc = build("searchconsole", "v1", credentials=creds, cache_discovery=False)

    # Sayfa bazlı son 28g performans
    resp = (
        svc.searchanalytics()
        .query(
            siteUrl=SC_SITE,
            body={
                "startDate": _days_ago(28),
                "endDate": _days_ago(1),
                "dimensions": ["page"],
                "rowLimit": 1000,
            },
        )
        .execute()
    )
    rows = resp.get("rows", [])
    total_clicks = sum(r.get("clicks", 0) for r in rows)
    total_impr = sum(r.get("impressions", 0) for r in rows)
    g8 = [r for r in rows if "/calismalar/8-sinif" in r["keys"][0]]
    g8_clicks = sum(r.get("clicks", 0) for r in g8)
    g8_impr = sum(r.get("impressions", 0) for r in g8)

    print(f"TÜM property (28g): tıklama {total_clicks} · gösterim {total_impr} · "
          f"performans gösteren sayfa {len(rows)}")
    print(f"8. SINIF (/calismalar/8-sinif*): {len(g8)} sayfa görünür · "
          f"tıklama {g8_clicks} · gösterim {g8_impr}")
    if g8:
        print("  En çok gösterim alan 8. sınıf sayfaları:")
        for r in sorted(g8, key=lambda x: -x.get("impressions", 0))[:8]:
            print(f"    {r.get('impressions',0):>5} gösterim · {r.get('clicks',0):>3} tık · {r['keys'][0]}")
    else:
        print("  (Henüz 8. sınıf sayfaları aramada görünmüyor — yeni; indekslenme sürebilir.)")


def _days_ago(n: int) -> str:
    # GA4 'NdaysAgo' kullanır; SC ISO tarih ister. time-bağımsız değil ama rapor anlık.
    import datetime as _dt

    return (_dt.date.today() - _dt.timedelta(days=n)).isoformat()


def main() -> int:
    if not Path(KEY).exists():
        print(f"HATA: service account anahtarı yok: {KEY}")
        return 1
    print(f"Anahtar: {KEY}\nGA4 property: {GA4_PROPERTY}\nSC site: {SC_SITE}")
    ok = True
    for fn in (ga4_report, sc_report):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            ok = False
            print(f"\n[!] {fn.__name__} başarısız: {type(exc).__name__}: {exc}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
