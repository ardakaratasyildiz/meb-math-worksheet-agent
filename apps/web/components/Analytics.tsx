"use client";

import Script from "next/script";
import { useEffect, useState } from "react";

import { CONSENT_STORAGE_KEY, CONSENT_GRANTED, getStoredConsent } from "./CookieConsent";

/**
 * Google Analytics 4 — KVKK uyumu gereği yalnız kullanıcı rızasından SONRA
 * yüklenir. Rıza yoksa gtag script hiç enjekte edilmez, hiçbir cookie/identifier
 * oluşmaz (GA4 default behavior tracking dahil).
 *
 * Consent durumu localStorage'da; değiştiğinde `consent-changed` event'i ile
 * yeniden render olur (CookieConsent.tsx dispatches this).
 */
export function Analytics() {
  const [consent, setConsent] = useState<string | null>(null);
  const measurementId = process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID;

  useEffect(() => {
    setConsent(getStoredConsent());
    const handler = () => setConsent(getStoredConsent());
    // Aynı tab'de banner'dan onay verince Analytics'e haber:
    window.addEventListener("consent-changed", handler);
    // Başka tab'de değişirse de senkron:
    window.addEventListener("storage", (e) => {
      if (e.key === CONSENT_STORAGE_KEY) handler();
    });
    return () => {
      window.removeEventListener("consent-changed", handler);
    };
  }, []);

  // GA_MEASUREMENT_ID set değilse veya kullanıcı reddettiyse hiçbir şey yapma.
  if (!measurementId || consent !== CONSENT_GRANTED) return null;

  return (
    <>
      <Script
        src={`https://www.googletagmanager.com/gtag/js?id=${measurementId}`}
        strategy="afterInteractive"
      />
      <Script id="ga4-init" strategy="afterInteractive">
        {`
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          // IP anonymize — KVKK + GDPR best practice.
          gtag('config', '${measurementId}', { anonymize_ip: true });
        `}
      </Script>
    </>
  );
}
