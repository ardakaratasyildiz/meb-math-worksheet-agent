"use client";

import * as React from "react";
import { useAuth } from "@clerk/nextjs";

import { setAuthTokenGetter } from "@/lib/api";

/**
 * Clerk oturum token'ını api.ts'e köprüler (P0 — billing ön koşulu).
 *
 * api.ts saf bir modül (React hook değil) → Clerk `getToken()`'a doğrudan
 * erişemez. Bu görünmez bileşen uygulama açılışında token sağlayıcısını bir kez
 * register eder; ardından `api.ts/request()` her istekte `Authorization: Bearer
 * <token>` başlığı ekler. Backend token imzasını doğrulayıp DOĞRULANMIŞ
 * tenant_id üretir (spoof koruması).
 *
 * ClerkProvider içinde, layout'ta global mount edilir. Kullanıcı girişsizse
 * `getToken()` null döner → header eklenmez (zararsız).
 */
export function AuthTokenBridge() {
  const { getToken } = useAuth();

  React.useEffect(() => {
    // Varsayılan oturum JWT'si (özel template yok) — `iss` claim'i Clerk issuer'ı.
    setAuthTokenGetter(() => getToken());
    return () => setAuthTokenGetter(null);
  }, [getToken]);

  return null;
}
