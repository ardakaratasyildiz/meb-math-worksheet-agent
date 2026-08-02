/**
 * Backend (FastAPI) için ince fetch wrapper.
 * Lokal: NEXT_PUBLIC_API_URL=http://localhost:8000
 * Prod : Render URL.
 */
import type { HistoryItem } from "./history";
import type {
  AssignmentResultsResponse,
  AssignmentWorksheetResponse,
  AttemptDetail,
  AttemptHistoryItem,
  AttemptResult,
  ChildItem,
  ClassroomDetail,
  ClassroomsResponse,
  CreateQuizRequest,
  EmailPrefsResponse,
  CreateShareResponse,
  Difficulty,
  GamificationResponse,
  GenerateWorksheetRequest,
  GenerateWorksheetResponse,
  GradeInfo,
  JoinClassroomResponse,
  KazanimInfo,
  MyAssignmentItem,
  MyQuizItem,
  ProgressResponse,
  Question,
  QuestionType,
  QuizPublic,
  QuizReview,
  ShareResultsResponse,
  ShareSummary,
  TeachingOverviewItem,
  StudyPlanResponse,
  SubmittedAnswer,
  TopicInfo,
  UnitInfo,
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
 * Clerk oturum token'ı sağlayıcısı (P0 — billing ön koşulu).
 *
 * api.ts saf modül (hook değil) → Clerk `getToken()`'a doğrudan erişemez.
 * `AuthTokenBridge` bileşeni uygulama açılışında bunu bir kez register eder;
 * `request()` her çağrıda token'ı çeker (Clerk kısa-ömürlü JWT'yi cache'ler →
 * ucuz) ve `Authorization: Bearer <token>` başlığı ekler. Backend
 * (app/services/clerk_auth.py) bu token'ın imzasını doğrulayıp DOĞRULANMIŞ
 * tenant_id üretir → client'ın gönderdiği tenant_id'ye güvenmek zorunda kalmaz.
 *
 * Register edilmemişse / kullanıcı girişsizse header eklenmez → backend
 * doğrulama kapalıyken (bugünkü prod) davranış aynen korunur.
 */
type TokenGetter = () => Promise<string | null>;
let _tokenGetter: TokenGetter | null = null;

export function setAuthTokenGetter(fn: TokenGetter | null): void {
  _tokenGetter = fn;
}

async function authHeader(): Promise<Record<string, string>> {
  if (!_tokenGetter) return {};
  try {
    const token = await _tokenGetter();
    return token ? { Authorization: `Bearer ${token}` } : {};
  } catch {
    return {}; // token alınamazsa sessiz geç (backend gerekiyorsa 401 döner)
  }
}

/**
 * Backend'i uyandırma ping'i (fire-and-forget). Render free tier 15 dk
 * trafiksiz kalınca container'ı uyutur; uyanması ~25 sn sürer. Kullanıcı
 * siteye girer girmez bu ping backend'i uyandırmaya başlar → /practice sekmelerine
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

/**
 * FastAPI hata gövdesinden okunabilir mesaj çıkarır. `detail` string olabilir
 * (bizim HTTPException'larımız) ama 422 doğrulama hatalarında DİZİ olur
 * ([{loc, msg, type}]) → doğrudan string'e atanırsa "[object Object]" görünür.
 * Bu helper diziyi/objeyi okunabilir metne indirir (örn. eski backend'e unit_id
 * gidip topic_id eksik kalınca "topic_id: Field required").
 */
function parseErrorDetail(j: unknown, fallback: string): string {
  if (!j || typeof j !== "object") return fallback;
  const d = (j as { detail?: unknown }).detail;
  if (typeof d === "string" && d) return d;
  if (Array.isArray(d)) {
    const parts = d.map((e) => {
      const loc = Array.isArray((e as { loc?: unknown[] })?.loc)
        ? (e as { loc: unknown[] }).loc
            .filter((x) => x !== "body")
            .join(".")
        : "";
      const msg = (e as { msg?: string })?.msg ?? "";
      return loc ? `${loc}: ${msg}` : msg;
    });
    const joined = parts.filter(Boolean).join(" · ");
    if (joined) return joined;
  }
  if (d && typeof d === "object") return JSON.stringify(d);
  return fallback;
}

/** Aylık üretim kotası dolduğunda backend HTTP 402 + yapısal sinyal döner. */
export interface QuotaInfo {
  plan?: string;
  limit?: number | null;
  used?: number;
  message?: string;
}

/**
 * Kota aşımı (HTTP 402, detail.error === "quota_exceeded"). UI bunu yakalayıp
 * paywall gösterir (jenerik hata toast'ı yerine). billing_enabled kapalıyken
 * backend bu hatayı hiç döndürmez → mevcut davranış değişmez.
 */
export class QuotaExceededError extends Error {
  info: QuotaInfo;
  constructor(info: QuotaInfo) {
    super(info.message || "Aylık üretim hakkın doldu.");
    this.name = "QuotaExceededError";
    this.info = info;
  }
}

/** 402 + quota_exceeded ise QuotaExceededError fırlatır; aksi halde no-op. */
function throwIfQuotaExceeded(status: number, json: unknown): void {
  if (status !== 402) return;
  const d = (json as { detail?: unknown } | null)?.detail;
  if (d && typeof d === "object" && (d as { error?: string }).error === "quota_exceeded") {
    const q = d as QuotaInfo & { error: string };
    throw new QuotaExceededError({
      plan: q.plan,
      limit: q.limit,
      used: q.used,
      message: q.message,
    });
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const auth = await authHeader();
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { ...headers(), ...auth, ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    const fallback = `${res.status} ${res.statusText}`;
    let json: unknown = null;
    try {
      json = await res.json();
    } catch {
      // gövde JSON değilse status metni kalır
    }
    throwIfQuotaExceeded(res.status, json);
    throw new Error(parseErrorDetail(json, fallback));
  }
  return res.json() as Promise<T>;
}

// ---- Curriculum ---------------------------------------------------------

// Ders (subject) query'si — matematik varsayılanda parametre eklenmez (geriye uyum).
function subjectQuery(subject?: string): string {
  return subject && subject !== "matematik" ? `?subject=${subject}` : "";
}

export async function listGrades(subject?: string): Promise<GradeInfo[]> {
  const r = await request<{ grades: GradeInfo[] }>(
    `/api/curriculum/grades${subjectQuery(subject)}`,
  );
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

// ---- MEB TYMM ünite (tema) akışı ----------------------------------------

export async function listUnits(
  grade: number,
  subject?: string,
): Promise<UnitInfo[]> {
  const r = await request<{ units: UnitInfo[] }>(
    `/api/curriculum/grades/${grade}/units${subjectQuery(subject)}`,
  );
  return r.units;
}

export async function listKazanimlarByUnit(
  grade: number,
  unitId: string,
  subject?: string,
): Promise<KazanimInfo[]> {
  const r = await request<{ kazanimlar: KazanimInfo[] }>(
    `/api/curriculum/grades/${grade}/units/${unitId}/kazanimlar${subjectQuery(subject)}`,
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
    // Bearer token → backend kota kararını DOĞRULANMIŞ tenant'a bağlar (spoof yok).
    // Girişsizde header eklenmez → anonim üretim kotasız (SEO) sürer.
    headers: { ...headers(tenantHeader(body.tenant_id)), ...(await authHeader()) },
    body: JSON.stringify(body),
    signal,
  });
  // Akış başlamadan önceki hatalar (402 kota, 429 rate limit, 401 auth, 422, 5xx) burada düşer.
  if (!res.ok || !res.body) {
    const fallback = `${res.status} ${res.statusText}`;
    let json: unknown = null;
    try {
      json = await res.json();
    } catch {
      // gövde JSON değilse status metni kalır
    }
    throwIfQuotaExceeded(res.status, json);
    throw new Error(parseErrorDetail(json, fallback));
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
  // 204 (gövdesiz) döndüğü için request() yerine ham fetch; ama Authorization
  // Bearer ŞART (backend artık doğrulanmış kimlik ister — spoof/IDOR koruması).
  const auth = await authHeader();
  const res = await fetch(
    `${BASE}/api/worksheets/history/${encodeURIComponent(id)}?tenant_id=${encodeURIComponent(tenantId)}`,
    { method: "DELETE", headers: { ...headers(), ...auth } },
  );
  if (!res.ok) throw new Error(`Geçmiş kaydı silinemedi: ${res.status}`);
}

export async function clearWorksheetHistory(tenantId: string): Promise<void> {
  const auth = await authHeader();
  const res = await fetch(
    `${BASE}/api/worksheets/history?tenant_id=${encodeURIComponent(tenantId)}`,
    { method: "DELETE", headers: { ...headers(), ...auth } },
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

/** Quiz'i sahibine CEVAPLI getir — öğretmen atamadan önce soruları inceler (owner-only). */
export async function getQuizReview(
  quizId: string,
  tenantId: string,
): Promise<QuizReview> {
  return request<QuizReview>(
    `/api/quizzes/${encodeURIComponent(quizId)}/review?tenant_id=${encodeURIComponent(tenantId)}`,
  );
}

/** Sahibin quiz'inde bir soruyu yeniden üret + kalıcı kıl → yeni soru (cevaplı) döner. */
export async function regenerateQuizQuestion(
  quizId: string,
  number: number,
  tenantId: string,
): Promise<Question> {
  const r = await request<{ question: Question }>(
    `/api/quizzes/${encodeURIComponent(quizId)}/questions/${number}/regenerate?tenant_id=${encodeURIComponent(tenantId)}`,
    { method: "POST", headers: tenantHeader(tenantId) },
  );
  return r.question;
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

/** AI destekli haftalık çalışma programı (eksiklere göre). LLM çağrısı içerir. */
/** Kayıtlı haftalık programı getir (LLM yok, hızlı). Kayıt yoksa created_at boş. */
export async function getStudyPlan(
  tenantId: string,
): Promise<StudyPlanResponse> {
  return request<StudyPlanResponse>(
    `/api/me/study-plan?tenant_id=${encodeURIComponent(tenantId)}`,
  );
}

/** Programı (yeniden) üret + kaydet (LLM çağrısı içerir). */
export async function createStudyPlan(
  tenantId: string,
): Promise<StudyPlanResponse> {
  return request<StudyPlanResponse>(
    `/api/me/study-plan?tenant_id=${encodeURIComponent(tenantId)}`,
    { method: "POST" },
  );
}

// ---- Veli ↔ öğrenci bağı (WS-6b) ----------------------------------------

/** Öğrencinin veli takip kodu (yoksa üretilir, kalıcı). */
export async function getParentCode(tenantId: string): Promise<{ code: string }> {
  return request<{ code: string }>("/api/me/parent-code", {
    method: "POST",
    body: JSON.stringify({ tenant_id: tenantId }),
  });
}

/** Veli, öğrencinin kodunu girerek bağlanır. */
export async function linkChild(
  tenantId: string,
  code: string,
  childLabel?: string,
): Promise<{ student_id: string }> {
  return request<{ student_id: string }>("/api/me/link-child", {
    method: "POST",
    body: JSON.stringify({ tenant_id: tenantId, code, child_label: childLabel ?? null }),
  });
}

/** Velinin bağlı olduğu öğrenciler. */
export async function listChildren(tenantId: string): Promise<ChildItem[]> {
  const r = await request<{ items: ChildItem[] }>(
    `/api/me/children?tenant_id=${encodeURIComponent(tenantId)}`,
  );
  return r.items;
}

/** Velinin, bağlı olduğu öğrencinin ilerlemesi (salt-okunur). */
export async function getChildProgress(
  tenantId: string,
  studentId: string,
): Promise<ProgressResponse> {
  return request<ProgressResponse>(
    `/api/me/children/${encodeURIComponent(studentId)}/progress?tenant_id=${encodeURIComponent(tenantId)}`,
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

/** Öğretmen: bir öğrencinin ödevdeki denemesini soru-soru getir (owner-only). */
export async function getStudentAttemptDetail(
  assignmentId: string,
  studentTenantId: string,
  tenantId: string,
): Promise<AttemptDetail> {
  return request<AttemptDetail>(
    `/api/assignments/${encodeURIComponent(assignmentId)}/attempts/${encodeURIComponent(studentTenantId)}?tenant_id=${encodeURIComponent(tenantId)}`,
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

// ---- Sınıf / Ödev (Faz 3.5) ---------------------------------------------

/** Yeni sınıf oluştur (öğretmen). Katılma kodu + detay döner. */
export async function createClassroom(
  tenantId: string,
  name: string,
): Promise<ClassroomDetail> {
  return request<ClassroomDetail>("/api/classrooms", {
    method: "POST",
    headers: tenantHeader(tenantId),
    body: JSON.stringify({ tenant_id: tenantId, name }),
  });
}

/** Öğrenci katılma koduyla sınıfa katılır. */
export async function joinClassroom(
  tenantId: string,
  code: string,
  displayName: string,
): Promise<JoinClassroomResponse> {
  return request<JoinClassroomResponse>("/api/classrooms/join", {
    method: "POST",
    headers: tenantHeader(tenantId),
    body: JSON.stringify({ tenant_id: tenantId, code, display_name: displayName }),
  });
}

/** Kullanıcının sınıfları: sahip olunanlar (teaching) + katılınanlar (enrolled). */
export async function listClassrooms(
  tenantId: string,
): Promise<ClassroomsResponse> {
  return request<ClassroomsResponse>(
    `/api/classrooms?tenant_id=${encodeURIComponent(tenantId)}`,
  );
}

/** Sınıf detayı (sahip: kod + üyeler; üye: ad + sayı). */
export async function getClassroom(
  classroomId: string,
  tenantId: string,
): Promise<ClassroomDetail> {
  return request<ClassroomDetail>(
    `/api/classrooms/${encodeURIComponent(classroomId)}?tenant_id=${encodeURIComponent(tenantId)}`,
  );
}

/** Sınıfı sil — yalnız sahibi (öğretmen). Üyeler + ödevler cascade silinir. */
export async function deleteClassroom(
  tenantId: string,
  classroomId: string,
): Promise<void> {
  await request<{ ok: boolean }>(
    `/api/classrooms/${encodeURIComponent(classroomId)}?tenant_id=${encodeURIComponent(tenantId)}`,
    { method: "DELETE" },
  );
}

/** Öğrenci sınıftan ayrılır (üyeliğini siler). */
export async function leaveClassroom(
  tenantId: string,
  classroomId: string,
): Promise<void> {
  await request<{ ok: boolean }>(
    `/api/classrooms/${encodeURIComponent(classroomId)}/leave?tenant_id=${encodeURIComponent(tenantId)}`,
    { method: "POST" },
  );
}

/** Öğretmen bir öğrenciyi sınıftan çıkarır (kick) — yalnız sahip. */
export async function removeMember(
  tenantId: string,
  classroomId: string,
  studentTenantId: string,
): Promise<void> {
  await request<{ ok: boolean }>(
    `/api/classrooms/${encodeURIComponent(classroomId)}/members/${encodeURIComponent(studentTenantId)}?tenant_id=${encodeURIComponent(tenantId)}`,
    { method: "DELETE" },
  );
}

/** Öğretmen bir ödevi siler — yalnız sınıf sahibi. */
export async function deleteAssignment(
  tenantId: string,
  classroomId: string,
  assignmentId: string,
): Promise<void> {
  await request<{ ok: boolean }>(
    `/api/classrooms/${encodeURIComponent(classroomId)}/assignments/${encodeURIComponent(assignmentId)}?tenant_id=${encodeURIComponent(tenantId)}`,
    { method: "DELETE" },
  );
}

// ---- Ödev (Faz 3.5 PR 2) -------------------------------------------------

/** Öğretmenin ödev atamak için seçebileceği kendi quiz'leri. */
export async function listMyQuizzes(tenantId: string): Promise<MyQuizItem[]> {
  const r = await request<{ items: MyQuizItem[] }>(
    `/api/me/quizzes?tenant_id=${encodeURIComponent(tenantId)}`,
  );
  return r.items;
}

/** Sınıfa quiz'i ödev olarak ata (yalnız sınıf sahibi). dueDate opsiyonel (YYYY-MM-DD). */
export async function assignQuiz(
  classroomId: string,
  tenantId: string,
  quizId: string,
  dueDate?: string | null,
): Promise<{ id: string; created_at: string }> {
  return request<{ id: string; created_at: string }>(
    `/api/classrooms/${encodeURIComponent(classroomId)}/assignments`,
    {
      method: "POST",
      headers: tenantHeader(tenantId),
      body: JSON.stringify({
        tenant_id: tenantId,
        quiz_id: quizId,
        due_date: dueDate || null,
      }),
    },
  );
}

/** Ödevin sonuç panosu (sınıf sahibi) — roster: kim çözdü, kaç doğru. */
export async function getAssignmentResults(
  assignmentId: string,
  tenantId: string,
): Promise<AssignmentResultsResponse> {
  return request<AssignmentResultsResponse>(
    `/api/assignments/${encodeURIComponent(assignmentId)}/results?tenant_id=${encodeURIComponent(tenantId)}`,
  );
}

/** Öğretmenin tüm sınıflarındaki ödevler + çözülme özeti ('Ödev Sonuçları' panosu). */
export async function getTeachingResults(
  tenantId: string,
): Promise<TeachingOverviewItem[]> {
  const r = await request<{ items: TeachingOverviewItem[] }>(
    `/api/me/teaching-results?tenant_id=${encodeURIComponent(tenantId)}`,
  );
  return r.items;
}

/** Sınıfa PDF (çalışma kağıdı) ödevi ata — worksheet snapshot'ı gönderilir. */
export async function assignPdf(
  classroomId: string,
  tenantId: string,
  worksheet: Worksheet,
  dueDate?: string | null,
): Promise<{ id: string; created_at: string }> {
  return request<{ id: string; created_at: string }>(
    `/api/classrooms/${encodeURIComponent(classroomId)}/assignments/pdf`,
    {
      method: "POST",
      headers: tenantHeader(tenantId),
      body: JSON.stringify({
        tenant_id: tenantId,
        worksheet,
        due_date: dueDate || null,
      }),
    },
  );
}

/** PDF ödevinin worksheet'ini getir (öğrenci istemcide PDF'e render eder). */
export async function getAssignmentWorksheet(
  assignmentId: string,
  tenantId: string,
): Promise<AssignmentWorksheetResponse> {
  return request<AssignmentWorksheetResponse>(
    `/api/assignments/${encodeURIComponent(assignmentId)}/worksheet?tenant_id=${encodeURIComponent(tenantId)}`,
  );
}

/** Öğrencinin ödevleri ("Ödevlerim") + çözüldü durumu. */
export async function listMyAssignments(
  tenantId: string,
): Promise<MyAssignmentItem[]> {
  const r = await request<{ items: MyAssignmentItem[] }>(
    `/api/me/assignments?tenant_id=${encodeURIComponent(tenantId)}`,
  );
  return r.items;
}

/** Ödev quiz'ini çözmek için getir (cevapsız, sınıf üyesi/sahibi). */
export async function getAssignmentQuiz(
  assignmentId: string,
  tenantId: string,
): Promise<QuizPublic> {
  return request<QuizPublic>(
    `/api/assignments/${encodeURIComponent(assignmentId)}?tenant_id=${encodeURIComponent(tenantId)}`,
  );
}

/** Ödev cevaplarını gönder → puanla → öğrencinin ilerlemesine + ödeve kaydet. */
export async function submitAssignmentAttempt(
  assignmentId: string,
  body: {
    tenant_id: string;
    answers: SubmittedAnswer[];
    duration_seconds?: number;
  },
): Promise<AttemptResult> {
  return request<AttemptResult>(
    `/api/assignments/${encodeURIComponent(assignmentId)}/attempt`,
    {
      method: "POST",
      headers: tenantHeader(body.tenant_id),
      body: JSON.stringify(body),
    },
  );
}

// ---- E-posta tercihleri (KVKK opt-in) -----------------------------------

/** Kullanıcının e-posta tercihi. is_set=false → onay kartı gösterilir. */
export async function getEmailPrefs(
  tenantId: string,
): Promise<EmailPrefsResponse> {
  return request<EmailPrefsResponse>(
    `/api/me/email-prefs?tenant_id=${encodeURIComponent(tenantId)}`,
  );
}

/** E-posta tercihini kaydet (bülten + hatırlatma izni). */
export async function setEmailPrefs(
  tenantId: string,
  email: string | null,
  newsletterOptin: boolean,
): Promise<EmailPrefsResponse> {
  return request<EmailPrefsResponse>("/api/me/email-prefs", {
    method: "POST",
    headers: tenantHeader(tenantId),
    body: JSON.stringify({
      tenant_id: tenantId,
      email,
      newsletter_optin: newsletterOptin,
    }),
  });
}

// ---- Hesap silme (/api/me/account/delete) -------------------------------

export interface DeleteAccountResponse {
  deleted: boolean;
  removed: Record<string, unknown>;
  clerk_deleted: boolean;
}

/**
 * Silme isteğinin başarısız uçları farklı davranır (bkz. backend sözleşmesi):
 * 400 = onay metni yanlış · 401 = oturum yok · 502 = veri silindi ama hesap
 * kapatılamadı (tekrar denenmeli) · 503 = sunucu yapılandırması eksik.
 * Çağıran tarafın bu ayrımı yapabilmesi için `status` taşıyan özel hata sınıfı.
 */
export class DeleteAccountError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "DeleteAccountError";
    this.status = status;
  }
}

/**
 * Hesabı ve TÜM verilerini kalıcı olarak siler (GERİ ALINAMAZ). Giriş şart;
 * onay metni birebir "HESABIMI SIL" olmalı (backend de doğrular). Başarıda
 * Clerk kullanıcısı sunucu tarafında silinmiş olur → çağıran signOut() yapmalı.
 * request() yerine ham fetch: ekranın 502'yi (kısmi silinme, tekrar dene)
 * diğer hatalardan `status` üzerinden ayırt edebilmesi gerekiyor.
 */
export async function deleteAccount(): Promise<DeleteAccountResponse> {
  const auth = await authHeader();
  const res = await fetch(`${BASE}/api/me/account/delete`, {
    method: "POST",
    headers: { ...headers(), ...auth },
    body: JSON.stringify({ confirm: "HESABIMI SIL" }),
  });
  const fallback = `${res.status} ${res.statusText}`;
  let json: unknown = null;
  try {
    json = await res.json();
  } catch {
    // gövde JSON değilse status metni kalır
  }
  if (!res.ok) throw new DeleteAccountError(parseErrorDetail(json, fallback), res.status);
  return json as DeleteAccountResponse;
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
