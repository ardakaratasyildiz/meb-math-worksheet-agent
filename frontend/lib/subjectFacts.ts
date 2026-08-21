// "Bunu biliyor muydun?" — üretim beklerken ders bazlı gösterilen bilgiler.
// Matematik için lib/mathFacts.ts kullanılır; diğer dersler burada. Quiz üretimi
// (SolveForm) seçili derse göre doğru havuzu gösterir.
import { MATH_FACTS } from "./mathFacts";
import type { Subject } from "./types";

const FEN_FACTS: string[] = [
  "Bal arısı bir kilo bal üretmek için yaklaşık 4 milyon çiçek ziyaret eder.",
  "Işık, Güneş’ten Dünya’ya yaklaşık 8 dakika 20 saniyede ulaşır.",
  "İnsan vücudundaki en güçlü kas, boyutuna göre çene kasıdır (masseter).",
  "Su, katı halde (buz) sıvı halinden daha hafiftir — bu yüzden buz suda yüzer.",
  "Ay’da KÜTLEN değişmez (hep aynı maddesin); değişen AĞIRLIKTIR. Ay’ın çekimi Dünya’nın ~1/6’sı olduğu için orada yaklaşık 6 kat daha hafif tartılırsın.",
  "Şimşek, sesten çok daha hızlı olan ışıkla görünür; gök gürültüsünü sonra duyarız.",
  "Bir yıldırımın sıcaklığı Güneş’in yüzeyinden yaklaşık 5 kat daha sıcaktır.",
  "Bitkiler fotosentezde karbondioksit alıp oksijen verir — soluduğumuz oksijenin kaynağı.",
  "Kemiklerimiz betondan daha sağlam; ama çok daha hafif ve esnektir.",
  "Dünya kendi ekseni etrafında saatte yaklaşık 1670 km hızla döner (ekvatorda).",
];

const TURKCE_FACTS: string[] = [
  "Türkçede en uzun sözcüklerden biri “muvaffakiyetsizleştiricileştiriveremeyebileceklerimizdenmişsinizcesine”dir.",
  "“de/da” bağlacı ayrı yazılır; hal eki olan “-de/-da” ise bitişik. (evde ↔ ev de geldi)",
  "Türk alfabesi 1928’de kabul edildi ve 29 harften oluşur.",
  "“Bir” sözcüğü hem sayı hem belirsizlik bildirir: “bir elma” ↔ “bir gün gelir”.",
  "Noktalı virgül (;), anlamca bağlı iki cümleyi ayırmak için kullanılır.",
  "Ünlü uyumu Türkçenin en belirgin kuralıdır: kalın ünlüyü kalın, ince ünlüyü ince izler.",
  "“Herkes” daima tek kelime ve “-s” ile yazılır; “herkez” yanlıştır.",
  "Deyimler kalıplaşmış sözlerdir; çoğu gerçek anlamıyla açıklanamaz (“etekleri zil çalmak”).",
  "Büyük ünlü uyumuna uymayan pek çok kelime alıntıdır (kitap, saat, insan).",
  "Atasözleri anonimdir — söyleyeni belli değildir ve toplumun ortak deneyimini taşır.",
];

const SOSYAL_FACTS: string[] = [
  "Türkiye Cumhuriyeti 29 Ekim 1923’te ilan edildi.",
  "23 Nisan 1920’de TBMM açıldı; bu tarih Ulusal Egemenlik ve Çocuk Bayramı’dır.",
  "İlk Türk kadın milletvekilleri 1935 seçimlerinde Meclis’e girdi.",
  "Anadolu, tarih boyunca Hititler, Frigler, Lidyalılar gibi pek çok uygarlığa ev sahipliği yaptı.",
  "Dünya’nın en uzun nehri Nil, en büyük okyanusu ise Büyük Okyanus’tur.",
  "Haritalarda ölçek, gerçek uzaklığın kağıda ne kadar küçültüldüğünü gösterir.",
  "Ekvator, Dünya’yı Kuzey ve Güney yarım küre olarak ikiye ayıran hayali çizgidir.",
  "Cumhuriyet, egemenliğin millete ait olduğu yönetim biçimidir.",
  "İlk yazı MÖ 3500’lerde Sümerler tarafından geliştirildi (çivi yazısı).",
  "Bir toplumda haklar kadar sorumluluklar da vardır; ikisi birlikte yürür.",
];

const INGILIZCE_FACTS: string[] = [
  "İngilizcede en çok kullanılan harf “e”dir.",
  "“I” (ben), İngilizcede her zaman büyük harfle yazılır.",
  "İngilizcede yaklaşık 170.000 kullanımda kelime vardır; günlük konuşma için ~3.000 yeterlidir.",
  "Simple Present’ta üçüncü tekil kişide (he/she/it) fiile “-s” eklenir: “She plays.”",
  "“Good” sıfatının karşılaştırması düzensizdir: good → better → best.",
  "İngilizcede bir cümle en az bir özne ve bir yüklem içerir.",
  "“a” ve “an” seçimi sesle ilgilidir: “an hour” (h okunmaz), “a university” (yu sesi).",
  "En kısa tam İngilizce cümle “I am.”dir.",
  "“Their, there, they’re” aynı okunur ama anlamları tamamen farklıdır.",
  "CEFR düzeyleri A1’den C2’ye uzanır; A1 başlangıç, C2 ana dile yakın düzeydir.",
];

const FACTS_BY_SUBJECT: Record<Subject, string[]> = {
  matematik: MATH_FACTS,
  fen: FEN_FACTS,
  turkce: TURKCE_FACTS,
  sosyal: SOSYAL_FACTS,
  ingilizce: INGILIZCE_FACTS,
};

export function factsForSubject(subject: Subject): string[] {
  return FACTS_BY_SUBJECT[subject] ?? MATH_FACTS;
}
