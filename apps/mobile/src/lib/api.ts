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

// ── Entitlements / abonelik (mobil paywall + gating; GÖSTERİM için) ──────────
export interface Quota {
  /** Aylık kağıt kotası; null = kotasız (fair-use/anonim). */
  limit: number | null;
  used: number;
  remaining: number | null;
}
export interface Entitlements {
  plan: "free" | "trial" | "pro" | "pro-plus";
  is_premium: boolean;
  status: string | null; // trialing | active | past_due | canceled | expired
  trial_end: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  quota: Quota;
}

/**
 * Kullanıcının efektif planı + kotası + abonelik durumu (backend karar verir).
 * Tenant-korumalı → Expo Go pk_test'te 401 olabilir; çağıran best-effort ele almalı
 * (useEntitlements free'ye düşer). Gating yine SUNUCUDA enforce edilir; bu yalnız gösterim.
 */
export function getEntitlements(tenantId: string): Promise<Entitlements> {
  return apiRequest<Entitlements>(
    `/api/me/entitlements?tenant_id=${encodeURIComponent(tenantId)}`,
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
  opts: { includeAnswerKey?: boolean; includeSolutions?: boolean } = {},
): Promise<string> {
  const auth = await authHeader();
  const res = await fetch(`${ENV.apiUrl}/api/worksheets/render.pdf`, {
    method: "POST",
    headers: { ...baseHeaders(), ...auth },
    body: JSON.stringify({
      worksheet,
      include_answer_key: opts.includeAnswerKey ?? true,
      include_solutions: opts.includeSolutions ?? true,
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

// ── Haftalık çalışma programı (WS-6a; /api/me/study-plan) ─────────────────────
export interface StudyPlanDay {
  day_no: number;
  weekday: string;
  kind: string; // focus (eksik) | review (tekrar) | mixed (karışık)
  title: string;
  subject: string;
  grade?: number | null;
  kazanim_kod: string;
  topic_name: string;
  question_count: number;
  tip: string;
  ratio: number; // mevcut doğruluk 0-1
}
export interface StudyPlanResponse {
  summary: string;
  days: StudyPlanDay[];
  ai_generated: boolean;
  created_at: string; // ISO; boşsa henüz plan yok
}

/** Kayıtlı haftalık programı getirir (LLM YOK, hızlı). created_at boş = plan yok. */
export function getStudyPlan(tenantId: string): Promise<StudyPlanResponse> {
  return apiRequest<StudyPlanResponse>(
    `/api/me/study-plan?tenant_id=${encodeURIComponent(tenantId)}`,
  );
}

/** Programı (yeniden) üretir + kaydeder (LLM çağrısı — birkaç sn sürebilir). */
export function createStudyPlan(tenantId: string): Promise<StudyPlanResponse> {
  return apiRequest<StudyPlanResponse>(
    `/api/me/study-plan?tenant_id=${encodeURIComponent(tenantId)}`,
    { method: "POST" },
  );
}

// ── Quiz paylaşımı + QR (viral döngü; /api/quizzes/{id}/share, /api/me/shares) ─
export interface CreateShareResponse {
  share_code: string;
  share_url: string; // göreli: /q/{code} — tam URL için origin eklenir
}
export interface ShareSummary {
  share_id: string;
  share_code: string;
  quiz_id: string;
  title: string;
  grade?: number | null;
  topic_id: string;
  created_at: string;
  attempt_count: number;
  avg_score_pct?: number | null;
}
export interface ShareResultItem {
  solver_label?: string | null;
  score: number;
  total: number;
  duration_seconds?: number | null;
  completed_at: string;
}
export interface ShareResultsResponse {
  title: string;
  question_count: number;
  items: ShareResultItem[];
}

/** Quiz için paylaşım linki oluştur (idempotent; yalnız sahibi). Giriş şart. */
export function createShare(quizId: string, tenantId: string): Promise<CreateShareResponse> {
  return apiRequest<CreateShareResponse>(
    `/api/quizzes/${encodeURIComponent(quizId)}/share?tenant_id=${encodeURIComponent(tenantId)}`,
    { method: "POST", headers: { "X-Tenant-Id": tenantId } },
  );
}

/** Kullanıcının oluşturduğu paylaşımlar + çözülme sayısı + ort. skor (pano). */
export async function listMyShares(tenantId: string): Promise<ShareSummary[]> {
  const r = await apiRequest<{ items: ShareSummary[] }>(
    `/api/me/shares?tenant_id=${encodeURIComponent(tenantId)}`,
  );
  return r.items;
}

/** Bir paylaşımın sonuç panosu — kim çözdü, kaç doğru (sahip-only). */
export function getShareResults(shareId: string, tenantId: string): Promise<ShareResultsResponse> {
  return apiRequest<ShareResultsResponse>(
    `/api/me/shares/${encodeURIComponent(shareId)}/results?tenant_id=${encodeURIComponent(tenantId)}`,
  );
}

/** Web origin — paylaşım linkleri buradan servis edilir (login'siz /q/{code}). */
export const WEB_ORIGIN = "https://soruatolyesi.com";

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

// ── Veli ↔ çocuk bağlama (/api/me) ───────────────────────────────────────────
/** Öğrencinin veli takip kodu (yoksa üretilir, kalıcı). Veli bu kodla bağlanır. */
export async function getParentCode(tenantId: string): Promise<string> {
  const r = await apiRequest<{ code: string }>("/api/me/parent-code", {
    method: "POST",
    body: JSON.stringify({ tenant_id: tenantId }),
  });
  return r.code;
}

/** Veli bir öğrenciyi takip koduyla bağlar. */
export function linkChild(
  tenantId: string,
  code: string,
  childLabel?: string,
): Promise<{ student_id: string; ok: boolean }> {
  return apiRequest("/api/me/link-child", {
    method: "POST",
    body: JSON.stringify({ tenant_id: tenantId, code, child_label: childLabel ?? null }),
  });
}

export interface ChildItem {
  student_id: string;
  label: string;
  linked_at: string;
}

/** Velinin bağlı olduğu öğrenciler. */
export async function listChildren(tenantId: string): Promise<ChildItem[]> {
  const r = await apiRequest<{ items: ChildItem[] }>(
    `/api/me/children?tenant_id=${encodeURIComponent(tenantId)}`,
  );
  return r.items;
}

/** Bağlı bir çocuğun ilerlemesi (salt-okunur; kendi progress'iyle aynı şekil). */
export function getChildProgress(
  tenantId: string,
  studentId: string,
): Promise<ProgressResponse> {
  return apiRequest<ProgressResponse>(
    `/api/me/children/${encodeURIComponent(studentId)}/progress?tenant_id=${encodeURIComponent(tenantId)}`,
  );
}

// ── Öğretmen sınıf / ödev (/api/classrooms, /api/assignments, /api/me) ────────
export interface ClassroomSummary {
  id: string;
  name: string;
  role: string; // 'owner' | 'student'
  member_count: number;
  created_at: string;
  join_code?: string | null;
}
export interface ClassroomMember {
  student_tenant_id: string;
  display_name: string;
  joined_at: string;
}
export interface AssignmentSummary {
  id: string;
  quiz_id: string;
  title: string;
  created_at: string;
  due_at?: string | null;
  assignment_type: string; // 'quiz' | 'pdf'
}
export interface ClassroomDetail {
  id: string;
  name: string;
  is_owner: boolean;
  member_count: number;
  created_at: string;
  join_code?: string | null;
  members: ClassroomMember[];
  assignments: AssignmentSummary[];
}
export interface MyQuizItem {
  id: string;
  title: string;
  grade?: number | null;
  topic_id: string;
  difficulty: string;
  created_at: string;
}
export interface AssignmentResultItem {
  student_tenant_id: string;
  display_name: string;
  solved: boolean;
  score?: number | null;
  total?: number | null;
  completed_at?: string | null;
}
export interface AssignmentResultsResponse {
  title: string;
  question_count: number;
  member_count: number;
  solved_count: number;
  items: AssignmentResultItem[];
}

/** Kullanıcının sınıfları: sahip olunan (teaching) + katılınan (enrolled). */
export function listClassrooms(
  tenantId: string,
): Promise<{ teaching: ClassroomSummary[]; enrolled: ClassroomSummary[] }> {
  return apiRequest(`/api/classrooms?tenant_id=${encodeURIComponent(tenantId)}`);
}

/** Yeni sınıf oluştur (öğretmen). Katılma kodunu içeren detay döner. */
export function createClassroom(tenantId: string, name: string): Promise<ClassroomDetail> {
  return apiRequest<ClassroomDetail>("/api/classrooms", {
    method: "POST",
    body: JSON.stringify({ tenant_id: tenantId, name }),
  });
}

/** Sınıf detayı (sahip: kod + üyeler + ödevler). */
export function getClassroom(id: string, tenantId: string): Promise<ClassroomDetail> {
  return apiRequest<ClassroomDetail>(
    `/api/classrooms/${encodeURIComponent(id)}?tenant_id=${encodeURIComponent(tenantId)}`,
  );
}

/** Sınıfı sil (yalnız sahibi). */
export function deleteClassroom(id: string, tenantId: string): Promise<{ ok: boolean }> {
  return apiRequest(
    `/api/classrooms/${encodeURIComponent(id)}?tenant_id=${encodeURIComponent(tenantId)}`,
    { method: "DELETE" },
  );
}

/** Sınıfa bir quiz'i ödev olarak ata (yalnız sahibi + kendi quiz'i). */
export function assignQuiz(
  classroomId: string,
  tenantId: string,
  quizId: string,
  dueDate?: string | null,
): Promise<{ id: string; created_at: string }> {
  return apiRequest(`/api/classrooms/${encodeURIComponent(classroomId)}/assignments`, {
    method: "POST",
    body: JSON.stringify({ tenant_id: tenantId, quiz_id: quizId, due_date: dueDate ?? null }),
  });
}

/** Öğretmenin ödev atamak için seçebileceği kendi quiz'leri (hafif meta). */
export async function listMyQuizzes(tenantId: string): Promise<MyQuizItem[]> {
  const r = await apiRequest<{ items: MyQuizItem[] }>(
    `/api/me/quizzes?tenant_id=${encodeURIComponent(tenantId)}`,
  );
  return r.items;
}

/** Ödevin sonuç panosu (sınıf roster'ı: çözen/çözmeyen). Yalnız sınıf sahibi. */
export function getAssignmentResults(
  assignmentId: string,
  tenantId: string,
): Promise<AssignmentResultsResponse> {
  return apiRequest<AssignmentResultsResponse>(
    `/api/assignments/${encodeURIComponent(assignmentId)}/results?tenant_id=${encodeURIComponent(tenantId)}`,
  );
}

/** Öğretmen: bir öğrencinin ödevdeki denemesini soru-soru görür (yalnız sınıf sahibi). */
export function getStudentAttemptDetail(
  assignmentId: string,
  studentId: string,
  tenantId: string,
): Promise<AttemptDetail> {
  return apiRequest<AttemptDetail>(
    `/api/assignments/${encodeURIComponent(assignmentId)}/attempts/${encodeURIComponent(studentId)}?tenant_id=${encodeURIComponent(tenantId)}`,
  );
}

/** Öğrenci sınıftan ayrılır (üyeliğini siler). */
export function leaveClassroom(id: string, tenantId: string): Promise<{ ok: boolean }> {
  return apiRequest(
    `/api/classrooms/${encodeURIComponent(id)}/leave?tenant_id=${encodeURIComponent(tenantId)}`,
    { method: "POST" },
  );
}

// ── Öğrenci: sınıfa katıl + ödevler (/api/classrooms/join, /api/me, /api/assignments) ──
/** Öğrenci katılma koduyla sınıfa katılır (görünen ad öğretmene gösterilir). */
export function joinClassroom(
  tenantId: string,
  code: string,
  displayName: string,
): Promise<{ classroom_id: string; name: string }> {
  return apiRequest("/api/classrooms/join", {
    method: "POST",
    body: JSON.stringify({ tenant_id: tenantId, code, display_name: displayName }),
  });
}

export interface MyAssignmentItem {
  assignment_id: string;
  classroom_id: string;
  classroom_name: string;
  quiz_id: string;
  title: string;
  created_at: string;
  solved: boolean;
  score?: number | null;
  total?: number | null;
  due_at?: string | null;
  assignment_type: string; // 'quiz' | 'pdf'
}

/** Öğrencinin sınıflarındaki ödevleri (çözülen durumu dahil). */
export async function listMyAssignments(tenantId: string): Promise<MyAssignmentItem[]> {
  const r = await apiRequest<{ items: MyAssignmentItem[] }>(
    `/api/me/assignments?tenant_id=${encodeURIComponent(tenantId)}`,
  );
  return r.items;
}

/** Ödevi çözmek için getir — CEVAPSIZ (quiz + PDF ödevi). */
export function getAssignment(assignmentId: string, tenantId: string): Promise<QuizPublic> {
  return apiRequest<QuizPublic>(
    `/api/assignments/${encodeURIComponent(assignmentId)}?tenant_id=${encodeURIComponent(tenantId)}`,
  );
}

/** Ödev cevaplarını gönder → sunucuda puanla → sonuç + kazanım kırılımı. */
export function submitAssignmentAttempt(
  assignmentId: string,
  body: { tenant_id: string; answers: SubmittedAnswer[]; duration_seconds?: number },
): Promise<AttemptResult> {
  return apiRequest<AttemptResult>(
    `/api/assignments/${encodeURIComponent(assignmentId)}/attempt`,
    { method: "POST", body: JSON.stringify(body) },
  );
}

/** PDF ödevinin worksheet'i (öğrenci istemcide PDF'e render/paylaş eder). */
export async function getAssignmentWorksheet(
  assignmentId: string,
  tenantId: string,
): Promise<Worksheet> {
  const r = await apiRequest<{ title: string; worksheet: Worksheet }>(
    `/api/assignments/${encodeURIComponent(assignmentId)}/worksheet?tenant_id=${encodeURIComponent(tenantId)}`,
  );
  return r.worksheet;
}

/** Backend uyandırma ping'i (Render free-tier cold start). Hata yutulur. */
export function pingHealth(): void {
  try {
    void fetch(`${ENV.apiUrl}/healthz`, { method: "GET" }).catch(() => {});
  } catch {
    /* no-op */
  }
}
