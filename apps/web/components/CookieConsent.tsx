"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Cookie, X } from "lucide-react";

import { Button } from "@/components/ui/button";

/**
 * KVKK uyumlu cookie consent banner.
 *
 * Yasal gereksinim: GA4 gibi analitik araçlar yalnız "açık rıza"dan SONRA
 * yüklenmelidir. Banner ilk ziyarette gösterilir; kullanıcı kabul ya da
 * reddedene kadar Analytics.tsx hiçbir script yüklemez.
 *
 * Veri saklama: localStorage'da `granted` veya `denied`. Üçüncü taraf cookie
 * setlenmez (banner'ın kendisi cookie kullanmaz).
 */
export const CONSENT_STORAGE_KEY = "soruatolyesi-consent";
export const CONSENT_GRANTED = "granted";
export const CONSENT_DENIED = "denied";

export function getStoredConsent(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem(CONSENT_STORAGE_KEY);
  } catch {
    return null;
  }
}

function setStoredConsent(value: string) {
  try {
    localStorage.setItem(CONSENT_STORAGE_KEY, value);
    // Analytics.tsx aynı tab'de yeniden değerlendirsin:
    window.dispatchEvent(new Event("consent-changed"));
  } catch {
    // ignore — private mode / disabled storage
  }
}

export function CookieConsent() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    // SSR'da render etme; client'ta consent kararı yoksa banner aç.
    const stored = getStoredConsent();
    if (stored === null) setShow(true);
  }, []);

  const accept = () => {
    setStoredConsent(CONSENT_GRANTED);
    setShow(false);
  };
  const deny = () => {
    setStoredConsent(CONSENT_DENIED);
    setShow(false);
  };

  if (!show) return null;

  return (
    <div
      role="dialog"
      aria-live="polite"
      aria-label="Çerez tercihleri"
      className="fixed inset-x-0 bottom-0 z-50 border-t bg-background/95 shadow-lg backdrop-blur"
    >
      <div className="container flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:gap-4">
        <Cookie className="h-5 w-5 shrink-0 text-primary" aria-hidden />
        <p className="flex-1 text-sm text-muted-foreground">
          Bu sitede deneyimi ölçmek için Google Analytics kullanıyoruz. Onayın
          olmadan analitik çerez yüklenmez.{" "}
          <Link href="/legal/kvkk" className="underline hover:text-foreground">
            KVKK
          </Link>{" "}
          ·{" "}
          <Link
            href="/legal/privacy"
            className="underline hover:text-foreground"
          >
            Gizlilik
          </Link>
        </p>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={deny}>
            <X className="mr-1 h-3 w-3" />
            Reddet
          </Button>
          <Button size="sm" onClick={accept}>
            Kabul et
          </Button>
        </div>
      </div>
    </div>
  );
}
