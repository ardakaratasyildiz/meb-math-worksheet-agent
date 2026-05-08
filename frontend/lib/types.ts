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
  | "oruntu_sekil";

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
}

export interface GenerateWorksheetResponse {
  worksheet: Worksheet;
  metadata: WorksheetMetadata;
}
