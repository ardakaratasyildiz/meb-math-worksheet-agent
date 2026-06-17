/**
 * Backend (FastAPI) için ince fetch wrapper.
 * Lokal: NEXT_PUBLIC_API_URL=http://localhost:8000
 * Prod : Render URL.
 */
import type { HistoryItem } from "./history";
import type {
  AttemptDetail,
  AttemptHistoryItem,
  AttemptResult,
  CreateQuizRequest,
  CreateShareResponse,
  Difficulty,
  GamificationResponse,
  GenerateWorksheetRequest,
  GenerateWorksheetResponse,
  GradeInfo,
  KazanimInfo,
  ProgressResponse,
  Question,
  QuestionType,
  QuizPublic,
  ShareResultsResponse,
  ShareSummary,
  SubmittedAnswer,
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

/**
 * Backend'i uyandırma ping'i (fire-and-forget). Render free tier 15 dk
 * trafiksiz kalınca container'ı uyutur; uyanması ~25 sn sürer. Kullanıcı
 * siteye girer girmez bu ping backend'i uyandırmaya başlar → /coz sekmelerine
 * vardığında instance ısınmış/ısınmakta olur. Hata yutulur (asla throw etmez).
 */
export function pingHealth(): void {
  try {
    void fetch(`${BASE}/healthz`, { method: "GET", cache: "no-store" }).catch(
      () => {},
    );
  } catch {
    /* SSR / fetch yoksa sessiz geç */
  }
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

/**
 * Rate-limit kimliği için header: giriş yapan kullanıcı per-tenant, anonim
 * per-IP bucket'a düşer (bkz. backend security._identifier). tenant_id null ise
 * header gönderilmez → backend IP'ye düşer.
 */
function tenantHeader(tenantId: string | null | undefined): Record<string, string> {
  return tenantId ? { "X-Tenant-Id": tenantId } : {};
}

export async function generateWorksheet(
  body: GenerateWorksheetRequest,
): Promise<GenerateWorksheetResponse> {
  return request<GenerateWorksheetResponse>("/api/worksheets/generate", {
    method: "POST",
    headers: tenantHeader(body.tenant_id),
    body: JSON.stringify(body),
  });
}

/**
 * SSE akışı `complete` event'i gelmeden kapandığında fırlatılır (bağlantı kesildi).
 * Çağıran taraf bunu yakalayıp geçmişten kurtarma deneyebilir — backend üretimi
 * arka planda bitirip kaydetmiş olabilir.
 */
export class StreamIncompleteError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "StreamIncompleteError";
  }
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
    headers: headers(tenantHeader(body.tenant_id)),
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
    // `complete` gelmeden akış kapandı → genelde bağlantı kesildi (mobil/uygulama-içi
    // tarayıcı uzun isteği timeout'ladı). Backend üretimi thread'de bitirip geçmişe
    // kaydetmiş olabilir → çağıran taraf geçmişten kurtarmayı denesin.
    throw new StreamIncompleteError(
      "Üretim tamamlanamadı (akış beklenmedik şekilde kesildi).",
    );
  }
  return final;
}

/**
 * Önceden üretilmiş worksheet'i PDF'e render eder. Tüm alanlar BODY'de gider
 * (brand_logo base64 olabildiği için query'ye sığmaz). White-label: kurum/öğretmen
 * adı + alt satır + opsiyonel logo PDF üst bilgisine basılır.
 */
export async function renderPdf(
  worksheet: Worksheet,
  opts: {
    include_answer_key?: boolean;
    include_solutions?: boolean;
    brand_name?: string;
    brand_subtitle?: string;
    brand_logo?: string;
  } = {},
): Promise<Blob> {
  const res = await fetch(`${BASE}/api/worksheets/render.pdf`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({
      worksheet,
      include_answer_key: opts.include_answer_key ?? true,
      include_solutions: opts.include_solutions ?? true,
      brand_name: opts.brand_name?.trim() || null,
      brand_subtitle: opts.brand_subtitle?.trim() || null,
      brand_logo: opts.brand_logo || null,
    }),
  });
  if (!res.ok) {
    throw new Error(`PDF render başarısız: ${res.status}`);
  }
  return res.blob();
}

/**
 * "Soruyu Değiştir" — tek soruyu aynı kazanım + tip + zorlukta yeniden üretir.
 * topic_id sunucuda kazanım kodundan çözülür. LLM çağrısı (~10-30 sn).
 */
export async function regenerateQuestion(body: {
  grade: number;
  kazanim_kod: string;
  difficulty: Difficulty;
  question_type: QuestionType;
  tenant_id?: string | null;
}): Promise<Question> {
  const r = await request<{ question: Question }>(
    "/api/worksheets/regenerate-question",
    {
      method: "POST",
      headers: tenantHeader(body.tenant_id),
      body: JSON.stringify(body),
    },
  );
  return r.question;
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

// ---- Çözülebilir quiz (öğrenme döngüsü) ---------------------------------

/** Çözülebilir quiz üret + kaydet. Cevapsız QuizPublic döner. */
export async function createQuiz(body: CreateQuizRequest): Promise<QuizPublic> {
  return request<QuizPublic>("/api/quizzes", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/** Quiz'i çözmek için getir (cevapsız, owner-only). */
export async function getQuiz(
  quizId: string,
  tenantId: string,
): Promise<QuizPublic> {
  return request<QuizPublic>(
    `/api/quizzes/${encodeURIComponent(quizId)}?tenant_id=${encodeURIComponent(tenantId)}`,
  );
}

/** Cevapları gönder → sunucuda puanlanır → sonuç + kazanım kırılımı döner. */
export async function submitAttempt(
  quizId: string,
  body: {
    tenant_id: string;
    answers: SubmittedAnswer[];
    duration_seconds?: number;
  },
): Promise<AttemptResult> {
  return request<AttemptResult>(
    `/api/quizzes/${encodeURIComponent(quizId)}/attempt`,
    { method: "POST", body: JSON.stringify(body) },
  );
}

/** Kullanıcının kazanım-bazlı ilerlemesi + zayıf konuları + genel özeti. */
export async function getProgress(tenantId: string): Promise<ProgressResponse> {
  return request<ProgressResponse>(
    `/api/me/progress?tenant_id=${encodeURIComponent(tenantId)}`,
  );
}

/** Kullanıcının geçmiş çözüm denemeleri (en yeni önce). */
export async function listMyAttempts(
  tenantId: string,
  limit = 50,
): Promise<AttemptHistoryItem[]> {
  const r = await request<{ items: AttemptHistoryItem[] }>(
    `/api/me/attempts?tenant_id=${encodeURIComponent(tenantId)}&limit=${limit}`,
  );
  return r.items;
}

/** Geçmiş bir denemenin tam gözden geçirmesi (soru + doğru cevap + senin cevabın). */
export async function getMyAttempt(
  attemptId: string,
  tenantId: string,
): Promise<AttemptDetail> {
  return request<AttemptDetail>(
    `/api/me/attempts/${encodeURIComponent(attemptId)}?tenant_id=${encodeURIComponent(tenantId)}`,
  );
}

/** Oyunlaştırma — XP / seviye / seri. */
export async function getGamification(
  tenantId: string,
): Promise<GamificationResponse> {
  return request<GamificationResponse>(
    `/api/me/gamification?tenant_id=${encodeURIComponent(tenantId)}`,
  );
}

// ---- Quiz paylaşımı (Faz 3) ---------------------------------------------

/** Quiz için link paylaşımı oluştur (idempotent) — yalnız sahibi. */
export async function createShare(
  quizId: string,
  tenantId: string,
): Promise<CreateShareResponse> {
  return request<CreateShareResponse>(
    `/api/quizzes/${encodeURIComponent(quizId)}/share?tenant_id=${encodeURIComponent(tenantId)}`,
    { method: "POST", headers: tenantHeader(tenantId) },
  );
}

/** Paylaşılan quiz'i çözmek için getir (cevapsız, PUBLIC — login gerekmez). */
export async function getSharedQuiz(code: string): Promise<QuizPublic> {
  return request<QuizPublic>(`/api/shared/${encodeURIComponent(code)}`);
}

/**
 * Paylaşılan quiz cevaplarını gönder → sunucuda puanla → sonuç.
 * Misafir: tenant_id yok (solver_label opsiyonel). Üye: tenant_id gönderilir →
 * kendi ilerlemesine sayılır. Rate-limit kimliği için üyede X-Tenant-Id header'ı.
 */
export async function submitSharedAttempt(
  code: string,
  body: {
    tenant_id?: string | null;
    solver_label?: string | null;
    answers: SubmittedAnswer[];
    duration_seconds?: number;
  },
): Promise<AttemptResult> {
  return request<AttemptResult>(
    `/api/shared/${encodeURIComponent(code)}/attempt`,
    {
      method: "POST",
      headers: tenantHeader(body.tenant_id),
      body: JSON.stringify(body),
    },
  );
}

/** Kullanıcının oluşturduğu paylaşımlar + çözülme sayısı + ort. skor (sahip panosu). */
export async function listMyShares(tenantId: string): Promise<ShareSummary[]> {
  const r = await request<{ items: ShareSummary[] }>(
    `/api/me/shares?tenant_id=${encodeURIComponent(tenantId)}`,
  );
  return r.items;
}

/** Bir paylaşımın sonuç panosu — kim çözdü, kaç doğru (sahip-only). */
export async function getShareResults(
  shareId: string,
  tenantId: string,
): Promise<ShareResultsResponse> {
  return request<ShareResultsResponse>(
    `/api/me/shares/${encodeURIComponent(shareId)}/results?tenant_id=${encodeURIComponent(tenantId)}`,
  );
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
