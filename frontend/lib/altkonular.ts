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
      "6. sınıf yüzde problemleri çalışma kağıdı: indirim, zam, kâr-zarar ve yüzde-kesir-ondalık ilişkisi. PDF, cevap anahtarı ve çözüm ile ücretsiz.",
    intro:
      "Bu çalışma kağıdı yüzde ile ilgili problemleri (bir miktarın yüzdesi, yüzde artış/azalış, indirim-zam) çözmeyi ve yüzdeyi kesir/ondalık ile ilişkilendirmeyi pekiştirir.",
    skills: [
      "Bir miktarın belirli yüzdesini hesaplama",
      "Yüzde artış ve azalış (zam, indirim) bulma",
      "Yüzdeyi kesir ve ondalık ile ilişkilendirme",
      "Verilen yüzdeden bütünü bulma",
      "Kâr-zarar ve indirim problemleri",
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
