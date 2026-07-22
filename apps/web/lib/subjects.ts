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

export function subjectMaxGrade(value: Subject): number {
  return META_BY_VALUE[value]?.maxGrade ?? 8;
}

export function subjectLabel(value: Subject): string {
  return META_BY_VALUE[value]?.label ?? value;
}

// ── Ders görsel dili (ortak) ────────────────────────────────────────────────
// Her ders bir renk + emoji ile kodlanır; bu kodlama TÜM uygulamada aynı kalır
// (ana sayfa vitrini, quiz akışı, ilerleme rozetleri). Tailwind sınıfları LİTERAL
// yazılır — JIT tarayıcı statik string görmeli, dinamik `text-${x}` çalışmaz.
export interface SubjectStyle {
  emoji: string;
  /** Sınıf aralığı etiketi — vitrin/rozet için (örn. "1–8. sınıf · LGS"). */
  grades: string;
  /** Kısa vitrin açıklaması. */
  blurb: string;
  text: string; // metin + ikon rengi
  bg: string; // yumuşak arka plan (ikon kutusu / seçili sekme)
  border: string; // kenarlık (seçili / hover)
  dot: string; // aksan noktası (sekme göstergesi)
  hex: string; // ham renk — inline stil (conic-gradient halka, grafik) için
}

const SUBJECT_STYLE: Record<Subject, SubjectStyle> = {
  matematik: {
    emoji: "➗",
    grades: "1–8. sınıf · LGS",
    blurb: "Sayılar, cebir, geometri ve veri — MEB kazanımlarına hizalı.",
    text: "text-blue-600 dark:text-blue-400",
    bg: "bg-blue-50 dark:bg-blue-950/40",
    border: "border-blue-500/40",
    dot: "bg-blue-500",
    hex: "#2563eb",
  },
  fen: {
    emoji: "🔬",
    grades: "3–8. sınıf",
    blurb: "Canlılar, madde, kuvvet ve Dünya — görselli yeni nesil sorular.",
    text: "text-emerald-600 dark:text-emerald-400",
    bg: "bg-emerald-50 dark:bg-emerald-950/40",
    border: "border-emerald-500/40",
    dot: "bg-emerald-500",
    hex: "#059669",
  },
  turkce: {
    emoji: "📖",
    grades: "1–8. sınıf",
    blurb: "Okuma, dil bilgisi, yazım-noktalama ve özgün metinler.",
    text: "text-rose-600 dark:text-rose-400",
    bg: "bg-rose-50 dark:bg-rose-950/40",
    border: "border-rose-500/40",
    dot: "bg-rose-500",
    hex: "#e11d48",
  },
  sosyal: {
    emoji: "🌍",
    grades: "1–8. sınıf · İnkılap",
    blurb: "Tarih, coğrafya, vatandaşlık ve T.C. İnkılap Tarihi.",
    text: "text-amber-600 dark:text-amber-400",
    bg: "bg-amber-50 dark:bg-amber-950/40",
    border: "border-amber-500/40",
    dot: "bg-amber-500",
    hex: "#d97706",
  },
  ingilizce: {
    emoji: "🔤",
    grades: "2–8. sınıf",
    blurb: "Kelime, dil bilgisi ve CEFR düzeyine uygun özgün İngilizce.",
    text: "text-violet-600 dark:text-violet-400",
    bg: "bg-violet-50 dark:bg-violet-950/40",
    border: "border-violet-500/40",
    dot: "bg-violet-500",
    hex: "#7c3aed",
  },
};

export function subjectStyle(value: Subject): SubjectStyle {
  return SUBJECT_STYLE[value] ?? SUBJECT_STYLE.matematik;
}

export function subjectEmoji(value: Subject): string {
  return subjectStyle(value).emoji;
}
