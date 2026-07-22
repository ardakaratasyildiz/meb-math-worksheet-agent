// "Bunu biliyor muydun?" — üretim beklerken gösterilen matematik bilgileri.
// Hem PDF üretiminde (QuestionPreview) hem quiz üretiminde (SolveForm/practice)
// kullanılır. Tek kaynak → iki yüzeyde de çeşitli ve tutarlı içerik.
// Rastgele başlangıç + 6 sn'de bir dönüş sayesinde her oturumda farklı bilgiler
// görünür.
export const MATH_FACTS: string[] = [
  "0! (sıfır faktöriyel) = 1'dir. Çünkü hiçbir şeyi sıralamanın tek bir yolu vardır: sıralamamak.",
  "Pisagor teoremi, Pisagor'dan 1300 yıl önce Babillilerce zaten biliniyordu — ama isim ona kaldı.",
  "Gauss 9 yaşındayken öğretmeni \"1'den 100'e kadar topla\" dedi. 30 saniyede 5050'yi söyledi — formülü kendi keşfetti.",
  "\"Algoritma\" kelimesi, 9. yüzyıl matematikçisi El-Harezmi'nin Latince adı \"Algoritmi\"den gelir.",
  "Bal arıları peteklerini altıgen yapar — çünkü altıgen, eşit alan için en az malzeme kullanan şekildir.",
  "Sonsuzluk simgesi ∞, John Wallis tarafından 1655'te icat edildi — Roma rakamı M (1000) şeklinin değişimi olabilir.",
  "Pi günü 14 Mart'tır (3.14) ve Albert Einstein'ın doğum günüyle aynı tarih.",
  "Bir A4 kâğıdı insan gücüyle en fazla 7 kez katlanabilir; 8.'sinde fizik durdurur.",
  "2 hariç tüm asal sayılar tektir — çünkü çift sayı zaten 2'ye bölünür.",
  "Fibonacci dizisi (1, 1, 2, 3, 5, 8...) ayçiçeği tohumlarında, deniz kabuğunda, kelebek kanadında doğal olarak çıkar.",
  "Sıfır sayısını matematiksel olarak ilk tanımlayan kişi Hint matematikçi Brahmagupta'dır (7. yüzyıl).",
  "Bir küpün 8 köşesi, 12 kenarı, 6 yüzü vardır. Köşe − Kenar + Yüz = 2 — Euler'in tüm konveks çokyüzlülerde geçerli formülü.",
  "Saniyede 1 sayma hızıyla 1 milyon sayısına 11,5 günde, 1 milyara ise 31,7 yılda ulaşırsın.",
  "0 sayısı çifttir — 2'ye tam bölünür ve çift sayıların tüm tanımlarını sağlar.",
  "Bir sayının rakamları toplamı 3'e bölünüyorsa, sayının kendisi de 3'e bölünür. (Örn. 123 → 1+2+3=6)",
  "Bir grupta sadece 23 kişi varsa, ikisinin doğum gününün aynı olma olasılığı %50'den fazladır.",
  "Satranç tahtasının karelerine 1, 2, 4, 8... diye katlayarak buğday koysan, 64. karede dünya üretiminden fazla tane olur.",
  "Üçgenin iç açıları toplamı düzlemde her zaman 180°'dir — ama bir kürenin üzerinde çizersen 180°'den fazla olur!",
  "Bir karenin köşegeni, kenarının √2 (yaklaşık 1,41) katıdır. Kenarı 1 olan karenin köşegeni 1,41'dir.",
  "Negatif × negatif = pozitif: \"borcunun silinmesi\" bir kazançtır — aynı mantık.",
  "Sıfıra bölme tanımsızdır: \"5'i kaç tane 0 oluşturur?\" sorusunun bir cevabı yoktur.",
  "Bir futbol topunda 12 beşgen ve 20 altıgen vardır — tam olarak Euler'in çokyüzlü formülüne uyar.",
  "Bir saat yüzünde akrep ile yelkovan günde 24 değil, tam 22 kez üst üste gelir.",
  "Bir çemberin çevresi, yarıçapının yaklaşık 6,28 (yani 2π) katıdır.",
  "Eski Mısırlılar 4000 yıl önce kesirleri kullanıyordu — ama neredeyse hep \"1 bölü bir şey\" biçiminde (birim kesirler).",
  "Çift + çift = çift, tek + tek = çift, çift + tek = tek. Toplamın tek/çift olması terimlerin sayısına bağlı.",
  "Bir sayı 4'e bölünüyorsa son iki basamağı da 4'e bölünür. (Örn. 1.328 → 28 ÷ 4 = 7)",
  "Kümülatif olarak: 1+2+3+...+n = n×(n+1)/2. Gauss'un 9 yaşında bulduğu kestirme yol bu.",
  "Bir pizzayı 3 düz kesikle en fazla 7 dilime ayırabilirsin — kesiklerin hepsi birbirini farklı noktada keserse.",
  "Asal sayılar sonsuzdur — bunu Öklid 2300 yıl önce, sadece mantıkla (deneyerek değil) kanıtladı.",
];
