/**
 * Frontend tarafı MEB müfredat (1-7. sınıf) snapshot'ı.
 *
 * Backend'in tek doğru kaynağı (`app/data/curriculum.py`); bu dosya build-time
 * bağımlılığını ortadan kaldırmak için elle replicate edilmiştir. Backend
 * güncellenirse aşağıdaki listeyi de yenile:
 *
 *   python -c "..." (scripts/regen-curriculum-slugs.py için to-do)
 *
 * 38 (sınıf × konu) kombinasyonu — sitemap + programmatic landing page için.
 */

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
];

export function getCurriculumPageBySlug(slug: string): CurriculumPage | undefined {
  return CURRICULUM_PAGES.find((p) => p.slug === slug);
}
