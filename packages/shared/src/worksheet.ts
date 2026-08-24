/**
 * Çalışma kağıdı üretim tipleri — backend Pydantic şemalarının TS karşılığı.
 * Web frontend/lib/types.ts ile hizalı (tek kaynağa doğru; web sonra buna geçecek).
 */
import type { SubjectSlug } from "./subjects";

export type Difficulty = "kolay" | "orta" | "zor";
export type DifficultyMode = "single" | "mixed" | "progressive";

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
  | "siralama"
  // Sözel dersler (Türkçe / Sosyal / İngilizce) — backend enum'unda vardı,
  // istemci tipinde YOKTU: bu yüzden mobil/web soru-tipi filtreleri yalnız
  // matematik tiplerini gönderebiliyordu (bkz. SUBJECT_TYPE_GROUPS).
  | "okuma_pasaji"
  | "diyalog_tamamlama"
  | "kelime_bilgisi"
  | "harita_yorumlama"
  | "kaynak_metin"
  | "dil_bilgisi"
  | "yazim_noktalama"
  | "gorsel_yorumlama";

export type EducationLevel = "İlkokul" | "Ortaokul";

export interface GradeInfo {
  id: number;
  name: string;
  level: EducationLevel;
}

/** MEB TYMM ünite (tema). */
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

export interface WorksheetMetadata {
  generated_at: string;
  model: string;
  curriculum: string;
}

export interface GenerateWorksheetRequest {
  grade: number;
  subject?: SubjectSlug; // varsayılan matematik
  unit_id?: string | null; // unit_id veya topic_id zorunlu
  topic_id?: string | null;
  kazanim_kod?: string | null;
  difficulty: Difficulty;
  question_count: number;
  tenant_id?: string | null;
  question_types?: QuestionType[] | null;
  difficulty_mode?: DifficultyMode;
  include_answer_key?: boolean;
  include_solutions?: boolean;
}

export interface GenerateWorksheetResponse {
  worksheet: Worksheet;
  metadata: WorksheetMetadata;
}
