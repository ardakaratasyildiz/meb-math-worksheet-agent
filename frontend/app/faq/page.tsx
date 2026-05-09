import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Footer } from "@/components/Footer";
import { PageHeader } from "@/components/PageHeader";

export const metadata = {
  title: "Sıkça Sorulanlar · Quiz Marketi",
  description:
    "Quiz Marketi hakkında en çok sorulan sorular — ürün, kalite, gizlilik, fiyat, hesap.",
};

type FaqItem = { q: string; a: string };
type FaqCategory = { title: string; items: FaqItem[] };

const FAQ_CATEGORIES: FaqCategory[] = [
  {
    title: "Ürün",
    items: [
      {
        q: "Hangi sınıflar destekleniyor?",
        a: "Şu an 1.→7. sınıf MEB matematik müfredatı tamamen destekleniyor. 8. sınıf (LGS) yol haritasında, sonbahar 2026'da gelmesi planlanıyor. Diğer dersler — Türkçe, Fen — sonraki adım.",
      },
      {
        q: "Hangi soru tipleri üretiliyor?",
        a: "Klasik (cevabı yazılan), çoktan seçmeli, doğru/yanlış ve eşleştirme türlerinde sorular üretiliyor. Sınıf seviyesine göre dağılım otomatik ayarlanıyor — 1. sınıfta görsel ağırlıklı, 7. sınıfta klasik ağırlıklı.",
      },
      {
        q: "Soru sayısını ben mi seçiyorum?",
        a: "Evet — kağıt başına 5 ile 20 arası soru sayısını sen belirliyorsun. Konuya ve zorluğa göre 10 soru standart, kapsamlı pratik için 15-20 öneririz.",
      },
      {
        q: "Cevap anahtarı ve çözüm de geliyor mu?",
        a: "Her PDF'de var: 1. sayfa(lar) sorular, son sayfada cevap anahtarı (kazanım koduyla beraber), ardından adım adım çözüm sayfası. Öğretmenin tek belge yetiyor.",
      },
    ],
  },
  {
    title: "Kalite ve müfredat",
    items: [
      {
        q: "MEB müfredatına nasıl uyduğunu garanti ediyorsunuz?",
        a: "Her soru, MEB tarafından yayımlanan kazanım kodlarına bire bir hizalanır. Sistem, MEB ders kitaplarından bağlam çekerek bağlam üretir; ikinci bir yapay zekâ kontrolü her soruyu kazanım uyumu açısından denetler — geçmeyenler atılır ve yenileri üretilir.",
      },
      {
        q: "Soruların matematiksel doğruluğu nasıl kontrol ediliyor?",
        a: "İki katmanlı: önce otomatik aritmetik denetim (formüller, hesaplamalar), sonra ikinci bir yapay zekâ uzun cümleli/kavramsal soruları denetler. Hatalı bulunanlar kullanıcıya hiç görünmez.",
      },
      {
        q: "Aynı konuyu ürettikçe hep benzer sorular mı geliyor?",
        a: "Hayır — anlamsal benzerlik denetimi sayesinde geçmişte aldığın sorulara benzer olanlar otomatik elenir. Aynı sınıf+konu+kazanım+zorluk kombinasyonunu 10 kez ürettiğinde 10 farklı set alırsın.",
      },
    ],
  },
  {
    title: "Gizlilik ve veri",
    items: [
      {
        q: "KVKK ve veri gizliliği nasıl?",
        a: "Üretim parametreleri ve geçmiş anonim olarak saklanır. Kişisel veri toplamıyoruz; sadece e-posta (giriş için) ve abonelik bilgileri. Tüm veri AB sunucularında (Frankfurt) tutulur.",
      },
      {
        q: "Ürettiğim kağıt başkalarıyla paylaşılıyor mu?",
        a: "Hayır. Üretilen sorular yalnızca senin hesabına bağlı; üçüncü tarafa açılmaz, eğitim verisi olarak kullanılmaz. Cache'leme yalnızca kendi tekrar indirmen için.",
      },
      {
        q: "Hesabımı silersem verilerim ne olur?",
        a: "Hesap silme talebinde tüm geçmiş ve üretim verilerini 30 gün içinde sileriz. Talep e-postasını destek@quizmarketi.com'a iletmen yeterli.",
      },
    ],
  },
  {
    title: "Hesap ve abonelik",
    items: [
      {
        q: "İptal kolay mı? Para iadesi var mı?",
        a: "Aboneliği panelden tek tıkla iptal edersin, sonraki dönem ücret çekilmez. İlk 14 gün içinde memnun kalmazsan koşulsuz iade — sebep sormuyoruz.",
      },
      {
        q: "Bir hesap birden fazla cihazda kullanılabilir mi?",
        a: "Evet — telefondan, tabletten, bilgisayardan aynı hesapla giriş yapabilirsin. Aynı anda farklı cihazlardan üretim yapmak da serbest.",
      },
      {
        q: "Diğer dersler eklenecek mi?",
        a: "Evet — Türkçe sonbahar 2026, Fen Bilimleri 2027 başında planda. Sosyal Bilgiler ve İngilizce sonra. Yol haritası blog'umuzdan takip edilebilir.",
      },
    ],
  },
];

export default function FaqPage() {
  return (
    <>
      <PageHeader
        eyebrow="Sıkça sorulanlar"
        title="Kafanda soru var mı?"
        body="Ürün, kalite, gizlilik, fiyat ve hesap konularında en çok merak edilenleri burada topladık. Aradığını bulamazsan destek@quizmarketi.com."
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
              Hâlâ sorun mu var?
            </h2>
            <p className="text-base text-muted-foreground">
              Sıkça sorulanlarda yoksa, e-posta gönder. Genelde 24 saat içinde
              cevaplıyoruz.
            </p>
            <Button asChild size="lg" className="gap-2 px-8">
              <a href="mailto:destek@quizmarketi.com">
                Bize yaz <ArrowRight className="h-4 w-4" />
              </a>
            </Button>
          </div>
        </div>
      </section>

      <Footer />
    </>
  );
}
