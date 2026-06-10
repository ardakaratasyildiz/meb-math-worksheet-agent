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

// Soru tipi grupları — UI'da 3 switch olarak gösterilir. Backend bu listeyi
// `question_types` alanı olarak alır; her grup kapatıldıkça listeden çıkar.
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
  format: [
    "coktan_secmeli",
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

export interface GenerateWorksheetRequest {
  grade: number;
  topic_id: string;
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
  topic_id: string;
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

export interface ProgressResponse {
  summary: ProgressSummary;
  mastery: KazanimProgress[];
  weak: KazanimProgress[];
  recent: AttemptSummary[];
}
