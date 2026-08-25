/*
 * TASLAK — yetkili mahkeme şimdilik genel (T.C. mahkemeleri) bırakıldı.
 * Resmi yayın öncesi metin bir hukuk danışmanı tarafından gözden geçirilmeli.
 *
 * ABONELİK BÖLÜMLERİ (§7-§10) MAĞAZA İNCELEMESİNİN OKUDUĞU METİNDİR.
 * Mobil paywall (apps/mobile/src/app/paywall.tsx) "Kullanım Koşulları" linkiyle
 * BURAYA çıkar; App Store 3.1.2 ve Play abonelik politikası, link verilen
 * sözleşmenin abonelik şartlarını (süre, otomatik yenileme, iptal, tahsilat)
 * içermesini şart koşuyor. Buradaki rakamlar app/config.py ile aynı olmalı:
 * ücretsiz 10 kağıt/ay + 2/gün · deneme 7 gün/20 kağıt · Pro 50 · Pro+ 120 ·
 * ek paket 30 gün. Fiyatlar bilinçli olarak YAZILMAZ — mağaza vitrini ülkeye
 * göre değişir ve sabit yazılan tutar sessizce yanlışa döner.
 */
import { LegalDocument, type LegalSection } from "@/components/LegalDocument";

export const metadata = {
  title: "Kullanım Koşulları · Soru Atölyesi",
  description:
    "Soru Atölyesi platformunun kullanımına ilişkin koşullar, abonelik şartları ve iptal kuralları.",
};

const SECTIONS: LegalSection[] = [
  {
    heading: "Hizmetin Tanımı",
    paragraphs: [
      "Soru Atölyesi (“Platform”), MEB müfredatı kapsamındaki kazanımlara göre yapay zeka destekli çalışma kağıdı, alıştırma ve quiz üreten bir çevrim içi hizmettir. Hizmet; matematik, fen bilimleri, Türkçe, sosyal bilgiler ve İngilizce derslerinde 1.–8. sınıf düzeyini (8. sınıf LGS hazırlık dahil) kapsar. Çıktılar PDF biçiminde; cevap anahtarı ve adım adım çözüm bölümleriyle birlikte sunulur.",
      "Platform’a web sitesi ve mobil uygulamalar (iOS / Android) üzerinden erişilir.",
      "Soru Atölyesi bağımsız bir eğitim uygulamasıdır. T.C. Millî Eğitim Bakanlığı (MEB) ile herhangi bir resmî bağlantısı, ortaklığı ya da onayı yoktur; MEB’i temsil etmez. Kazanım, ünite ve sınıf başlıkları MEB’in kamuya açık müfredat belgelerinden alınmıştır; üretilen içerik MEB’in resmî yayını, ders kitabı veya sınav materyali değildir.",
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
      "18 yaşından küçük kullanıcılar Platform’u ancak veli veya öğretmen gözetiminde kullanabilir. Çocuk hesabını kendi hesabına bağlayan veli, çocuğun Platform’u kullanmasına izin verdiğini beyan etmiş olur.",
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
    heading: "Ücretsiz Kullanım, Kota ve Deneme Süresi",
    paragraphs: [
      "Platform’un ücretsiz bir kademesi vardır. Ücretsiz kademede hesap başına aylık 10 çalışma kağıdı üretilebilir ve günlük üretim en fazla 2 çalışma kağıdı ile sınırlıdır. Kota her takvim ayının başında yenilenir; kullanılmayan haklar sonraki aya devretmez.",
      "Yeni hesaplara bir kez 7 gün süreli ve 20 çalışma kağıdı hakkı içeren ücretsiz deneme tanımlanır. Bu deneme doğrudan Platform tarafından sağlanır: ödeme aracı bilgisi istenmez, otomatik olarak ücretli bir aboneliğe dönüşmez ve süre sonunda hesap kendiliğinden ücretsiz kademeye döner.",
      "Kotalar ve ücretsiz kademenin kapsamı, önceden bilgilendirme yapılarak değiştirilebilir.",
    ],
  },
  {
    heading: "Ücretli Planlar ve Abonelik",
    paragraphs: [
      "Platform aylık dönemli iki ücretli plan sunar: Pro (ayda 50 çalışma kağıdı) ve Pro+ (ayda 120 çalışma kağıdı). Planların güncel fiyatı, satın alma ekranında ve ilgili uygulama mağazasının vitrininde yerel para biriminde, vergiler dahil olarak gösterilir.",
      "Mobil uygulama üzerinden alınan abonelikler Apple App Store veya Google Play üzerinden satılır ve tahsil edilir. Ödeme, satın almayı onayladığınızda mağaza hesabınızdan tahsil edilir.",
      "Abonelikler aylıktır ve otomatik olarak yenilenir. İçinde bulunulan dönemin bitiminden en az 24 saat önce iptal edilmezse abonelik aynı süre ve ücretle kendiliğinden yenilenir; yenileme ücreti dönem sonundan önceki 24 saat içinde tahsil edilir.",
      "Aboneliğinizi, satın aldığınız mağazanın hesap ayarlarından (App Store: Ayarlar → Apple Kimliği → Abonelikler; Google Play: Play Store → Abonelikler) dilediğiniz zaman yönetebilir veya iptal edebilirsiniz. İptal, ödemesi yapılmış dönemin sonunda yürürlüğe girer; o tarihe kadar plan hakları kullanılmaya devam eder.",
      "Aylık kağıt hakkı her abonelik döneminin başında yenilenir. Kullanılmayan haklar sonraki döneme devretmez ve nakde çevrilemez.",
      "Ücrette veya plan kapsamında yapılacak değişiklikler önceden duyurulur; mağaza kuralları gereği fiyat artışları abonenin onayına tabidir. Değişikliği kabul etmemeniz halinde aboneliğinizi dönem sonunda iptal edebilirsiniz.",
    ],
  },
  {
    heading: "Ek Kağıt Paketleri",
    paragraphs: [
      "Aktif aboneler, aylık hakları tükendiğinde ek kağıt paketi (+25 veya +75 çalışma kağıdı) satın alabilir. Ek paketler tek seferlik satın almalardır; abonelik değildir ve otomatik olarak yenilenmez.",
      "Ek paket hakları satın alma tarihinden itibaren 30 gün içinde kullanılabilir. Süre sonunda kalan haklar geçersiz olur, sonraki döneme devretmez ve nakde çevrilemez.",
    ],
  },
  {
    heading: "Cayma Hakkı, İade ve Fatura",
    paragraphs: [
      "Platform, elektronik ortamda anında ifa edilen dijital içerik ve hizmet sunar. Mesafeli Sözleşmeler Yönetmeliği’nin 15/1-(ğ) maddesi uyarınca, kullanıcının onayıyla ifasına başlanan bu tür hizmetlerde cayma hakkı bulunmamaktadır. Kullanıcı, satın alma anında hizmetin derhal sunulmasını talep ettiğini ve bu nedenle cayma hakkının sona erdiğini kabul eder.",
      "Uygulama mağazaları üzerinden yapılan satın almalarda satış işlemi ilgili mağaza tarafından gerçekleştirilir. İade talepleri mağazanın kendi iade politikasına tabidir ve doğrudan Apple’a (reportaproblem.apple.com) veya Google Play’e iletilmelidir; bu taleplerin sonuçlandırılması Platform’un yetkisinde değildir.",
      "Satın almaya ilişkin ödeme belgesi/faturası ilgili uygulama mağazası tarafından düzenlenir ve mağaza hesabınıza tanımlı e-posta adresine iletilir.",
      "Teknik bir arıza nedeniyle satın aldığınız hakları kullanamadıysanız destek@soruatolyesi.com adresinden bize ulaşın; sorunu gidermek ya da hakkı yeniden tanımlamak için çalışırız.",
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
      "Kullanıcı hesabını dilediği zaman kapatabilir. Veri Sorumlusu, bu koşulların ihlali halinde hesabı askıya alma veya kapatma hakkını saklı tutar.",
      "Önemli: Hesabın silinmesi, uygulama mağazası üzerinden alınmış bir aboneliği kendiliğinden iptal etmez. Ücretlendirmenin durması için aboneliğin ayrıca mağaza hesabı ayarlarından iptal edilmesi gerekir.",
    ],
    linkHref: "/hesap/sil",
    linkLabel: "Hesabımı ve verilerimi sil",
  },
  {
    heading: "Değişiklikler, Uyuşmazlık ve Uygulanacak Hukuk",
    paragraphs: [
      "Bu Kullanım Koşulları güncellenebilir; güncel sürüm bu sayfada yayımlanır.",
      "Bu koşullara Türkiye Cumhuriyeti hukuku uygulanır. Tüketici sıfatını taşıyan kullanıcılar, yasal parasal sınırlar dahilinde Tüketici Hakem Heyetlerine ya da Tüketici Mahkemelerine başvurabilir. Bunun dışındaki uyuşmazlıklarda Türkiye Cumhuriyeti mahkemeleri ve icra daireleri yetkilidir.",
    ],
  },
];

export default function TermsPage() {
  return (
    <LegalDocument
      eyebrow="Hukuki"
      title="Kullanım Koşulları"
      intro="Bu Kullanım Koşulları, Soru Atölyesi platformunun kullanımına, abonelik ve ödeme şartlarına ilişkin kuralları düzenler. Lütfen Platform’u kullanmadan önce dikkatlice okuyunuz."
      updated="25 Ağustos 2026"
      sections={SECTIONS}
    />
  );
}
