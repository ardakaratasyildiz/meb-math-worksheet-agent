/**
 * Frontend tarafı MEB müfredat (1-8. sınıf, 8 = LGS hazırlık) snapshot'ı.
 *
 * Backend'in tek doğru kaynağı (`app/data/curriculum.py`); bu dosya build-time
 * bağımlılığını ortadan kaldırmak için elle replicate edilmiştir. Backend
 * güncellenirse aşağıdaki listeyi de yenile:
 *
 *   python -c "..." (scripts/regen-curriculum-slugs.py için to-do)
 *
 * 38 (sınıf × konu) kombinasyonu — sitemap + programmatic landing page için.
 */

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

export const CURRICULUM_PAGES: CurriculumPage[] = [
  { grade: 1, topicId: "dogal_sayilar", topicName: "Doğal Sayılar ve İşlemler", description: "100'e kadar sayılar, toplama-çıkarma", slug: "1-sinif-dogal-sayilar", kazanimCount: 5 },
  { grade: 1, topicId: "geometri", topicName: "Geometri", description: "Temel geometrik şekilleri tanıma (kare, üçgen, daire)", slug: "1-sinif-geometri", kazanimCount: 2 },
  { grade: 1, topicId: "olcme", topicName: "Ölçme", description: "Uzunluk karşılaştırma, standart olmayan birimler", slug: "1-sinif-olcme", kazanimCount: 3 },
  { grade: 1, topicId: "cebir", topicName: "Cebir ve Denklemler", description: "Basit sayı örüntüleri", slug: "1-sinif-cebir", kazanimCount: 2 },
  { grade: 2, topicId: "dogal_sayilar", topicName: "Doğal Sayılar ve İşlemler", description: "1000'e kadar sayılar, toplama-çıkarma, çarpmaya giriş", slug: "2-sinif-dogal-sayilar", kazanimCount: 5 },
  { grade: 2, topicId: "geometri", topicName: "Geometri", description: "Kenar ve köşe kavramı, şekil özellikleri", slug: "2-sinif-geometri", kazanimCount: 2 },
  { grade: 2, topicId: "olcme", topicName: "Ölçme", description: "cm-m, saat okuma, tartma", slug: "2-sinif-olcme", kazanimCount: 3 },
  { grade: 2, topicId: "cebir", topicName: "Cebir ve Denklemler", description: "Sayı ve şekil örüntüleri", slug: "2-sinif-cebir", kazanimCount: 2 },
  { grade: 3, topicId: "dogal_sayilar", topicName: "Doğal Sayılar ve İşlemler", description: "10.000'e kadar sayılar, dört işlem", slug: "3-sinif-dogal-sayilar", kazanimCount: 5 },
  { grade: 3, topicId: "kesirler", topicName: "Kesirler ve Ondalık Sayılar", description: "Kesirlere giriş: yarım, çeyrek, bütün-parça", slug: "3-sinif-kesirler", kazanimCount: 3 },
  { grade: 3, topicId: "geometri", topicName: "Geometri", description: "Çevre hesaplama, simetri", slug: "3-sinif-geometri", kazanimCount: 2 },
  { grade: 3, topicId: "olcme", topicName: "Ölçme", description: "Birim dönüşümleri (km-m-cm-mm), zaman", slug: "3-sinif-olcme", kazanimCount: 2 },
  { grade: 3, topicId: "cebir", topicName: "Cebir ve Denklemler", description: "Örüntülerde kural bulma", slug: "3-sinif-cebir", kazanimCount: 2 },
  { grade: 4, topicId: "dogal_sayilar", topicName: "Doğal Sayılar ve İşlemler", description: "Büyük doğal sayılar, dört işlem, bölme", slug: "4-sinif-dogal-sayilar", kazanimCount: 5 },
  { grade: 4, topicId: "kesirler", topicName: "Kesirler ve Ondalık Sayılar", description: "Kesir türleri, ondalık gösterim, sıralama", slug: "4-sinif-kesirler", kazanimCount: 4 },
  { grade: 4, topicId: "geometri", topicName: "Geometri", description: "Açılar (dar, dik, geniş), çevre-alan", slug: "4-sinif-geometri", kazanimCount: 3 },
  { grade: 4, topicId: "olcme", topicName: "Ölçme", description: "Birim dönüşümleri, alan-çevre birimleri", slug: "4-sinif-olcme", kazanimCount: 2 },
  { grade: 4, topicId: "cebir", topicName: "Cebir ve Denklemler", description: "Örüntü ve ilişkilerde genelleme", slug: "4-sinif-cebir", kazanimCount: 2 },
  { grade: 5, topicId: "dogal_sayilar", topicName: "Doğal Sayılar ve İşlemler", description: "Doğal sayılarla işlemler, işlem önceliği", slug: "5-sinif-dogal-sayilar", kazanimCount: 5 },
  { grade: 5, topicId: "kesirler", topicName: "Kesirler ve Ondalık Sayılar", description: "Kesirlerle toplama-çıkarma", slug: "5-sinif-kesirler", kazanimCount: 5 },
  { grade: 5, topicId: "geometri", topicName: "Geometri", description: "Üçgen ve dörtgenlerin çevre-alan hesabı, temel geometrik kavramlar", slug: "5-sinif-geometri", kazanimCount: 5 },
  { grade: 5, topicId: "olcme", topicName: "Ölçme", description: "Hacim ölçme, litre-mililitre", slug: "5-sinif-olcme", kazanimCount: 3 },
  { grade: 5, topicId: "cebir", topicName: "Cebir ve Denklemler", description: "Basit denklemler (x + 3 = 7)", slug: "5-sinif-cebir", kazanimCount: 2 },
  { grade: 5, topicId: "veri_isleme", topicName: "Veri İşleme ve İstatistik", description: "Sıklık tablosu, sütun ve şekil grafiği", slug: "5-sinif-veri-isleme", kazanimCount: 1 },
  { grade: 6, topicId: "dogal_sayilar", topicName: "Doğal Sayılar ve İşlemler", description: "Tam sayılar, mutlak değer, toplama-çıkarma", slug: "6-sinif-dogal-sayilar", kazanimCount: 7 },
  { grade: 6, topicId: "kesirler", topicName: "Kesirler ve Ondalık Sayılar", description: "Kesirlerle dört işlem, ondalık gösterim, yüzdeler", slug: "6-sinif-kesirler", kazanimCount: 5 },
  { grade: 6, topicId: "geometri", topicName: "Geometri", description: "Alan hesaplamaları (paralelkenar, üçgen, yamuk), açılar, çember", slug: "6-sinif-geometri", kazanimCount: 5 },
  { grade: 6, topicId: "olcme", topicName: "Ölçme", description: "Sıvı ölçüleri, hacim hesaplama", slug: "6-sinif-olcme", kazanimCount: 2 },
  { grade: 6, topicId: "cebir", topicName: "Cebir ve Denklemler", description: "Cebirsel ifadeler, birinci dereceden denklemler", slug: "6-sinif-cebir", kazanimCount: 4 },
  { grade: 6, topicId: "veri_isleme", topicName: "Veri İşleme ve İstatistik", description: "Veri analizi, sütun/çizgi grafiği, merkezi eğilim ölçüleri", slug: "6-sinif-veri-isleme", kazanimCount: 2 },
  { grade: 6, topicId: "olasilik", topicName: "Olasılık", description: "Bir olayın olasılığını basit yollarla yorumlama", slug: "6-sinif-olasilik", kazanimCount: 1 },
  { grade: 7, topicId: "dogal_sayilar", topicName: "Doğal Sayılar ve İşlemler", description: "Tam sayılarla çarpma-bölme, işlem önceliği", slug: "7-sinif-dogal-sayilar", kazanimCount: 4 },
  { grade: 7, topicId: "kesirler", topicName: "Kesirler ve Ondalık Sayılar", description: "Rasyonel sayılar, rasyonel sayılarla işlemler", slug: "7-sinif-kesirler", kazanimCount: 4 },
  { grade: 7, topicId: "geometri", topicName: "Geometri", description: "Çember ve dairede uzunluk-alan, merkez açı", slug: "7-sinif-geometri", kazanimCount: 5 },
  { grade: 7, topicId: "olcme", topicName: "Ölçme", description: "Prizmaların hacmi ve yüzey alanı", slug: "7-sinif-olcme", kazanimCount: 2 },
  { grade: 7, topicId: "cebir", topicName: "Cebir ve Denklemler", description: "Eşitsizlikler, doğrusal denklemler, oran-orantı", slug: "7-sinif-cebir", kazanimCount: 4 },
  { grade: 7, topicId: "veri_isleme", topicName: "Veri İşleme ve İstatistik", description: "Veri analizi, daire grafiği, merkezi eğilim", slug: "7-sinif-veri-isleme", kazanimCount: 2 },
  { grade: 7, topicId: "olasilik", topicName: "Olasılık", description: "Olası durumlar, basit olasılık hesabı", slug: "7-sinif-olasilik", kazanimCount: 1 },
  // 8. sınıf — LGS hazırlık kapsamı (gerçek çıkmış LGS soruları few-shot havuzunda)
  { grade: 8, topicId: "dogal_sayilar", topicName: "Sayılar ve İşlemler", description: "Çarpanlar-katlar, EBOB-EKOK, üslü ifadeler, kareköklü ifadeler, gerçek sayılar", slug: "8-sinif-dogal-sayilar", kazanimCount: 14 },
  { grade: 8, topicId: "cebir", topicName: "Cebir, Denklemler ve Eşitsizlikler", description: "Çarpanlara ayırma, özdeşlikler, doğrusal denklemler, eğim, eşitsizlikler", slug: "8-sinif-cebir", kazanimCount: 9 },
  { grade: 8, topicId: "geometri", topicName: "Geometri ve Ölçme", description: "Üçgenler, Pisagor bağıntısı, dönüşüm geometrisi, geometrik cisimler (silindir-koni-piramit)", slug: "8-sinif-geometri", kazanimCount: 13 },
  { grade: 8, topicId: "veri_isleme", topicName: "Veri İşleme ve İstatistik", description: "Daire grafiği, çizgi grafiği, veriye uygun grafik türü seçimi", slug: "8-sinif-veri-isleme", kazanimCount: 3 },
  { grade: 8, topicId: "olasilik", topicName: "Olasılık", description: "Olası durumlar, olma olasılığı, eşit şanslı olaylar", slug: "8-sinif-olasilik", kazanimCount: 4 },
];

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

// "Bu kazanımda pratik yap" derin-linki: /coz/yeni?grade=&topic=&kazanim=.
// SolveForm bu parametreleri okuyup formu ön-doldurur. Üç çağrı yeri paylaşır
// (ilerleme panosu, çöz-sonrası sonuç, hub önerisi).
export function practiceHref(kod: string): string {
  const info = findKazanimByKod(kod);
  if (!info) return "/coz/yeni";
  const p = new URLSearchParams({
    grade: String(info.grade),
    topic: info.topicId,
    kazanim: kod,
  });
  return `/coz/yeni?${p.toString()}`;
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
