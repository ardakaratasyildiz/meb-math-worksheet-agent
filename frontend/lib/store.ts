/**
 * Generate sayfasının form + sonuç state'i.
 * localStorage'a son seçilen sınıf/konu/zorluk persistlenir → öğretmen
 * aynı sınıfla çalışırken tekrar tekrar seçim yapmasın.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";

import type {
  Difficulty,
  DifficultyMode,
  GenerateWorksheetResponse,
} from "./types";

export type TypeGroupKey = "open_ended" | "visual" | "format";

export interface FormState {
  grade: number;
  topicId: string;
  kazanimKod: string | null; // null = tüm kazanımlar (auto)
  difficulty: Difficulty;
  questionCount: number;
  // Sprint 12-A toggle paketi
  typeGroups: Record<TypeGroupKey, boolean>;
  difficultyMode: DifficultyMode;
  includeAnswerKey: boolean;
  includeSolutions: boolean;
}

interface GenerateStore extends FormState {
  status: "idle" | "loading" | "success" | "error";
  error: string | null;
  result: GenerateWorksheetResponse | null;

  setForm: (patch: Partial<FormState>) => void;
  startGenerate: () => void;
  setSuccess: (r: GenerateWorksheetResponse) => void;
  setError: (e: string) => void;
  reset: () => void;
}

const DEFAULT_FORM: FormState = {
  grade: 5,
  topicId: "cebir",
  kazanimKod: null,
  difficulty: "orta",
  questionCount: 10,
  // Varsayılan: 3 grup da AÇIK, tek zorluk, hem cevap anahtarı hem çözüm dahil.
  typeGroups: { open_ended: true, visual: true, format: true },
  difficultyMode: "single",
  includeAnswerKey: true,
  includeSolutions: true,
};

export const useGenerateStore = create<GenerateStore>()(
  persist(
    (set) => ({
      ...DEFAULT_FORM,
      status: "idle",
      error: null,
      result: null,
      setForm: (patch) => set((s) => ({ ...s, ...patch })),
      startGenerate: () =>
        set({ status: "loading", error: null, result: null }),
      setSuccess: (r) => set({ status: "success", result: r, error: null }),
      setError: (e) => set({ status: "error", error: e }),
      reset: () => set({ status: "idle", result: null, error: null }),
    }),
    {
      name: "meb-generate-form",
      partialize: (s) => ({
        grade: s.grade,
        topicId: s.topicId,
        kazanimKod: s.kazanimKod,
        difficulty: s.difficulty,
        questionCount: s.questionCount,
        typeGroups: s.typeGroups,
        difficultyMode: s.difficultyMode,
        includeAnswerKey: s.includeAnswerKey,
        includeSolutions: s.includeSolutions,
      }),
    },
  ),
);
