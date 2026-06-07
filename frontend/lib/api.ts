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
  Question,
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

export interface GenerateStreamCallbacks {
  /** Akış başında bir kez — request echo'su (grade/topic/count …). */
  onMeta?: (meta: unknown) => void;
  /** Her üretilen soru için (sıfır-indeksli). Canlı ilerleme göstergesi için. */
  onQuestion?: (question: Question, index: number) => void;
}

/**
 * SSE streaming üretim — bloklayan `/generate` yerine `/generate.stream`.
 *
 * Neden: bloklayan tek HTTP isteği ~30-90 sn sürebiliyor; bu sürede hiç byte
 * akmadığı için araya giren proxy / tarayıcı bağlantıyı koparabiliyor → kullanıcı
 * "hata" görüyor ama backend üretimi bitirip geçmişe yazıyor ("hata aldım ama
 * geçmişte var" şikâyetinin kök sebebi). Streaming endpoint her soruyu ayrı event
 * olarak yolladığı için bağlantı canlı kalır, idle-timeout tetiklenmez.
 *
 * Native EventSource yalnızca GET + header'sız çalışır; bu endpoint POST + body +
 * X-API-Key gerektirdiği için fetch + ReadableStream ile SSE frame'lerini elle
 * parse ediyoruz. Backend frame formatı: `event: <tip>\ndata: <json>\n\n`.
 *
 * `complete` event'i bloklayan endpoint ile birebir aynı GenerateWorksheetResponse
 * döndürür → çağıran taraf (store/history) değişmeden çalışır.
 */
export async function generateWorksheetStream(
  body: GenerateWorksheetRequest,
  cb: GenerateStreamCallbacks = {},
  signal?: AbortSignal,
): Promise<GenerateWorksheetResponse> {
  const res = await fetch(`${BASE}/api/worksheets/generate.stream`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(body),
    signal,
  });
  // Akış başlamadan önceki hatalar (429 rate limit, 401 auth, 5xx) burada düşer.
  if (!res.ok || !res.body) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const j = await res.json();
      if (j?.detail) detail = j.detail;
    } catch {
      // ignore — gövde JSON değilse status metni kalır
    }
    throw new Error(detail);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let questionIndex = 0;
  let final: GenerateWorksheetResponse | null = null;
  let streamError: string | null = null;

  const handleFrame = (frame: string) => {
    let event = "message";
    const dataLines: string[] = [];
    for (const line of frame.split("\n")) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:")) dataLines.push(line.slice(5).replace(/^ /, ""));
    }
    if (dataLines.length === 0) return;
    let data: unknown;
    try {
      data = JSON.parse(dataLines.join("\n"));
    } catch {
      return; // bozuk frame — atla
    }
    switch (event) {
      case "meta":
        cb.onMeta?.(data);
        break;
      case "question":
        cb.onQuestion?.(data as Question, questionIndex++);
        break;
      case "complete":
        final = data as GenerateWorksheetResponse;
        break;
      case "error":
        streamError =
          (data as { detail?: string })?.detail ?? "Üretim başarısız.";
        break;
    }
  };

  // SSE frame'leri boş satırla (\n\n) ayrılır; chunk sınırlarına yayılabilir,
  // o yüzden buffer'da biriktirip tam frame'leri ayıkla.
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let sep: number;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      if (frame.trim()) handleFrame(frame);
    }
  }
  if (buffer.trim()) handleFrame(buffer); // olası kuyruk frame

  if (streamError) throw new Error(streamError);
  if (!final) {
    throw new Error("Üretim tamamlanamadı (akış beklenmedik şekilde kesildi).");
  }
  return final;
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
  opts: {
    include_answer_key?: boolean;
    include_solutions?: boolean;
    brand_name?: string;
    brand_subtitle?: string;
  } = {},
): Promise<Blob> {
  const params = new URLSearchParams();
  if (opts.include_answer_key === false) params.set("include_answer_key", "false");
  if (opts.include_solutions === false) params.set("include_solutions", "false");
  // White-label: kurum/öğretmen adı + alt satır PDF üst bilgisine basılır.
  if (opts.brand_name?.trim()) params.set("brand_name", opts.brand_name.trim());
  if (opts.brand_subtitle?.trim()) params.set("brand_subtitle", opts.brand_subtitle.trim());
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
