import { z } from "zod";

/**
 * Ders (subject) tanımları — web + mobil ortak kaynak.
 *
 * Slug'lar backend `subject_resolve` ve `NEXT_PUBLIC_ENABLED_SUBJECTS` ile
 * hizalı. Renk/tema değerleri UI wiring aşamasında frontend'den senkronlanacak
 * (şimdilik slug + görünen ad — kesin/stabil kısım).
 */
export const SUBJECT_SLUGS = [
  "matematik",
  "fen",
  "turkce",
  "sosyal",
  "ingilizce",
] as const;

export const SubjectSlug = z.enum(SUBJECT_SLUGS);
export type SubjectSlug = z.infer<typeof SubjectSlug>;

export const SUBJECT_LABELS: Record<SubjectSlug, string> = {
  matematik: "Matematik",
  fen: "Fen Bilimleri",
  turkce: "Türkçe",
  sosyal: "Sosyal Bilgiler",
  ingilizce: "İngilizce",
};

/** Ders ana rengi (hex) — web frontend/lib/subjects.ts SUBJECT_STYLE ile birebir. */
export const SUBJECT_COLORS: Record<SubjectSlug, string> = {
  matematik: "#2563eb", // mavi
  fen: "#059669", // yeşil
  turkce: "#e11d48", // mercan
  sosyal: "#d97706", // amber
  ingilizce: "#7c3aed", // mor
};

/** Ders emojisi — web ile ortak. */
export const SUBJECT_EMOJI: Record<SubjectSlug, string> = {
  matematik: "➗",
  fen: "🔬",
  turkce: "📖",
  sosyal: "🌍",
  ingilizce: "🔤",
};

export function subjectLabel(slug: SubjectSlug): string {
  return SUBJECT_LABELS[slug];
}

export function subjectColor(slug: SubjectSlug): string {
  return SUBJECT_COLORS[slug];
}
