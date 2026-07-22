/**
 * Backend (FastAPI) için ince fetch wrapper — web'deki frontend/lib/api.ts'in
 * mobil karşılığı. Aynı sözleşme: X-API-Key + (giriş varsa) Authorization Bearer.
 */
import type {
  GenerateWorksheetRequest,
  GenerateWorksheetResponse,
  GradeInfo,
  KazanimInfo,
  SubjectSlug,
  UnitInfo,
} from "@soruatolyesi/shared";

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

// ── Curriculum (ders → sınıf → ünite → kazanım) ──────────────────────────────
function subjectQuery(subject?: SubjectSlug): string {
  return subject && subject !== "matematik" ? `?subject=${subject}` : "";
}

export async function listGrades(subject?: SubjectSlug): Promise<GradeInfo[]> {
  const r = await apiRequest<{ grades: GradeInfo[] }>(
    `/api/curriculum/grades${subjectQuery(subject)}`,
  );
  return r.grades;
}

export async function listUnits(
  grade: number,
  subject?: SubjectSlug,
): Promise<UnitInfo[]> {
  const r = await apiRequest<{ units: UnitInfo[] }>(
    `/api/curriculum/grades/${grade}/units${subjectQuery(subject)}`,
  );
  return r.units;
}

export async function listKazanimlarByUnit(
  grade: number,
  unitId: string,
  subject?: SubjectSlug,
): Promise<KazanimInfo[]> {
  const q = subject && subject !== "matematik" ? `?subject=${subject}` : "";
  const r = await apiRequest<{ kazanimlar: KazanimInfo[] }>(
    `/api/curriculum/grades/${grade}/units/${encodeURIComponent(unitId)}/kazanimlar${q}`,
  );
  return r.kazanimlar;
}

// ── Çalışma kağıdı üretimi ───────────────────────────────────────────────────
/**
 * Çalışma kağıdı üret (bloklayan uç; ~30-90 sn — iyi bir yükleniyor durumu şart).
 * Rate-limit kimliği için X-Tenant-Id + (giriş varsa) Bearer token gönderilir.
 * İleride SSE streaming (expo/fetch) ile bağlantı-kesme dayanıklılığı eklenebilir.
 */
export function generateWorksheet(
  body: GenerateWorksheetRequest,
): Promise<GenerateWorksheetResponse> {
  return apiRequest<GenerateWorksheetResponse>("/api/worksheets/generate", {
    method: "POST",
    headers: body.tenant_id ? { "X-Tenant-Id": body.tenant_id } : {},
    body: JSON.stringify(body),
  });
}

/** Backend uyandırma ping'i (Render free-tier cold start). Hata yutulur. */
export function pingHealth(): void {
  try {
    void fetch(`${ENV.apiUrl}/healthz`, { method: "GET" }).catch(() => {});
  } catch {
    /* no-op */
  }
}
