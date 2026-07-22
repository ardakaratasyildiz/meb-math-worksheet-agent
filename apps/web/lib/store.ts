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
  Question,
  Subject,
} from "./types";

export type TypeGroupKey =
  | "open_ended"
  | "visual"
  | "multiple_choice"
  | "other_format";

export interface FormState {
  subject: Subject; // ders — varsayılan matematik (fen flag arkasında)
  grade: number;
  unitId: string | null; // MEB TYMM ünite (tema); null = henüz seçilmedi (ilk üniteye düşer)
  kazanimKod: string | null; // null = tüm kazanımlar (auto)
  difficulty: Difficulty;
  questionCount: number;
  // Sprint 12-A toggle paketi
  typeGroups: Record<TypeGroupKey, boolean>;
  difficultyMode: DifficultyMode;
  includeAnswerKey: boolean;
  includeSolutions: boolean;
  // White-label PDF üst bilgisi — bir kez girilir, kalıcı (kurum/öğretmen + alt satır).
  brandName: string;
  brandSubtitle: string;
  // Opsiyonel logo (base64 data URL) — PDF header'a basılır. Cihazda saklanır.
  brandLogo: string;
}

interface GenerateStore extends FormState {
  status: "idle" | "loading" | "success" | "error";
  error: string | null;
  result: GenerateWorksheetResponse | null;
  // SSE streaming sırasında gelen soru sayısı — canlı ilerleme göstergesi için.
  streamedCount: number;

  setForm: (patch: Partial<FormState>) => void;
  startGenerate: () => void;
  setStreamedCount: (n: number) => void;
  setSuccess: (r: GenerateWorksheetResponse) => void;
  setError: (e: string) => void;
  // "Soruyu Değiştir": numarası verilen soruyu yenisiyle değiştirir (numara korunur)
  // ve cevap anahtarı girişini günceller.
  replaceQuestion: (number: number, q: Question) => void;
  reset: () => void;
}

const DEFAULT_FORM: FormState = {
  subject: "matematik",
  grade: 5,
  unitId: null, // form ilk render'da sınıfın ilk ünitesini otomatik seçer
  kazanimKod: null,
  difficulty: "orta",
  questionCount: 10,
  // Varsayılan: tüm gruplar AÇIK, tek zorluk, hem cevap anahtarı hem çözüm dahil.
  typeGroups: {
    open_ended: true,
    visual: true,
    multiple_choice: true,
    other_format: true,
  },
  difficultyMode: "single",
  includeAnswerKey: true,
  includeSolutions: true,
  brandName: "",
  brandSubtitle: "",
  brandLogo: "",
};

export const useGenerateStore = create<GenerateStore>()(
  persist(
    (set) => ({
      ...DEFAULT_FORM,
      status: "idle",
      error: null,
      result: null,
      streamedCount: 0,
      setForm: (patch) => set((s) => ({ ...s, ...patch })),
      startGenerate: () =>
        set({ status: "loading", error: null, result: null, streamedCount: 0 }),
      setStreamedCount: (n) => set({ streamedCount: n }),
      setSuccess: (r) => set({ status: "success", result: r, error: null }),
      setError: (e) => set({ status: "error", error: e }),
      replaceQuestion: (number, q) =>
        set((s) => {
          if (!s.result) return {};
          const nq = { ...q, number };
          const ws = s.result.worksheet;
          return {
            result: {
              ...s.result,
              worksheet: {
                ...ws,
                questions: ws.questions.map((x) =>
                  x.number === number ? nq : x,
                ),
                answer_key: ws.answer_key.map((a) =>
                  a.number === number ? { number, answer: q.answer } : a,
                ),
              },
            },
          };
        }),
      reset: () =>
        set({ status: "idle", result: null, error: null, streamedCount: 0 }),
    }),
    {
      name: "meb-generate-form",
      // v1: "format" grubu "multiple_choice" + "other_format" olarak ikiye
      // bölündü. Eski persist edilmiş state'te tek "format" boolean'ı var →
      // her iki yeni gruba da aynı değeri taşı (aksi halde yeni switch'ler
      // undefined kalır ve "hepsi açık" tespiti bozulur).
      version: 2,
      migrate: (persisted, version) => {
        const s = (persisted ?? {}) as Partial<FormState> & {
          typeGroups?: Record<string, boolean>;
          topicId?: string; // v1 alanı — v2'de kaldırıldı (konu → ünite geçişi)
        };
        if (version < 1 && s.typeGroups && "format" in s.typeGroups) {
          const legacyFormat = s.typeGroups.format;
          s.typeGroups = {
            open_ended: s.typeGroups.open_ended ?? true,
            visual: s.typeGroups.visual ?? true,
            multiple_choice: legacyFormat ?? true,
            other_format: legacyFormat ?? true,
          };
        }
        if (version < 2) {
          // Konu → ünite geçişi: eski persistlenen topicId/kazanimKod artık geçersiz
          // (kazanım kodları M.* → MAT.*). Temiz başlangıç: ünite/kazanım sıfırlanır,
          // form ilk üniteyi otomatik seçer. Sınıf/zorluk/tercihler korunur.
          delete s.topicId;
          s.unitId = null;
          s.kazanimKod = null;
        }
        // Kısmi veri döner; zustand merge default değerlerle birleştirir.
        return s as unknown as GenerateStore;
      },
      partialize: (s) => ({
        subject: s.subject,
        grade: s.grade,
        unitId: s.unitId,
        kazanimKod: s.kazanimKod,
        difficulty: s.difficulty,
        questionCount: s.questionCount,
        typeGroups: s.typeGroups,
        difficultyMode: s.difficultyMode,
        includeAnswerKey: s.includeAnswerKey,
        includeSolutions: s.includeSolutions,
        brandName: s.brandName,
        brandSubtitle: s.brandSubtitle,
        brandLogo: s.brandLogo,
        // Üretilen kağıdı da persistle: anonim kullanıcı üretip PDF indirmek için
        // üye olunca Clerk redirect'i sayfayı yeniliyordu → kağıt kayboluyor, üretim
        // boşa gidiyordu. Sadece BAŞARILI sonucu sakla (loading/error yeniden yüklenmez).
        status: s.status === "success" ? "success" : "idle",
        result: s.status === "success" ? s.result : null,
      }),
    },
  ),
);
