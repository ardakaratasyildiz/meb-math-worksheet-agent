"use client";

import * as React from "react";
import { useAuth } from "@clerk/nextjs";

import { track } from "@/lib/analytics";

/**
 * Başarılı girişte GTM dataLayer'a `login` event'i basar:
 *   dataLayer.push({ event: "login" })
 *
 * NEDEN sessionId ile işaretleme: Clerk girişi tamamlandığında sayfa yeniden
 * yüklenir (redirect) → bu bileşen ZATEN girişli olarak mount olur, yani
 * "girişsiz → girişli" geçişini React state'inde yakalamak mümkün değil. Naif
 * çözüm (mount'ta girişliyse bas) ise her sayfa yenilemesinde tekrar basar ve
 * GA4'te login sayısını şişirir.
 *
 * Bu yüzden Clerk'in `sessionId`'si localStorage'da tutulur: event YALNIZCA
 * daha önce görülmemiş bir oturum kimliği için basılır.
 *   - Girişten sonraki ilk yükleme → yeni sessionId → basılır ✔
 *   - Aynı oturumda gezinme/yenileme → aynı sessionId → basılmaz ✔
 *   - Çıkış + tekrar giriş → yeni sessionId → yeniden basılır ✔
 *
 * localStorage (sessionStorage değil) bilinçli: Clerk oturumu tarayıcı
 * kapansa da sürüyor; tarayıcıyı yeniden açmak yeni bir "login" değildir.
 *
 * Görünmez; ClerkProvider içinde layout'a global monte edilir.
 */
const STORAGE_KEY = "soruatolyesi-login-event-session";

export function LoginEvent() {
  const { isLoaded, isSignedIn, sessionId } = useAuth();

  React.useEffect(() => {
    if (!isLoaded || !isSignedIn || !sessionId) return;

    let seen: string | null = null;
    try {
      seen = localStorage.getItem(STORAGE_KEY);
    } catch {
      // private mode / storage kapalı → tekilleştirme yapılamaz. Yine de
      // basmak, hiç basmamaktan iyi (ölçüm kaybı > küçük fazla sayım).
    }
    if (seen === sessionId) return;

    track("login");

    try {
      localStorage.setItem(STORAGE_KEY, sessionId);
    } catch {
      // ignore — private mode / disabled storage
    }
  }, [isLoaded, isSignedIn, sessionId]);

  return null;
}
