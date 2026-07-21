/**
 * Clerk oturum token'ı köprüsü (web'deki lib/api.ts deseninin aynısı).
 *
 * api.ts saf bir modül (hook değil) → Clerk `getToken()`'a doğrudan erişemez.
 * `AuthTokenBridge` bileşeni açılışta bir kez register eder; `apiRequest()` her
 * çağrıda token'ı çekip `Authorization: Bearer <token>` ekler. Backend
 * (app/services/clerk_auth.py) imzayı doğrulayıp DOĞRULANMIŞ tenant_id üretir
 * → client'ın gönderdiği tenant_id'ye güvenmez (spoof/IDOR koruması).
 */
type TokenGetter = () => Promise<string | null>;

let _getter: TokenGetter | null = null;

export function setAuthTokenGetter(fn: TokenGetter | null): void {
  _getter = fn;
}

export async function authHeader(): Promise<Record<string, string>> {
  if (!_getter) return {};
  try {
    const token = await _getter();
    return token ? { Authorization: `Bearer ${token}` } : {};
  } catch {
    return {}; // token alınamazsa sessiz geç (backend gerekiyorsa 401 döner)
  }
}
