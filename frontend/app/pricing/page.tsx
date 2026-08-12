import Link from "next/link";
import {
  ArrowRight,
  Building2,
  Check,
  GraduationCap,
  Sparkles,
  User,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Footer } from "@/components/Footer";
import { PageHeader } from "@/components/PageHeader";
import { PricingInterestButton } from "@/components/PricingInterestButton";

export const metadata = {
  title: "Fiyatlandırma · Soru Atölyesi",
  description:
    "Ücretsiz plan ayda 10 çalışma kağıdı (günde 2) + kayıtta 7 gün kartsız deneme. Pro ₺199/ay (50 kağıt), Pro+ ₺349/ay (120 kağıt + veli/öğretmen takibi). Fiyatlar KDV dahil.",
};

interface Plan {
  slug: string;
  name: string;
  audience: string;
  price: string;
  priceNote: string;
  icon: React.ReactNode;
  features: string[];
  featured?: boolean;
  cta: "signup" | "interest" | "quote";
}

const PLANS: Plan[] = [
  {
    slug: "ucretsiz",
    name: "Ücretsiz",
    audience: "Denemek isteyen herkes için",
    price: "0₺",
    priceNote: "Her zaman ücretsiz",
    icon: <Sparkles className="h-5 w-5" />,
    cta: "signup",
    features: [
      "Ayda 10 çalışma kağıdı (kalıcı ücretsiz) — günde en çok 2",
      "Kayıt anında 7 günlük kartsız deneme: 20 kağıt, Pro+ kalitesi",
      "1'den 8. sınıfa kadar + LGS için kazanım bazlı üretim",
      "Cevap anahtarı ve adım adım çözüm içeren PDF'ler",
      "Çöz & Geliş modülü ve temel sınıf/veli takibi",
    ],
  },
  {
    slug: "pro",
    name: "Pro",
    audience: "Veli ve Öğrenciler için ideal",
    price: "₺199",
    priceNote: "/ay · KDV dahil",
    icon: <User className="h-5 w-5" />,
    cta: "interest",
    features: [
      "Ayda 50 çalışma kağıdı · günlük sınır yok",
      "Yeni nesil (senaryo bazlı) soru kalitesi",
      "Filigransız PDF — Kendi logonuzu ekleyin",
      "Çöz & Geliş: Sınırsız pratik ve oyunlaştırma",
      "Sistemde öncelikli soru üretimi",
    ],
  },
  {
    slug: "pro-plus",
    name: "Pro+",
    audience: "Öğretmenler ve yoğun kullanım için",
    price: "₺349",
    priceNote: "/ay · KDV dahil",
    icon: <GraduationCap className="h-5 w-5" />,
    featured: true,
    cta: "interest",
    features: [
      "Pro planındaki her şeye ek olarak:",
      "Ayda 120 çalışma kağıdı",
      "Aile paylaşımı: tek havuz, 3 çocuğa kadar",
      "Çoklu sınıf yönetimi, ödev verme ve sonuç panosu",
      "Detaylı kazanım analitiği ile tam takip",
      "Öncelikli müşteri desteği",
    ],
  },
  {
    slug: "kurumsal",
    name: "Kurumsal",
    audience: "Okullar ve Dershaneler için",
    price: "Teklif",
    priceNote: "Kuruma Özel · Faturalı",
    icon: <Building2 className="h-5 w-5" />,
    cta: "quote",
    features: [
      "Pro+ planındaki her şeye ek olarak:",
      "Çoklu öğretmen / kullanıcı koltuğu yönetimi",
      "Kurumunuza özel tasarım ve yönetici paneli",
      "Kuruma özel eğitim ve sisteme entegrasyon",
      "Özel faturalandırma ve VIP destek",
    ],
  },
];

export default function PricingPage() {
  return (
    <>
      <PageHeader
        eyebrow="Fiyatlandırma"
        title="Sana En Uygun Planı Seç"
        body="Ücretsiz planımız yayında! Kayıt olan herkese anında 7 günlük kartsız deneme (20 çalışma kağıdı, Pro+ kalitesi) hediye ediyoruz. Pro ve Pro+ paketlerimiz çok yakında aktif olacak; aşağıdan ilgilendiğini belirt, açıldığında ilk senin haberin olsun."
      />

      {/* Kampanya şeridi */}
      <div className="container">
        <div className="mx-auto max-w-5xl rounded-xl border border-primary/20 bg-accent/40 px-5 py-3 text-center text-sm text-foreground">
          🎁 <span className="font-semibold">Üye olana 7 gün kartsız deneme — 20 kağıt, Pro+ kalitesi</span> ·
          <span className="font-semibold">İstediğin an iptal</span>
        </div>
      </div>

      <section className="container py-12">
        <div className="grid gap-6 lg:grid-cols-4 md:grid-cols-2">
          {PLANS.map((p) => (
            <div
              key={p.slug}
              className={`relative flex flex-col rounded-2xl border bg-card p-6 shadow-sm ${
                p.featured ? "border-primary shadow-pop ring-1 ring-primary/30" : ""
              }`}
            >
              {p.featured && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-primary px-3 py-1 text-xs font-semibold text-primary-foreground">
                  En popüler
                </span>
              )}
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                {p.icon}
              </div>
              <h2 className="mt-4 text-xl font-bold tracking-tight text-foreground">
                {p.name}
              </h2>
              <p className="text-sm text-muted-foreground">{p.audience}</p>
              <div className="mt-4">
                <span className="text-3xl font-bold tracking-tight text-foreground">
                  {p.price}
                </span>
                <p className="mt-1 text-xs text-muted-foreground">{p.priceNote}</p>
              </div>
              <ul className="mt-6 flex-1 space-y-3 text-sm text-foreground">
                {p.features.map((f) => (
                  <li key={f} className="flex items-start gap-2">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-mint" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
              <div className="mt-8">
                {p.cta === "signup" && (
                  <Button asChild size="lg" className="w-full gap-2">
                    <Link href="/sign-up">
                      Ücretsiz Başla <ArrowRight className="h-4 w-4" />
                    </Link>
                  </Button>
                )}
                {p.cta === "interest" && (
                  <PricingInterestButton
                    plan={p.slug}
                    mailtoSubject={`${p.name} plan ilgi bildirimi`}
                    size="lg"
                    variant={p.featured ? "default" : "outline"}
                    className="w-full gap-2"
                  >
                    İlgileniyorum · Yakında
                  </PricingInterestButton>
                )}
                {p.cta === "quote" && (
                  <PricingInterestButton
                    plan={p.slug}
                    mailtoSubject="Kurumsal / okul teklif talebi"
                    size="lg"
                    variant="outline"
                    className="w-full gap-2"
                  >
                    Teklif Al
                  </PricingInterestButton>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="mx-auto mt-10 max-w-3xl space-y-2 text-center text-xs text-muted-foreground">
          <p>
            📌 Ücretsiz planımız şu an kullanıma açıktır. Pro ve Pro+ paketleri çok
            yakında eklenecektir. Belirtilen fiyatlar lansman dönemine özel
            planlanmıştır ve ileride güncellenebilir.
          </p>
          <p>
            💡 İpucu: Aynı parametrelerle daha önce ürettiğiniz sorular önbellekten
            gelir ve aylık kotanızdan düşmez.
          </p>
          <p>
            Destek için:{" "}
            <a
              href="mailto:destek@soruatolyesi.com"
              className="underline-offset-2 hover:underline"
            >
              destek@soruatolyesi.com
            </a>
          </p>
        </div>
      </section>

      <Footer />
    </>
  );
}
