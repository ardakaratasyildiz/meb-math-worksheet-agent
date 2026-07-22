// Backend Pydantic schema'larının TypeScript karşılığı.
// FastAPI /openapi.json'dan otomatik üretilebilir; şimdilik elle senkron.

export type Difficulty = "kolay" | "orta" | "zor";

export type QuestionType =
  | "islem"
  | "sozel_problem"
  | "kavram_sorusu"
  | "akil_yurutme"
  | "modelleme"
  | "gunluk_hayat"
  | "salt_islem"
  | "tablo_sorusu"
  | "gorsel_geometri"
  | "grafik_okuma"
  | "oruntu_sekil"
  | "coktan_secmeli"
  | "bosluk_doldurma"
  | "dogru_yanlis"
  | "eslestirme"
  | "siralama";

export type DifficultyMode = "single" | "mixed" | "progressive";

// Soru tipi grupları — kullanıcıya UI'da 3 switch olarak gösterilir (açık uçlu,
// çoktan seçmeli, diğer soru tipleri). "visual" grubu kullanıcıya gösterilmez;
// sunucu konuya göre otomatik ekler (bkz. GenerateForm flattenTypeGroups).
// Backend bu listeyi `question_types` alanı olarak alır; her grup kapatıldıkça
// listeden çıkar.
export const QUESTION_TYPE_GROUPS = {
  open_ended: [
    "islem",
    "sozel_problem",
    "kavram_sorusu",
    "akil_yurutme",
    "modelleme",
    "gunluk_hayat",
  ] satisfies QuestionType[],
  visual: [
    "salt_islem",
    "tablo_sorusu",
    "gorsel_geometri",
    "grafik_okuma",
    "oruntu_sekil",
  ] satisfies QuestionType[],
  // Çoktan seçmeli, kullanıcı isteği üzerine ayrı bir grup (tek başına açılıp
  // kapatılabilsin). Kalan format tipleri "other_format" altında toplanır.
  multiple_choice: ["coktan_secmeli"] satisfies QuestionType[],
  other_format: [
    "bosluk_doldurma",
    "dogru_yanlis",
    "eslestirme",
    "siralama",
  ] satisfies QuestionType[],
} as const;

export type EducationLevel = "İlkokul" | "Ortaokul";

export interface GradeInfo {
  id: number;
  name: string;
  level: EducationLevel;
}

export interface TopicInfo {
  id: string;
  name: string;
  description: string;
  kazanim_count: number;
}

// MEB TYMM ünite (tema) — yeni seçim akışının dropdown öğesi.
export interface UnitInfo {
  unit_id: string;
  name: string;
  no: number;
  kazanim_count: number;
}

export interface KazanimInfo {
  kod: string;
  metin: string;
}

export interface SolutionStep {
  step_no: number;
  description: string;
  computation: string | null;
}

export interface Question {
  number: number;
  question: string;
  answer: string;
  solution_steps: string | SolutionStep[];
  kazanim_kod: string;
  question_type: QuestionType;
  // Yapısal cevap alanları (Adım 0 — site içi çözme). Yalnız çözülebilir
  // tiplerde dolar; PDF/açık-uçlu akışta null. Eski kod bunları yok sayar.
  options?: string[] | null;
  correct_index?: number | null;
  blanks?: string[] | null;
  correct_bool?: boolean | null;
}

export interface AnswerKeyEntry {
  number: number;
  answer: string;
}

export interface Worksheet {
  title: string;
  grade: number;
  topic: string;
  difficulty: Difficulty;
  question_count: number;
  questions: Question[];
  answer_key: AnswerKeyEntry[];
}

export interface GenerationTrace {
  few_shot_source: string;
  few_shot_count: number;
  textbook_count: number;
  retrieval_avg_distance: number | null;
  model_used: string;
  provider: string;
  temperature: number;
  final_temperature: number | null;
  seed: number;
  retry_rounds: number;
  dedup_rejected_string: number;
  dedup_rejected_semantic: number;
  math_verifier_rejected: number;
  critic_rejected: number;
  requested_count: number;
  delivered_count: number;
  cache_hit: boolean;
  prompt_tokens: number;
  completion_tokens: number;
  estimated_cost_usd: number;
}

export interface WorksheetMetadata {
  generated_at: string;
  model: string;
  curriculum: string;
  trace: GenerationTrace | null;
}

// Ders (subject) ekseni — varsayılan matematik. Yeni dersler kalite kapısını
// (NEXT_PUBLIC_ENABLED_SUBJECTS listesi, bkz. lib/subjects.ts) geçene kadar UI'da gizli.
export type Subject =
  | "matematik"
  | "fen"
  | "turkce"
  | "sosyal"
  | "ingilizce";

export interface GenerateWorksheetRequest {
  grade: number;
  subject?: Subject; // varsayılan matematik (backend default); fen flag arkasında
  unit_id?: string | null; // yeni MEB ünite akışı — unit_id veya topic_id zorunlu
  topic_id?: string | null;
  kazanim_kod?: string | null;
  difficulty: Difficulty;
  question_count: number;
  tenant_id?: string | null;
  // Sprint 12-A toggle paketi — UI'dan seçilebilir kontroller.
  question_types?: QuestionType[] | null;
  difficulty_mode?: DifficultyMode;
  include_answer_key?: boolean;
  include_solutions?: boolean;
}

export interface GenerateWorksheetResponse {
  worksheet: Worksheet;
  metadata: WorksheetMetadata;
}

// ── Çözülebilir quiz + puanlama (öğrenme döngüsü) ──────────────────────────

export interface CreateQuizRequest {
  grade: number;
  subject?: Subject; // varsayılan matematik
  unit_id?: string | null; // yeni MEB ünite akışı — unit_id veya topic_id zorunlu
  topic_id?: string | null;
  kazanim_kod?: string | null;
  difficulty: Difficulty;
  question_count: number;
  tenant_id: string;
  // Gelişmiş (opsiyonel): çözülebilir tip alt kümesi + zorluk modu.
  question_types?: QuestionType[] | null;
  difficulty_mode?: DifficultyMode;
}

// Çözme için soru — CEVAPSIZ. options = çoktan seçmeli şıkları (cevap değil);
// blank_count = boşluk doldurmada kaç giriş gerektiği.
export interface QuizQuestionPublic {
  number: number;
  question: string;
  question_type: QuestionType;
  kazanim_kod: string;
  options?: string[] | null;
  blank_count?: number | null;
  // Açık uçlu (sozel_problem) öz-değerlendirmede "cevabı gör" ile gösterilir.
  reveal_answer?: string | null;
}

export interface QuizPublic {
  id: string;
  title: string;
  grade: number;
  topic_id: string;
  difficulty: Difficulty;
  question_count: number;
  questions: QuizQuestionPublic[];
  created_at: string;
  // "quiz" (Çöz&Geliş — açık uçlu öz-değerlendirme) | "worksheet" (sınıf worksheet
  // ödevi — yapılandırılmamış tipler metin kutusuyla çözülür, sunucu eşleştirir).
  answer_mode?: "quiz" | "worksheet";
}

/** Sahibe quiz önizleme — CEVAPLI tam sorular (öğretmen inceleme/yenileme). */
export interface QuizReview {
  id: string;
  title: string;
  grade: number;
  topic_id: string;
  difficulty: Difficulty;
  question_count: number;
  questions: Question[];
  created_at: string;
}

export interface SubmittedAnswer {
  number: number;
  selected_index?: number | null;
  bool_answer?: boolean | null;
  texts?: string[] | null;
}

export interface QuestionResult {
  number: number;
  is_correct: boolean;
  kazanim_kod: string;
  question_type: QuestionType;
  correct_answer: string;
  solution_steps: string | SolutionStep[];
  options?: string[] | null;
  correct_index?: number | null;
}

export interface KazanimBreakdown {
  kazanim_kod: string;
  correct: number;
  total: number;
}

export interface AttemptResult {
  attempt_id: string;
  quiz_id: string;
  score: number;
  total: number;
  duration_seconds?: number | null;
  per_kazanim: KazanimBreakdown[];
  results: QuestionResult[];
  completed_at: string;
}

// ── Paylaşım (Faz 3) ─────────────────────────────────────────────────────────

export interface CreateShareResponse {
  share_code: string;
  share_url: string; // görece: /q/{code}
}

// Paylaşılan quiz çözümü — tenant_id opsiyonel (misafir login'siz çözer).
export interface SharedAttemptRequest {
  tenant_id?: string | null;
  solver_label?: string | null;
  answers: SubmittedAnswer[];
  duration_seconds?: number | null;
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

// ── Sınıf / Ödev (Faz 3.5) ───────────────────────────────────────────────────

export interface ClassroomSummary {
  id: string;
  name: string;
  role: "owner" | "student";
  member_count: number;
  created_at: string;
  join_code?: string | null; // yalnız sahip
}

export interface ClassroomsResponse {
  teaching: ClassroomSummary[]; // sahip olunan
  enrolled: ClassroomSummary[]; // katılınan
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
  due_at?: string | null; // son teslim (ISO); yoksa null
  assignment_type?: "quiz" | "pdf";
}

export interface AssignmentWorksheetResponse {
  title: string;
  worksheet: Worksheet;
}

export interface ClassroomDetail {
  id: string;
  name: string;
  is_owner: boolean;
  member_count: number;
  created_at: string;
  join_code?: string | null; // yalnız sahip
  members: ClassroomMember[]; // yalnız sahip için dolu
  assignments: AssignmentSummary[]; // sınıfa atanmış ödevler
}

export interface JoinClassroomResponse {
  classroom_id: string;
  name: string;
}

// E-posta tercihi (KVKK opt-in). is_set=false → onay kartı gösterilir.
export interface EmailPrefsResponse {
  is_set: boolean;
  newsletter_optin: boolean;
  email?: string | null;
}

// Öğrencinin ödevi ("Ödevlerim").
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
  due_at?: string | null; // son teslim (ISO); yoksa null
  assignment_type?: "quiz" | "pdf";
}

export interface MyAssignmentsResponse {
  items: MyAssignmentItem[];
}

// Öğretmenin ödev atamak için seçtiği kendi quiz'i.
export interface MyQuizItem {
  id: string;
  title: string;
  grade?: number | null;
  topic_id: string;
  difficulty: string;
  created_at: string;
}

export interface MyQuizzesResponse {
  items: MyQuizItem[];
}

// Öğretmen ödev sonuç panosu (sınıf roster'ı: çözen/çözmeyen).
export interface AssignmentResultItem {
  student_tenant_id: string;
  display_name: string;
  solved: boolean;
  score?: number | null;
  total?: number | null;
  completed_at?: string | null;
}

export interface TeachingOverviewItem {
  classroom_id: string;
  classroom_name: string;
  assignment_id: string;
  title: string;
  assignment_type?: "quiz" | "pdf";
  due_at?: string | null;
  created_at: string;
  member_count: number;
  solved_count: number;
}

export interface AssignmentResultsResponse {
  title: string;
  question_count: number;
  member_count: number;
  solved_count: number;
  items: AssignmentResultItem[];
}

// ── Quiz geçmişi ───────────────────────────────────────────────────────────

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

// ── İlerleme panosu ────────────────────────────────────────────────────────

export interface KazanimProgress {
  kazanim_kod: string;
  correct: number;
  total: number;
  ratio: number;
  last_seen_at: string;
  // Ders ekseni — backend kazanim_kod'dan çözer (subject_resolve). Eski yanıtlarda
  // olmayabilir → opsiyonel; okuyan taraf matematik'e düşer.
  subject?: Subject;
  topic_name?: string;
  grade?: number | null;
}

export interface ProgressSummary {
  total_answered: number;
  total_correct: number;
  accuracy: number;
  kazanim_count: number;
  quizzes_solved: number;
}

export interface AttemptSummary {
  completed_at: string;
  score: number;
  total: number;
  ratio: number;
}

export interface DailyTrendPoint {
  date: string;
  score: number;
  total: number;
  ratio: number;
  attempts: number;
}

export interface ProgressResponse {
  summary: ProgressSummary;
  mastery: KazanimProgress[];
  weak: KazanimProgress[];
  recent: AttemptSummary[];
  daily_trend?: DailyTrendPoint[];
}

// AI haftalık çalışma programı (WS-6a)
export interface StudyPlanDay {
  day_no: number;
  weekday?: string;
  kind?: "focus" | "review" | "mixed";
  title: string;
  subject?: Subject;
  grade?: number | null;
  kazanim_kod?: string;
  topic_name?: string;
  question_count: number;
  tip?: string;
  ratio?: number;
}

export interface StudyPlanResponse {
  summary: string;
  days: StudyPlanDay[];
  ai_generated: boolean;
  created_at?: string;
}

// Veli ↔ öğrenci bağı (WS-6b)
export interface ChildItem {
  student_id: string;
  label: string;
  linked_at: string;
}

// ── Oyunlaştırma ───────────────────────────────────────────────────────────

export interface GamificationResponse {
  xp: number;
  level: number;
  xp_in_level: number;
  xp_for_next: number;
  streak_current: number;
  streak_longest: number;
  total_active_days: number;
}

export type BadgeTier = "bronze" | "silver" | "gold";

export interface TopicBadge {
  topicId: string;
  topicName: string;
  tier: BadgeTier;
  ratio: number;
  total: number;
}
