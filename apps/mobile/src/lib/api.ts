/**
 * Backend (FastAPI) için ince fetch wrapper — web'deki frontend/lib/api.ts'in
 * mobil karşılığı. Aynı sözleşme: X-API-Key + (giriş varsa) Authorization Bearer.
 */
import { ENV } from "./env";
import { authHeader } from "./auth-token";

function baseHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const h: Record<string, string> = { "Content-Type": "application/json", ...extra };
  if (ENV.apiKey) h["X-API-Key"] = ENV.apiKey;
  return h;
}

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const auth = await authHeader();
  const res = await fetch(`${ENV.apiUrl}${path}`, {
    ...init,
    headers: { ...baseHeaders(), ...auth, ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const j = (await res.json()) as { detail?: unknown };
      if (typeof j?.detail === "string" && j.detail) detail = j.detail;
    } catch {
      // gövde JSON değil — status metni kalır
    }
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

// ── /api/me/gamification (öğrenme döngüsü — ilk doğrulanmış çağrı) ────────────
export interface GamificationResponse {
  xp: number;
  level: number;
  xp_in_level: number;
  xp_for_next: number;
  streak_current: number;
  streak_longest: number;
  total_active_days: number;
}

/** Kullanıcının XP / seviye / seri verisi. Bearer token backend'te doğrulanır. */
export function getGamification(tenantId: string): Promise<GamificationResponse> {
  return apiRequest<GamificationResponse>(
    `/api/me/gamification?tenant_id=${encodeURIComponent(tenantId)}`,
  );
}

/** Backend uyandırma ping'i (Render free-tier cold start). Hata yutulur. */
export function pingHealth(): void {
  try {
    void fetch(`${ENV.apiUrl}/healthz`, { method: "GET" }).catch(() => {});
  } catch {
    /* no-op */
  }
}
