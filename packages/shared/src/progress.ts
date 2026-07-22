/**
 * Öğrenci ilerleme panosu tipleri — /api/me/progress yanıtı.
 */
import type { SubjectSlug } from "./subjects";

export interface KazanimProgress {
  kazanim_kod: string;
  correct: number;
  total: number;
  ratio: number;
  last_seen_at: string;
  subject?: SubjectSlug;
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
