/*
 * TASLAK — Ön Bilgilendirme Formu (Mesafeli Sözleşmeler Yönetmeliği m.5).
 * Satıcı kimliği @/lib/legal SELLER'dan gelir (kuruluş sonrası doldurulacak).
 * Yayın öncesi bir hukuk danışmanınca gözden geçirilmeli. Fiyat/plan bilgisi
 * kesinleşen SKU setine göre güncellenmeli.
 */
import { LegalDocument, type LegalSection } from "@/components/LegalDocument";
import { SELLER, SELLER_BULLETS } from "@/lib/legal";

export const metadata = {
  title: "Ön Bilgilendirme Formu · Soru Atölyesi",
  description:
    "Mesafeli Sözleşmeler Yönetmeliği kapsamında Soru Atölyesi abonelik hizmetine ilişkin ön bilgilendirme formu.",
};

const SECTIONS: LegalSection[] = [
  {
    heading: "Satıcı / Hizmet Sağlayıcı Bilgileri",
    paragraphs: [
      "Bu form, 6502 sayılı Tüketicinin Korunması Hakkında Kanun ve Mesafeli Sözleşmeler Yönetmeliği uyarınca, siz (“Alıcı/Tüketici”) ile aşağıda bilgileri yer alan satıcı arasında kurulacak mesafeli hizmet sözleşmesi öncesinde bilgilendirme amacıyla sunulmaktadır.",
    ],
    bullets: SELLER_BULLETS,
  },
  {
    heading: "Sözleşme Konusu Hizmetin Temel Nitelikleri",
    paragraphs: [
      `${SELLER.markaAdi}, MEB müfredatına uygun soru/çalışma kağıdı ve quiz üretimi ile çevrimiçi öğrenme özelliklerini sunan dijital bir abonelik hizmetidir.`,
      "Hizmet tamamen dijitaldir; fiziksel bir ürün teslimi içermez. Abonelik, seçilen plana göre belirli bir kullanım kapsamı (aylık soru kotası, filigransız/white-label PDF, sınıf/ödev yönetimi gibi) sağlar.",
    ],
  },
  {
    heading: "Hizmet Bedeli ve Ödeme",
    paragraphs: [
      "Seçtiğiniz planın güncel bedeli, tüm vergiler (KDV dahil) ile birlikte toplam tutar olarak ödeme adımında açıkça gösterilir. Fiyatlar Türk Lirası (₺) cinsindendir.",
      `Ödeme, ${SELLER.odemeKurulusu} altyapısı üzerinden kredi/banka kartı ile güvenli şekilde alınır. Kart bilgileriniz satıcı tarafından saklanmaz.`,
      "Abonelik süreli ve otomatik yenilenen bir hizmettir; seçtiğiniz döneme (aylık/yıllık) göre, iptal edilmediği sürece dönem sonunda aynı bedelle otomatik olarak yenilenir.",
    ],
  },
  {
    heading: "İfa (Hizmetin Sunumu)",
    paragraphs: [
      "Ödemenin onaylanmasının ardından abonelik kapsamındaki dijital özelliklere erişim anında (elektronik ortamda, derhal) açılır.",
    ],
  },
  {
    heading: "Cayma Hakkı ve İstisnası",
    paragraphs: [
      "Mesafeli Sözleşmeler Yönetmeliği uyarınca tüketici, kural olarak 14 gün içinde gerekçe göstermeksizin cayma hakkına sahiptir.",
      "Ancak aynı Yönetmeliğin 15. maddesi gereğince; elektronik ortamda anında ifa edilen hizmetler ile tüketiciye anında sunulan gayrimaddi (dijital) içeriklere ilişkin sözleşmelerde, tüketicinin onayı ile ifaya başlanmışsa cayma hakkı kullanılamaz.",
      "Bu nedenle, aboneliği başlatırken hizmete anında erişimi ve bu durumda cayma hakkınızın sona ereceğini açıkça onaylamanız istenir. Onay vermeniz hâlinde 14 günlük cayma hakkı ortadan kalkar. Dilediğiniz zaman aboneliğinizi iptal ederek dönem sonunda yenilenmesini durdurabilirsiniz.",
    ],
  },
  {
    heading: "İptal, Yenileme ve İade",
    paragraphs: [
      "Aboneliğinizi hesabınızdaki abonelik yönetimi ekranından dilediğiniz an iptal edebilirsiniz. İptal, mevcut ödenmiş dönemin sonunda geçerli olur; dönem sonuna kadar hizmete erişiminiz devam eder ve dönem sonunda otomatik yenileme durur.",
      "Ücret iadesi koşulları için İptal & İade Koşulları sayfasına bakınız.",
    ],
  },
  {
    heading: "Şikâyet ve Uyuşmazlık Çözümü",
    paragraphs: [
      `Talep ve şikâyetlerinizi ${SELLER.eposta} adresine iletebilirsiniz.`,
      "Uyuşmazlık hâlinde, ilgili parasal sınırlar dâhilinde Tüketici Hakem Heyetlerine veya Tüketici Mahkemelerine başvurabilirsiniz.",
    ],
  },
];

export default function OnBilgilendirmePage() {
  return (
    <LegalDocument
      eyebrow="Hukuki"
      title="Ön Bilgilendirme Formu"
      intro="Abonelik satın almadan önce, Mesafeli Sözleşmeler Yönetmeliği kapsamında hizmete ilişkin temel bilgiler aşağıda sunulmaktadır."
      updated="15 Temmuz 2026"
      sections={SECTIONS}
    />
  );
}
