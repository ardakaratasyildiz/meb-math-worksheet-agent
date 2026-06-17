/**
 * Frontend tarafı MEB müfredat (1-8. sınıf, 8 = LGS hazırlık) snapshot'ı.
 *
 * CURRICULUM_PAGES verisi backend'in TEK doğru kaynağından
 * (`app/data/curriculum.py`) OTOMATİK üretilir → `curriculum-pages.json`.
 * Build-time backend bağımlılığı olmasın diye JSON snapshot'tan okunur
 * (kazanimlar.json ile aynı desen).
 *
 * Müfredata sınıf/konu/kazanım eklenince TEK komutla yenile (elle düzenleme YOK):
 *   PYTHONIOENCODING=utf-8 python scripts/export_seo_data.py
 * → sitemap.ts + programmatic landing page'ler bu listeden otomatik beslenir.
 */

import curriculumPagesData from "./curriculum-pages.json";
import { KAZANIM_PAGES } from "./kazanimlar";
import type {
  EducationLevel,
  GradeInfo,
  KazanimInfo,
  TopicInfo,
} from "./types";

export interface CurriculumPage {
  grade: number;
  topicId: string;
  topicName: string;
  description: string;
  slug: string; // URL slug — örn. "5-sinif-kesirler"
  kazanimCount: number;
}

export const CURRICULUM_PAGES: CurriculumPage[] =
  curriculumPagesData as unknown as CurriculumPage[];

export function getCurriculumPageBySlug(slug: string): CurriculumPage | undefined {
  return CURRICULUM_PAGES.find((p) => p.slug === slug);
}

// ── Form dropdown verisi (lokal, anında) ───────────────────────────────────
// GenerateForm'daki sınıf/konu/kazanım seçenekleri eskiden her açılışta Render
// backend'ine gidiyordu; backend free-tier'da uykuya geçince ilk istek 30-40 sn
// sürüyor ve seçenekler boş kalıyordu. Müfredat statik olduğu için aşağıdaki
// builder'lar bu listeleri lokal snapshot'tan (CURRICULUM_PAGES + KAZANIM_PAGES)
// üretir → seçenekler cold-start'a bağımlı olmadan anında gelir. Backend yine
// arka planda yoklanıp olası drift'i düzeltir.

const GRADE_LEVELS: Record<number, EducationLevel> = {
  1: "İlkokul",
  2: "İlkokul",
  3: "İlkokul",
  4: "İlkokul",
  5: "Ortaokul",
  6: "Ortaokul",
  7: "Ortaokul",
  8: "Ortaokul",
};

export function getGradesLocal(): GradeInfo[] {
  return Object.keys(GRADE_LEVELS)
    .map(Number)
    .sort((a, b) => a - b)
    .map((grade) => ({
      id: grade,
      name: `${grade}. Sınıf`,
      level: GRADE_LEVELS[grade],
    }));
}

export function getTopicsLocal(grade: number): TopicInfo[] {
  return CURRICULUM_PAGES.filter((p) => p.grade === grade).map((p) => ({
    id: p.topicId,
    name: p.topicName,
    description: p.description,
    kazanim_count: p.kazanimCount,
  }));
}

export function getKazanimlarLocal(
  grade: number,
  topicId: string,
): KazanimInfo[] {
  return KAZANIM_PAGES.filter(
    (k) => k.grade === grade && k.topicId === topicId,
  ).map((k) => ({ kod: k.kod, metin: k.metin }));
}

// İlerleme panosu: kazanım kodundan (mastery_state yalnız kod tutar) okunabilir
// metni + sınıf/konuyu çözer → "bu kazanımda pratik yap" derin-linki kurulabilir.
export function findKazanimByKod(
  kod: string,
): { grade: number; topicId: string; topicName: string; metin: string } | undefined {
  const k = KAZANIM_PAGES.find((x) => x.kod === kod);
  if (!k) return undefined;
  return {
    grade: k.grade,
    topicId: k.topicId,
    topicName: k.topicName,
    metin: k.metin,
  };
}

// "Bu kazanımda pratik yap" derin-linki: /practice/new?grade=&topic=&kazanim=.
// SolveForm bu parametreleri okuyup formu ön-doldurur. Üç çağrı yeri paylaşır
// (ilerleme panosu, çöz-sonrası sonuç, hub önerisi).
export function practiceHref(kod: string): string {
  const info = findKazanimByKod(kod);
  if (!info) return "/practice/new";
  const p = new URLSearchParams({
    grade: String(info.grade),
    topic: info.topicId,
    kazanim: kod,
  });
  return `/practice/new?${p.toString()}`;
}

export interface TopicRollup {
  topicId: string;
  topicName: string;
  correct: number;
  total: number;
  ratio: number;
}

// Kazanım-bazlı doğru/toplam sayıları KONU bazında toplar — raporlarda kazanım
// kodları (M.5.2.1) yerine anlaşılır konu ("Kesirler %80") göstermek için.
export function rollupByTopic(
  items: { kazanim_kod: string; correct: number; total: number }[],
): TopicRollup[] {
  const map = new Map<
    string,
    { topicName: string; correct: number; total: number }
  >();
  for (const it of items) {
    const info = findKazanimByKod(it.kazanim_kod);
    const topicId = info?.topicId ?? "diger";
    const topicName = info?.topicName ?? "Diğer";
    const cur = map.get(topicId) ?? { topicName, correct: 0, total: 0 };
    cur.correct += it.correct;
    cur.total += it.total;
    map.set(topicId, cur);
  }
  return Array.from(map.entries()).map(([topicId, v]) => ({
    topicId,
    topicName: v.topicName,
    correct: v.correct,
    total: v.total,
    ratio: v.total ? v.correct / v.total : 0,
  }));
}
