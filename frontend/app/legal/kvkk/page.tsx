/*
 * TASLAK — veri sorumlusu kimliği şimdilik "Soru Atölyesi" olarak girildi.
 * Resmi yayın öncesi gerçek tüzel/şahıs kimliği ve adres eklenmeli, metin bir
 * hukuk danışmanı tarafından gözden geçirilmeli.
 */
import { LegalDocument, type LegalSection } from "@/components/LegalDocument";

export const metadata = {
  title: "KVKK Aydınlatma Metni · Soru Atölyesi",
  description:
    "6698 sayılı KVKK kapsamında Soru Atölyesi kullanıcılarının kişisel verilerinin işlenmesine ilişkin aydınlatma metni.",
};

const SECTIONS: LegalSection[] = [
  {
    heading: "Veri Sorumlusu",
    paragraphs: [
      "Soru Atölyesi (“Platform”), bu aydınlatma metni kapsamında veri sorumlusu (“Veri Sorumlusu”) sıfatıyla hareket etmektedir.",
      "Veri Sorumlusu’na destek@soruatolyesi.com adresi üzerinden ulaşılabilir.",
    ],
  },
  {
    heading: "İşlenen Kişisel Veriler",
    paragraphs: [
      "Platform’u kullanmanız kapsamında işlenen kişisel veri kategorileri şunlardır:",
    ],
    bullets: [
      "Kimlik ve iletişim verisi: ad-soyad ve e-posta adresi (hesap oluşturma sırasında, kimlik doğrulama sağlayıcısı aracılığıyla).",
      "İşlem güvenliği verisi: IP adresi, oturum kayıtları ve erişim/işlem logları.",
      "Kullanım verisi: oluşturduğunuz çalışma kağıtları, seçtiğiniz sınıf/konu/kazanım parametreleri ve üretim geçmişi.",
    ],
  },
  {
    heading: "Kişisel Verilerin İşlenme Amaçları",
    paragraphs: ["Kişisel verileriniz aşağıdaki amaçlarla işlenir:"],
    bullets: [
      "Üyelik hesabının oluşturulması ve yönetilmesi,",
      "Çalışma kağıdı üretim hizmetinin sunulması,",
      "Üretim geçmişinin saklanması ve tekrar erişim imkânı tanınması,",
      "Hizmet güvenliğinin sağlanması ve kötüye kullanımın önlenmesi,",
      "Yürürlükteki mevzuattan doğan yasal yükümlülüklerin yerine getirilmesi.",
    ],
  },
  {
    heading: "İşlemenin Hukuki Sebepleri",
    paragraphs: [
      "Kişisel verileriniz KVKK’nın 5. maddesi kapsamında şu hukuki sebeplere dayanılarak işlenir:",
    ],
    bullets: [
      "Bir sözleşmenin kurulması veya ifası için verilerin işlenmesinin gerekli olması (hesap ve hizmet sunumu),",
      "Veri Sorumlusu’nun hukuki yükümlülüğünü yerine getirebilmesi,",
      "İlgili kişinin temel hak ve özgürlüklerine zarar vermemek kaydıyla, Veri Sorumlusu’nun meşru menfaati (hizmet güvenliği ve iyileştirme).",
    ],
  },
  {
    heading: "Aktarım ve Yurt Dışına Aktarım",
    paragraphs: [
      "Hizmetin sunulabilmesi için kişisel verileriniz, yalnızca ilgili hizmetin gerektirdiği ölçüde aşağıdaki hizmet sağlayıcılarla paylaşılır. Bu sağlayıcıların sunucuları yurt dışında bulunabildiğinden, veriler KVKK’nın 9. maddesi kapsamında yurt dışına aktarılmaktadır:",
    ],
    bullets: [
      "Clerk — kimlik doğrulama ve oturum yönetimi,",
      "Google (Gemini) ve Anthropic (Claude) — çalışma kağıdı içeriğinin yapay zeka ile üretilmesi,",
      "Render, Vercel ve Turso — uygulama barındırma ve veritabanı hizmetleri.",
    ],
  },
  {
    heading: "Kişisel Verilerin Toplanma Yöntemi",
    paragraphs: [
      "Kişisel verileriniz; Platform’a internet üzerinden eriştiğinizde ve hesabınızla işlem yaptığınızda, elektronik ortamda ve otomatik yollarla toplanır.",
      "Verileriniz üçüncü taraflara satılmaz, pazarlama/reklam amacıyla kullanılmaz ve yapay zeka modeli eğitiminde kullanılmaz.",
    ],
  },
  {
    heading: "İlgili Kişinin Hakları (KVKK m. 11)",
    paragraphs: [
      "KVKK’nın 11. maddesi uyarınca Veri Sorumlusu’na başvurarak şu haklara sahipsiniz:",
    ],
    bullets: [
      "Kişisel verinizin işlenip işlenmediğini öğrenme ve işlenmişse buna ilişkin bilgi talep etme,",
      "İşlenme amacını ve amacına uygun kullanılıp kullanılmadığını öğrenme,",
      "Yurt içinde veya yurt dışında verilerin aktarıldığı üçüncü kişileri bilme,",
      "Eksik veya yanlış işlenmiş verilerin düzeltilmesini isteme,",
      "Mevzuatta öngörülen şartlarla verilerin silinmesini veya yok edilmesini isteme,",
      "Düzeltme/silme işlemlerinin verilerin aktarıldığı üçüncü kişilere bildirilmesini isteme,",
      "Münhasıran otomatik sistemlerle yapılan analiz sonucu aleyhinize bir sonuç çıkmasına itiraz etme,",
      "Kanuna aykırı işleme nedeniyle zarara uğramanız hâlinde zararın giderilmesini talep etme.",
    ],
  },
  {
    heading: "Başvuru",
    paragraphs: [
      "Yukarıdaki haklarınıza ilişkin taleplerinizi destek@soruatolyesi.com adresine iletebilirsiniz. Başvurularınız, KVKK ve ilgili mevzuatta öngörülen süre içinde (en geç 30 gün) sonuçlandırılır.",
    ],
  },
];

export default function KvkkPage() {
  return (
    <LegalDocument
      eyebrow="Hukuki"
      title="KVKK Aydınlatma Metni"
      intro="6698 sayılı Kişisel Verilerin Korunması Kanunu (“KVKK”) uyarınca, Soru Atölyesi kullanıcılarının kişisel verilerinin işlenmesine ilişkin aşağıdaki bilgilendirme yapılmaktadır."
      updated="22 Mayıs 2026"
      sections={SECTIONS}
    />
  );
}
