/*
 * TASLAK — İptal & İade / Cayma Hakkı Koşulları.
 * Satıcı kimliği @/lib/legal SELLER'dan gelir (kuruluş sonrası doldurulacak).
 * Yayın öncesi bir hukuk danışmanınca gözden geçirilmeli. İade politikası
 * (kısmi iade var mı, hangi hallerde) ticari karar olarak netleştirilmeli.
 */
import { LegalDocument, type LegalSection } from "@/components/LegalDocument";
import { SELLER } from "@/lib/legal";

export const metadata = {
  title: "İptal & İade Koşulları · Soru Atölyesi",
  description:
    "Soru Atölyesi abonelik hizmetinde iptal, otomatik yenilemenin durdurulması, cayma hakkı ve iade koşulları.",
};

const SECTIONS: LegalSection[] = [
  {
    heading: "Aboneliğin İptali",
    paragraphs: [
      "Aboneliğinizi, giriş yaptıktan sonra hesabınızdaki abonelik yönetimi ekranından dilediğiniz zaman iptal edebilirsiniz. İptal için ayrıca bir gerekçe belirtmeniz gerekmez.",
      "İptal, o an ödemiş olduğunuz dönemin (aylık veya yıllık) sonunda geçerli olur. Dönem sonuna kadar hizmete erişiminiz aynen devam eder; dönem sonunda abonelik otomatik olarak yenilenmez ve ek ücret alınmaz.",
    ],
  },
  {
    heading: "Otomatik Yenileme",
    paragraphs: [
      "Abonelikler, iptal edilmediği sürece seçtiğiniz döneme göre güncel bedelle otomatik olarak yenilenir. Yenilemeyi durdurmak için dönem bitmeden aboneliğinizi iptal etmeniz yeterlidir.",
    ],
  },
  {
    heading: "Cayma Hakkı ve Dijital Hizmet İstisnası",
    paragraphs: [
      "Mesafeli Sözleşmeler Yönetmeliği uyarınca tüketicinin kural olarak 14 gün içinde cayma hakkı bulunur.",
      "Ancak elektronik ortamda anında ifa edilen dijital hizmetlerde, tüketicinin açık onayı ile hizmete anında erişim sağlanması hâlinde cayma hakkı kullanılamaz (Yönetmelik m.15). Aboneliği başlatırken bu onayı verdiğiniz için, hizmete erişiminizin açılmasından sonra 14 günlük cayma hakkı sona erer.",
    ],
  },
  {
    heading: "İade",
    paragraphs: [
      "Yukarıdaki dijital hizmet istisnası nedeniyle, erişimi açılmış dönemlere ilişkin ücretler kural olarak iade edilmez. Bununla birlikte aşağıdaki durumlarda talebiniz değerlendirilir:",
    ],
    bullets: [
      "Teknik bir arıza nedeniyle hizmete uzun süre erişilememesi,",
      "Yanlışlıkla çift tahsilat veya hatalı ücretlendirme,",
      "Mevzuatın iade öngördüğü diğer hâller.",
    ],
  },
  {
    heading: "İade Süreci ve Yöntemi",
    paragraphs: [
      `İade talebinizi ${SELLER.eposta} adresine, ödeme ve hesap bilgilerinizle birlikte iletebilirsiniz. Uygun bulunan iadeler, ödemenin yapıldığı yöntem üzerinden (kartınıza) gerçekleştirilir.`,
      `İade tutarının kartınıza yansıma süresi, ${SELLER.odemeKurulusu} ve bankanızın süreçlerine bağlı olarak değişebilir.`,
    ],
  },
  {
    heading: "İletişim ve Uyuşmazlık",
    paragraphs: [
      `Tüm iptal ve iade talepleriniz için: ${SELLER.eposta}.`,
      "Uyuşmazlık hâlinde, ilgili parasal sınırlar dâhilinde Tüketici Hakem Heyetlerine veya Tüketici Mahkemelerine başvurabilirsiniz.",
    ],
  },
];

export default function IptalIadePage() {
  return (
    <LegalDocument
      eyebrow="Hukuki"
      title="İptal & İade Koşulları"
      intro="Abonelik iptali, otomatik yenilemenin durdurulması, cayma hakkı ve iade koşullarına ilişkin bilgiler aşağıda yer almaktadır."
      updated="15 Temmuz 2026"
      sections={SECTIONS}
    />
  );
}
