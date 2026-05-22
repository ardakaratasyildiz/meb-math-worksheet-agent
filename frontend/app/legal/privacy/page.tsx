/*
 * TASLAK — resmi yayın öncesi metin bir hukuk danışmanı tarafından gözden
 * geçirilmeli.
 */
import { LegalDocument, type LegalSection } from "@/components/LegalDocument";

export const metadata = {
  title: "Gizlilik Politikası · Soru Atölyesi",
  description:
    "Soru Atölyesi'nin hangi verileri topladığı, nasıl kullandığı ve koruduğuna ilişkin gizlilik politikası.",
};

const SECTIONS: LegalSection[] = [
  {
    heading: "Topladığımız Veriler",
    paragraphs: ["Platform’u kullanırken aşağıdaki veriler toplanır:"],
    bullets: [
      "Hesap verileri: e-posta adresi ve ad-soyad.",
      "Kullanım verileri: oluşturduğunuz çalışma kağıtları, seçtiğiniz sınıf/konu/kazanım parametreleri ve üretim geçmişi.",
      "Teknik veriler: IP adresi, tarayıcı bilgisi ve erişim/işlem logları.",
    ],
  },
  {
    heading: "Verileri Nasıl Kullanıyoruz",
    paragraphs: ["Toplanan veriler yalnızca şu amaçlarla kullanılır:"],
    bullets: [
      "Çalışma kağıdı üretim hizmetinin sunulması,",
      "Hesabın oluşturulması ve yönetilmesi,",
      "Üretim geçmişine cihazlar arası erişim sağlanması,",
      "Hizmet güvenliğinin korunması ve kötüye kullanımın önlenmesi.",
    ],
  },
  {
    heading: "Üçüncü Taraf Hizmetler",
    paragraphs: [
      "Hizmetin sağlanabilmesi için aşağıdaki sağlayıcılar kullanılır:",
    ],
    bullets: [
      "Clerk — kimlik doğrulama ve oturum yönetimi,",
      "Google (Gemini) ve Anthropic (Claude) — çalışma kağıdı içeriğinin üretilmesi,",
      "Render ve Vercel — uygulamanın barındırılması,",
      "Turso — veritabanı hizmeti.",
    ],
  },
  {
    heading: "Verilerin Paylaşımı",
    paragraphs: [
      "Verileriniz, yukarıdaki hizmet sağlayıcılarla yalnızca hizmetin teknik olarak sağlanması için gerekli ölçüde paylaşılır. Verileriniz üçüncü taraflara satılmaz, reklam amacıyla kullanılmaz ve yapay zeka modeli eğitiminde kullanılmaz.",
    ],
  },
  {
    heading: "Çerezler",
    paragraphs: [
      "Platform; yalnızca oturum yönetimi ve kimlik doğrulama için gerekli olan çerezleri kullanır (bu çerezler kimlik doğrulama sağlayıcısı tarafından yerleştirilir). Pazarlama veya üçüncü taraf reklam çerezi kullanılmaz.",
    ],
  },
  {
    heading: "Veri Saklama Süresi",
    paragraphs: [
      "Hesap verileri, hesabınız aktif olduğu sürece saklanır. Üretim geçmişi, hesap başına sınırlı sayıda (en yeni kayıtlar) tutulur. Hesabınızı kapatmanız hâlinde verileriniz makul bir süre içinde silinir.",
    ],
  },
  {
    heading: "Veri Güvenliği",
    paragraphs: [
      "Veriler şifreli bağlantılar (HTTPS) üzerinden iletilir ve yetkilendirme denetimleriyle korunur. Hiçbir sistem mutlak güvenlik sağlayamasa da, verilerinizi korumak için makul teknik ve idari tedbirler alınır.",
    ],
  },
  {
    heading: "Haklarınız",
    paragraphs: [
      "Kişisel verilerinize erişme, düzeltilmesini veya silinmesini isteme dâhil tüm haklarınız ve başvuru yöntemi, KVKK Aydınlatma Metni sayfasında ayrıntılı olarak açıklanmıştır.",
    ],
  },
  {
    heading: "Çocukların Gizliliği",
    paragraphs: [
      "Platform öncelikle öğretmenler ve veliler için tasarlanmıştır. 18 yaşından küçük kullanıcıların hesap oluşturması ve Platform’u kullanması, bir veli veya öğretmen gözetiminde olmalıdır.",
    ],
  },
  {
    heading: "Değişiklikler ve İletişim",
    paragraphs: [
      "Bu Gizlilik Politikası güncellenebilir; güncel sürüm, “son güncelleme” tarihiyle birlikte bu sayfada yayımlanır.",
      "Gizliliğe ilişkin sorularınız için destek@soruatolyesi.com adresine yazabilirsiniz.",
    ],
  },
];

export default function PrivacyPage() {
  return (
    <LegalDocument
      eyebrow="Hukuki"
      title="Gizlilik Politikası"
      intro="Bu Gizlilik Politikası; Soru Atölyesi’nin hangi verileri topladığını, bu verileri nasıl kullandığını ve koruduğunu açıklar. Kişisel verilerin işlenmesine ilişkin ayrıntılı bilgilendirme KVKK Aydınlatma Metni sayfasındadır."
      updated="22 Mayıs 2026"
      sections={SECTIONS}
    />
  );
}
