import Link from "next/link";
import { ArrowRight, Check, X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Footer } from "@/components/Footer";
import { PageHeader, SectionHeader } from "@/components/PageHeader";

export const metadata = {
  title: "Fiyatlandırma · Quiz Marketi",
  description:
    "Ücretsiz başla. İhtiyacın oldukça Pro'ya yükselt. Şeffaf fiyat — gizli ücret yok.",
};

const PLANS = [
  {
    name: "Ücretsiz",
    price: "0",
    period: "Süresiz",
    note: "Ürünü tanımak ve ara sıra kullanım için yeterli.",
    cta: "Ücretsiz başla",
    href: "/sign-up",
    featured: false,
    features: [
      { label: "100 soru / ay", on: true },
      { label: "Tüm sınıflar (1.→7.)", on: true },
      { label: "Tüm konular ve kazanımlar", on: true },
      { label: "Cevap anahtarı + adım çözüm", on: true },
      { label: "PDF Quiz Marketi watermark'lı", on: true },
      { label: "Geçmiş — son 7 gün", on: true },
      { label: "Sınırsız soru", on: false },
      { label: "Watermark yok", on: false },
      { label: "Geçmiş — sınırsız", on: false },
    ],
  },
  {
    name: "Pro",
    price: "99",
    period: "/ ay",
    note: "Aktif öğretmen, veli ve öğrenci için en uygun.",
    cta: "Pro'ya geç",
    href: "/sign-up?plan=pro",
    featured: true,
    annualHint: "Yıllık ödemede 79 ₺/ay (12 × 79 ₺ = 948 ₺/yıl)",
    features: [
      { label: "Sınırsız soru", on: true },
      { label: "Tüm sınıflar (1.→7.)", on: true },
      { label: "Tüm konular ve kazanımlar", on: true },
      { label: "Cevap anahtarı + adım çözüm", on: true },
      { label: "PDF watermark yok", on: true },
      { label: "Geçmiş — sınırsız", on: true },
      { label: "Öncelikli destek", on: true },
      { label: "İptal her an, taahhüt yok", on: true },
    ],
  },
];

const PRICING_FAQS = [
  {
    q: "Ücretsiz plan gerçekten ücretsiz mi?",
    a: "Evet — kredi kartı bile sormuyoruz. Aylık 100 soruya kadar tamamen ücretsiz. Bu, yaklaşık 10 çalışma kağıdı (kağıt başına 5-15 soru) anlamına gelir.",
  },
  {
    q: "Pro'ya geçince yıllık indirim var mı?",
    a: "Evet — yıllık ödemede ay başına 79 ₺ (toplam 948 ₺/yıl). Aylık plana göre %20 tasarruf. İstediğinde aylığa dönüş yapabilirsin.",
  },
  {
    q: "İptal kolay mı? Para iadesi var mı?",
    a: "Aboneliği panelden tek tıkla iptal edersin, sonraki dönem ücret çekilmez. İlk 14 gün içinde memnun kalmazsan koşulsuz iade — sebep sormuyoruz.",
  },
  {
    q: "Quotamı aştığımda ne olur?",
    a: "Ücretsiz planda 100. soruyu ürettikten sonra ay sonuna kadar yeni üretim duraklar (geçmişe erişimin devam eder). Pro'ya istediğin an yükselebilir, anında devam edersin.",
  },
  {
    q: "Soru sayısı nasıl sayılıyor — bir kağıttaki tüm sorular mı?",
    a: "Evet — bir kağıt 5 soruysa 5, 15 soruysa 15 sayılır. Cache'den gelen tekrar indirmeler sayılmaz (aynı kağıdı 5 kez indirsen 1 kez sayılır).",
  },
  {
    q: "Fatura kesiliyor mu?",
    a: "Pro abonelerine her dönem otomatik e-fatura gönderiyoruz. Kurumsal hesap için faturayı şirket bilgilerine düzenleyebiliriz — destek@quizmarketi.com.",
  },
];

export default function PricingPage() {
  return (
    <>
      <PageHeader
        eyebrow="Fiyatlandırma"
        title="Ücretsiz başla, ihtiyacın oldukça yükselt"
        body="Karmaşık plan tablosu yok. İki seçenek: tanımak için Ücretsiz, aktif kullanım için Pro. Taahhüt yok, istediğinde dur."
      />

      <section className="py-20">
        <div className="container max-w-5xl">
          <div className="grid gap-6 md:grid-cols-2">
            {PLANS.map((p) => (
              <div
                key={p.name}
                className={`relative flex flex-col rounded-2xl border p-8 ${
                  p.featured
                    ? "border-primary/40 bg-card shadow-lg ring-2 ring-primary/20"
                    : "border-border bg-card"
                }`}
              >
                {p.featured && (
                  <Badge className="absolute right-6 top-6 bg-primary text-primary-foreground">
                    Popüler
                  </Badge>
                )}
                <p className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                  {p.name}
                </p>
                <div className="mt-3 flex items-baseline gap-1">
                  <span className="text-5xl font-bold text-foreground">
                    {p.price}
                  </span>
                  <span className="text-base text-muted-foreground">
                    {" "}
                    ₺ {p.period}
                  </span>
                </div>
                <p className="mt-3 text-sm text-muted-foreground">{p.note}</p>
                {p.annualHint && (
                  <p className="mt-2 inline-flex w-fit rounded-md bg-accent px-2.5 py-1 text-xs font-medium text-accent-foreground">
                    {p.annualHint}
                  </p>
                )}
                <ul className="mt-6 flex flex-col gap-2.5 text-sm">
                  {p.features.map((f, i) => (
                    <li
                      key={i}
                      className={`flex items-start gap-2.5 ${
                        f.on
                          ? "text-foreground"
                          : "text-muted-foreground line-through"
                      }`}
                    >
                      {f.on ? (
                        <Check className="mt-0.5 h-4 w-4 flex-shrink-0 text-primary" />
                      ) : (
                        <X className="mt-0.5 h-4 w-4 flex-shrink-0 text-muted-foreground/50" />
                      )}
                      <span>{f.label}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-8">
                  <Button
                    asChild
                    size="lg"
                    variant={p.featured ? "default" : "outline"}
                    className="w-full gap-2"
                  >
                    <Link href={p.href}>
                      {p.cta} <ArrowRight className="h-4 w-4" />
                    </Link>
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-card py-20">
        <div className="container max-w-3xl">
          <SectionHeader
            eyebrow="Pricing SSS"
            title="Fiyat hakkında sorular"
            align="left"
          />
          <div className="mt-10 divide-y divide-border rounded-xl border bg-background">
            {PRICING_FAQS.map((f, i) => (
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
      </section>

      <Footer />
    </>
  );
}
