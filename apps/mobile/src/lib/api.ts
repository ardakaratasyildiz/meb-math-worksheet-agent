/**
 * Backend (FastAPI) için ince fetch wrapper — web'deki frontend/lib/api.ts'in
 * mobil karşılığı. Aynı sözleşme: X-API-Key + (giriş varsa) Authorization Bearer.
 */
import type {
  AttemptResult,
  CreateQuizRequest,
  GenerateWorksheetRequest,
  GenerateWorksheetResponse,
  GradeInfo,
  KazanimBreakdown,
  KazanimInfo,
  ProgressResponse,
  QuestionType,
  QuizPublic,
  SolutionStep,
  SubjectSlug,
  SubmittedAnswer,
  UnitInfo,
  Worksheet,
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
  let res: Response;
  try {
    res = await fetch(`${ENV.apiUrl}${path}`, {
      ...init,
      headers: { ...baseHeaders(), ...auth, ...(init?.headers ?? {}) },
    });
  } catch {
    // fetch reddi = ağ hatası (bağlantı yok / sunucuya ulaşılamadı).
    throw new Error("İnternet bağlantısı yok. Bağlantını kontrol edip tekrar dene.");
  }
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

// ── Matematik render (LaTeX → SVG segmentleri; QuestionText tüketir) ─────────
export interface MathSegment {
  kind: "text" | "math";
  text: string; // düz metin içeriği veya matematik Unicode fallback'i
  svg: string | null; // math + render başarılıysa SVG; aksi halde null
  display: boolean; // $$...$$ (blok) mu
}

/**
 * Soru metnindeki $...$ / $$...$$ bloklarını sunucuda SVG'ye render eder →
 * segment listesi. Tenant-korumalı DEĞİL (yalnız X-API-Key) → Expo Go'da da çalışır.
 * QuestionText progressive enhancement için kullanır (başarısızsa Unicode fallback).
 */
export async function renderMath(text: string, fontSize = 16): Promise<MathSegment[]> {
  const r = await apiRequest<{ segments: MathSegment[] }>("/api/render/math", {
    method: "POST",
    body: JSON.stringify({ text, font_size: fontSize }),
  });
  return r.segments;
}

// ── Rol onboarding (RoleGate — publicMetadata.role sunucu-set) ───────────────
/**
 * Kullanıcının rolünü backend'e kaydeder (Clerk publicMetadata.role TEK SEFER).
 * Doğrulanmış oturum ŞART; tenant_id token'dan alınır (body'de gönderilmez).
 * Dev/Expo Go'da pk_test → 401 olabilir; çağıran best-effort ele almalı
 * (RoleGate ayrıca client-side unsafeMetadata'ya yazar). Dönen: kalıcılaşan rol.
 */
export async function setRole(role: "student" | "teacher" | "parent"): Promise<string> {
  const r = await apiRequest<{ role: string }>("/api/me/role", {
    method: "POST",
    body: JSON.stringify({ role }),
  });
  return r.role;
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

// ── PDF render ───────────────────────────────────────────────────────────────
function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("PDF verisi okunamadı."));
    reader.onloadend = () => {
      const dataUrl = String(reader.result); // "data:application/pdf;base64,XXXX"
      resolve(dataUrl.split(",")[1] ?? "");
    };
    reader.readAsDataURL(blob);
  });
}

/**
 * Worksheet'i backend'de PDF'e render eder → base64 döner (dosyaya yazmak için).
 * Cevap anahtarı + çözümler dahil. JSON dönmediği için apiRequest yerine ham fetch.
 */
export async function fetchWorksheetPdfBase64(
  worksheet: Worksheet,
): Promise<string> {
  const auth = await authHeader();
  const res = await fetch(`${ENV.apiUrl}/api/worksheets/render.pdf`, {
    method: "POST",
    headers: { ...baseHeaders(), ...auth },
    body: JSON.stringify({
      worksheet,
      include_answer_key: true,
      include_solutions: true,
    }),
  });
  if (!res.ok) throw new Error(`PDF oluşturulamadı: ${res.status}`);
  const blob = await res.blob();
  return blobToBase64(blob);
}

// ── Çözülebilir quiz (öğrenme döngüsü) ───────────────────────────────────────
/** Çözülebilir quiz üret + kaydet (cevapsız QuizPublic döner). Giriş şart. */
export function createQuiz(body: CreateQuizRequest): Promise<QuizPublic> {
  return apiRequest<QuizPublic>("/api/quizzes", {
    method: "POST",
    headers: body.tenant_id ? { "X-Tenant-Id": body.tenant_id } : {},
    body: JSON.stringify(body),
  });
}

/** Kullanıcının kazanım-bazlı ilerlemesi + zayıf konular + genel özet. */
export function getProgress(tenantId: string): Promise<ProgressResponse> {
  return apiRequest<ProgressResponse>(
    `/api/me/progress?tenant_id=${encodeURIComponent(tenantId)}`,
  );
}

// ── Deneme geçmişi (/api/me/attempts) ────────────────────────────────────────
/** Geçmiş listesi satırı (hafif — sorular yok). Backend AttemptHistoryItem aynası. */
export interface AttemptHistoryItem {
  attempt_id: string;
  quiz_id: string;
  title: string;
  grade?: number | null;
  topic_id: string;
  difficulty: string;
  score: number;
  total: number;
  completed_at: string;
  has_detail: boolean;
}

/** Geçmiş detayında tek soru: doğru cevap + çözüm + kullanıcının cevabı. */
export interface AttemptReviewItem {
  number: number;
  question: string;
  question_type: QuestionType;
  kazanim_kod: string;
  options?: string[] | null;
  is_correct: boolean;
  correct_answer: string;
  correct_index?: number | null;
  solution_steps: string | SolutionStep[];
  submitted?: SubmittedAnswer | null;
}

/** Geçmiş bir denemenin tam gözden geçirmesi. Backend AttemptDetail aynası. */
export interface AttemptDetail {
  attempt_id: string;
  quiz_id: string;
  title: string;
  grade?: number | null;
  topic_id: string;
  difficulty: string;
  score: number;
  total: number;
  duration_seconds?: number | null;
  completed_at: string;
  per_kazanim: KazanimBreakdown[];
  review: AttemptReviewItem[];
  has_detail: boolean;
}

/** Kullanıcının geçmiş çözüm denemeleri — en yeni önce. */
export async function listAttempts(
  tenantId: string,
  limit = 50,
): Promise<AttemptHistoryItem[]> {
  const r = await apiRequest<{ items: AttemptHistoryItem[] }>(
    `/api/me/attempts?tenant_id=${encodeURIComponent(tenantId)}&limit=${limit}`,
  );
  return r.items;
}

/** Bir denemenin tam gözden geçirmesi (soru + doğru cevap + senin cevabın). */
export function getAttemptDetail(
  attemptId: string,
  tenantId: string,
): Promise<AttemptDetail> {
  return apiRequest<AttemptDetail>(
    `/api/me/attempts/${encodeURIComponent(attemptId)}?tenant_id=${encodeURIComponent(tenantId)}`,
  );
}

/** Cevapları gönder → sunucuda puanlanır → sonuç + kazanım kırılımı. */
export function submitAttempt(
  quizId: string,
  body: { tenant_id: string; answers: SubmittedAnswer[]; duration_seconds?: number },
): Promise<AttemptResult> {
  return apiRequest<AttemptResult>(
    `/api/quizzes/${encodeURIComponent(quizId)}/attempt`,
    { method: "POST", body: JSON.stringify(body) },
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
