/**
 * "Bunu biliyor muydun?" — üretim beklerken (30-90 sn) gösterilen ders bilgileri.
 *
 * İçerik web'deki `frontend/lib/mathFacts.ts` + `frontend/lib/subjectFacts.ts` ile
 * AYNI olmalı. Kopya duruyor çünkü `frontend/` bir npm workspace üyesi değil
 * (kök package.json workspaces: apps/*, packages/*) → `packages/shared` üzerinden
 * paylaşmak Vercel derlemesini değiştirmeyi gerektiriyor. Metin değişirse iki
 * dosyayı birlikte güncelle.
 */
import type { SubjectSlug } from "@soruatolyesi/shared";

const MATH_FACTS: string[] = [
  "0! (sıfır faktöriyel) = 1'dir. Çünkü hiçbir şeyi sıralamanın tek bir yolu vardır: sıralamamak.",
  "Pisagor teoremi, Pisagor'dan 1300 yıl önce Babillilerce zaten biliniyordu — ama isim ona kaldı.",
  "Gauss 9 yaşındayken öğretmeni \"1'den 100'e kadar topla\" dedi. 30 saniyede 5050'yi söyledi.",
  "\"Algoritma\" kelimesi, 9. yüzyıl matematikçisi El-Harezmi'nin Latince adı \"Algoritmi\"den gelir.",
  "Bal arıları peteklerini altıgen yapar — altıgen, eşit alan için en az malzeme kullanan şekildir.",
  "Pi günü 14 Mart'tır (3.14) ve Albert Einstein'ın doğum günüyle aynı tarih.",
  "Bir A4 kağıdı insan gücüyle en fazla 7 kez katlanabilir; 8.'sinde fizik durdurur.",
  "2 hariç tüm asal sayılar tektir — çünkü çift sayı zaten 2'ye bölünür.",
  "Fibonacci dizisi (1, 1, 2, 3, 5, 8...) ayçiçeğinde, deniz kabuğunda, kelebek kanadında çıkar.",
  "Sıfır sayısını matematiksel olarak ilk tanımlayan Hint matematikçi Brahmagupta'dır (7. yüzyıl).",
  "Bir küpün 8 köşesi, 12 kenarı, 6 yüzü vardır. Köşe − Kenar + Yüz = 2 (Euler formülü).",
  "Saniyede 1 sayma hızıyla 1 milyona 11,5 günde, 1 milyara 31,7 yılda ulaşırsın.",
  "Bir grupta sadece 23 kişi varsa, ikisinin doğum gününün aynı olma olasılığı %50'den fazladır.",
  "Üçgenin iç açıları toplamı düzlemde 180°'dir — ama bir kürenin üzerinde daha fazla olur!",
  "Negatif × negatif = pozitif: \"borcunun silinmesi\" bir kazançtır — aynı mantık.",
  "Sıfıra bölme tanımsızdır: \"5'i kaç tane 0 oluşturur?\" sorusunun bir cevabı yoktur.",
  "Bir futbol topunda 12 beşgen ve 20 altıgen vardır — tam olarak Euler'in formülüne uyar.",
  "Bir saat yüzünde akrep ile yelkovan günde 24 değil, tam 22 kez üst üste gelir.",
  "Asal sayılar sonsuzdur — Öklid bunu 2300 yıl önce sadece mantıkla kanıtladı.",
];

const FEN_FACTS: string[] = [
  "Bal arısı bir kilo bal üretmek için yaklaşık 4 milyon çiçek ziyaret eder.",
  "Işık, Güneş'ten Dünya'ya yaklaşık 8 dakika 20 saniyede ulaşır.",
  "İnsan vücudundaki en güçlü kas, boyutuna göre çene kasıdır.",
  "Su, katı halde (buz) sıvı halinden daha hafiftir — bu yüzden buz suda yüzer.",
  "Ay'da kütlen değişmez, ağırlığın değişir: Ay'ın çekimi Dünya'nın ~1/6'sı kadardır.",
  "Şimşek ışıkla görünür, gök gürültüsünü sonra duyarız — ışık sesten çok daha hızlıdır.",
  "Bir yıldırımın sıcaklığı Güneş'in yüzeyinden yaklaşık 5 kat daha sıcaktır.",
  "Bitkiler fotosentezde karbondioksit alıp oksijen verir — soluduğumuz oksijenin kaynağı.",
  "Kemiklerimiz betondan daha sağlam; ama çok daha hafif ve esnektir.",
  "Dünya kendi ekseni etrafında ekvatorda saatte yaklaşık 1670 km hızla döner.",
];

const TURKCE_FACTS: string[] = [
  "\"de/da\" bağlacı ayrı yazılır; hal eki olan \"-de/-da\" ise bitişik. (evde ↔ ev de geldi)",
  "Türk alfabesi 1928'de kabul edildi ve 29 harften oluşur.",
  "\"Bir\" sözcüğü hem sayı hem belirsizlik bildirir: \"bir elma\" ↔ \"bir gün gelir\".",
  "Noktalı virgül (;), anlamca bağlı iki cümleyi ayırmak için kullanılır.",
  "Ünlü uyumu Türkçenin en belirgin kuralıdır: kalın ünlüyü kalın, ince ünlüyü ince izler.",
  "\"Herkes\" daima tek kelime ve \"-s\" ile yazılır; \"herkez\" yanlıştır.",
  "Deyimler kalıplaşmış sözlerdir; çoğu gerçek anlamıyla açıklanamaz (\"etekleri zil çalmak\").",
  "Büyük ünlü uyumuna uymayan pek çok kelime alıntıdır (kitap, saat, insan).",
  "Atasözleri anonimdir — söyleyeni belli değildir, toplumun ortak deneyimini taşır.",
];

const SOSYAL_FACTS: string[] = [
  "Türkiye Cumhuriyeti 29 Ekim 1923'te ilan edildi.",
  "23 Nisan 1920'de TBMM açıldı; bu tarih Ulusal Egemenlik ve Çocuk Bayramı'dır.",
  "İlk Türk kadın milletvekilleri 1935 seçimlerinde Meclis'e girdi.",
  "Anadolu; Hititler, Frigler, Lidyalılar gibi pek çok uygarlığa ev sahipliği yaptı.",
  "Dünya'nın en uzun nehri Nil, en büyük okyanusu Büyük Okyanus'tur.",
  "Haritalarda ölçek, gerçek uzaklığın kağıda ne kadar küçültüldüğünü gösterir.",
  "Ekvator, Dünya'yı Kuzey ve Güney yarım küre olarak ikiye ayıran hayali çizgidir.",
  "Cumhuriyet, egemenliğin millete ait olduğu yönetim biçimidir.",
  "İlk yazı MÖ 3500'lerde Sümerler tarafından geliştirildi (çivi yazısı).",
];

const INGILIZCE_FACTS: string[] = [
  "İngilizcede en çok kullanılan harf \"e\"dir.",
  "\"I\" (ben), İngilizcede her zaman büyük harfle yazılır.",
  "İngilizcede ~170.000 kelime vardır; günlük konuşma için ~3.000 yeterlidir.",
  "Simple Present'ta üçüncü tekil kişide (he/she/it) fiile \"-s\" eklenir: \"She plays.\"",
  "\"Good\" sıfatının karşılaştırması düzensizdir: good → better → best.",
  "\"a\" ve \"an\" seçimi sesle ilgilidir: \"an hour\" (h okunmaz), \"a university\" (yu sesi).",
  "En kısa tam İngilizce cümle \"I am.\"dir.",
  "\"Their, there, they're\" aynı okunur ama anlamları tamamen farklıdır.",
  "CEFR düzeyleri A1'den C2'ye uzanır; A1 başlangıç, C2 ana dile yakın düzeydir.",
];

const BY_SUBJECT: Record<string, string[]> = {
  matematik: MATH_FACTS,
  fen: FEN_FACTS,
  turkce: TURKCE_FACTS,
  sosyal: SOSYAL_FACTS,
  ingilizce: INGILIZCE_FACTS,
};

/** Derse ait bilgi havuzu; bilinmeyen ders → matematik (güvenli varsayılan). */
export function factsForSubject(subject: SubjectSlug | string | undefined): string[] {
  return BY_SUBJECT[subject ?? "matematik"] ?? MATH_FACTS;
}
