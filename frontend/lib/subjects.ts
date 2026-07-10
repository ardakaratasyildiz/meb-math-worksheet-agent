/**
 * Ders (subject) ekseni — frontend meta + feature-flag.
 *
 * Görünürlük tek env ile: NEXT_PUBLIC_ENABLED_SUBJECTS = "fen,turkce,..." (virgüllü
 * slug listesi). Matematik HER ZAMAN açık. Kapalı dersler ders seçicide görünmez ve
 * /generate?subject=<x> deep-link'i matematik'e düşer. Backend ayrıca kendi per-ders
 * flag'iyle (fen_enabled vb.) üretimi kapatır → çift kapı.
 *
 * Yeni ders eklemek: SUBJECT_META'ya bir satır + backend paketi. Frontend'de başka
 * değişiklik gerekmez (form/route otomatik).
 */
import type { Subject } from "./types";

export interface SubjectMeta {
  value: Subject;
  label: string;
  minGrade: number; // backend müfredat alt sınırı (grade reset için)
  maxGrade: number;
}

export const SUBJECT_META: SubjectMeta[] = [
  { value: "matematik", label: "Matematik", minGrade: 1, maxGrade: 8 },
  { value: "turkce", label: "Türkçe", minGrade: 1, maxGrade: 8 },
  { value: "ingilizce", label: "İngilizce", minGrade: 2, maxGrade: 8 },
  { value: "fen", label: "Fen Bilimleri", minGrade: 3, maxGrade: 8 },
  { value: "sosyal", label: "Sosyal Bilgiler", minGrade: 1, maxGrade: 8 },
];

const META_BY_VALUE: Record<string, SubjectMeta> = Object.fromEntries(
  SUBJECT_META.map((m) => [m.value, m]),
);

// NEXT_PUBLIC_* build-time inline edilir → statik referans şart (dinamik erişim çalışmaz).
const _ENABLED_RAW = process.env.NEXT_PUBLIC_ENABLED_SUBJECTS ?? "";
const _ENABLED = new Set(
  _ENABLED_RAW.split(",")
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean),
);

export function isSubjectEnabled(value: Subject): boolean {
  return value === "matematik" || _ENABLED.has(value);
}

/** Ders seçicide gösterilecek dersler (matematik + flag'li açık olanlar). */
export function availableSubjects(): SubjectMeta[] {
  return SUBJECT_META.filter((m) => isSubjectEnabled(m.value));
}

/** Matematik dışında en az bir ders açık mı (ders seçiciyi göstermek için). */
export function hasMultipleSubjects(): boolean {
  return availableSubjects().length > 1;
}

export function subjectMinGrade(value: Subject): number {
  return META_BY_VALUE[value]?.minGrade ?? 1;
}

export function subjectLabel(value: Subject): string {
  return META_BY_VALUE[value]?.label ?? value;
}
