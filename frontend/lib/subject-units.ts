/**
 * Matematik-dışı derslerin ünite/kazanım ağacı (Konular sayfası + ana sayfa vitrini).
 *
 * Kaynak: backend `app/subjects/<ders>/curriculum.py` → `scripts/export_subject_units.py`
 * → bu JSON snapshot (build-time backend bağımlılığı yok; units.ts / curriculum.ts deseni).
 * Matematik BURADA YOK — o zaten lib/units.ts (UNIT_PAGES) üzerinden gelir.
 *
 * Güncelleme: backend curriculum değişince
 *   PYTHONIOENCODING=utf-8 python scripts/export_subject_units.py
 */
import data from "./subject-units.json";
import type { Subject } from "./types";

export interface SubjectUnitKazanim {
  kod: string;
  metin: string;
}

export interface SubjectUnit {
  unit_id: string;
  no: number;
  name: string;
  kazanimlar: SubjectUnitKazanim[];
}

/** grade (string anahtar, JSON gereği) → o sınıfın üniteleri */
export type SubjectUnitsByGrade = Record<string, SubjectUnit[]>;

const SUBJECT_UNITS = data as unknown as Record<string, SubjectUnitsByGrade>;

/** Bir ders için var mı (matematik-dışı ağaç). */
export function hasSubjectUnits(subject: Subject): boolean {
  const g = SUBJECT_UNITS[subject];
  return !!g && Object.keys(g).length > 0;
}

/** Ders için [sınıf, üniteler] listesi — sınıf artan sırada. */
export function subjectUnitsByGrade(subject: Subject): [number, SubjectUnit[]][] {
  const g = SUBJECT_UNITS[subject] ?? {};
  return Object.keys(g)
    .map((k) => Number(k))
    .sort((a, b) => a - b)
    .map((grade) => [grade, g[String(grade)]] as [number, SubjectUnit[]]);
}
