/**
 * Çözülebilir quiz + puanlama tipleri (öğrenme döngüsü) — backend ile hizalı.
 */
import type { SubjectSlug } from "./subjects";
import type { Difficulty, DifficultyMode, QuestionType, SolutionStep } from "./worksheet";

export interface CreateQuizRequest {
  grade: number;
  subject?: SubjectSlug;
  unit_id?: string | null;
  topic_id?: string | null;
  kazanim_kod?: string | null;
  difficulty: Difficulty;
  question_count: number;
  tenant_id: string; // quiz üretimi giriş ister (worksheet'in aksine)
  question_types?: QuestionType[] | null;
  difficulty_mode?: DifficultyMode;
}

/** Çözme için soru — CEVAPSIZ. options = çoktan seçmeli şıkları; blank_count = kaç boşluk. */
export interface QuizQuestionPublic {
  number: number;
  question: string;
  question_type: QuestionType;
  kazanim_kod: string;
  options?: string[] | null;
  blank_count?: number | null;
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
  answer_mode?: "quiz" | "worksheet";
}

export interface SubmittedAnswer {
  number: number;
  selected_index?: number | null;
  bool_answer?: boolean | null;
  texts?: string[] | null;
}

export interface KazanimBreakdown {
  kazanim_kod: string;
  correct: number;
  total: number;
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
