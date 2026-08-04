/**
 * Event yardımcısı — Google Tag Manager (GTM-P2QLKRKT) dataLayer'a yazar.
 *
 * Doğrudan GA4 kurulumu (eski components/Analytics.tsx + gtag) KALDIRILDI;
 * GA4 artık GTM container'ı üzerinden yönetiliyor. Buradaki her çağrı
 * dataLayer'a `{ event: "<isim>", ...params }` olarak düşer → GTM'de
 * "Custom Event" trigger'ı ile GA4 event tag'ine bağlanır.
 *
 * GTM script'i layout'ta senkron yüklendiği için dataLayer sayfa açılışında
 * hazır; yine de defansif olarak dizi yoksa oluşturulur (GTM daha sonra aynı
 * diziyi devralır, event kaybolmaz).
 *
 * Funnel: landing → kayıt → ilk üretim (aktivasyon) → tekrar üretim (retention)
 *         → PDF indirme. Ayrıca üretim event'i cache_hit/model/süre taşır →
 *         GA4 hem dönüşüm hem CACHE HIT ORANI panosu olur.
 */
declare global {
  interface Window {
    dataLayer?: Record<string, unknown>[];
  }
}

export function track(event: string, params: Record<string, unknown> = {}): void {
  if (typeof window === "undefined") return;
  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push({ event, ...params });
}
