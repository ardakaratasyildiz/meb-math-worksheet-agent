"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Cookie, X } from "lucide-react";

import { Button } from "@/components/ui/button";

/**
 * Çerez bilgilendirme bandı.
 *
 * DİKKAT — bu banner script/çerez ENGELLEMEZ. Kullanıcı kararına göre hiçbir
 * tag koşullanmıyor: Google Tag Manager (GTM-P2QLKRKT) app/layout.tsx'te
 * koşulsuz yükleniyor ve tag'ler GTM tarafında yönetiliyor. Banner yalnızca
 * bilgilendirme + kapatma amaçlı ("Tamam" = okundu, tekrar gösterme).
 *
 * Bu yüzden "Reddet" butonu ve rıza-kapılı yükleme mantığı kaldırıldı: hiçbir
 * şeyi durdurmayan bir "Reddet" düğmesi kullanıcıyı yanıltır. Gerçek engelleme
 * istenirse GTM Consent Mode kurulup banner buna bağlanmalı.
 *
 * Kapatma durumu localStorage'da (`soruatolyesi-consent`). Eski rıza değerleri
 * (`granted`/`denied`) da "okundu" sayılır → daha önce karar vermiş kullanıcıya
 * banner yeniden açılmaz.
 */
export const CONSENT_STORAGE_KEY = "soruatolyesi-consent";
export const NOTICE_ACKNOWLEDGED = "acknowledged";

export function getStoredConsent(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem(CONSENT_STORAGE_KEY);
  } catch {
    return null;
  }
}

export function CookieConsent() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    // SSR'da render etme; client'ta daha önce kapatılmadıysa bandı göster.
    if (getStoredConsent() === null) setShow(true);
  }, []);

  const dismiss = () => {
    try {
      localStorage.setItem(CONSENT_STORAGE_KEY, NOTICE_ACKNOWLEDGED);
    } catch {
      // ignore — private mode / disabled storage
    }
    setShow(false);
  };

  if (!show) return null;

  return (
    <div
      role="region"
      aria-live="polite"
      aria-label="Çerez bilgilendirmesi"
      className="fixed inset-x-0 bottom-0 z-50 border-t bg-background/95 shadow-lg backdrop-blur"
    >
      <div className="container flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:gap-4">
        <Cookie className="h-5 w-5 shrink-0 text-primary" aria-hidden />
        <p className="flex-1 text-sm text-muted-foreground">
          Bu sitede deneyimi ölçmek ve iyileştirmek için çerezler kullanılıyor.
          Ayrıntılar için{" "}
          <Link href="/legal/kvkk" className="underline hover:text-foreground">
            KVKK
          </Link>{" "}
          ve{" "}
          <Link
            href="/legal/privacy"
            className="underline hover:text-foreground"
          >
            Gizlilik
          </Link>{" "}
          metinlerine bakabilirsin.
        </p>
        <div className="flex gap-2">
          <Button
            size="sm"
            onClick={dismiss}
            aria-label="Çerez bilgilendirmesini kapat"
          >
            <X className="mr-1 h-3 w-3" />
            Tamam
          </Button>
        </div>
      </div>
    </div>
  );
}
