"use client";

import * as React from "react";

import { pingHealth } from "@/lib/api";

// Render free tier 15 dk trafiksiz kalınca uyur (cold start ~25 sn). Bu bileşen:
//   1. Sayfa ilk açıldığında backend'i uyandırır → kullanıcı /practice sekmelerine
//      vardığında instance ısınmış olur (algılanan gecikme ~0).
//   2. Sekme açık ve görünürken her 10 dk bir ping atar → aktif kullanıcı
//      instance'ı sıcak tutar (15 dk uyku eşiğinin altında).
//   3. Kullanıcı sekmeye geri döndüğünde (focus/visibility) tekrar uyandırır.
// Tek satır görünmez; sadece yan etki. Layout'ta global mount edilir.
const KEEPALIVE_MS = 10 * 60 * 1000; // 10 dk

export function BackendWarmup() {
  React.useEffect(() => {
    pingHealth(); // ilk açılış

    const interval = setInterval(() => {
      if (document.visibilityState === "visible") pingHealth();
    }, KEEPALIVE_MS);

    const onVisible = () => {
      if (document.visibilityState === "visible") pingHealth();
    };
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("focus", onVisible);

    return () => {
      clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("focus", onVisible);
    };
  }, []);

  return null;
}
