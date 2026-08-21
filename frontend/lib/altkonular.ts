/**
 * Alt-konu (sub-topic) landing page verisi — programatik SEO.
 *
 * NEDEN AYRI BİR KATMAN:
 *   `kazanimlar.ts` (123 kazanım) ÜRETİM hattına bağlıdır (form dropdown + RAG +
 *   Gemini'ye giden zorluk ipuçları). Bu dosya ise SADECE SEO landing'leri besler;
 *   üretim hattına SIFIR dokunur. Bu yüzden alt-konu CTA'ları kazanım koduna değil,
 *   KONU seviyesine (?grade=&topic=) deep-link eder — backend bunu zaten destekler.
 *
 * NEDEN ALT-KONU (kazanım kodu değil):
 *   Gerçek arama hacmi doğal-dil alt-konuda ("5. sınıf kesirlerle toplama çıkarma
 *   çalışma kağıdı"), kazanım kodunda değil ("M.5.2.3" ~sıfır arama). Her sayfa
 *   benzersiz öz içerik (intro + alt-beceriler + zorluk ipuçları) taşır → thin/
 *   doorway içerik değil. Mevcut kazanım koduyla ÇAKIŞMAZ (farklı URL şeması, farklı
 *   slug uzayı).
 *
 * Route: /calismalar/<topicSlug>/<slug>   (mevcut [slug]/[kazanim] route'u paylaşır;
 *   page.tsx önce alt-konuyu, bulamazsa kazanımı çözer.)
 */

const TOPIC_NAMES: Record<string, string> = {
  dogal_sayilar: "Doğal Sayılar ve İşlemler",
  kesirler: "Kesirler ve Ondalık Sayılar",
  geometri: "Geometri",
  olcme: "Ölçme",
  cebir: "Cebir ve Denklemler",
  veri_isleme: "Veri İşleme ve İstatistik",
  olasilik: "Olasılık",
};

export interface AltKonu {
  slug: string; // ikinci seviye URL parçası, örn. "kesirlerle-toplama-cikarma"
  topicSlug: string; // ebeveyn konu, örn. "5-sinif-kesirler"
  grade: number;
  topicId: string;
  topicName: string;
  title: string; // H1 / doğal-dil sorgu, örn. "Kesirlerle Toplama ve Çıkarma"
  description: string; // meta description (benzersiz)
  intro: string; // benzersiz tanıtım paragrafı
  skills: string[]; // 4-6 alt-beceri (benzersiz öz içerik)
  difficulty: { kolay: string; orta: string; zor: string };
  family?: string; // sınıflar arası iç-link için (örn. "yuzde" → 5/6/7 yüzde sayfaları)
}

interface AltKonuInput {
  grade: number;
  topicId: string;
  slug: string;
  title: string;
  description: string;
  intro: string;
  skills: string[];
  difficulty: [string, string, string];
  family?: string;
}

function ak(i: AltKonuInput): AltKonu {
  const topicSlug = `${i.grade}-sinif-${i.topicId.replace(/_/g, "-")}`;
  return {
    slug: i.slug,
    topicSlug,
    grade: i.grade,
    topicId: i.topicId,
    topicName: TOPIC_NAMES[i.topicId] ?? i.topicId,
    title: i.title,
    description: i.description,
    intro: i.intro,
    skills: i.skills,
    difficulty: {
      kolay: i.difficulty[0],
      orta: i.difficulty[1],
      zor: i.difficulty[2],
    },
    family: i.family,
  };
}

export const ALTKONU_PAGES: AltKonu[] = [
  // ─── 1. SINIF ──────────────────────────────────────────────────────────────
  ak({
    grade: 1,
    topicId: "dogal_sayilar",
    slug: "ritmik-sayma",
    title: "Ritmik Sayma",
    description:
      "1. sınıf ritmik sayma çalışma kağıdı: birer, ikişer, beşer ve onar sayma. PDF, cevap anahtarı ve adım adım çözüm ile ücretsiz üret.",
    intro:
      "Ritmik sayma, sayıları belirli bir kural (birer, ikişer, beşer, onar) ile sıralı sayma becerisidir. Bu çalışma kağıdı verilen sayıdan başlayarak ileri ve geri ritmik saymayı pekiştirir.",
    skills: [
      "Birer birer ileri ve geri sayma",
      "İkişer ve beşer ritmik sayma",
      "Onar ritmik sayma",
      "Verilen sayıdan devam ederek sayma",
      "Eksik bırakılan sayıyı tamamlama",
    ],
    difficulty: [
      "20'ye kadar birer birer sayma.",
      "İkişer veya beşer ritmik sayma.",
      "Onar sayma veya geriye doğru ritmik sayma.",
    ],
  }),
  ak({
    grade: 1,
    topicId: "dogal_sayilar",
    slug: "toplama-islemi",
    title: "Toplama İşlemi (20'ye Kadar)",
    description:
      "1. sınıf toplama işlemi çalışma kağıdı: 20'ye kadar zihinden ve yazılı toplama. PDF + cevap anahtarı + çözüm, ücretsiz.",
    intro:
      "Bu çalışma kağıdı toplamları en çok 20 olan iki doğal sayıyı zihinden ve yazılı olarak toplamayı, toplama işleminin günlük hayattaki karşılığını pekiştirir.",
    skills: [
      "Toplamı 10'a kadar olan işlemler",
      "Toplamı 20'ye kadar olan işlemler",
      "Zihinden toplama",
      "Toplama içeren basit problemler",
    ],
    difficulty: [
      "Toplamı 10'a kadar olan işlemler.",
      "Toplamı 20'ye kadar olan işlemler.",
      "Toplama gerektiren kısa sözel problemler.",
    ],
    family: "toplama-islemi",
  }),
  ak({
    grade: 1,
    topicId: "dogal_sayilar",
    slug: "cikarma-islemi",
    title: "Çıkarma İşlemi (20'ye Kadar)",
    description:
      "1. sınıf çıkarma işlemi çalışma kağıdı: 20'ye kadar çıkarma ve eksik sayı bulma. PDF, cevap anahtarı ve adım adım çözüm ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı 20'ye kadar olan sayılarla çıkarma işlemini, toplama-çıkarma ilişkisini ve eksik sayıyı bulmayı pekiştirir.",
    skills: [
      "10'a kadar çıkarma işlemi",
      "20'ye kadar çıkarma işlemi",
      "Eksik sayıyı bulma (örn. 7 − ? = 3)",
      "Çıkarma içeren basit problemler",
    ],
    difficulty: [
      "10'dan küçük sayılarla çıkarma.",
      "20'ye kadar çıkarma.",
      "Eksik sayı veya kısa sözel problemler.",
    ],
    family: "cikarma-islemi",
  }),
  ak({
    grade: 1,
    topicId: "dogal_sayilar",
    slug: "onluk-birlik",
    title: "Onluk ve Birlik (Basamak Değeri)",
    description:
      "1. sınıf onluk-birlik çalışma kağıdı: iki basamaklı sayıları onluk ve birliklerine ayırma. PDF + cevap anahtarı + çözüm, ücretsiz.",
    intro:
      "Bu çalışma kağıdı iki basamaklı sayıları onluk ve birlik kavramlarıyla çözümlemeyi, basamak değerini anlamayı pekiştirir.",
    skills: [
      "Bir sayıyı onluk ve birliklerine ayırma",
      "Onluk-birlik verilip sayıyı bulma",
      "Basamak değerini belirleme",
      "Onluk-birlik modeliyle sayı oluşturma",
    ],
    difficulty: [
      "Sayıyı onluk ve birliğine ayırma.",
      "Onluk-birlikten sayıyı bulma.",
      "Eksik bilgi içeren çözümleme.",
    ],
    family: "basamak-deger",
  }),
  ak({
    grade: 1,
    topicId: "geometri",
    slug: "geometrik-sekiller",
    title: "Geometrik Şekiller: Kare, Üçgen, Daire, Dikdörtgen",
    description:
      "1. sınıf geometrik şekiller çalışma kağıdı: kare, üçgen, daire ve dikdörtgeni tanıma ve eşleştirme. PDF, cevap anahtarı ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı temel geometrik şekilleri tanımayı, adlandırmayı ve çevredeki nesnelerle eşleştirmeyi pekiştirir.",
    skills: [
      "Kare, üçgen, daire ve dikdörtgeni tanıma",
      "Şekilleri adlandırma",
      "Nesneleri geometrik şekille eşleştirme",
      "Şekilleri özelliklerine göre gruplama",
    ],
    difficulty: [
      "Şekli tanıma ve adlandırma.",
      "Nesneyle şekli eşleştirme.",
      "Şekilleri özelliğine göre ayırma.",
    ],
  }),
  ak({
    grade: 1,
    topicId: "olcme",
    slug: "uzunluk-karsilastirma",
    title: "Uzunlukları Karşılaştırma (Kısa-Uzun)",
    description:
      "1. sınıf uzunluk karşılaştırma çalışma kağıdı: kısa-uzun, ince-kalın ve standart olmayan birimlerle ölçme. PDF + cevap anahtarı, ücretsiz.",
    intro:
      "Bu çalışma kağıdı nesnelerin uzunluklarını kısa-uzun, ince-kalın olarak karşılaştırmayı ve karış, adım gibi standart olmayan birimlerle ölçmeyi pekiştirir.",
    skills: [
      "İki nesneyi kısa-uzun olarak karşılaştırma",
      "İnce-kalın ayrımı yapma",
      "Standart olmayan birimlerle (karış, adım) ölçme",
      "Nesneleri uzunluğa göre sıralama",
    ],
    difficulty: [
      "İki nesneyi karşılaştırma.",
      "Standart olmayan birimle ölçme.",
      "Üç ve daha fazla nesneyi sıralama.",
    ],
  }),
  ak({
    grade: 1,
    topicId: "olcme",
    slug: "saat-okuma-tam",
    title: "Saat Okuma (Tam Saatler)",
    description:
      "1. sınıf saat okuma çalışma kağıdı: tam saatleri okuma ve gösterme. PDF, cevap anahtarı ve adım adım çözüm ile ücretsiz üret.",
    intro:
      "Bu çalışma kağıdı analog saatte tam saatleri okumayı ve verilen tam saati saat üzerinde göstermeyi pekiştirir.",
    skills: [
      "Tam saatleri okuma",
      "Verilen saati gösterme",
      "Günlük olayları saatle ilişkilendirme",
      "Akrep ve yelkovanı tanıma",
    ],
    difficulty: [
      "Tam saati okuma.",
      "Verilen tam saati gösterme.",
      "Saat ve günlük olay eşleştirme.",
    ],
    family: "saat-okuma",
  }),
  ak({
    grade: 1,
    topicId: "cebir",
    slug: "sayi-oruntuleri",
    title: "Sayı Örüntüleri",
    description:
      "1. sınıf sayı örüntüleri çalışma kağıdı: basit örüntüleri tanıma ve eksik öğeyi bulma. PDF + cevap anahtarı + çözüm, ücretsiz.",
    intro:
      "Bu çalışma kağıdı birer ve ikişer ritmik sayarak oluşan basit örüntüleri tanımayı ve örüntüdeki eksik sayı veya şekli bulmayı pekiştirir.",
    skills: [
      "Basit sayı örüntüsünü tanıma",
      "Örüntüyü devam ettirme",
      "Eksik öğeyi bulma",
      "Şekil örüntülerini tanıma",
    ],
    difficulty: [
      "Birer artan örüntüyü tanıma.",
      "Örüntüyü devam ettirme.",
      "Eksik öğeyi bulma.",
    ],
    family: "oruntu",
  }),

  // ─── 2. SINIF ──────────────────────────────────────────────────────────────
  ak({
    grade: 2,
    topicId: "dogal_sayilar",
    slug: "eldeli-toplama",
    title: "Eldeli Toplama İşlemi",
    description:
      "2. sınıf eldeli toplama çalışma kağıdı: 100'e kadar elde ederek toplama. PDF, cevap anahtarı ve adım adım çözüm ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı toplamları en çok 100 olan sayılarda elde ederek toplama işlemini ve toplama içeren problemleri pekiştirir.",
    skills: [
      "Elde olmadan iki basamaklı toplama",
      "Elde ederek toplama",
      "Üç sayıyı toplama",
      "Toplama içeren problemler",
    ],
    difficulty: [
      "Elde olmadan toplama.",
      "Elde ederek toplama.",
      "Toplama gerektiren sözel problemler.",
    ],
    family: "toplama-islemi",
  }),
  ak({
    grade: 2,
    topicId: "dogal_sayilar",
    slug: "onluk-bozarak-cikarma",
    title: "Onluk Bozarak Çıkarma",
    description:
      "2. sınıf çıkarma çalışma kağıdı: 100'e kadar onluk bozarak çıkarma. PDF + cevap anahtarı + adım adım çözüm, ücretsiz üret.",
    intro:
      "Bu çalışma kağıdı iki basamaklı sayılarda onluk bozarak çıkarma işlemini ve çıkarma içeren günlük hayat problemlerini pekiştirir.",
    skills: [
      "Onluk bozmadan çıkarma",
      "Onluk bozarak çıkarma",
      "Toplama-çıkarma ilişkisini kullanma",
      "Çıkarma içeren problemler",
    ],
    difficulty: [
      "Onluk bozmadan çıkarma.",
      "Onluk bozarak çıkarma.",
      "Çıkarma gerektiren sözel problemler.",
    ],
    family: "cikarma-islemi",
  }),
  ak({
    grade: 2,
    topicId: "dogal_sayilar",
    slug: "carpmaya-giris",
    title: "Çarpmaya Giriş (Tekrarlı Toplama)",
    description:
      "2. sınıf çarpmaya giriş çalışma kağıdı: tekrarlı toplama ve çarpma ilişkisi. PDF, cevap anahtarı ve çözüm ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı çarpma işlemini tekrarlı toplama olarak açıklamayı ve 5'e kadar olan sayılarla basit çarpma yapmayı pekiştirir.",
    skills: [
      "Tekrarlı toplamayı çarpma olarak yazma",
      "Çarpma işlemini modelle gösterme",
      "5'e kadar olan sayılarla çarpma",
      "Çarpma içeren basit problemler",
    ],
    difficulty: [
      "Tekrarlı toplamayı çarpmaya çevirme.",
      "Küçük sayılarla çarpma.",
      "Çarpma gerektiren basit problemler.",
    ],
    family: "carpma-islemi",
  }),
  ak({
    grade: 2,
    topicId: "dogal_sayilar",
    slug: "basamak-degeri",
    title: "Basamak Değeri (Onluk-Birlik)",
    description:
      "2. sınıf basamak değeri çalışma kağıdı: üç basamaklı sayıları basamaklarına göre çözümleme. PDF + cevap anahtarı + çözüm, ücretsiz.",
    intro:
      "Bu çalışma kağıdı üç basamaklı doğal sayıları yüzlük, onluk ve birliklerine ayırarak basamak değerlerini belirlemeyi pekiştirir.",
    skills: [
      "Sayıyı basamaklarına ayırma",
      "Basamak değerini belirleme",
      "Verilen basamaklardan sayıyı oluşturma",
      "Sayıları okuma ve yazma",
    ],
    difficulty: [
      "İki basamaklı çözümleme.",
      "Üç basamaklı çözümleme.",
      "Eksik basamak bilgisiyle sayı bulma.",
    ],
    family: "basamak-deger",
  }),
  ak({
    grade: 2,
    topicId: "geometri",
    slug: "kenar-kose",
    title: "Kenar ve Köşe Sayısı",
    description:
      "2. sınıf geometri çalışma kağıdı: şekillerin kenar ve köşe sayıları, kare-dikdörtgen özellikleri. PDF, cevap anahtarı ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı geometrik şekillerin kenar ve köşe sayılarını belirlemeyi; karenin ve dikdörtgenin kenar özelliklerini fark etmeyi pekiştirir.",
    skills: [
      "Şekillerin kenar sayısını belirleme",
      "Şekillerin köşe sayısını belirleme",
      "Karenin kenar özelliklerini fark etme",
      "Dikdörtgenin karşılıklı kenarlarını tanıma",
    ],
    difficulty: [
      "Kenar/köşe sayma.",
      "Şekilleri kenar-köşeye göre ayırt etme.",
      "Özelliklere göre şekil belirleme.",
    ],
  }),
  ak({
    grade: 2,
    topicId: "olcme",
    slug: "metre-santimetre",
    title: "Metre ve Santimetre",
    description:
      "2. sınıf uzunluk ölçme çalışma kağıdı: metre ve santimetre ile ölçme ve karşılaştırma. PDF + cevap anahtarı + çözüm, ücretsiz.",
    intro:
      "Bu çalışma kağıdı metre ve santimetre birimlerini tanımayı, bu birimlerle uzunluk ölçmeyi ve karşılaştırmayı pekiştirir.",
    skills: [
      "Metre ve santimetreyi tanıma",
      "Uygun birimi seçme",
      "Uzunlukları ölçme ve karşılaştırma",
      "Uzunluk içeren basit problemler",
    ],
    difficulty: [
      "Uygun birimi seçme.",
      "Ölçme ve karşılaştırma.",
      "Uzunluk problemleri.",
    ],
  }),
  ak({
    grade: 2,
    topicId: "olcme",
    slug: "saat-okuma-yarim-ceyrek",
    title: "Saat Okuma (Yarım ve Çeyrek)",
    description:
      "2. sınıf saat okuma çalışma kağıdı: tam, yarım ve çeyrek saatleri okuma. PDF, cevap anahtarı ve adım adım çözüm ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı saat ve dakika kavramlarını kullanarak tam, yarım ve çeyrek saatleri okumayı ve göstermeyi pekiştirir.",
    skills: [
      "Tam ve yarım saatleri okuma",
      "Çeyrek saatleri okuma",
      "Verilen saati gösterme",
      "Saat içeren günlük durumlar",
    ],
    difficulty: [
      "Tam ve yarım saat.",
      "Çeyrek saatleri okuma.",
      "Saat ve süre içeren problemler.",
    ],
    family: "saat-okuma",
  }),
  ak({
    grade: 2,
    topicId: "cebir",
    slug: "sayi-sekil-oruntuleri",
    title: "Sayı ve Şekil Örüntüleri",
    description:
      "2. sınıf örüntü çalışma kağıdı: sayı ve şekil örüntülerinde ilişkiyi bulma ve genişletme. PDF + cevap anahtarı + çözüm, ücretsiz.",
    intro:
      "Bu çalışma kağıdı bir örüntüdeki ilişkiyi belirlemeyi, örüntüyü genişletmeyi ve eksik öğeleri tamamlamayı pekiştirir.",
    skills: [
      "Örüntüdeki kuralı bulma",
      "Örüntüyü genişletme",
      "Eksik öğeyi tamamlama",
      "Sayı ve şekil örüntüsünü ilişkilendirme",
    ],
    difficulty: [
      "Kuralı belirleme.",
      "Örüntüyü genişletme.",
      "Eksik öğeyi bulma.",
    ],
    family: "oruntu",
  }),

  // ─── 3. SINIF ──────────────────────────────────────────────────────────────
  ak({
    grade: 3,
    topicId: "dogal_sayilar",
    slug: "toplama-islemi",
    title: "Üç Basamaklı Sayılarla Toplama",
    description:
      "3. sınıf toplama çalışma kağıdı: dört basamağa kadar elde ederek toplama ve problemler. PDF, cevap anahtarı ve çözüm ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı en çok dört basamaklı doğal sayılarla elde ederek toplama işlemini ve toplama içeren çok adımlı problemleri pekiştirir.",
    skills: [
      "Üç ve dört basamaklı toplama",
      "Elde ederek toplama",
      "Toplamı tahmin etme",
      "Toplama içeren problemler",
    ],
    difficulty: [
      "Elde olmadan toplama.",
      "Elde ederek toplama.",
      "Çok adımlı toplama problemleri.",
    ],
    family: "toplama-islemi",
  }),
  ak({
    grade: 3,
    topicId: "dogal_sayilar",
    slug: "cikarma-islemi",
    title: "Çıkarma İşlemi",
    description:
      "3. sınıf çıkarma çalışma kağıdı: dört basamağa kadar onluk bozarak çıkarma ve problemler. PDF + cevap anahtarı + çözüm, ücretsiz.",
    intro:
      "Bu çalışma kağıdı en çok dört basamaklı doğal sayılarla onluk bozarak çıkarma işlemini ve çıkarma içeren problemleri pekiştirir.",
    skills: [
      "Onluk bozarak çıkarma",
      "Ardışık bozma gerektiren çıkarma",
      "Toplama ile çıkarmayı doğrulama",
      "Çıkarma içeren problemler",
    ],
    difficulty: [
      "Tek bozmalı çıkarma.",
      "Ardışık bozmalı çıkarma.",
      "Çıkarma gerektiren problemler.",
    ],
    family: "cikarma-islemi",
  }),
  ak({
    grade: 3,
    topicId: "dogal_sayilar",
    slug: "carpma-islemi",
    title: "Çarpma İşlemi",
    description:
      "3. sınıf çarpma çalışma kağıdı: iki basamaklı sayılarla çarpma ve çarpım tablosu. PDF, cevap anahtarı ve adım adım çözüm ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı çarpım tablosunu kullanarak iki basamaklı doğal sayılarla çarpma işlemini ve çarpma içeren problemleri pekiştirir.",
    skills: [
      "Çarpım tablosunu kullanma",
      "İki basamaklı bir sayıyı bir basamaklıyla çarpma",
      "İki basamaklı sayıları çarpma",
      "Çarpma içeren problemler",
    ],
    difficulty: [
      "Bir basamaklı çarpan ile çarpma.",
      "İki basamaklı çarpma.",
      "Çarpma gerektiren problemler.",
    ],
    family: "carpma-islemi",
  }),
  ak({
    grade: 3,
    topicId: "dogal_sayilar",
    slug: "bolmeye-giris",
    title: "Bölme İşlemine Giriş",
    description:
      "3. sınıf bölme çalışma kağıdı: bölmeyi paylaştırma olarak anlama ve basit bölme. PDF + cevap anahtarı + çözüm, ücretsiz üret.",
    intro:
      "Bu çalışma kağıdı bölme işlemini eşit paylaştırma ve gruplama olarak anlamayı; iki basamaklı bir sayıyı bir basamaklıya bölmeyi pekiştirir.",
    skills: [
      "Bölmeyi paylaştırma olarak anlama",
      "Çarpma-bölme ilişkisini kullanma",
      "İki basamaklıyı bir basamaklıya bölme",
      "Bölme içeren basit problemler",
    ],
    difficulty: [
      "Kalansız basit bölme.",
      "Çarpmadan bölmeye geçiş.",
      "Bölme gerektiren problemler.",
    ],
    family: "bolme-islemi",
  }),
  ak({
    grade: 3,
    topicId: "kesirler",
    slug: "kesirlere-giris",
    title: "Kesirlere Giriş: Yarım, Çeyrek, Bütün",
    description:
      "3. sınıf kesirler çalışma kağıdı: bütün, yarım, çeyrek ve birim kesirler. PDF, cevap anahtarı ve adım adım çözüm ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı bütün, yarım ve çeyrek kavramlarını model üzerinde göstermeyi; bir bütünü eşit parçalara ayırarak parça-bütün ilişkisini ve pay-payda kavramını pekiştirir.",
    skills: [
      "Bütün, yarım ve çeyreği modelle gösterme",
      "Bir bütünü eşit parçalara ayırma",
      "Pay ve payda kavramını kullanma",
      "Basit kesirleri yazma",
    ],
    difficulty: [
      "Yarım ve çeyreği tanıma.",
      "Pay-payda ile basit kesir yazma.",
      "Parça-bütün içeren problemler.",
    ],
    family: "kesir-temel",
  }),
  ak({
    grade: 3,
    topicId: "geometri",
    slug: "cevre-hesaplama",
    title: "Çevre Hesaplama",
    description:
      "3. sınıf çevre çalışma kağıdı: düzgün çokgenlerin çevre uzunluğunu hesaplama. PDF + cevap anahtarı + adım adım çözüm, ücretsiz.",
    intro:
      "Bu çalışma kağıdı bir şeklin kenar uzunluklarını toplayarak çevresini bulmayı; düzgün çokgenlerde çevre hesaplamayı pekiştirir.",
    skills: [
      "Kenarları toplayarak çevre bulma",
      "Düzgün çokgende çevre hesaplama",
      "Verilen çevreden kenar bulma",
      "Çevre içeren problemler",
    ],
    difficulty: [
      "Kenarları toplama.",
      "Düzgün çokgende çevre.",
      "Verilen çevreden kenar bulma.",
    ],
    family: "cevre",
  }),
  ak({
    grade: 3,
    topicId: "geometri",
    slug: "simetri",
    title: "Simetri ve Simetri Ekseni",
    description:
      "3. sınıf simetri çalışma kağıdı: simetri eksenini belirleme ve simetrik şekil oluşturma. PDF, cevap anahtarı ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı bir şeklin simetri eksenini belirlemeyi ve verilen eksene göre simetrik şekiller oluşturmayı pekiştirir.",
    skills: [
      "Simetri eksenini belirleme",
      "Simetrik olan/olmayan şekilleri ayırt etme",
      "Eksene göre simetriğini çizme",
      "Birden fazla simetri eksenini bulma",
    ],
    difficulty: [
      "Simetri eksenini bulma.",
      "Simetriğini tamamlama.",
      "Birden fazla eksen veya karmaşık şekil.",
    ],
  }),
  ak({
    grade: 3,
    topicId: "olcme",
    slug: "uzunluk-olculeri",
    title: "Uzunluk Ölçüleri (km, m, cm)",
    description:
      "3. sınıf uzunluk ölçüleri çalışma kağıdı: km, m, cm, mm arası dönüşüm ve problemler. PDF + cevap anahtarı + çözüm, ücretsiz.",
    intro:
      "Bu çalışma kağıdı kilometre, metre, santimetre ve milimetre arasındaki dönüşümleri ve bu birimleri kullanan problemleri pekiştirir.",
    skills: [
      "m-cm ve cm-mm dönüşümü",
      "km-m dönüşümü",
      "Uygun birimi seçme",
      "Uzunluk içeren problemler",
    ],
    difficulty: [
      "Komşu birim dönüşümü.",
      "Birkaç birim arası dönüşüm.",
      "Dönüşüm + işlem problemleri.",
    ],
  }),
  ak({
    grade: 3,
    topicId: "olcme",
    slug: "zaman-olcme",
    title: "Zaman Ölçme (Saat ve Dakika)",
    description:
      "3. sınıf zaman ölçme çalışma kağıdı: saat-dakika ilişkisi ve zaman problemleri. PDF, cevap anahtarı ve adım adım çözüm ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı saat, dakika ve saniye arasındaki ilişkiyi kullanarak zaman ölçme problemlerini çözmeyi pekiştirir.",
    skills: [
      "Saat ve dakikayı okuma",
      "Saat-dakika dönüşümü",
      "Geçen süreyi hesaplama",
      "Zaman içeren problemler",
    ],
    difficulty: [
      "Saati okuma.",
      "Geçen süreyi bulma.",
      "Çok adımlı zaman problemleri.",
    ],
    family: "saat-okuma",
  }),
  ak({
    grade: 3,
    topicId: "cebir",
    slug: "oruntude-kural",
    title: "Örüntülerde Kural Bulma",
    description:
      "3. sınıf örüntü çalışma kağıdı: sayı ve şekil örüntülerinde kuralı bulma ve tamamlama. PDF + cevap anahtarı + çözüm, ücretsiz.",
    intro:
      "Bu çalışma kağıdı sayı ve şekil örüntülerindeki kuralı belirlemeyi ve eksik öğeleri kurala göre tamamlamayı pekiştirir.",
    skills: [
      "Örüntüdeki kuralı sözel ifade etme",
      "Kurala göre örüntüyü sürdürme",
      "Eksik öğeleri tamamlama",
      "Kuralı verilen örüntü oluşturma",
    ],
    difficulty: [
      "Sabit artan örüntü kuralı.",
      "Değişen adımlı örüntü.",
      "Kuralı verilen örüntüyü kurma.",
    ],
    family: "oruntu",
  }),

  // ─── 4. SINIF ──────────────────────────────────────────────────────────────
  ak({
    grade: 4,
    topicId: "dogal_sayilar",
    slug: "buyuk-sayilar",
    title: "Büyük Sayıları Okuma ve Yazma",
    description:
      "4. sınıf büyük sayılar çalışma kağıdı: altı basamağa kadar sayıları okuma, yazma ve çözümleme. PDF, cevap anahtarı ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı en çok altı basamaklı doğal sayıları okumayı, yazmayı, bölük ve basamaklarına göre çözümlemeyi ve sıralamayı pekiştirir.",
    skills: [
      "Büyük sayıları okuma ve yazma",
      "Bölük ve basamakları belirleme",
      "Basamak değerini bulma",
      "Sayıları sıralama ve karşılaştırma",
    ],
    difficulty: [
      "Dört-beş basamaklı sayılar.",
      "Altı basamaklı çözümleme.",
      "Sıralama ve karşılaştırma problemleri.",
    ],
  }),
  ak({
    grade: 4,
    topicId: "dogal_sayilar",
    slug: "carpma-islemi",
    title: "Çarpma İşlemi (Çok Basamaklı)",
    description:
      "4. sınıf çarpma çalışma kağıdı: üç basamaklıyı iki basamaklıyla çarpma ve problemler. PDF + cevap anahtarı + çözüm, ücretsiz.",
    intro:
      "Bu çalışma kağıdı üç basamaklı bir doğal sayıyı iki basamaklı bir sayı ile çarpmayı ve çarpma içeren çok adımlı problemleri pekiştirir.",
    skills: [
      "Çok basamaklı çarpma algoritması",
      "Çarpımı tahmin etme",
      "Çarpma-toplama bir arada",
      "Çarpma içeren problemler",
    ],
    difficulty: [
      "İki basamaklı çarpma.",
      "Üç basamaklıyı iki basamaklıyla çarpma.",
      "Çok adımlı çarpma problemleri.",
    ],
    family: "carpma-islemi",
  }),
  ak({
    grade: 4,
    topicId: "dogal_sayilar",
    slug: "bolme-islemi",
    title: "Bölme İşlemi",
    description:
      "4. sınıf bölme çalışma kağıdı: iki basamaklıya bölme, kalanlı bölme ve problemler. PDF, cevap anahtarı ve adım adım çözüm ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı üç basamaklı bir doğal sayıyı iki basamaklıya bölmeyi, kalanı yorumlamayı ve bölme içeren problemleri pekiştirir.",
    skills: [
      "Çok basamaklı bölme algoritması",
      "Kalanı bulma ve yorumlama",
      "Bölme işlemini doğrulama",
      "Bölme içeren problemler",
    ],
    difficulty: [
      "Bir basamaklıya bölme.",
      "İki basamaklıya bölme.",
      "Kalanı yorumlayan problemler.",
    ],
    family: "bolme-islemi",
  }),
  ak({
    grade: 4,
    topicId: "dogal_sayilar",
    slug: "dort-islem-problemleri",
    title: "Dört İşlem Problemleri",
    description:
      "4. sınıf dört işlem problemleri çalışma kağıdı: toplama, çıkarma, çarpma ve bölme içeren çok adımlı problemler. PDF + cevap anahtarı, ücretsiz.",
    intro:
      "Bu çalışma kağıdı dört işlemi birlikte gerektiren çok adımlı problemleri çözmeyi; problemi adımlara ayırarak çözüm stratejisi kurmayı pekiştirir.",
    skills: [
      "Problemi adımlara ayırma",
      "Uygun işlemi seçme",
      "Çok adımlı çözüm kurma",
      "Sonucu mantık açısından kontrol etme",
    ],
    difficulty: [
      "İki işlemli problemler.",
      "Üç-dört işlemli problemler.",
      "İşlem önceliği gerektiren problemler.",
    ],
  }),
  ak({
    grade: 4,
    topicId: "kesirler",
    slug: "kesir-cesitleri",
    title: "Kesir Çeşitleri (Basit, Bileşik, Tam Sayılı)",
    description:
      "4. sınıf kesir çeşitleri çalışma kağıdı: basit, bileşik ve tam sayılı kesirleri tanıma. PDF, cevap anahtarı ve çözüm ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı basit, bileşik ve tam sayılı kesirleri tanımayı, modelle göstermeyi ve birbirine dönüştürmeyi pekiştirir.",
    skills: [
      "Basit, bileşik ve tam sayılı kesri tanıma",
      "Kesri modelle gösterme",
      "Bileşik kesri tam sayılı kesre çevirme",
      "Tam sayılı kesri bileşik kesre çevirme",
    ],
    difficulty: [
      "Kesir türünü belirleme.",
      "Modelle gösterme.",
      "Türler arası dönüşüm.",
    ],
    family: "kesir-temel",
  }),
  ak({
    grade: 4,
    topicId: "kesirler",
    slug: "denk-kesirler",
    title: "Denk Kesirler",
    description:
      "4. sınıf denk kesirler çalışma kağıdı: eşit kesirleri model ve genişletmeyle bulma. PDF + cevap anahtarı + adım adım çözüm, ücretsiz.",
    intro:
      "Bu çalışma kağıdı eşit (denk) kesirleri model üzerinde göstermeyi ve genişletme yoluyla denk kesirler bulmayı pekiştirir.",
    skills: [
      "Denk kesirleri modelle gösterme",
      "Genişleterek denk kesir bulma",
      "İki kesrin denkliğini kontrol etme",
      "Denk kesir örnekleri verme",
    ],
    difficulty: [
      "Modelle denklik gösterme.",
      "Genişleterek denk kesir bulma.",
      "Denkliği kullanan problemler.",
    ],
    family: "denk-kesirler",
  }),
  ak({
    grade: 4,
    topicId: "kesirler",
    slug: "ondalik-gosterime-giris",
    title: "Ondalık Gösterime Giriş",
    description:
      "4. sınıf ondalık sayılar çalışma kağıdı: kesirleri ondalık gösterimle ifade etme (1/2 = 0,5). PDF, cevap anahtarı ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı paydası 10 ve 100 olan kesirleri ondalık gösterimle ifade etmeyi ve ondalık gösterimi okumayı pekiştirir.",
    skills: [
      "Kesri ondalık gösterimle yazma",
      "Ondalık gösterimi okuma",
      "Ondalık-kesir ilişkisini kurma",
      "Ondalık gösterimleri karşılaştırma",
    ],
    difficulty: [
      "Yarım/çeyreği ondalık yazma.",
      "Paydası 10/100 kesri ondalığa çevirme.",
      "Ondalık karşılaştırma ve sıralama.",
    ],
  }),
  ak({
    grade: 4,
    topicId: "geometri",
    slug: "acilar",
    title: "Açılar: Dar, Dik, Geniş",
    description:
      "4. sınıf açılar çalışma kağıdı: dar, dik, geniş ve doğru açıyı tanıma ve sınıflandırma. PDF + cevap anahtarı + çözüm, ücretsiz.",
    intro:
      "Bu çalışma kağıdı açıları dar, dik, geniş ve doğru açı olarak sınıflandırmayı ve çevredeki açıları tanımayı pekiştirir.",
    skills: [
      "Açı çeşitlerini tanıma",
      "Açıyı dik açıyla karşılaştırma",
      "Açıları sınıflandırma",
      "Şekillerdeki açıları belirleme",
    ],
    difficulty: [
      "Açı türünü tanıma.",
      "Dik açıyla karşılaştırma.",
      "Şekillerdeki açıları sınıflandırma.",
    ],
  }),
  ak({
    grade: 4,
    topicId: "geometri",
    slug: "cevre-hesaplama",
    title: "Üçgen ve Dörtgenlerde Çevre",
    description:
      "4. sınıf çevre çalışma kağıdı: üçgen, kare, dikdörtgen ve çokgenlerin çevresi. PDF, cevap anahtarı ve adım adım çözüm ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı üçgen ve dörtgenlerin çevrelerini kenar uzunluklarını toplayarak hesaplamayı ve verilen çevreden kenar bulmayı pekiştirir.",
    skills: [
      "Üçgenin çevresini bulma",
      "Kare ve dikdörtgenin çevresini hesaplama",
      "Verilen çevreden kenar bulma",
      "Çevre içeren problemler",
    ],
    difficulty: [
      "Kenarları toplama.",
      "Formülle çevre/kenar bulma.",
      "Çevre içeren problemler.",
    ],
    family: "cevre",
  }),
  ak({
    grade: 4,
    topicId: "geometri",
    slug: "alan-birim-kare",
    title: "Alan (Birim Kare ile)",
    description:
      "4. sınıf alan çalışma kağıdı: birim karelerle alan belirleme ve karşılaştırma. PDF + cevap anahtarı + çözüm, ücretsiz üret.",
    intro:
      "Bu çalışma kağıdı şekillerin alanını birim kareler kullanarak belirlemeyi, alanları karşılaştırmayı ve alan kavramını çevreden ayırt etmeyi pekiştirir.",
    skills: [
      "Birim kareleri sayarak alan bulma",
      "Şekillerin alanlarını karşılaştırma",
      "Alan ve çevreyi ayırt etme",
      "Verilen alana göre şekil çizme",
    ],
    difficulty: [
      "Birim kare sayma.",
      "Yarım kareler içeren alan.",
      "Alan-çevre ayrımı gerektiren problemler.",
    ],
    family: "alan",
  }),
  ak({
    grade: 4,
    topicId: "olcme",
    slug: "birim-donusumleri",
    title: "Uzunluk Birimi Dönüşümleri",
    description:
      "4. sınıf birim dönüşümleri çalışma kağıdı: uzunluk birimleri arası dönüşüm ve problem çözme. PDF, cevap anahtarı ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı uzunluk birimleri arasında dönüşüm yapmayı ve dönüşüm gerektiren günlük hayat problemlerini pekiştirir.",
    skills: [
      "Birimler arası dönüşüm yapma",
      "Bileşik uzunlukları tek birime çevirme",
      "Dönüşüm sonrası işlem yapma",
      "Dönüşüm içeren problemler",
    ],
    difficulty: [
      "Tek adımlı dönüşüm.",
      "Çok adımlı dönüşüm.",
      "Dönüşüm + işlem problemleri.",
    ],
  }),
  ak({
    grade: 4,
    topicId: "cebir",
    slug: "oruntu-iliskiler",
    title: "Örüntü ve İlişkilerde Genelleme",
    description:
      "4. sınıf örüntü çalışma kağıdı: örüntüdeki ilişkiyi genelleme ve istenen adımı bulma. PDF + cevap anahtarı + çözüm, ücretsiz.",
    intro:
      "Bu çalışma kağıdı bir örüntüdeki ilişkiyi belirleyip genellemeyi ve örüntünün istenen adımındaki öğeyi bulmayı pekiştirir.",
    skills: [
      "Örüntüdeki kuralı genelleme",
      "İstenen adımdaki öğeyi bulma",
      "Kuralı sözel ifade etme",
      "Örüntü içeren problemler",
    ],
    difficulty: [
      "Sabit kurallı örüntüyü sürdürme.",
      "İstenen adımı kuralla bulma.",
      "Kuralı genelleyen problemler.",
    ],
    family: "oruntu",
  }),

  // ─── 5. SINIF ──────────────────────────────────────────────────────────────
  ak({
    grade: 5,
    topicId: "dogal_sayilar",
    slug: "islem-onceligi",
    title: "İşlem Önceliği",
    description:
      "5. sınıf işlem önceliği çalışma kağıdı: parantez, çarpma-bölme, toplama-çıkarma sırası. PDF, cevap anahtarı ve adım adım çözüm dahil, ücretsiz üret.",
    intro:
      "İçinde birden fazla işlem bulunan ifadelerde hangi işlemin önce yapılacağını belirleme becerisi, 5. sınıf doğal sayılar konusunun temel taşıdır. Bu çalışma kağıdı parantez, çarpma/bölme ve toplama/çıkarma sıralamasını adım adım pekiştirir.",
    skills: [
      "Parantez içindeki işlemleri önce yapma",
      "Çarpma ve bölmeyi soldan sağa sırayla uygulama",
      "Toplama ve çıkarmayı en son yapma",
      "İç içe parantezli ifadeleri çözümleme",
      "İşlem önceliğini günlük hayat problemlerine uygulama",
    ],
    difficulty: [
      "Tek parantezli, iki işlemli kısa ifadeler.",
      "Çarpma/bölme ile toplama/çıkarmanın karıştığı çok adımlı ifadeler.",
      "İç içe parantez veya işlem önceliğini gerektiren sözel problemler.",
    ],
  }),
  ak({
    grade: 5,
    topicId: "dogal_sayilar",
    slug: "bolme-kalanli-problemler",
    title: "Bölme ve Kalanlı Bölme Problemleri",
    description:
      "5. sınıf bölme işlemi ve kalanı yorumlama çalışma kağıdı. Bölme problemleri, kalanın anlamı; PDF + cevap anahtarı + çözüm ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı, çok basamaklı bölme işlemlerinin yanı sıra bölme sonucundaki kalanın bir problem bağlamında ne anlama geldiğini yorumlamaya odaklanır. Öğrenci, kalanı yuvarlama veya gruplama gerektiren gerçek hayat durumlarıyla pratik yapar.",
    skills: [
      "Çok basamaklı sayılarla bölme işlemi yapma",
      "Bölme işleminde kalanı bulma ve yorumlama",
      "Kalana göre sonucu yukarı/aşağı yuvarlama",
      "Bölme gerektiren sözel problemleri çözme",
      "Bölüm ve kalanı doğrulama (bölme algoritması)",
    ],
    difficulty: [
      "İki basamaklıya bölünen kalansız işlemler.",
      "Kalanlı bölme ve kalanın sayısal yorumu.",
      "Kalanı bağlama göre yorumlamayı gerektiren çok adımlı problemler.",
    ],
  }),
  ak({
    grade: 5,
    topicId: "kesirler",
    slug: "kesirlerle-toplama-cikarma",
    title: "Kesirlerle Toplama ve Çıkarma",
    description:
      "5. sınıf kesirlerle toplama ve çıkarma çalışma kağıdı: paydaları eşit ve eşit olmayan kesirler. PDF, cevap anahtarı, adım adım çözüm — ücretsiz.",
    intro:
      "Bu çalışma kağıdı, paydaları eşit ve paydaları farklı kesirlerde toplama-çıkarma becerisini kademeli olarak geliştirir. Payda eşitleme, sadeleştirme ve tam sayılı kesirlere geçiş adımları örneklerle pekiştirilir.",
    skills: [
      "Paydaları eşit kesirlerde toplama ve çıkarma",
      "Paydaları eşit olmayan kesirlerde payda eşitleme",
      "Sonucu sadeleştirme",
      "Tam sayılı kesirleri bileşik kesre çevirip işlem yapma",
      "Kesir toplama-çıkarma içeren sözel problemler",
    ],
    difficulty: [
      "Paydaları eşit basit kesirlerle toplama/çıkarma.",
      "Paydaları farklı iki kesirde payda eşitleyerek işlem.",
      "Tam sayılı kesir ve sadeleştirme içeren problem çözümü.",
    ],
    family: "kesir-toplama-cikarma",
  }),
  ak({
    grade: 5,
    topicId: "kesirler",
    slug: "denk-kesirler",
    title: "Denk (Eşit) Kesirler",
    description:
      "5. sınıf denk kesirler çalışma kağıdı: eşit kesirleri bulma, genişletme ve sadeleştirme. PDF + cevap anahtarı + çözüm, ücretsiz üret.",
    intro:
      "Denk kesirler, bir kesrin pay ve paydasını aynı sayıyla çarparak veya bölerek elde edilen eşit değerli kesirlerdir. Bu çalışma kağıdı genişletme ve sadeleştirme yoluyla denk kesir bulmayı model ve işlemle birlikte pekiştirir.",
    skills: [
      "Bir kesrin denk kesirlerini genişleterek bulma",
      "Kesri sadeleştirerek en sade biçime getirme",
      "İki kesrin denk olup olmadığını kontrol etme",
      "Denklik ilişkisini model üzerinde gösterme",
    ],
    difficulty: [
      "Verilen kesri 2-3 ile genişletme.",
      "Sadeleştirme veya verilen denk kesirde eksik payı/paydayı bulma.",
      "Denkliği kullanarak karşılaştırma/problem çözme.",
    ],
    family: "denk-kesirler",
  }),
  ak({
    grade: 5,
    topicId: "kesirler",
    slug: "kesirleri-siralama-karsilastirma",
    title: "Kesirleri Sıralama ve Karşılaştırma",
    description:
      "5. sınıf kesirleri karşılaştırma ve sıralama çalışma kağıdı: paydası/payı eşit kesirler, sayı doğrusu. PDF + cevap anahtarı, ücretsiz.",
    intro:
      "Bu çalışma kağıdı, kesirleri büyüklük açısından karşılaştırma ve sıralama becerisini geliştirir. Paydaları eşit, payları eşit ve sayı doğrusu üzerinde konumlandırma yöntemleri örneklerle ele alınır.",
    skills: [
      "Paydaları eşit kesirleri sıralama",
      "Payları eşit kesirleri sıralama",
      "Kesirleri sayı doğrusunda gösterme",
      "Birim kesirleri karşılaştırma",
      "Karşılaştırma sembollerini (<, >, =) doğru kullanma",
    ],
    difficulty: [
      "Paydaları eşit iki kesri karşılaştırma.",
      "Payları eşit veya sayı doğrusunda sıralama.",
      "Farklı pay-paydalı birden çok kesri sıralama.",
    ],
  }),
  ak({
    grade: 5,
    topicId: "kesirler",
    slug: "yuzde-hesaplari",
    title: "Yüzde Hesapları",
    description:
      "5. sınıf yüzde çalışma kağıdı: yüzde sembolü, basit yüzde hesapları ve kesir-yüzde ilişkisi. PDF, cevap anahtarı ve çözüm dahil — ücretsiz.",
    intro:
      "Yüzde, paydası 100 olan bir kesir olarak tanıtılır. Bu çalışma kağıdı yüzde sembolünü tanımayı, basit yüzde hesaplarını ve yüzdeyi kesir/ondalık ile ilişkilendirmeyi temel düzeyde pekiştirir.",
    skills: [
      "Yüzde sembolünü tanıma ve okuma",
      "Bir miktarın %25, %50, %10'unu bulma",
      "Yüzdeyi kesir olarak ifade etme (%50 = 1/2)",
      "Basit yüzde içeren günlük hayat durumları",
    ],
    difficulty: [
      "%50 ve %25 gibi tanıdık yüzdeleri bulma.",
      "%10, %20 gibi yüzdeleri hesaplama.",
      "Yüzde-kesir ilişkisini gerektiren problemler.",
    ],
    family: "yuzde",
  }),
  ak({
    grade: 5,
    topicId: "geometri",
    slug: "ucgen-dortgen-cevre",
    title: "Üçgen ve Dörtgenlerde Çevre",
    description:
      "5. sınıf çevre hesaplama çalışma kağıdı: üçgen, kare, dikdörtgen ve çokgenlerin çevresi. PDF + cevap anahtarı + adım adım çözüm, ücretsiz.",
    intro:
      "Bir çokgenin çevresi, kenar uzunluklarının toplamıdır. Bu çalışma kağıdı üçgen, kare, dikdörtgen ve diğer çokgenlerde çevre hesaplamayı, ayrıca verilen çevreden kenar bulma gibi ters problemleri içerir.",
    skills: [
      "Üçgenin çevresini kenarları toplayarak bulma",
      "Kare ve dikdörtgenin çevresini hesaplama",
      "Verilen çevreden bilinmeyen kenarı bulma",
      "Düzgün çokgenlerde çevre hesaplama",
      "Çevre içeren günlük hayat problemleri",
    ],
    difficulty: [
      "Kenarları verilen şeklin çevresini toplama.",
      "Kare/dikdörtgende formülle çevre veya kenar bulma.",
      "Verilen çevreden kenar bulma içeren problemler.",
    ],
    family: "cevre",
  }),
  ak({
    grade: 5,
    topicId: "geometri",
    slug: "dikdortgen-kare-alan",
    title: "Dikdörtgen ve Karenin Alanı",
    description:
      "5. sınıf alan hesaplama çalışma kağıdı: dikdörtgen ve karenin alanı, birim kare sayma. PDF, cevap anahtarı ve çözüm ile ücretsiz üret.",
    intro:
      "Alan, bir şeklin kapladığı yüzeydir ve birim karelerle ölçülür. Bu çalışma kağıdı dikdörtgen ve karede alanı hem birim kare sayarak hem de uzunluk × genişlik formülüyle hesaplamayı pekiştirir.",
    skills: [
      "Birim kareleri sayarak alan bulma",
      "Dikdörtgenin alanını (kısa × uzun kenar) hesaplama",
      "Karenin alanını (kenar × kenar) hesaplama",
      "Verilen alandan kenar bulma",
      "Alan ve çevreyi ayırt etme",
    ],
    difficulty: [
      "Birim kare sayarak alan bulma.",
      "Formülle dikdörtgen/kare alanı hesaplama.",
      "Verilen alandan kenar bulma veya birleşik şekiller.",
    ],
    family: "alan",
  }),
  ak({
    grade: 5,
    topicId: "cebir",
    slug: "basit-denklemler",
    title: "Basit Denklemler (x + a = b)",
    description:
      "5. sınıf denklem çözme çalışma kağıdı: bir bilinmeyenli basit denklemler ve sözel ifadeleri denkleme çevirme. PDF + cevap anahtarı, ücretsiz.",
    intro:
      "Bu çalışma kağıdı, x + a = b ve x − a = b biçimindeki bir bilinmeyenli basit denklemleri çözmeyi ve sözel olarak verilen durumları cebirsel denklem olarak yazmayı pekiştirir.",
    skills: [
      "x + a = b biçimindeki denklemleri çözme",
      "x − a = b biçimindeki denklemleri çözme",
      "Bilinmeyeni yalnız bırakma mantığını kullanma",
      "Sözel durumu cebirsel denkleme çevirme",
      "Çözümü denklemde yerine koyarak doğrulama",
    ],
    difficulty: [
      "Tek adımda çözülen x + a = b denklemleri.",
      "Sözel ifadeyi denkleme çevirip çözme.",
      "Çok adımlı kurulum gerektiren problem denklemleri.",
    ],
    family: "denklem",
  }),
  ak({
    grade: 5,
    topicId: "olcme",
    slug: "uzunluk-olculeri-donusum",
    title: "Uzunluk Ölçüleri ve Dönüşümler",
    description:
      "5. sınıf uzunluk ölçüleri çalışma kağıdı: km, m, cm, mm arası dönüşüm ve problemler. PDF, cevap anahtarı ve adım adım çözüm — ücretsiz.",
    intro:
      "Bu çalışma kağıdı kilometre, metre, santimetre ve milimetre arasındaki birim dönüşümlerini ve bu birimleri kullanan günlük hayat problemlerini pekiştirir.",
    skills: [
      "km-m, m-cm, cm-mm dönüşümleri yapma",
      "Birden fazla birim içeren uzunlukları tek birime çevirme",
      "Uzunluk toplama-çıkarma problemleri",
      "Ölçek/uzaklık içeren sözel problemler",
    ],
    difficulty: [
      "Komşu birimler arası tek adımlı dönüşüm.",
      "Birkaç birim arası dönüşüm ve işlem.",
      "Dönüşüm + dört işlem gerektiren problemler.",
    ],
  }),

  // ─── 6. SINIF ──────────────────────────────────────────────────────────────
  ak({
    grade: 6,
    topicId: "dogal_sayilar",
    slug: "tam-sayilarla-toplama-cikarma",
    title: "Tam Sayılarla Toplama ve Çıkarma",
    description:
      "6. sınıf tam sayılar çalışma kağıdı: negatif-pozitif tam sayılarda toplama ve çıkarma, sayı doğrusu. PDF + cevap anahtarı + çözüm, ücretsiz.",
    intro:
      "Bu çalışma kağıdı tam sayıları sayı doğrusunda göstermeyi ve negatif-pozitif tam sayılarla toplama-çıkarma işlemlerini, işaret kurallarıyla birlikte pekiştirir.",
    skills: [
      "Tam sayıları sayı doğrusunda gösterme",
      "Aynı işaretli tam sayıları toplama",
      "Farklı işaretli tam sayıları toplama",
      "Tam sayılarda çıkarmayı toplamaya çevirme",
      "Mutlak değeri yorumlama",
    ],
    difficulty: [
      "Sayı doğrusunda gösterim ve aynı işaretli toplama.",
      "Farklı işaretli toplama-çıkarma.",
      "Çok terimli ifadeler ve sözel problemler.",
    ],
  }),
  ak({
    grade: 6,
    topicId: "dogal_sayilar",
    slug: "bolunebilme-kurallari",
    title: "Bölünebilme Kuralları",
    description:
      "6. sınıf bölünebilme kuralları çalışma kağıdı: 2, 3, 4, 5, 6, 9, 10 ile bölünebilme. PDF, cevap anahtarı ve adım adım çözüm — ücretsiz üret.",
    intro:
      "Bu çalışma kağıdı bir doğal sayının 2, 3, 4, 5, 6, 9 ve 10 ile kalansız bölünüp bölünmediğini, bölme işlemi yapmadan kurallarla belirlemeyi pekiştirir.",
    skills: [
      "2, 5, 10 ile bölünebilme kurallarını uygulama",
      "3 ve 9 ile bölünebilmede rakamlar toplamını kullanma",
      "4 ve 6 ile bölünebilme kuralları",
      "Birden fazla kurala uyan sayıları bulma",
      "Eksik rakamı bölünebilme kuralına göre tamamlama",
    ],
    difficulty: [
      "2, 5, 10 ile bölünebilmeyi belirleme.",
      "3, 9, 4, 6 kurallarını uygulama.",
      "Bilinmeyen rakamı kurala göre bulma.",
    ],
  }),
  ak({
    grade: 6,
    topicId: "dogal_sayilar",
    slug: "obeb-okek",
    title: "OBEB ve OKEK",
    description:
      "6. sınıf OBEB-OKEK çalışma kağıdı: ortak bölen, ortak kat, en büyük ortak bölen ve en küçük ortak kat problemleri. PDF + cevap anahtarı, ücretsiz.",
    intro:
      "Bu çalışma kağıdı iki sayının ortak bölenlerini ve ortak katlarını bulmayı, OBEB (en büyük ortak bölen) ve OKEK (en küçük ortak kat) kavramlarını ve bunları gerektiren problemleri pekiştirir.",
    skills: [
      "Bir sayının bölenlerini ve katlarını listeleme",
      "İki sayının ortak bölenlerini bulma (OBEB)",
      "İki sayının ortak katlarını bulma (OKEK)",
      "OBEB-OKEK içeren paylaştırma ve periyot problemleri",
    ],
    difficulty: [
      "Küçük sayıların bölen/katlarını listeleme.",
      "İki sayının OBEB veya OKEK'ini bulma.",
      "OBEB/OKEK seçimi gerektiren sözel problemler.",
    ],
  }),
  ak({
    grade: 6,
    topicId: "dogal_sayilar",
    slug: "asal-sayilar-carpanlar",
    title: "Asal Sayılar ve Çarpanlara Ayırma",
    description:
      "6. sınıf asal sayılar çalışma kağıdı: asal sayıları tanıma, asal çarpanlara ayırma. PDF, cevap anahtarı ve adım adım çözüm ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı asal sayı, çarpan ve kat kavramlarını açıklamayı; bir doğal sayıyı asal çarpanlarına ayırmayı pekiştirir.",
    skills: [
      "Asal sayıları tanıma ve örnek verme",
      "Bir sayının çarpanlarını bulma",
      "Asal çarpanlara ayırma (çarpan ağacı)",
      "Asal/bileşik sayıları ayırt etme",
    ],
    difficulty: [
      "Küçük sayıların asal olup olmadığını belirleme.",
      "Çarpanları listeleme ve asal çarpanlara ayırma.",
      "Asal çarpanları kullanan problemler.",
    ],
  }),
  ak({
    grade: 6,
    topicId: "kesirler",
    slug: "kesirlerle-carpma",
    title: "Kesirlerle Çarpma",
    description:
      "6. sınıf kesirlerle çarpma çalışma kağıdı: kesir × kesir, kesir × doğal sayı ve problemler. PDF + cevap anahtarı + adım adım çözüm, ücretsiz.",
    intro:
      "Bu çalışma kağıdı kesirlerle çarpma işlemini model ve algoritma ile açıklar; kesir × kesir, kesir × doğal sayı ve sadeleştirerek çarpma becerilerini pekiştirir.",
    skills: [
      "Kesir × doğal sayı işlemini yapma",
      "Kesir × kesir işlemini pay-payda çarparak yapma",
      "Çarpmadan önce sadeleştirme",
      "Tam sayılı kesirlerle çarpma",
      "Kesirle çarpma içeren sözel problemler",
    ],
    difficulty: [
      "Kesir × doğal sayı.",
      "Kesir × kesir ve sadeleştirme.",
      "Tam sayılı kesir ve çok adımlı problemler.",
    ],
  }),
  ak({
    grade: 6,
    topicId: "kesirler",
    slug: "kesirlerle-bolme",
    title: "Kesirlerle Bölme",
    description:
      "6. sınıf kesirlerle bölme çalışma kağıdı: ters çevirip çarpma yöntemi ve problemler. PDF, cevap anahtarı ve adım adım çözüm ile ücretsiz üret.",
    intro:
      "Bu çalışma kağıdı kesirlerle bölme işlemini, böleni ters çevirip çarpma (ters işlem) yöntemiyle açıklar ve kesir bölme içeren problemleri pekiştirir.",
    skills: [
      "Bir kesrin çarpmaya göre tersini bulma",
      "Kesir ÷ kesir işlemini yapma",
      "Doğal sayı ÷ kesir ve kesir ÷ doğal sayı",
      "Tam sayılı kesirlerde bölme",
      "Bölme içeren paylaştırma problemleri",
    ],
    difficulty: [
      "Birim kesre bölme.",
      "Kesir ÷ kesir (ters çevirip çarpma).",
      "Tam sayılı kesir ve sözel problemler.",
    ],
  }),
  ak({
    grade: 6,
    topicId: "kesirler",
    slug: "ondalik-gosterimle-dort-islem",
    title: "Ondalık Gösterimlerle Dört İşlem",
    description:
      "6. sınıf ondalık sayılar çalışma kağıdı: ondalık gösterimlerle toplama, çıkarma, çarpma ve bölme. PDF + cevap anahtarı + çözüm, ücretsiz.",
    intro:
      "Bu çalışma kağıdı ondalık gösterimlerle dört işlemi pekiştirir: virgülleri hizalayarak toplama-çıkarma, basamak kaydırarak çarpma-bölme ve ondalık içeren problemler.",
    skills: [
      "Ondalık sayılarda virgül hizalayarak toplama-çıkarma",
      "Ondalık sayıları çarpma ve virgül konumunu belirleme",
      "Ondalık sayılarda bölme",
      "Ondalık-kesir dönüşümünü kullanma",
      "Para/ölçü içeren ondalık problemler",
    ],
    difficulty: [
      "Ondalıkla toplama-çıkarma.",
      "Ondalıkla çarpma veya 10/100 ile bölme.",
      "Dört işlemi birleştiren problemler.",
    ],
  }),
  ak({
    grade: 6,
    topicId: "kesirler",
    slug: "yuzde-problemleri",
    title: "Yüzde Problemleri",
    description:
      "6. sınıf yüzde problemleri çalışma kağıdı: indirim, zam, kar-zarar ve yüzde-kesir-ondalık ilişkisi. PDF, cevap anahtarı ve çözüm ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı yüzde ile ilgili problemleri (bir miktarın yüzdesi, yüzde artış/azalış, indirim-zam) çözmeyi ve yüzdeyi kesir/ondalık ile ilişkilendirmeyi pekiştirir.",
    skills: [
      "Bir miktarın belirli yüzdesini hesaplama",
      "Yüzde artış ve azalış (zam, indirim) bulma",
      "Yüzdeyi kesir ve ondalık ile ilişkilendirme",
      "Verilen yüzdeden bütünü bulma",
      "Kar-zarar ve indirim problemleri",
    ],
    difficulty: [
      "Bir sayının yüzdesini bulma.",
      "Yüzde artış/azalış ve indirim hesabı.",
      "Verilen parçadan bütünü bulan ters problemler.",
    ],
    family: "yuzde",
  }),
  ak({
    grade: 6,
    topicId: "geometri",
    slug: "paralelkenar-ucgen-alan",
    title: "Paralelkenar ve Üçgenin Alanı",
    description:
      "6. sınıf alan çalışma kağıdı: paralelkenar ve üçgenin alanı, taban-yükseklik ilişkisi. PDF + cevap anahtarı + adım adım çözüm, ücretsiz.",
    intro:
      "Bu çalışma kağıdı paralelkenarın (taban × yükseklik) ve üçgenin (taban × yükseklik ÷ 2) alanını hesaplamayı, taban ve yüksekliği doğru belirlemeyi pekiştirir.",
    skills: [
      "Paralelkenarda taban ve yüksekliği belirleme",
      "Paralelkenarın alanını hesaplama",
      "Üçgenin alanını hesaplama",
      "Verilen alandan taban veya yükseklik bulma",
      "Alan içeren günlük hayat problemleri",
    ],
    difficulty: [
      "Taban-yükseklik verilen paralelkenar/üçgen alanı.",
      "Verilen alandan kenar/yükseklik bulma.",
      "Birleşik şekiller ve problemler.",
    ],
    family: "alan",
  }),
  ak({
    grade: 6,
    topicId: "geometri",
    slug: "aci-cesitleri",
    title: "Açı Çeşitleri: Tümler, Bütünler, Komşu ve Ters Açılar",
    description:
      "6. sınıf açılar çalışma kağıdı: tümler, bütünler, komşu ve ters açılar; açı hesaplama. PDF, cevap anahtarı ve çözüm ile ücretsiz üret.",
    intro:
      "Bu çalışma kağıdı açıları çeşitlerine göre tanımayı ve tümler (toplamı 90°), bütünler (toplamı 180°), komşu ve ters açı ilişkilerini kullanarak bilinmeyen açıyı bulmayı pekiştirir.",
    skills: [
      "Tümler açıları bulma (toplam 90°)",
      "Bütünler açıları bulma (toplam 180°)",
      "Komşu açıları tanıma",
      "Ters açıların eşitliğini kullanma",
      "Açı ilişkileriyle bilinmeyeni hesaplama",
    ],
    difficulty: [
      "Tümler/bütünler açıyı doğrudan bulma.",
      "Komşu ve ters açı ilişkilerini kullanma.",
      "Birden çok açı ilişkisini birleştiren problemler.",
    ],
  }),
  ak({
    grade: 6,
    topicId: "cebir",
    slug: "cebirsel-ifadeler",
    title: "Cebirsel İfadeler",
    description:
      "6. sınıf cebirsel ifadeler çalışma kağıdı: değişken kullanma, ifade yazma ve değer hesaplama. PDF + cevap anahtarı + adım adım çözüm, ücretsiz.",
    intro:
      "Bu çalışma kağıdı bir bilinmeyeni (değişkeni) temsil eden cebirsel ifadeler yazmayı ve değişkene değer vererek ifadenin sayısal değerini hesaplamayı pekiştirir.",
    skills: [
      "Sözel durumu cebirsel ifadeyle yazma",
      "Değişkene değer vererek ifadeyi hesaplama",
      "Benzer terimleri tanıma",
      "İfadeyi sadeleştirme (temel)",
    ],
    difficulty: [
      "Tek terimli ifade yazma ve değer hesaplama.",
      "İki terimli ifadeler ve sözel çeviri.",
      "Benzer terim toplama ve çok adımlı değer bulma.",
    ],
  }),
  ak({
    grade: 6,
    topicId: "cebir",
    slug: "birinci-dereceden-denklemler",
    title: "Birinci Dereceden Bir Bilinmeyenli Denklemler",
    description:
      "6. sınıf denklem çözme çalışma kağıdı: ax + b = c biçimindeki denklemleri kurma ve çözme. PDF, cevap anahtarı ve çözüm ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı birinci dereceden bir bilinmeyenli denklemleri kurmayı ve eşitliğin korunumunu kullanarak çözmeyi pekiştirir; sözel problemleri denkleme çevirmeyi içerir.",
    skills: [
      "ax + b = c biçimindeki denklemleri çözme",
      "Eşitliğin her iki tarafına aynı işlemi uygulama",
      "Sözel problemi denkleme çevirme",
      "Çözümü denklemde doğrulama",
      "Denklem kurma gerektiren problemler",
    ],
    difficulty: [
      "Tek adımlı denklemler.",
      "İki adımlı (ax + b = c) denklemler.",
      "Denklem kurmayı gerektiren sözel problemler.",
    ],
    family: "denklem",
  }),
  ak({
    grade: 6,
    topicId: "veri_isleme",
    slug: "aritmetik-ortalama-ortanca-tepe",
    title: "Aritmetik Ortalama, Ortanca ve Tepe Değeri",
    description:
      "6. sınıf veri çalışma kağıdı: aritmetik ortalama, ortanca (medyan) ve tepe değeri (mod) hesaplama. PDF + cevap anahtarı + çözüm, ücretsiz.",
    intro:
      "Bu çalışma kağıdı bir veri grubunun merkezi eğilim ölçülerini — aritmetik ortalama, ortanca ve tepe değeri — hesaplamayı ve yorumlamayı pekiştirir.",
    skills: [
      "Aritmetik ortalamayı hesaplama",
      "Veriyi sıralayıp ortancayı bulma",
      "Tepe değerini (en çok tekrar eden) belirleme",
      "Ölçüleri bir bağlamda yorumlama",
      "Eksik veriyi ortalamadan geri bulma",
    ],
    difficulty: [
      "Küçük veri grubunda ortalama/tepe değeri.",
      "Ortancayı sıralayarak bulma.",
      "Ortalamadan eksik veriyi bulan ters problemler.",
    ],
  }),

  // ─── 7. SINIF ──────────────────────────────────────────────────────────────
  ak({
    grade: 7,
    topicId: "dogal_sayilar",
    slug: "tam-sayilarla-carpma-bolme",
    title: "Tam Sayılarla Çarpma ve Bölme",
    description:
      "7. sınıf tam sayılar çalışma kağıdı: işaretli sayılarda çarpma-bölme ve işlem önceliği. PDF, cevap anahtarı ve adım adım çözüm ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı tam sayılarla çarpma ve bölme işlemlerini işaret kurallarıyla birlikte pekiştirir; çok işlemli ifadelerde işlem önceliğini içerir.",
    skills: [
      "Tam sayılarda çarpmanın işaret kuralı",
      "Tam sayılarda bölmenin işaret kuralı",
      "Çok işlemli ifadelerde işlem önceliği",
      "Tam sayı işlemleri içeren problemler",
    ],
    difficulty: [
      "İki tam sayıyı çarpma/bölme.",
      "İşaret + işlem önceliği birlikte.",
      "Çok adımlı ifade ve sözel problemler.",
    ],
  }),
  ak({
    grade: 7,
    topicId: "dogal_sayilar",
    slug: "uslu-sayilar",
    title: "Üslü Sayılar (Tam Sayıların Kuvvetleri)",
    description:
      "7. sınıf üslü sayılar çalışma kağıdı: taban-üs, kuvvet hesaplama ve üslü ifadelerle işlemler. PDF + cevap anahtarı + çözüm, ücretsiz üret.",
    intro:
      "Bu çalışma kağıdı bir tam sayının kuvvetini (üslü gösterim) hesaplamayı, taban ve üs kavramını ve üslü ifadelerle temel işlemleri pekiştirir.",
    skills: [
      "Taban ve üssü belirleme",
      "Bir sayının kuvvetini hesaplama",
      "Negatif tabanlı kuvvetlerin işaretini belirleme",
      "Üslü ifadeleri karşılaştırma",
      "Üslü sayı içeren işlemler",
    ],
    difficulty: [
      "Küçük tabanlı kuvvet hesaplama.",
      "Negatif taban ve işaret belirleme.",
      "Üslü ifadelerle çok adımlı işlemler.",
    ],
  }),
  ak({
    grade: 7,
    topicId: "kesirler",
    slug: "rasyonel-sayilar",
    title: "Rasyonel Sayılar",
    description:
      "7. sınıf rasyonel sayılar çalışma kağıdı: rasyonel sayıyı tanıma, sayı doğrusunda gösterme ve farklı biçimlerde yazma. PDF + cevap anahtarı, ücretsiz.",
    intro:
      "Bu çalışma kağıdı rasyonel sayıları tanımayı, sayı doğrusunda göstermeyi ve kesir-ondalık biçimleri arasında geçiş yapmayı pekiştirir.",
    skills: [
      "Rasyonel sayıyı tanıma ve örnek verme",
      "Rasyonel sayıları sayı doğrusunda gösterme",
      "Kesir-ondalık biçimleri arasında dönüşüm",
      "Rasyonel sayıları sıralama ve karşılaştırma",
    ],
    difficulty: [
      "Rasyonel sayıyı tanıma ve gösterme.",
      "Biçim dönüşümü ve karşılaştırma.",
      "Sıralama ve sayı doğrusu konumlandırma problemleri.",
    ],
  }),
  ak({
    grade: 7,
    topicId: "kesirler",
    slug: "rasyonel-sayilarla-islemler",
    title: "Rasyonel Sayılarla İşlemler",
    description:
      "7. sınıf rasyonel sayılarla işlemler çalışma kağıdı: toplama, çıkarma, çarpma ve bölme. PDF, cevap anahtarı ve adım adım çözüm ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı rasyonel sayılarla dört işlemi (işaret kuralları dahil) pekiştirir ve rasyonel sayı içeren problemleri ele alır.",
    skills: [
      "Rasyonel sayılarla toplama ve çıkarma",
      "Rasyonel sayılarla çarpma",
      "Rasyonel sayılarla bölme",
      "İşaret kurallarını uygulama",
      "Rasyonel sayı içeren problemler",
    ],
    difficulty: [
      "Aynı işaretli toplama-çıkarma.",
      "Farklı işaretli dört işlem.",
      "Çok adımlı ifadeler ve problemler.",
    ],
  }),
  ak({
    grade: 7,
    topicId: "cebir",
    slug: "oran-oranti",
    title: "Oran ve Orantı",
    description:
      "7. sınıf oran orantı çalışma kağıdı: oran kurma, orantı ve günlük hayat problemleri. PDF + cevap anahtarı + adım adım çözüm, ücretsiz üret.",
    intro:
      "Bu çalışma kağıdı iki çokluğu oranlamayı, orantı kurmayı ve orantıyı kullanarak bilinmeyeni bulmayı; ölçek, hız ve karışım gibi günlük hayat problemlerini pekiştirir.",
    skills: [
      "İki çokluğun oranını yazma ve sadeleştirme",
      "Orantı kurma ve içler-dışlar çarpımı",
      "Orantıdan bilinmeyeni bulma",
      "Ölçek ve harita problemleri",
      "Oran-orantı içeren günlük hayat problemleri",
    ],
    difficulty: [
      "Basit oran kurma ve sadeleştirme.",
      "Orantıdan bilinmeyeni bulma.",
      "Ölçek/karışım gibi çok adımlı problemler.",
    ],
    family: "oran",
  }),
  ak({
    grade: 7,
    topicId: "cebir",
    slug: "dogru-ters-oranti",
    title: "Doğru ve Ters Orantı",
    description:
      "7. sınıf doğru ve ters orantı çalışma kağıdı: orantı türünü belirleme ve problem çözme. PDF, cevap anahtarı ve çözüm ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı iki çokluk arasındaki ilişkinin doğru mu ters mi orantılı olduğunu belirlemeyi ve uygun orantı kurarak problem çözmeyi pekiştirir.",
    skills: [
      "Doğru orantılı çoklukları tanıma",
      "Ters orantılı çoklukları tanıma",
      "Orantı türüne göre denklem kurma",
      "İşçi-gün, hız-zaman gibi ters orantı problemleri",
      "Doğru orantı ile ölçek/fiyat problemleri",
    ],
    difficulty: [
      "Orantı türünü belirleme.",
      "Tek adımlı doğru/ters orantı problemi.",
      "Çok adımlı işçi-gün/karışım problemleri.",
    ],
    family: "oran",
  }),
  ak({
    grade: 7,
    topicId: "cebir",
    slug: "esitsizlikler",
    title: "Birinci Dereceden Eşitsizlikler",
    description:
      "7. sınıf eşitsizlikler çalışma kağıdı: bir bilinmeyenli eşitsizlik çözme ve sayı doğrusunda gösterme. PDF + cevap anahtarı + çözüm, ücretsiz.",
    intro:
      "Bu çalışma kağıdı birinci dereceden bir bilinmeyenli eşitsizlikleri çözmeyi ve çözüm kümesini sayı doğrusunda göstermeyi pekiştirir.",
    skills: [
      "Eşitsizlik sembollerini (<, >, ≤, ≥) okuma",
      "Bir bilinmeyenli eşitsizliği çözme",
      "Negatif sayıyla çarpma/bölmede yön değiştirme",
      "Çözüm kümesini sayı doğrusunda gösterme",
      "Eşitsizlik kuran problemler",
    ],
    difficulty: [
      "Tek adımlı eşitsizlik çözme.",
      "İki adımlı çözüm ve yön değişimi.",
      "Eşitsizlik kuran sözel problemler.",
    ],
  }),
  ak({
    grade: 7,
    topicId: "geometri",
    slug: "cember-daire-uzunluk-alan",
    title: "Çember ve Dairede Uzunluk ve Alan",
    description:
      "7. sınıf çember ve daire çalışma kağıdı: çevre (çember uzunluğu) ve daire alanı, π kullanımı. PDF, cevap anahtarı ve çözüm ile ücretsiz üret.",
    intro:
      "Bu çalışma kağıdı çemberin uzunluğunu (2πr) ve dairenin alanını (πr²) π sayısını kullanarak hesaplamayı; yarıçap, çap ve bu büyüklükler arasındaki ilişkiyi pekiştirir.",
    skills: [
      "Yarıçap ve çap arasında dönüşüm",
      "Çemberin uzunluğunu (çevre) hesaplama",
      "Dairenin alanını hesaplama",
      "Verilen çevre/alandan yarıçap bulma",
      "Çember-daire içeren günlük hayat problemleri",
    ],
    difficulty: [
      "Yarıçap verildiğinde çevre/alan bulma.",
      "Çaptan veya verilen değerden geri hesap.",
      "Birleşik şekil ve problemler.",
    ],
    family: "cevre",
  }),
  ak({
    grade: 7,
    topicId: "geometri",
    slug: "daire-dilimi-merkez-aci",
    title: "Daire Dilimi ve Merkez Açı",
    description:
      "7. sınıf daire dilimi çalışma kağıdı: merkez açı ile daire dilimi alanı/yay uzunluğu ilişkisi. PDF + cevap anahtarı + adım adım çözüm, ücretsiz.",
    intro:
      "Bu çalışma kağıdı merkez açının gördüğü daire diliminin alanı ve yay uzunluğu ile 360° arasındaki orantı ilişkisini kullanarak hesap yapmayı pekiştirir.",
    skills: [
      "Merkez açıyı tanıma",
      "Daire dilimi alanını orantıyla hesaplama",
      "Yay uzunluğunu orantıyla hesaplama",
      "Verilen dilim alanından merkez açıyı bulma",
    ],
    difficulty: [
      "90°, 180° gibi tanıdık açılarda dilim hesabı.",
      "Genel merkez açıyla orantı kurma.",
      "Dilim alanından açı bulan ters problemler.",
    ],
  }),
  ak({
    grade: 7,
    topicId: "veri_isleme",
    slug: "daire-grafigi",
    title: "Daire Grafiği",
    description:
      "7. sınıf daire grafiği çalışma kağıdı: veriyi daire grafiğiyle gösterme, yüzde ve merkez açı hesabı. PDF, cevap anahtarı ve çözüm ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı bir veri grubunu daire grafiğiyle göstermeyi, her kategoriye düşen yüzdeyi ve merkez açıyı hesaplamayı, grafiği okuyup yorumlamayı pekiştirir.",
    skills: [
      "Veriyi yüzdeye çevirme",
      "Her kategori için merkez açıyı hesaplama (yüzde × 3,6)",
      "Daire grafiğini okuma ve yorumlama",
      "Grafikten eksik veriyi bulma",
    ],
    difficulty: [
      "Verilen yüzdelerden merkez açı bulma.",
      "Ham veriyi yüzde ve açıya çevirme.",
      "Grafikten geri okuma ve problem çözme.",
    ],
  }),

  // ─── 8. SINIF — LGS HAZIRLIK ─────────────────────────────────────────────
  // LGS'de en çok soru çıkan alt-konular. description'larda "LGS" çerçevesi
  // long-tail aramayı yakalar; /lgs-matematik hub bu sayfalara link verir.
  ak({
    grade: 8,
    topicId: "dogal_sayilar",
    slug: "uslu-ifadeler",
    title: "Üslü İfadeler",
    description:
      "8. sınıf LGS üslü ifadeler çalışma kağıdı: üslü sayılarla çarpma-bölme, negatif ve sıfır üs, üssün üssü. PDF, cevap anahtarı ve adım adım çözüm ile ücretsiz üret.",
    intro:
      "Üslü ifadeler LGS matematikte neredeyse her yıl soru çıkan temel konudur. Bu çalışma kağıdı tam sayı kuvvetlerini, negatif ve sıfır üssü, aynı tabanlı üslü sayılarda işlem kurallarını ve 10'un kuvvetleriyle gösterimi pekiştirir.",
    skills: [
      "Aynı tabanlı üslü sayılarda çarpma ve bölme",
      "Negatif tam sayı ve sıfır üssünü yorumlama",
      "Üslü bir ifadenin üssünü alma",
      "10'un tam sayı kuvvetleriyle büyük/küçük sayı yazma",
      "Üslü ifadeleri karşılaştırma ve sıralama",
    ],
    difficulty: [
      "Tek kuralla aynı tabanlı çarpma-bölme.",
      "Negatif üs ve birden çok kuralın birlikte kullanımı.",
      "LGS tarzı çok adımlı üslü ifade sadeleştirme.",
    ],
    family: "uslu-ifadeler",
  }),
  ak({
    grade: 8,
    topicId: "dogal_sayilar",
    slug: "karekoklu-ifadeler",
    title: "Kareköklü İfadeler",
    description:
      "8. sınıf LGS kareköklü ifadeler çalışma kağıdı: kareköklü sayılarla çarpma-bölme, kök içine alma/dışına çıkarma, toplama-çıkarma. PDF + cevap anahtarı + çözüm, ücretsiz.",
    intro:
      "Kareköklü ifadeler LGS'nin vazgeçilmez konularından biridir. Bu çalışma kağıdı tam kare sayıları tanımayı, kök içindeki çarpanı dışarı çıkarmayı, kareköklü sayılarla dört işlemi ve kareköklü ifadeleri karşılaştırmayı kapsar.",
    skills: [
      "Tam kare sayıların kareköklerini bulma",
      "Kök içine alma ve kök dışına çarpan çıkarma",
      "Kareköklü sayılarla çarpma ve bölme",
      "Benzer kareköklü ifadelerde toplama-çıkarma",
      "Kareköklü ifadeleri ondalık değerle karşılaştırma",
    ],
    difficulty: [
      "Tam kare köklerini bulma, basit sadeleştirme.",
      "Kök dışına çıkarma ve dört işlem birlikte.",
      "LGS tarzı kareköklü ifade problemleri.",
    ],
    family: "karekoklu-ifadeler",
  }),
  ak({
    grade: 8,
    topicId: "dogal_sayilar",
    slug: "carpanlar-ve-katlar",
    title: "Çarpanlar ve Katlar (EBOB - EKOK)",
    description:
      "8. sınıf LGS çarpanlar ve katlar çalışma kağıdı: asal çarpanlar, EBOB-EKOK ve problem uygulamaları. PDF, cevap anahtarı ve adım adım çözüm ile ücretsiz üret.",
    intro:
      "Çarpanlar ve katlar (EBOB-EKOK) LGS'de hem doğrudan hem de günlük hayat problemi olarak sık çıkar. Bu çalışma kağıdı asal çarpanlara ayırmayı, ortak bölen/kat bulmayı ve EBOB-EKOK'u problemlerde kullanmayı pekiştirir.",
    skills: [
      "Bir sayıyı asal çarpanlarına ayırma",
      "İki sayının EBOB'unu bulma",
      "İki sayının EKOK'unu bulma",
      "EBOB-EKOK ile günlük hayat problemleri çözme",
      "Aralarında asal sayıları tanıma",
    ],
    difficulty: [
      "Küçük sayılarda EBOB-EKOK bulma.",
      "Asal çarpan tablosuyla EBOB-EKOK.",
      "LGS tarzı çok adımlı EBOB-EKOK problemleri.",
    ],
    family: "carpanlar-katlar",
  }),
  ak({
    grade: 8,
    topicId: "dogal_sayilar",
    slug: "gercek-sayilar",
    title: "Gerçek Sayılar (Rasyonel ve İrrasyonel)",
    description:
      "8. sınıf LGS gerçek sayılar çalışma kağıdı: rasyonel ve irrasyonel sayıları tanıma, sayı kümeleri ve sayı doğrusunda yerleştirme. PDF + cevap anahtarı + çözüm.",
    intro:
      "Gerçek sayılar, rasyonel ve irrasyonel sayıların birleşimidir. Bu çalışma kağıdı bir sayının hangi kümeye ait olduğunu belirlemeyi, irrasyonel sayıları tanımayı ve gerçek sayıları sayı doğrusunda karşılaştırmayı pekiştirir.",
    skills: [
      "Rasyonel ve irrasyonel sayıları ayırt etme",
      "Sayı kümeleri arasındaki kapsama ilişkisini kurma",
      "İrrasyonel sayıları sayı doğrusunda yaklaşık yerleştirme",
      "Gerçek sayıları karşılaştırma ve sıralama",
    ],
    difficulty: [
      "Verilen sayının türünü belirleme.",
      "Küme ilişkileri ve karşılaştırma.",
      "LGS tarzı sayı kümesi muhakeme soruları.",
    ],
  }),
  ak({
    grade: 8,
    topicId: "cebir",
    slug: "carpanlara-ayirma",
    title: "Çarpanlara Ayırma",
    description:
      "8. sınıf LGS çarpanlara ayırma çalışma kağıdı: ortak çarpan parantezine alma, özdeşliklerle çarpanlara ayırma. PDF, cevap anahtarı ve adım adım çözüm ile ücretsiz.",
    intro:
      "Çarpanlara ayırma, cebirsel ifadeleri sadeleştirmenin ve denklem çözmenin anahtarıdır; LGS'de özdeşliklerle birlikte sık sorulur. Bu çalışma kağıdı ortak çarpan parantezine almayı ve özdeşlik kalıplarını kullanarak çarpanlara ayırmayı pekiştirir.",
    skills: [
      "Ortak çarpanı parantezine alma",
      "İki kare farkı ile çarpanlara ayırma",
      "Tam kare özdeşliğini tanıyıp çarpanlara ayırma",
      "Çarpanlara ayırarak cebirsel ifade sadeleştirme",
    ],
    difficulty: [
      "Tek terimli ortak çarpan parantezi.",
      "İki kare farkı ve tam kare ile ayırma.",
      "LGS tarzı çok adımlı çarpanlara ayırma.",
    ],
    family: "carpanlara-ayirma",
  }),
  ak({
    grade: 8,
    topicId: "cebir",
    slug: "ozdeslikler",
    title: "Cebirsel İfadeler ve Özdeşlikler",
    description:
      "8. sınıf LGS özdeşlikler çalışma kağıdı: tam kare ve iki kare farkı özdeşlikleri, cebirsel ifadelerde işlemler. PDF, cevap anahtarı ve adım adım çözüm, ücretsiz.",
    intro:
      "Cebirsel özdeşlikler LGS'de hem doğrudan hem de geometrik modellerle (alan) sorulur. Bu çalışma kağıdı tam kare ((a±b)²) ve iki kare farkı (a²−b²) özdeşliklerini açmayı, modellemeyi ve hesaplamalarda kullanmayı pekiştirir.",
    skills: [
      "(a+b)² ve (a−b)² tam kare özdeşliklerini açma",
      "a²−b² iki kare farkı özdeşliğini kullanma",
      "Özdeşlikleri alan modeliyle ilişkilendirme",
      "Özdeşliklerle pratik hesap yapma (örn. 99², 101×99)",
    ],
    difficulty: [
      "Özdeşliği doğrudan açma.",
      "Modelle ilişkilendirme ve pratik hesap.",
      "LGS tarzı özdeşlik muhakeme soruları.",
    ],
    family: "ozdeslikler",
  }),
  ak({
    grade: 8,
    topicId: "cebir",
    slug: "dogrusal-denklemler",
    title: "Doğrusal Denklemler",
    description:
      "8. sınıf LGS doğrusal denklemler çalışma kağıdı: birinci dereceden denklem kurma ve çözme, koordinat düzleminde doğru. PDF + cevap anahtarı + çözüm, ücretsiz.",
    intro:
      "Doğrusal denklemler LGS cebir sorularının omurgasıdır. Bu çalışma kağıdı birinci dereceden bir bilinmeyenli denklem kurmayı ve çözmeyi, denklemi koordinat düzleminde doğruyla ilişkilendirmeyi ve problem çözmeyi pekiştirir.",
    skills: [
      "Birinci dereceden denklem kurma ve çözme",
      "Denklemi sözel problemden modelleme",
      "Doğrusal denklemi koordinat düzleminde gösterme",
      "Doğru üzerindeki noktaları belirleme",
    ],
    difficulty: [
      "Tek adımlı denklem çözme.",
      "Problemden denklem kurup çözme.",
      "LGS tarzı doğru-denklem ilişkisi soruları.",
    ],
    family: "dogrusal-denklemler",
  }),
  ak({
    grade: 8,
    topicId: "cebir",
    slug: "dogrunun-egimi",
    title: "Doğrunun Eğimi",
    description:
      "8. sınıf LGS doğrunun eğimi çalışma kağıdı: eğimi hesaplama, eğim ile diklik-paralellik, grafikten eğim okuma. PDF, cevap anahtarı ve adım adım çözüm, ücretsiz.",
    intro:
      "Doğrunun eğimi, LGS'de grafik yorumlama sorularında öne çıkar. Bu çalışma kağıdı iki noktadan geçen doğrunun eğimini hesaplamayı, eğimin işaretini yorumlamayı ve grafikten eğim okumayı pekiştirir.",
    skills: [
      "İki noktası verilen doğrunun eğimini hesaplama",
      "Eğimin işaretini (artan/azalan) yorumlama",
      "Grafikten doğrunun eğimini okuma",
      "Yatay ve düşey doğruların eğimini belirleme",
    ],
    difficulty: [
      "İki noktadan eğim hesaplama.",
      "Grafikten eğim okuma ve yorumlama.",
      "LGS tarzı eğim muhakeme soruları.",
    ],
  }),
  ak({
    grade: 8,
    topicId: "cebir",
    slug: "esitsizlikler",
    title: "Eşitsizlikler",
    description:
      "8. sınıf LGS eşitsizlikler çalışma kağıdı: birinci dereceden bir bilinmeyenli eşitsizlik çözme ve sayı doğrusunda gösterme. PDF + cevap anahtarı + çözüm, ücretsiz.",
    intro:
      "Eşitsizlikler LGS cebir konusunun önemli bir parçasıdır. Bu çalışma kağıdı birinci dereceden bir bilinmeyenli eşitsizlikleri çözmeyi, çözüm kümesini sayı doğrusunda göstermeyi ve eşitsizlik problemlerini modellemeyi pekiştirir.",
    skills: [
      "Birinci dereceden eşitsizlik çözme",
      "Çözüm kümesini sayı doğrusunda gösterme",
      "Negatifle çarpma/bölmede yön değiştirmeyi uygulama",
      "Sözel problemden eşitsizlik kurma",
    ],
    difficulty: [
      "Tek adımlı eşitsizlik çözme.",
      "Yön değiştirme ve sayı doğrusu gösterimi.",
      "LGS tarzı eşitsizlik problemleri.",
    ],
  }),
  ak({
    grade: 8,
    topicId: "geometri",
    slug: "ucgenler-pisagor",
    title: "Üçgenler ve Pisagor Bağıntısı",
    description:
      "8. sınıf LGS üçgenler ve Pisagor çalışma kağıdı: dik üçgende Pisagor bağıntısı, kenar-açı ilişkileri, üçgen eşitsizliği. PDF, cevap anahtarı ve çözüm, ücretsiz.",
    intro:
      "Üçgenler ve Pisagor bağıntısı LGS geometrinin en çok soru çıkan başlığıdır. Bu çalışma kağıdı dik üçgende kenar uzunluğu bulmayı, üçgen eşitsizliğini ve kenar-açı ilişkilerini pekiştirir.",
    skills: [
      "Dik üçgende Pisagor bağıntısıyla kenar bulma",
      "Pisagor üçlülerini tanıma (3-4-5, 5-12-13 ...)",
      "Üçgen eşitsizliğini uygulama",
      "Kenar-açı ilişkilerini yorumlama",
      "Pisagor'u günlük hayat problemlerinde kullanma",
    ],
    difficulty: [
      "Tanıdık Pisagor üçlüleriyle kenar bulma.",
      "Pisagor bağıntısıyla hesap ve eşitsizlik.",
      "LGS tarzı çok adımlı üçgen problemleri.",
    ],
    family: "ucgenler",
  }),
  ak({
    grade: 8,
    topicId: "geometri",
    slug: "donusum-geometrisi",
    title: "Dönüşüm Geometrisi (Öteleme - Yansıma - Dönme)",
    description:
      "8. sınıf LGS dönüşüm geometrisi çalışma kağıdı: öteleme, yansıma ve dönme; koordinat düzleminde dönüşümler. PDF + cevap anahtarı + adım adım çözüm, ücretsiz.",
    intro:
      "Dönüşüm geometrisi LGS'de koordinat düzlemiyle birleşerek soru olarak çıkar. Bu çalışma kağıdı bir şeklin ötelenmesini, bir doğruya göre yansımasını ve bir nokta etrafında dönmesini koordinatlarla belirlemeyi pekiştirir.",
    skills: [
      "Koordinat düzleminde öteleme yapma",
      "Eksenlere göre yansımayı belirleme",
      "Bir nokta etrafında dönme (90°, 180°)",
      "Dönüşüm sonrası koordinatları bulma",
      "Birden çok dönüşümü sırayla uygulama",
    ],
    difficulty: [
      "Tek bir öteleme veya yansıma.",
      "Dönme ve koordinat hesabı.",
      "LGS tarzı çoklu dönüşüm soruları.",
    ],
  }),
  ak({
    grade: 8,
    topicId: "geometri",
    slug: "geometrik-cisimler",
    title: "Geometrik Cisimler (Silindir - Koni - Piramit)",
    description:
      "8. sınıf LGS geometrik cisimler çalışma kağıdı: dik prizma, silindir, koni ve piramidin yüzey alanı ve hacmi. PDF, cevap anahtarı ve adım adım çözüm, ücretsiz.",
    intro:
      "Geometrik cisimler LGS'de hacim ve yüzey alanı hesaplarıyla çıkar. Bu çalışma kağıdı dik prizma, silindir, koni ve piramidin temel elemanlarını tanımayı, hacim ve yüzey alanı hesaplamayı pekiştirir.",
    skills: [
      "Silindirin hacmini ve yüzey alanını hesaplama",
      "Dik prizmaların hacmini bulma",
      "Koni ve piramidin temel elemanlarını tanıma",
      "Hacim-yüzey alanı problemlerini çözme",
    ],
    difficulty: [
      "Tanıdık ölçülerle silindir/prizma hacmi.",
      "Yüzey alanı ve birden çok cisim.",
      "LGS tarzı çok adımlı hacim problemleri.",
    ],
  }),
  ak({
    grade: 8,
    topicId: "veri_isleme",
    slug: "veri-analizi",
    title: "Veri Analizi ve Grafikler",
    description:
      "8. sınıf LGS veri analizi çalışma kağıdı: daire, sütun ve çizgi grafiği okuma-yorumlama, uygun grafik türü seçme. PDF + cevap anahtarı + çözüm, ücretsiz.",
    intro:
      "Veri analizi LGS'de grafik okuma ve yorumlama soruları olarak çıkar. Bu çalışma kağıdı daire, sütun ve çizgi grafiklerini okumayı, karşılaştırmayı ve veriye uygun grafik türünü seçmeyi pekiştirir.",
    skills: [
      "Daire grafiğini okuma ve yüzde-açı hesabı",
      "Sütun ve çizgi grafiğini yorumlama",
      "Veriye uygun grafik türünü seçme",
      "Grafikler arası karşılaştırma yapma",
    ],
    difficulty: [
      "Tek grafikten doğrudan okuma.",
      "Yüzde-açı hesabı ve karşılaştırma.",
      "LGS tarzı çoklu grafik yorumlama.",
    ],
    family: "veri-analizi",
  }),
  ak({
    grade: 8,
    topicId: "olasilik",
    slug: "basit-olaylarin-olasiligi",
    title: "Basit Olayların Olasılığı",
    description:
      "8. sınıf LGS olasılık çalışma kağıdı: basit bir olayın olasılığını hesaplama, olası durumları sayma. PDF, cevap anahtarı ve adım adım çözüm ile ücretsiz üret.",
    intro:
      "Olasılık LGS'de kısa ama garanti soru çıkan konudur. Bu çalışma kağıdı bir olayın olası tüm durumlarını saymayı, istenen durum sayısını belirlemeyi ve basit olasılığı kesir/yüzde olarak hesaplamayı pekiştirir.",
    skills: [
      "Bir deneyin olası tüm durumlarını sayma",
      "İstenen durum sayısını belirleme",
      "Basit bir olayın olasılığını hesaplama",
      "Olasılığı kesir, ondalık ve yüzde olarak ifade etme",
    ],
    difficulty: [
      "Zar/para gibi tanıdık deneylerde olasılık.",
      "Olası durumları sayıp olasılık hesabı.",
      "LGS tarzı olasılık muhakeme soruları.",
    ],
    family: "olasilik",
  }),
];

export function getAltKonu(
  topicSlug: string,
  slug: string,
): AltKonu | undefined {
  return ALTKONU_PAGES.find(
    (a) => a.topicSlug === topicSlug && a.slug === slug,
  );
}

export function getAltKonularByTopic(topicSlug: string): AltKonu[] {
  return ALTKONU_PAGES.filter((a) => a.topicSlug === topicSlug);
}

// Aynı alt-konunun farklı sınıflardaki versiyonları (family) — dikey iç-link (SEO).
export function getAltKonuFamily(
  family: string | undefined,
  excludeTopicSlug: string,
): AltKonu[] {
  if (!family) return [];
  return ALTKONU_PAGES.filter(
    (a) => a.family === family && a.topicSlug !== excludeTopicSlug,
  );
}
