import Link from "next/link";
import {
  ArrowRight,
  Backpack,
  BookOpen,
  CheckCircle2,
  FileCheck,
  GraduationCap,
  Hash,
  Layers,
  ShieldCheck,
  Sparkles,
  Users,
  Zap,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Footer } from "@/components/Footer";
import { SectionHeader } from "@/components/PageHeader";

export default function LandingPage() {
  return (
    <>
      <Hero />
      <LiveSamples />
      <Problem />
      <HowItWorks />
      <Personas />
      <Features />
      <Testimonials />
      <PricingTeaser />
      <Faq />
      <FinalCta />
      <Footer />
    </>
  );
}

// ─── HERO ────────────────────────────────────────────────────────────────────

function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[600px] bg-[radial-gradient(ellipse_at_top,_hsl(var(--primary)/0.18),transparent_60%)]"
      />
      <div className="container flex flex-col items-center gap-7 py-20 text-center sm:py-28">
        <Badge
          variant="outline"
          className="border-primary/30 bg-accent text-accent-foreground"
        >
          <Sparkles className="mr-1.5 h-3 w-3" />
          1. → 7. sınıf · MEB müfredatı · Yapay zekâ
        </Badge>
        <h1 className="max-w-4xl text-balance text-4xl font-bold tracking-tight text-foreground sm:text-5xl md:text-6xl">
          MEB&apos;e %100 uyumlu matematik çalışma kağıdı,{" "}
          <span className="bg-gradient-to-r from-primary to-indigo-400 bg-clip-text text-transparent">
            30 saniyede
          </span>
          .
        </h1>
        <p className="max-w-2xl text-balance text-lg text-muted-foreground sm:text-xl">
          Sınıfı, kazanımı ve zorluğu seç. Yapay zekâ üretir, otomatik
          aritmetik denetim ve ikinci bir yapay zekâ kontrolü kazanım uyumunu
          doğrular. A4 PDF olarak indir, derste dağıt.
        </p>
        <div className="flex flex-col items-center gap-3 sm:flex-row">
          <Button asChild size="lg" className="gap-2 px-7">
            <Link href="/generate">
              Ücretsiz başla <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
          <Button asChild size="lg" variant="outline" className="px-7">
            <Link href="#how">Nasıl çalışıyor?</Link>
          </Button>
        </div>
        <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-muted-foreground">
          <TrustBullet>Kayıt 30 saniye</TrustBullet>
          <TrustBullet>Kredi kartı yok</TrustBullet>
          <TrustBullet>İlk 5 kağıt ücretsiz</TrustBullet>
        </div>
      </div>
    </section>
  );
}

function TrustBullet({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <CheckCircle2 className="h-3.5 w-3.5 text-primary" />
      {children}
    </span>
  );
}

// ─── LIVE PDF SAMPLES ────────────────────────────────────────────────────────

const SAMPLES = [
  {
    file: "/samples/sample-1.svg",
    grade: "5. Sınıf",
    topic: "Cebir",
    difficulty: "Orta",
  },
  {
    file: "/samples/sample-2.svg",
    grade: "6. Sınıf",
    topic: "Kesirler",
    difficulty: "Kolay",
  },
  {
    file: "/samples/sample-3.svg",
    grade: "7. Sınıf",
    topic: "Geometri",
    difficulty: "Zor",
  },
  {
    file: "/samples/sample-4.svg",
    grade: "4. Sınıf",
    topic: "Çıkarma",
    difficulty: "Kolay",
  },
];

function LiveSamples() {
  return (
    <section className="bg-card py-20">
      <div className="container">
        <SectionHeader
          eyebrow="Canlı örnekler"
          title="Yapay zekânın ürettiği gerçek çalışma kağıtları"
          body="Aşağıdaki PDF'lerin tamamı Quiz Marketi tarafından otomatik üretildi — sıfır el müdahalesi."
        />
        <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {SAMPLES.map((s, i) => (
            <PdfPreviewCard key={i} {...s} />
          ))}
        </div>
      </div>
    </section>
  );
}

function PdfPreviewCard({
  file,
  grade,
  topic,
  difficulty,
}: {
  file: string;
  grade: string;
  topic: string;
  difficulty: string;
}) {
  return (
    <Link
      href="/generate"
      className="group flex flex-col overflow-hidden rounded-xl border bg-card transition-all hover:-translate-y-1 hover:border-primary/40 hover:shadow-lg"
    >
      <div className="relative aspect-[1/1.41] w-full overflow-hidden bg-muted">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-[linear-gradient(180deg,_hsl(var(--accent))_0%,_hsl(var(--background))_100%)]"
        />
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={file}
          alt={`${grade} ${topic} örnek PDF`}
          className="relative h-full w-full object-cover transition-transform group-hover:scale-105"
        />
      </div>
      <div className="flex items-center justify-between border-t p-4">
        <div>
          <p className="text-sm font-semibold text-foreground">{grade}</p>
          <p className="text-xs text-muted-foreground">{topic}</p>
        </div>
        <Badge variant="outline" className="text-xs">
          {difficulty}
        </Badge>
      </div>
    </Link>
  );
}

// ─── PROBLEM ─────────────────────────────────────────────────────────────────

const PAINS = [
  {
    icon: <Hash className="h-5 w-5" />,
    title: "Kazanıma uyumsuz",
    body: "Hazır PDF/dergiler %60 oranında müfredatın dışına çıkıyor.",
  },
  {
    icon: <Layers className="h-5 w-5" />,
    title: "Tekrarlanan sorular",
    body: "Her dönem aynı sorular; öğrenci ezberliyor, ölçme bozuluyor.",
  },
  {
    icon: <FileCheck className="h-5 w-5" />,
    title: "Cevap anahtarı yok",
    body: "Hocanın elle çözmesi gerekiyor; düzeltme 1 saatten başlıyor.",
  },
];

function Problem() {
  return (
    <section className="py-20">
      <div className="container">
        <SectionHeader
          eyebrow="Mevcut durum"
          title="Klasik kaynaklar neden yetmiyor?"
          body="Öğretmen, veli ve etüt sahibi her hafta aynı 3 sorunla yüzleşiyor."
        />
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {PAINS.map((p, i) => (
            <div
              key={i}
              className="flex flex-col gap-3 rounded-xl border border-destructive/20 bg-destructive/5 p-6"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-destructive/10 text-destructive">
                {p.icon}
              </div>
              <h3 className="text-base font-semibold text-foreground">
                {p.title}
              </h3>
              <p className="text-sm text-muted-foreground">{p.body}</p>
            </div>
          ))}
        </div>
        <div className="mt-10 rounded-xl border-l-4 border-primary bg-accent p-6 text-accent-foreground">
          <p className="text-sm font-medium">
            <span className="font-semibold">Quiz Marketi:</span> kazanım kodunu
            gir, %100 hizalı + çeşitli varyantlar, otomatik cevap anahtarı +
            adım adım çözüm.
          </p>
        </div>
      </div>
    </section>
  );
}

// ─── HOW IT WORKS ────────────────────────────────────────────────────────────

const STEPS = [
  {
    n: "1",
    title: "Sınıf + konu seç",
    body: "1.→7. sınıf, MEB konularından biri, opsiyonel kazanım kodu, zorluk düzeyi.",
    icon: <BookOpen className="h-6 w-6" />,
  },
  {
    n: "2",
    title: "Yapay zekâ üretir",
    body: "30 saniye içinde 5-20 arası özgün soru. Otomatik aritmetik denetim ve ikinci bir yapay zekâ kontrolü her soruyu süzer.",
    icon: <Sparkles className="h-6 w-6" />,
  },
  {
    n: "3",
    title: "PDF olarak indir",
    body: "A4 baskı-hazır kağıt + cevap anahtarı + adım adım çözüm. Tek tıkla, watermark yok.",
    icon: <Zap className="h-6 w-6" />,
  },
];

function HowItWorks() {
  return (
    <section id="how" className="bg-card py-20">
      <div className="container">
        <SectionHeader
          eyebrow="Nasıl çalışır?"
          title="3 adımda çalışma kağıdı"
          body=""
        />
        <div className="mt-14 grid gap-8 md:grid-cols-3">
          {STEPS.map((s) => (
            <div key={s.n} className="relative flex flex-col items-start gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary text-primary-foreground">
                {s.icon}
              </div>
              <span className="text-xs font-semibold uppercase tracking-wider text-primary">
                Adım {s.n}
              </span>
              <h3 className="text-xl font-semibold text-foreground">{s.title}</h3>
              <p className="text-sm text-muted-foreground">{s.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── PERSONAS ────────────────────────────────────────────────────────────────

const PERSONAS = [
  {
    icon: <GraduationCap className="h-6 w-6" />,
    title: "Öğretmen",
    body: "Ders öncesi 5 dakikada 10 soruluk pratik üret, sınıfta dağıt. Konu eksiği gördüğün anda yedek kağıt yarat.",
  },
  {
    icon: <Users className="h-6 w-6" />,
    title: "Veli",
    body: "Çocuğunun bu hafta zorlandığı konuyu seç, evde çözebileceği seviyede pratik kağıdı al. Cevap anahtarıyla beraber.",
  },
  {
    icon: <Backpack className="h-6 w-6" />,
    title: "Öğrenci",
    body: "Sınav öncesi zorlandığın konuyu seç, kendine özel pratik kağıdı çık. Çözümü yan sayfada — kafanı karıştırmaz.",
  },
];

function Personas() {
  return (
    <section className="py-20">
      <div className="container">
        <SectionHeader
          eyebrow="Kim için"
          title="Üç farklı kullanıcı, tek araç"
          body=""
        />
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {PERSONAS.map((p, i) => (
            <div
              key={i}
              className="flex flex-col gap-4 rounded-xl border bg-card p-6"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                {p.icon}
              </div>
              <h3 className="text-lg font-semibold text-foreground">{p.title}</h3>
              <p className="text-sm text-muted-foreground">{p.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── FEATURES ────────────────────────────────────────────────────────────────

const FEATURES = [
  {
    icon: <BookOpen className="h-5 w-5" />,
    title: "MEB müfredatı %100",
    body: "1.→7. sınıf tüm kazanımlar; her kağıt belirlediğin koda göre üretilir.",
  },
  {
    icon: <ShieldCheck className="h-5 w-5" />,
    title: "İki katmanlı kalite kontrol",
    body: "Her soru önce otomatik aritmetik denetimden, sonra ikinci bir yapay zekâ kontrolünden geçer; uyumsuzlar elenir.",
  },
  {
    icon: <Zap className="h-5 w-5" />,
    title: "Saniyeler içinde PDF",
    body: "İlk üretim ~30 sn; tekrar indirme anında. Türkçe karakter problemi yok.",
  },
  {
    icon: <FileCheck className="h-5 w-5" />,
    title: "Cevap + çözüm",
    body: "Otomatik cevap anahtarı + adım adım çözüm; düzeltme dakikalar değil saniyeler.",
  },
  {
    icon: <Hash className="h-5 w-5" />,
    title: "Kazanım kodu görünür",
    body: "Her sorunun yanında MEB kazanım kodu — denetlenebilir, takip edilebilir.",
  },
  {
    icon: <Sparkles className="h-5 w-5" />,
    title: "Akıllı çeşitlilik",
    body: "Aynı konuyu 10 kez ürettiğinde 10 farklı set; tekrar yok, sıkıcılık yok.",
  },
];

function Features() {
  return (
    <section id="features" className="bg-card py-20">
      <div className="container">
        <SectionHeader
          eyebrow="Özellikler"
          title="Bir dergiden değil, üreticiden"
          body=""
        />
        <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f, i) => (
            <div
              key={i}
              className="flex flex-col gap-3 rounded-xl border bg-background/50 p-5"
            >
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                {f.icon}
              </div>
              <h3 className="text-base font-semibold text-foreground">
                {f.title}
              </h3>
              <p className="text-sm text-muted-foreground">{f.body}</p>
            </div>
          ))}
        </div>
        <div className="mt-10 flex justify-center">
          <Button asChild variant="outline" className="gap-2">
            <Link href="/features">
              Detaylı özellikler ve karşılaştırma{" "}
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </section>
  );
}

// ─── TESTIMONIALS ────────────────────────────────────────────────────────────

const TESTIMONIALS = [
  {
    quote:
      "Müfredata uygunluğu inanılmaz; ders öncesi hazırlık süremi 30 dakikadan 3 dakikaya indirdi.",
    name: "Ayşe Y.",
    role: "5. sınıf öğretmeni, İstanbul",
  },
  {
    quote:
      "Çocuğumla hafta sonu pratik için ideal. Cevap anahtarı olduğu için kontrol etmek 30 saniye.",
    name: "Selin B.",
    role: "Veli, İzmir",
  },
  {
    quote:
      "Sınava hazırlanırken zorlandığım konuyu seçip kendime özel pratik kağıdı üretiyorum. Çözüm adımları çok faydalı.",
    name: "Defne A.",
    role: "7. sınıf öğrencisi, Ankara",
  },
];

function Testimonials() {
  return (
    <section className="py-20">
      <div className="container">
        <SectionHeader
          eyebrow="Kullanıcı yorumları"
          title="Öğretmen, veli ve etüt sahibi neler diyor?"
          body=""
        />
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {TESTIMONIALS.map((t, i) => (
            <figure
              key={i}
              className="flex flex-col gap-4 rounded-xl border bg-card p-6"
            >
              <blockquote className="text-sm leading-relaxed text-foreground">
                &ldquo;{t.quote}&rdquo;
              </blockquote>
              <figcaption className="mt-auto">
                <p className="text-sm font-semibold text-foreground">{t.name}</p>
                <p className="text-xs text-muted-foreground">{t.role}</p>
              </figcaption>
            </figure>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── PRICING TEASER ──────────────────────────────────────────────────────────

const PLANS = [
  {
    name: "Ücretsiz",
    price: "0",
    quota: "100 soru / ay",
    note: "Ürünü tanı, dene",
  },
  {
    name: "Pro",
    price: "99",
    quota: "Sınırsız soru",
    note: "Aktif kullanıcı için",
    featured: true,
  },
];

function PricingTeaser() {
  return (
    <section
      id="pricing"
      className="relative overflow-hidden bg-gradient-to-br from-primary to-indigo-700 py-20 text-primary-foreground"
    >
      <div className="container text-center">
        <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
          Ücretsiz başla. İhtiyacın oldukça yükselt.
        </h2>
        <p className="mx-auto mt-3 max-w-xl text-base opacity-90">
          Kart bilgisi vermeden ilk soruları üret. İstediğinde Pro&apos;ya geç,
          istediğinde durdur — taahhüt yok.
        </p>
        <div className="mx-auto mt-10 grid max-w-2xl gap-4 sm:grid-cols-2">
          {PLANS.map((p) => (
            <div
              key={p.name}
              className={`rounded-xl border p-6 text-left transition ${
                p.featured
                  ? "border-white/50 bg-white/15 ring-2 ring-white/30"
                  : "border-white/20 bg-white/5"
              }`}
            >
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold uppercase tracking-wider opacity-75">
                  {p.name}
                </p>
                {p.featured && (
                  <span className="rounded-full bg-white/20 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider">
                    Popüler
                  </span>
                )}
              </div>
              <p className="mt-3 text-4xl font-bold">
                {p.price}
                <span className="text-base font-normal opacity-75"> ₺/ay</span>
              </p>
              <p className="mt-2 text-sm font-medium opacity-95">{p.quota}</p>
              <p className="text-xs opacity-70">{p.note}</p>
            </div>
          ))}
        </div>
        <div className="mt-10">
          <Button
            asChild
            size="lg"
            variant="secondary"
            className="gap-2 bg-white text-primary hover:bg-white/90"
          >
            <Link href="/pricing">
              Plan ayrıntıları <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </section>
  );
}

// ─── FAQ ─────────────────────────────────────────────────────────────────────

const FAQS = [
  {
    q: "Hangi sınıflar destekleniyor?",
    a: "Şu an 1.→7. sınıf MEB matematik müfredatı tamamen destekleniyor. 8. sınıf (LGS) ve diğer dersler yol haritasında.",
  },
  {
    q: "MEB müfredatına nasıl uyduğunu garanti ediyorsunuz?",
    a: "Her soru, MEB tarafından yayımlanan kazanım kodlarına göre üretilir. Sistem MEB ders kitaplarından bağlam çeker; ikinci bir yapay zekâ kontrolü her soruyu kazanım uyumu açısından denetler, geçmeyenler elenir.",
  },
  {
    q: "İptal kolay mı? Para iadesi var mı?",
    a: "Aboneliğini panelden tek tıkla iptal edebilirsin, sonraki dönem ücret çekilmez. İlk 14 gün içinde memnun kalmazsan koşulsuz iade.",
  },
];

function Faq() {
  return (
    <section id="faq" className="bg-card py-20">
      <div className="container max-w-3xl">
        <SectionHeader
          eyebrow="Sıkça sorulanlar"
          title="Kafanda soru var mı?"
          body=""
          align="left"
        />
        <div className="mt-10 divide-y divide-border rounded-xl border bg-background">
          {FAQS.map((f, i) => (
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
        <div className="mt-8 flex justify-center">
          <Button asChild variant="outline" className="gap-2">
            <Link href="/faq">
              Tüm soruları gör <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </section>
  );
}

// ─── FINAL CTA ───────────────────────────────────────────────────────────────

function FinalCta() {
  return (
    <section className="py-20">
      <div className="container">
        <div className="mx-auto flex max-w-3xl flex-col items-center gap-6 rounded-2xl border bg-card p-12 text-center shadow-sm">
          <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            Şimdi ilk kağıdını ücretsiz üret.
          </h2>
          <p className="text-base text-muted-foreground">
            30 saniye yeterli. Kart bilgisi gerekmiyor.
          </p>
          <Button asChild size="lg" className="gap-2 px-8">
            <Link href="/generate">
              Ücretsiz başla <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </section>
  );
}

// (Footer + SectionHeader components/Footer.tsx ve components/PageHeader.tsx
// içine taşındı; /features, /pricing, /faq sayfalarıyla paylaşılıyor.)
