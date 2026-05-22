/**
 * Backend (FastAPI) için ince fetch wrapper.
 * Lokal: NEXT_PUBLIC_API_URL=http://localhost:8000
 * Prod : Render URL.
 */
import type { HistoryItem } from "./history";
import type {
  GenerateWorksheetRequest,
  GenerateWorksheetResponse,
  GradeInfo,
  KazanimInfo,
  TopicInfo,
  Worksheet,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "";

function headers(extra: Record<string, string> = {}): HeadersInit {
  const h: Record<string, string> = { "Content-Type": "application/json", ...extra };
  if (API_KEY) h["X-API-Key"] = API_KEY;
  return h;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { ...headers(), ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const j = await res.json();
      if (j?.detail) detail = j.detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

// ---- Curriculum ---------------------------------------------------------

export async function listGrades(): Promise<GradeInfo[]> {
  const r = await request<{ grades: GradeInfo[] }>("/api/curriculum/grades");
  return r.grades;
}

export async function listTopics(grade: number): Promise<TopicInfo[]> {
  const r = await request<{ topics: TopicInfo[] }>(
    `/api/curriculum/grades/${grade}/topics`,
  );
  return r.topics;
}

export async function listKazanimlar(
  grade: number,
  topicId: string,
): Promise<KazanimInfo[]> {
  const r = await request<{ kazanimlar: KazanimInfo[] }>(
    `/api/curriculum/grades/${grade}/topics/${topicId}/kazanimlar`,
  );
  return r.kazanimlar;
}

// ---- Worksheets ---------------------------------------------------------

export async function generateWorksheet(
  body: GenerateWorksheetRequest,
): Promise<GenerateWorksheetResponse> {
  return request<GenerateWorksheetResponse>("/api/worksheets/generate", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/**
 * PDF olarak doğrudan üretim — JSON sonuç dönmez.
 * İhtiyacımıza göre: önce JSON üret, sonra render.pdf'e gönder (cache hit'lerde
 * de aynı PDF üretilir, ek LLM çağrısı yapılmaz).
 *
 * Sprint 12-A: include_answer_key / include_solutions toggle'ları query
 * parametresi olarak gider (false → cevap anahtarı / çözüm sayfası atlanır).
 */
export async function renderPdf(
  worksheet: Worksheet,
  opts: { include_answer_key?: boolean; include_solutions?: boolean } = {},
): Promise<Blob> {
  const params = new URLSearchParams();
  if (opts.include_answer_key === false) params.set("include_answer_key", "false");
  if (opts.include_solutions === false) params.set("include_solutions", "false");
  const qs = params.toString();
  const url = `${BASE}/api/worksheets/render.pdf${qs ? `?${qs}` : ""}`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(worksheet),
  });
  if (!res.ok) {
    throw new Error(`PDF render başarısız: ${res.status}`);
  }
  return res.blob();
}

// ---- Worksheet history (kullanıcı bazlı, backend kalıcı) ----------------
// Geçmiş artık tarayıcı localStorage'ı yerine tenant_id (Clerk userId) ile
// backend'de saklanır → cihazlar arası erişilebilir.

export async function listWorksheetHistory(
  tenantId: string,
): Promise<HistoryItem[]> {
  const r = await request<{ items: HistoryItem[] }>(
    `/api/worksheets/history?tenant_id=${encodeURIComponent(tenantId)}`,
  );
  return r.items;
}

export async function deleteWorksheetHistory(
  tenantId: string,
  id: string,
): Promise<void> {
  const res = await fetch(
    `${BASE}/api/worksheets/history/${encodeURIComponent(id)}?tenant_id=${encodeURIComponent(tenantId)}`,
    { method: "DELETE", headers: headers() },
  );
  if (!res.ok) throw new Error(`Geçmiş kaydı silinemedi: ${res.status}`);
}

export async function clearWorksheetHistory(tenantId: string): Promise<void> {
  const res = await fetch(
    `${BASE}/api/worksheets/history?tenant_id=${encodeURIComponent(tenantId)}`,
    { method: "DELETE", headers: headers() },
  );
  if (!res.ok) throw new Error(`Geçmiş temizlenemedi: ${res.status}`);
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
