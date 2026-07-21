import { useAuth } from "@clerk/expo";
import { useEffect } from "react";

import { setAuthTokenGetter } from "@/lib/auth-token";

/**
 * Clerk `getToken()`'ı api.ts'e köprüler (web'deki AuthTokenBridge'in aynısı).
 * ClerkProvider içinde bir kez mount edilir. Görünmez (null döner).
 */
export function AuthTokenBridge() {
  const { getToken } = useAuth();

  useEffect(() => {
    setAuthTokenGetter(() => getToken());
    return () => setAuthTokenGetter(null);
  }, [getToken]);

  return null;
}
