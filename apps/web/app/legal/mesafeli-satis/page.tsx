/*
 * TASLAK — Mesafeli Satış Sözleşmesi (6502 sayılı Kanun + Mesafeli Sözleşmeler
 * Yönetmeliği). Satıcı kimliği @/lib/legal SELLER'dan gelir (kuruluş sonrası
 * doldurulacak). Yayın öncesi bir hukuk danışmanınca gözden geçirilmeli.
 */
import { LegalDocument, type LegalSection } from "@/components/LegalDocument";
import { SELLER, SELLER_BULLETS } from "@/lib/legal";

export const metadata = {
  title: "Mesafeli Satış Sözleşmesi · Soru Atölyesi",
  description:
    "Soru Atölyesi dijital abonelik hizmetine ilişkin mesafeli satış sözleşmesi.",
};

const SECTIONS: LegalSection[] = [
  {
    heading: "Taraflar ve Konu",
    paragraphs: [
      "İşbu Mesafeli Satış Sözleşmesi (“Sözleşme”), aşağıda bilgileri yer alan Satıcı ile Platform üzerinden abonelik satın alan Alıcı (Tüketici) arasında, 6502 sayılı Tüketicinin Korunması Hakkında Kanun ve Mesafeli Sözleşmeler Yönetmeliği hükümlerine uygun olarak elektronik ortamda kurulmuştur.",
      "Sözleşme’nin konusu, Alıcı’nın Platform üzerinden seçtiği dijital abonelik hizmetinin sunulması ve buna ilişkin tarafların hak ve yükümlülüklerinin belirlenmesidir.",
    ],
    bullets: SELLER_BULLETS,
  },
  {
    heading: "Sözleşmeye Konu Hizmet",
    paragraphs: [
      `Hizmet, ${SELLER.markaAdi} platformunda sunulan, MEB müfredatına uygun dijital soru/çalışma kağıdı ve quiz üretimi ile çevrimiçi öğrenme özelliklerini kapsayan süreli abonelik hizmetidir.`,
      "Hizmet tamamen dijitaldir ve fiziksel ürün teslimi içermez. Abonelik kapsamı, Alıcı’nın satın aldığı plana göre değişir ve satın alma anında Alıcı’ya gösterilir.",
    ],
  },
  {
    heading: "Bedel ve Ödeme Koşulları",
    paragraphs: [
      "Hizmet bedeli, satın alma adımında tüm vergiler dâhil (KDV dahil) toplam tutar olarak Türk Lirası (₺) cinsinden gösterilir. Alıcı, bu bedeli onaylayarak ödemeyi gerçekleştirir.",
      `Ödemeler ${SELLER.odemeKurulusu} altyapısı üzerinden alınır. Kart bilgileri Satıcı tarafından görülmez ve saklanmaz.`,
      "Abonelik otomatik yenilenir: Alıcı iptal etmediği sürece, seçilen dönem (aylık/yıllık) sonunda güncel bedelle otomatik olarak yenilenir ve Alıcı’nın ödeme yöntemi tahsil edilir.",
    ],
  },
  {
    heading: "Hizmetin İfası",
    paragraphs: [
      "Ödemenin başarıyla onaylanmasının ardından, abonelik kapsamındaki dijital özelliklere erişim Alıcı’ya anında (elektronik ortamda) açılır.",
      "Deneme süresi (trial) sunulması hâlinde, deneme süresi boyunca ücret alınmaz; koşulları satın alma ekranında belirtilir.",
    ],
  },
  {
    heading: "Cayma Hakkı ve İstisnası",
    paragraphs: [
      "Tüketici, kural olarak 14 gün içinde herhangi bir gerekçe göstermeksizin ve cezai şart ödemeksizin sözleşmeden cayma hakkına sahiptir.",
      "Ancak Mesafeli Sözleşmeler Yönetmeliği’nin 15. maddesi uyarınca; elektronik ortamda anında ifa edilen hizmetler ve tüketiciye anında sunulan gayrimaddi (dijital) içeriklere ilişkin sözleşmelerde, tüketicinin açık onayı ile ifaya başlanmış olması hâlinde cayma hakkı kullanılamaz.",
      "Alıcı, aboneliği başlatırken hizmete anında erişim sağlanmasını ve bu durumda cayma hakkının sona ereceğini açıkça onaylar. Bu onayla birlikte 14 günlük cayma hakkı ortadan kalkar.",
    ],
  },
  {
    heading: "İptal ve Otomatik Yenilemenin Durdurulması",
    paragraphs: [
      "Alıcı, aboneliğini hesabındaki abonelik yönetimi ekranından dilediği zaman iptal edebilir. İptal, o an ödenmiş bulunan dönemin sonunda yürürlüğe girer; dönem sonuna kadar hizmete erişim devam eder ve dönem sonunda otomatik yenileme durur.",
      "İade koşulları için İptal & İade Koşulları sayfasına bakınız.",
    ],
  },
  {
    heading: "Tarafların Yükümlülükleri",
    bullets: [
      "Alıcı, hesap ve ödeme bilgilerinin doğruluğundan sorumludur.",
      "Alıcı, hizmeti hukuka ve işbu Sözleşme’ye uygun kullanmayı; içerikleri kötüye kullanmamayı kabul eder.",
      "Satıcı, hizmeti Sözleşme ve mevzuata uygun sunmak; kesinti/aksaklık durumunda makul çabayı göstermekle yükümlüdür.",
      "Satıcı, dijital hizmetin niteliği gereği kesintisizlik ve hatasızlık konusunda mutlak garanti vermez; ancak hizmet kalitesini korumak için makul özeni gösterir.",
    ],
  },
  {
    heading: "Kişisel Verilerin Korunması",
    paragraphs: [
      "Alıcı’nın kişisel verileri, KVKK Aydınlatma Metni ve Gizlilik Politikası kapsamında işlenir.",
    ],
  },
  {
    heading: "Uyuşmazlıkların Çözümü",
    paragraphs: [
      `Alıcı, talep ve şikâyetlerini ${SELLER.eposta} adresine iletebilir.`,
      "Uyuşmazlık hâlinde, Ticaret Bakanlığı’nca ilan edilen parasal sınırlar dâhilinde Alıcı’nın yerleşim yerindeki Tüketici Hakem Heyetleri veya Tüketici Mahkemeleri yetkilidir.",
    ],
  },
  {
    heading: "Yürürlük",
    paragraphs: [
      "Alıcı’nın elektronik ortamda ödemeyi onaylaması ile işbu Sözleşme kurulmuş ve yürürlüğe girmiş sayılır. Alıcı, Sözleşme koşullarını ve Ön Bilgilendirme Formu’nu okuduğunu ve kabul ettiğini beyan eder.",
    ],
  },
];

export default function MesafeliSatisPage() {
  return (
    <LegalDocument
      eyebrow="Hukuki"
      title="Mesafeli Satış Sözleşmesi"
      intro="Soru Atölyesi dijital abonelik hizmetinin satın alınmasına ilişkin, Satıcı ile Alıcı arasında elektronik ortamda kurulan mesafeli satış sözleşmesidir."
      updated="15 Temmuz 2026"
      sections={SECTIONS}
    />
  );
}
