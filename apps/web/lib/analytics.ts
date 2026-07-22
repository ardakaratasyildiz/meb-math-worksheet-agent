/**
 * GA4 event yardımcısı.
 *
 * gtag YALNIZCA KVKK rızasından sonra yüklenir (components/Analytics.tsx). Rıza
 * yoksa `window.gtag` tanımsızdır → track() sessiz no-op olur, hiçbir veri
 * gönderilmez. Bu yüzden burada ayrıca consent kontrolü gerekmez — rıza yoksa
 * çağrı doğal olarak hiçbir şey yapmaz (KVKK uyumu by construction).
 *
 * Funnel: landing → kayıt → ilk üretim (aktivasyon) → tekrar üretim (retention)
 *         → PDF indirme. Ayrıca üretim event'i cache_hit/model/süre taşır →
 *         GA4 hem dönüşüm hem CACHE HIT ORANI panosu olur.
 */
declare global {
  interface Window {
    gtag?: (...args: unknown[]) => void;
  }
}

export function track(event: string, params: Record<string, unknown> = {}): void {
  if (typeof window === "undefined" || typeof window.gtag !== "function") return;
  window.gtag("event", event, params);
}
