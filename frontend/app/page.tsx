import Link from "next/link";
import {
  ArrowRight,
  Backpack,
  BookOpen,
  CheckCircle2,
  FileCheck,
  GraduationCap,
  Hash,
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
      <SystemSummary />
      <HowItWorks />
      <UseCases />
      <Features />
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
          1.→7. sınıf · MEB matematik müfredatı
        </Badge>
        <h1 className="max-w-4xl text-balance text-4xl font-bold tracking-tight text-foreground sm:text-5xl md:text-6xl">
          MEB kazanım kodu bazlı{" "}
          <span className="bg-gradient-to-r from-primary to-blue-500 bg-clip-text text-transparent">
            çalışma kağıdı
          </span>{" "}
          üretim sistemi
        </h1>
        <p className="max-w-2xl text-balance text-lg text-muted-foreground sm:text-xl">
          Sınıf, konu ve kazanım kodu seçilir. Sistem soru üretir, aritmetik
          denetimden ve kazanım uyumu kontrolünden geçirir; sonucu A4 PDF
          olarak teslim eder.
        </p>
        <div className="flex flex-col items-center gap-3 sm:flex-row">
          <Button asChild size="lg" className="gap-2 px-7">
            <Link href="/sign-up">
              Hesap aç <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
          <Button asChild size="lg" variant="outline" className="px-7">
            <Link href="#how">Sistem nasıl çalışır</Link>
          </Button>
        </div>
        <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-muted-foreground">
          <TrustBullet>Aylık 100 soru ücretsiz</TrustBullet>
          <TrustBullet>Kayıt için yalnızca e-posta</TrustBullet>
          <TrustBullet>Ödeme bilgisi alınmaz</TrustBullet>
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

// ─── SYSTEM SUMMARY ──────────────────────────────────────────────────────────

function SystemSummary() {
  return (
    <section className="py-20">
      <div className="container max-w-4xl">
        <div className="rounded-2xl border bg-card p-8 sm:p-12">
          <p className="text-sm font-semibold uppercase tracking-wider text-primary">
            Soru Atölyesi nedir
          </p>
          <h2 className="mt-2 text-3xl font-bold tracking-tight text-foreground">
            MEB matematik müfredatı kapsamında otomatik çalışma kağıdı üretimi
          </h2>
          <p className="mt-4 text-base leading-relaxed text-muted-foreground">
            Soru Atölyesi; 1.→7. sınıf MEB matematik müfredatı kapsamında,
            seçilen kazanım koduna göre çalışma kağıdı üreten bir yazılım
            sistemidir. Üretilen her soru, kullanıcıya sunulmadan önce iki
            aşamalı bir denetimden geçer: önce sembolik hesap motoru ile
            aritmetik denetim, ardından ikinci bir model tarafından kazanım
            uyumu denetimi. Üretim sonucu A4 PDF formatında — sorular, cevap
            anahtarı ve adım adım çözüm — şeklinde teslim edilir.
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
    title: "Parametre seçimi",
    body: "Sınıf, konu ve isteğe bağlı olarak kazanım kodu seçilir. Zorluk düzeyi (kolay/orta/zor) ve soru sayısı (5–20) belirlenir.",
    icon: <BookOpen className="h-6 w-6" />,
  },
  {
    n: "2",
    title: "Üretim ve denetim",
    body: "Sistem MEB ders kitaplarından bağlam çekerek soruları üretir. Üretilen her soru aritmetik denetimden ve kazanım uyumu denetiminden geçer; denetimleri geçemeyenler elenir.",
    icon: <Sparkles className="h-6 w-6" />,
  },
  {
    n: "3",
    title: "PDF teslimi",
    body: "Sorular, cevap anahtarı ve adım adım çözüm; tek bir A4 PDF dosyası olarak indirilebilir hale getirilir. Ortalama süre 30 saniyedir.",
    icon: <Zap className="h-6 w-6" />,
  },
];

function HowItWorks() {
  return (
    <section id="how" className="bg-card py-20">
      <div className="container">
        <SectionHeader
          eyebrow="Üretim akışı"
          title="Üç aşamada çalışma kağıdı"
          body="Üretim talebi gönderildiğinde sistem aşağıdaki adımları sırasıyla yürütür."
        />
        <div className="mt-14 grid gap-8 md:grid-cols-3">
          {STEPS.map((s) => (
            <div key={s.n} className="relative flex flex-col items-start gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary text-primary-foreground">
                {s.icon}
              </div>
              <span className="text-xs font-semibold uppercase tracking-wider text-primary">
                Aşama {s.n}
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

// ─── USE CASES ───────────────────────────────────────────────────────────────

const USE_CASES = [
  {
    icon: <GraduationCap className="h-6 w-6" />,
    title: "Öğretmen kullanımı",
    body: "Ders öncesi ilgili kazanım kodu seçilir; sistem 5–20 soruluk çalışma kağıdı ile cevap anahtarını hazırlar. Konu eksiği gözlendiğinde aynı kazanım için ek varyant üretilebilir.",
  },
  {
    icon: <Users className="h-6 w-6" />,
    title: "Veli kullanımı",
    body: "Öğrencinin haftalık konusu için kazanım kodu seçilir; sistem zorluk düzeyine uygun çalışma kağıdı üretir. Cevap anahtarı PDF içinde yer aldığı için değerlendirme PDF üzerinden yapılabilir.",
  },
  {
    icon: <Backpack className="h-6 w-6" />,
    title: "Öğrenci kullanımı",
    body: "Eksik kalınan kazanım için kendi başına çalışma kağıdı üretilebilir. PDF içindeki adım adım çözüm sayfası, ödevin çözümünden sonra kontrol amacıyla kullanılır.",
  },
];

function UseCases() {
  return (
    <section className="py-20">
      <div className="container">
        <SectionHeader
          eyebrow="Tipik kullanım senaryoları"
          title="Sistem hangi senaryolar için kullanılır?"
          body="Öğretmen, veli ve öğrenci kullanımlarında ortak adımlar farklıdır; sistem her üç durumu da destekler."
        />
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {USE_CASES.map((p, i) => (
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
    title: "Kazanım kodu bazlı üretim",
    body: "1.→7. sınıf MEB matematik kazanımları; her sorunun yanında ilgili kazanım kodu görünür.",
  },
  {
    icon: <ShieldCheck className="h-5 w-5" />,
    title: "İki aşamalı denetim",
    body: "Sembolik aritmetik denetim ve kazanım uyumu denetimi. Denetim geçmeyen sorular yeniden üretilir.",
  },
  {
    icon: <FileCheck className="h-5 w-5" />,
    title: "Cevap anahtarı ve çözüm",
    body: "Her PDF içinde cevap anahtarı ve adım adım çözüm sayfası yer alır.",
  },
  {
    icon: <Sparkles className="h-5 w-5" />,
    title: "Anlamsal benzerlik denetimi",
    body: "Aynı parametrelerle tekrar üretimde önceki sorulara yakın varyantlar üretim havuzundan elenir.",
  },
  {
    icon: <Hash className="h-5 w-5" />,
    title: "İzlenebilir kazanım kodları",
    body: "Her çıktıda M.X.Y.Z formatında kazanım kodu açıkça görünür — sınıf bazlı takip yapılabilir.",
  },
  {
    icon: <Zap className="h-5 w-5" />,
    title: "Önbellek destekli yeniden indirme",
    body: "Aynı parametrelerle yapılan tekrar talepler önbellekten döner ve aylık kotadan düşmez.",
  },
];

function Features() {
  return (
    <section id="features" className="bg-card py-20">
      <div className="container">
        <SectionHeader
          eyebrow="Sistem özellikleri"
          title="Çıktıyı ve üretim akışını belirleyen özellikler"
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
              Tüm özellikler ve karşılaştırma
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </section>
  );
}

// ─── PRICING TEASER ──────────────────────────────────────────────────────────

function PricingTeaser() {
  return (
    <section
      id="pricing"
      className="relative overflow-hidden bg-gradient-to-br from-primary to-blue-950 py-20 text-primary-foreground"
    >
      <div className="container max-w-3xl text-center">
        <p className="text-xs font-semibold uppercase tracking-wider opacity-80">
          Fiyatlandırma
        </p>
        <h2 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">
          Erken kullanım dönemi
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-base opacity-90">
          Soru Atölyesi şu anda erken kullanım dönemindedir. Tüm hesaplara
          aylık 100 soruluk ücretsiz kullanım hakkı tanınmaktadır. Pro
          abonelik seçenekleri ileriki aşamada duyurulacaktır.
        </p>
        <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Button
            asChild
            size="lg"
            variant="secondary"
            className="gap-2 bg-white text-primary hover:bg-white/90"
          >
            <Link href="/sign-up">
              Hesap aç <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
          <Button
            asChild
            size="lg"
            variant="outline"
            className="gap-2 border-white/40 bg-transparent text-white hover:bg-white/10 hover:text-white"
          >
            <Link href="/pricing">Detaylar</Link>
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
    a: "1.→7. sınıf MEB matematik müfredatının tamamı şu an desteklenmektedir. 8. sınıf (LGS) kapsamının eklenmesi yol haritasındadır.",
  },
  {
    q: "Sistem MEB kazanımına nasıl uyuyor?",
    a: "Üretim, MEB tarafından yayımlanan kazanım kodlarına göre yapılır. Sistem MEB ders kitaplarından bağlam çeker; üretilen her soru, ikinci bir model tarafından kazanım uyumu denetiminden geçirilir. Denetimi geçemeyen sorular yeniden üretilir.",
  },
  {
    q: "Aynı parametrelerle tekrar üretim aynı soruları mı getiriyor?",
    a: "Hayır. Anlamsal benzerlik denetimi devreye girer; önceki sorulara cosine benzerliği yüksek olanlar üretim havuzundan elenir.",
  },
];

function Faq() {
  return (
    <section id="faq" className="bg-card py-20">
      <div className="container max-w-3xl">
        <SectionHeader
          eyebrow="Sıkça sorulanlar"
          title="Sistem hakkında sık sorulan sorular"
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
              Tüm sorular <ArrowRight className="h-4 w-4" />
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
            Sistemi kullanmak için
          </h2>
          <p className="text-base text-muted-foreground">
            Hesap açmak için yalnızca e-posta adresi yeterlidir. Aylık 100
            soru kotası tüm kullanıcılara açıktır.
          </p>
          <Button asChild size="lg" className="gap-2 px-8">
            <Link href="/sign-up">
              Hesap aç <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </section>
  );
}
