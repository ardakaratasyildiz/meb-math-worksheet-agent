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
    "Ücretsiz plan aylık 100 soru; Bireysel, Sınıf ve Kurumsal planlar daha yüksek kota, filigransız PDF, sınıf/ödev yönetimi ve white-label ile yakında.",
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
    audience: "Denemek isteyen herkes",
    price: "0₺",
    priceNote: "her zaman ücretsiz",
    icon: <Sparkles className="h-5 w-5" />,
    cta: "signup",
    features: [
      "Aylık 100 soru",
      "1.→8. sınıf + LGS, kazanım bazlı üretim",
      "Cevap anahtarı + adım adım çözüm PDF",
      "Çöz & Geliş: site içinde çöz, puanla (kişisel)",
      "Kayıt için yalnızca e-posta",
    ],
  },
  {
    slug: "bireysel",
    name: "Bireysel",
    audience: "Veli & öğrenci",
    price: "₺99",
    priceNote: "/ay · yıllık ₺990 (2 ay bedava)",
    icon: <User className="h-5 w-5" />,
    cta: "interest",
    features: [
      "Aylık 1.000 soru",
      "Filigransız PDF",
      "Tam çözüm + cevap anahtarı",
      "Çöz & Geliş: sınırsız pratik + oyunlaştırma",
      "Öncelikli üretim",
    ],
  },
  {
    slug: "sinif",
    name: "Sınıf",
    audience: "Öğretmenler için",
    price: "₺249",
    priceNote: "/ay · yıllık ₺2.490 (2 ay bedava)",
    icon: <GraduationCap className="h-5 w-5" />,
    featured: true,
    cta: "interest",
    features: [
      "Bireysel'deki her şey",
      "Aylık 2.000 soru",
      "Sınıf oluştur + katılma kodu + ödev ata",
      "Öğrenci sonuç panosu (kim çözdü, kaç doğru)",
      "White-label PDF — kendi logon",
    ],
  },
  {
    slug: "kurumsal",
    name: "Kurumsal",
    audience: "Okul & dershane",
    price: "₺499'dan",
    priceNote: "/ay · kuruma özel teklif",
    icon: <Building2 className="h-5 w-5" />,
    cta: "quote",
    features: [
      "Sınıf'taki her şey",
      "Adil kullanım yüksek kota",
      "Çoklu öğretmen / koltuk yönetimi",
      "Kurumsal white-label + yönetici paneli",
      "Fatura + öncelikli destek",
    ],
  },
];

export default function PricingPage() {
  return (
    <>
      <PageHeader
        eyebrow="Fiyatlandırma"
        title="Sana uygun planı seç"
        body="Ücretsiz plan bugün canlı — aylık 100 soru, tüm sınıflar. Bireysel, Sınıf ve Kurumsal planlar yakında; aşağıdan ilgini bildir, açılınca ilk sen haberdar ol."
      />

      {/* Kampanya şeridi */}
      <div className="container">
        <div className="mx-auto max-w-5xl rounded-xl border border-primary/20 bg-accent/40 px-5 py-3 text-center text-sm text-foreground">
          🎉 <span className="font-semibold">Yıllık ödemede 2 ay bedava</span> ·
          erken kullanıcılara <span className="font-semibold">ilk 3 ay indirimli</span> ·
          öğretmenlere özel indirim
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
                      Ücretsiz başla <ArrowRight className="h-4 w-4" />
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
                    İlgileniyorum · yakında
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
                    Teklif al
                  </PricingInterestButton>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="mx-auto mt-10 max-w-3xl space-y-2 text-center text-xs text-muted-foreground">
          <p>
            Ücretsiz plan bugün kullanılabilir. Ücretli planlar yakında; fiyatlar
            erken kullanım dönemi için planlanmıştır, lansmanda güncellenebilir.
          </p>
          <p>
            Aynı parametrelerle yapılan tekrar üretimler önbellekten gelir ve
            kotadan düşmez. Sorular için:{" "}
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
