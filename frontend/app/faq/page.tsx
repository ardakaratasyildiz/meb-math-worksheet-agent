import { ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Footer } from "@/components/Footer";
import { JsonLd, faqPageSchema } from "@/components/JsonLd";
import { PageHeader } from "@/components/PageHeader";

export const metadata = {
  title: "Sıkça Sorulanlar · Soru Atölyesi",
  description:
    "Soru Atölyesi hakkında en sık sorulan teknik ve kullanım soruları.",
};

type FaqItem = { q: string; a: string };
type FaqCategory = { title: string; items: FaqItem[] };

const FAQ_CATEGORIES: FaqCategory[] = [
  {
    title: "Üretim süreci",
    items: [
      {
        q: "Sistem soruları nasıl üretiyor?",
        a: "Üretim, seçilen sınıf ve kazanım kodu temel alınarak yapılır. Sistem MEB ders kitaplarından bağlam çekerek soruları üretir; üretilen her soru önce aritmetik denetimden, ardından kazanım uyumu denetiminden geçer. Bu denetimleri geçemeyen sorular kullanıcıya sunulmadan elenir.",
      },
      {
        q: "Hangi soru tipleri üretiliyor?",
        a: "Klasik (açık uçlu), çoktan seçmeli, doğru/yanlış ve eşleştirme türlerinde sorular üretilebilir. Soru tipi dağılımı sınıf seviyesine göre otomatik ayarlanır.",
      },
      {
        q: "Bir kağıtta kaç soru olabilir?",
        a: "Kağıt başına soru sayısı 5 ile 20 arasında seçilebilir. Sayı, üretim formundaki kaydırıcı (slider) ile belirlenir.",
      },
      {
        q: "Aynı parametrelerle tekrar üretim yapınca aynı sorular mı geliyor?",
        a: "Hayır. Anlamsal benzerlik denetimi devreye girer: önceki üretimde çıkan sorulara cosine benzerliği yüksek olanlar üretim havuzundan elenir. Aynı parametre setiyle tekrar üretim her seferinde farklı bir soru kümesi getirir.",
      },
    ],
  },
  {
    title: "Çıktı ve PDF",
    items: [
      {
        q: "PDF'in içinde neler yer alıyor?",
        a: "PDF üç bölümden oluşur: (1) soru sayfaları, (2) cevap anahtarı — her sorunun yanında ilgili MEB kazanım kodu görünür, (3) adım adım çözüm sayfası.",
      },
      {
        q: "PDF Türkçe karakterleri doğru gösteriyor mu?",
        a: "Evet. PDF üretimi DejaVu yazı tipi ailesi ile yapılır; tüm Türkçe karakterler (ç, ğ, ı, ö, ş, ü) doğru biçimde basılır. A4 baskı boyutu varsayılan olarak ayarlıdır.",
      },
      {
        q: "Aynı PDF'i tekrar indirmek mümkün mü?",
        a: "Üretim Geçmişi sayfasından önceki üretimlere erişilir ve aynı PDF tekrar indirilebilir. Bu indirme aylık kotadan düşmez.",
      },
    ],
  },
  {
    title: "Kapsam ve yol haritası",
    items: [
      {
        q: "Hangi sınıflar destekleniyor?",
        a: "1.→8. sınıf MEB matematik müfredatının tamamı desteklenmektedir. 8. sınıf, LGS hazırlık kapsamını da içerir — gerçek çıkmış LGS soruları örnek havuzunda kullanılır.",
      },
      {
        q: "Diğer dersler eklenecek mi?",
        a: "Şu anda yalnızca matematik üretilmektedir. Diğer derslerin (Türkçe, Fen Bilimleri vb.) eklenmesi yol haritasındadır; takvim henüz kesinleşmemiştir.",
      },
    ],
  },
  {
    title: "Hesap ve veri",
    items: [
      {
        q: "Kayıt için hangi bilgiler gereklidir?",
        a: "Yalnızca e-posta adresi gereklidir. Şu anda erken kullanım döneminde ödeme bilgisi alınmamaktadır.",
      },
      {
        q: "Üretim verileri başka kullanıcılarla paylaşılıyor mu?",
        a: "Hayır. Üretilen sorular kullanıcı hesabına özel olarak saklanır. Sistem önbelleği yalnızca aynı kullanıcının tekrar üretim taleplerinde kullanılır; üçüncü taraflarla paylaşılmaz, model eğitiminde kullanılmaz.",
      },
      {
        q: "Hesap birden fazla cihazda kullanılabilir mi?",
        a: "Evet. Aynı hesapla telefon, tablet ve bilgisayardan eş zamanlı giriş yapılabilir. Üretim geçmişi merkezi olarak saklanır ve tüm cihazlardan erişilebilir.",
      },
    ],
  },
];

export default function FaqPage() {
  // Tüm kategorilerden tek düz liste — schema.org FAQPage tek mainEntity dizisi ister.
  const allFaqs = FAQ_CATEGORIES.flatMap((c) => c.items);
  return (
    <>
      <JsonLd id="faq-schema" data={faqPageSchema(allFaqs)} />
      <PageHeader
        eyebrow="Sıkça sorulanlar"
        title="Sistem hakkında sık sorulan sorular"
        body="Üretim süreci, çıktı formatı, kapsam ve hesap konularındaki temel soruların yanıtları aşağıdadır. Listede yer almayan sorular için destek@soruatolyesi.com adresine yazılabilir."
      />

      <section className="py-20">
        <div className="container max-w-3xl">
          {FAQ_CATEGORIES.map((cat, ci) => (
            <div key={ci} className="mb-12 last:mb-0">
              <h2 className="mb-5 text-sm font-semibold uppercase tracking-wider text-primary">
                {cat.title}
              </h2>
              <div className="divide-y divide-border rounded-xl border bg-card">
                {cat.items.map((f, i) => (
                  <details key={i} className="group p-5">
                    <summary className="flex cursor-pointer items-center justify-between gap-4 text-base font-medium text-foreground marker:hidden">
                      <span>{f.q}</span>
                      <span
                        aria-hidden
                        className="flex h-6 w-6 items-center justify-center rounded-md bg-accent text-accent-foreground transition-transform group-open:rotate-45"
                      >
                        +
                      </span>
                    </summary>
                    <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                      {f.a}
                    </p>
                  </details>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-card py-20">
        <div className="container">
          <div className="mx-auto flex max-w-3xl flex-col items-center gap-6 rounded-2xl border bg-background p-12 text-center">
            <h2 className="text-3xl font-bold tracking-tight text-foreground">
              Yanıtını bulamadığın bir soru var mı?
            </h2>
            <p className="text-base text-muted-foreground">
              Listede yer almayan sorular için destek adresine yazabilirsin.
              Yanıt süresi ortalama 24 saattir.
            </p>
            <Button asChild size="lg" className="gap-2 px-8">
              <a href="mailto:destek@soruatolyesi.com">
                Destek ekibine yaz <ArrowRight className="h-4 w-4" />
              </a>
            </Button>
          </div>
        </div>
      </section>

      <Footer />
    </>
  );
}
