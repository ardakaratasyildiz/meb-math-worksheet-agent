/*
 * TASLAK — yetkili mahkeme şimdilik genel (T.C. mahkemeleri) bırakıldı.
 * Resmi yayın öncesi metin bir hukuk danışmanı tarafından gözden geçirilmeli.
 */
import { LegalDocument, type LegalSection } from "@/components/LegalDocument";

export const metadata = {
  title: "Kullanım Koşulları · Soru Atölyesi",
  description:
    "Soru Atölyesi platformunun kullanımına ilişkin koşullar ve şartlar.",
};

const SECTIONS: LegalSection[] = [
  {
    heading: "Hizmetin Tanımı",
    paragraphs: [
      "Soru Atölyesi (“Platform”), MEB matematik müfredatı (1.–7. sınıf) kapsamında, seçilen kazanım koduna göre yapay zeka destekli çalışma kağıdı üreten bir çevrim içi hizmettir. Çıktılar PDF biçiminde; cevap anahtarı ve adım adım çözüm bölümleriyle birlikte sunulur.",
    ],
  },
  {
    heading: "Koşulların Kabulü",
    paragraphs: [
      "Platform’u kullanarak bu Kullanım Koşulları’nı kabul etmiş sayılırsınız. Koşulları kabul etmiyorsanız Platform’u kullanmamanız gerekir.",
    ],
  },
  {
    heading: "Hesap",
    paragraphs: [
      "Hizmetten yararlanmak için geçerli bir e-posta adresiyle hesap oluşturulması gerekir. Hesap bilgilerinin doğruluğundan ve hesap güvenliğinin korunmasından kullanıcı sorumludur. Hesabınız üzerinden gerçekleştirilen işlemlerden siz sorumlu tutulursunuz.",
    ],
  },
  {
    heading: "Kullanım Kuralları",
    paragraphs: ["Platform’u kullanırken aşağıdaki kurallara uymayı kabul edersiniz:"],
    bullets: [
      "Platform yalnızca eğitim amacıyla ve hukuka uygun şekilde kullanılır.",
      "Platform’a otomatik/toplu erişim, tersine mühendislik veya sistemi aşırı yükleyecek işlemler yapılamaz.",
      "Üretilen içerikler hukuka aykırı veya başkalarının haklarını ihlal eden amaçlarla kullanılamaz.",
      "Hesap, üçüncü kişilerle paylaşılarak kötüye kullanılamaz.",
    ],
  },
  {
    heading: "Yapay Zeka Kaynaklı İçerik ve Doğruluk",
    paragraphs: [
      "Çalışma kağıtları yapay zeka modelleri tarafından üretilir. Platform, üretilen içeriğe aritmetik doğrulama ve müfredat uyumu denetimleri uygulasa da, içeriğin tümüyle hatasız olduğu garanti edilmez.",
      "Kullanıcı, üretilen çalışma kağıtlarını öğrencilerle paylaşmadan veya sınavda kullanmadan önce içeriği kontrol etmekle yükümlüdür.",
    ],
  },
  {
    heading: "Fikri Mülkiyet",
    paragraphs: [
      "Platform yazılımı, tasarımı, “Soru Atölyesi” adı ve markası Veri Sorumlusu’na aittir; izinsiz kullanılamaz.",
      "Kullanıcı, Platform üzerinden ürettiği çalışma kağıtlarını eğitim amacıyla serbestçe kullanabilir, çoğaltabilir ve dağıtabilir.",
    ],
  },
  {
    heading: "Kota ve Erken Kullanım Dönemi",
    paragraphs: [
      "Platform erken kullanım dönemindedir. Hesap başına aylık üretim kotası uygulanır. Hizmet özellikleri, kotalar ve fiyatlandırma; önceden bilgilendirme yapılarak değiştirilebilir.",
    ],
  },
  {
    heading: "Sorumluluğun Sınırlandırılması",
    paragraphs: [
      "Hizmet “olduğu gibi” sunulur. Veri Sorumlusu; hizmet kesintilerinden, üretilen içerikteki hatalardan veya bu içeriğin kullanımından doğabilecek doğrudan ya da dolaylı zararlardan, yürürlükteki mevzuatın izin verdiği azami ölçüde sorumlu tutulamaz.",
    ],
  },
  {
    heading: "Hesabın Askıya Alınması ve Fesih",
    paragraphs: [
      "Kullanıcı hesabını dilediği zaman kapatabilir. Veri Sorumlusu, bu koşulların ihlali hâlinde hesabı askıya alma veya kapatma hakkını saklı tutar.",
    ],
  },
  {
    heading: "Değişiklikler ve Uygulanacak Hukuk",
    paragraphs: [
      "Bu Kullanım Koşulları güncellenebilir; güncel sürüm bu sayfada yayımlanır.",
      "Bu koşullara Türkiye Cumhuriyeti hukuku uygulanır. Doğabilecek uyuşmazlıkların çözümünde Türkiye Cumhuriyeti mahkemeleri ve icra daireleri yetkilidir.",
    ],
  },
];

export default function TermsPage() {
  return (
    <LegalDocument
      eyebrow="Hukuki"
      title="Kullanım Koşulları"
      intro="Bu Kullanım Koşulları, Soru Atölyesi platformunun kullanımına ilişkin şartları düzenler. Lütfen Platform’u kullanmadan önce dikkatlice okuyunuz."
      updated="22 Mayıs 2026"
      sections={SECTIONS}
    />
  );
}
