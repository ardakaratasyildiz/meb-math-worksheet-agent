import Link from "next/link";
import {
  ArrowRight,
  Backpack,
  BarChart3,
  BookOpen,
  CheckCircle2,
  FileCheck,
  GraduationCap,
  Hash,
  ListChecks,
  PencilLine,
  ShieldCheck,
  Sparkles,
  Target,
  Trophy,
  Users,
  Zap,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Footer } from "@/components/Footer";
import { JsonLd, organizationSchema, websiteSchema } from "@/components/JsonLd";
import { SectionHeader } from "@/components/PageHeader";
import { CURRICULUM_PAGES } from "@/lib/curriculum";
import { KAZANIM_PAGES } from "@/lib/kazanimlar";
import sampleData from "@/lib/sample-questions.json";

// Gerçek müfredat kapsamı (statik snapshot'tan dinamik sayılır — uydurma değil).
const KAZANIM_COUNT = KAZANIM_PAGES.length;
const WORKAREA_COUNT = CURRICULUM_PAGES.length; // sınıf × konu
const TOPIC_COUNT = new Set(CURRICULUM_PAGES.map((p) => p.topicId)).size;

export default function LandingPage() {
  return (
    <>
      <JsonLd id="org-schema" data={organizationSchema()} />
      <JsonLd id="website-schema" data={websiteSchema()} />
      <Hero />
      <SocialProof />
      <Showroom />
      <SolveAndGrow />
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
          Matematik çalışma kağıtlarını{" "}
          <span className="bg-gradient-to-r from-primary to-blue-500 bg-clip-text text-transparent">
            saniyeler içinde
          </span>{" "}
          hazırlayın
        </h1>
        <p className="max-w-2xl text-balance text-lg text-muted-foreground sm:text-xl">
          Sınıf ve konuyu seçin; MEB kazanımlarına uygun sorular, cevap anahtarı
          ve adım adım çözümüyle hazır PDF birkaç saniyede elinizde. İndirin,
          yazdırın, öğrencilerinizle paylaşın.
        </p>
        <div className="flex flex-col items-center gap-3 sm:flex-row sm:flex-wrap sm:justify-center">
          <Button asChild size="lg" className="gap-2 px-7">
            <Link href="/sign-up">
              Ücretsiz dene <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
          <Button asChild size="lg" variant="secondary" className="gap-2 px-7">
            <Link href="/coz">
              Çözerek çalış <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
          <Button asChild size="lg" variant="outline" className="px-7">
            <Link href="#ornekler">Örnek soruları gör</Link>
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

// ─── SOCIAL PROOF — gerçek müfredat kapsamı (uydurma metrik DEĞİL) ────────────

function SocialProof() {
  const stats = [
    { value: String(KAZANIM_COUNT), label: "MEB kazanımı" },
    { value: "1–7", label: "sınıf kapsamı" },
    { value: String(TOPIC_COUNT), label: "konu başlığı" },
    { value: String(WORKAREA_COUNT), label: "sınıf × konu çalışma alanı" },
  ];
  return (
    <section className="border-y bg-card/50">
      <div className="container grid grid-cols-2 gap-6 py-10 sm:grid-cols-4">
        {stats.map((s) => (
          <div key={s.label} className="text-center">
            <p className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              {s.value}
            </p>
            <p className="mt-1 text-xs text-muted-foreground sm:text-sm">
              {s.label}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}

// ─── ÇÖZ & GELİŞ TANITIMI — öğrenme döngüsü ──────────────────────────────────

const SOLVE_FEATURES = [
  {
    icon: <PencilLine className="h-5 w-5" />,
    title: "Site içinde çöz",
    body: "Üretilen quizi test gibi çöz: çoktan seçmeli, doğru/yanlış, boşluk doldurma ve işlem.",
  },
  {
    icon: <BarChart3 className="h-5 w-5" />,
    title: "Anında puan + konu raporu",
    body: "Kaç doğru kaç yanlış, konu bazında kırılım — kazanım eksiğini hemen gör.",
  },
  {
    icon: <Target className="h-5 w-5" />,
    title: "Eksiğine göre pratik",
    body: "Zayıf kazanımına tek tıkla yeni test; öğrenme döngüsünü kapat.",
  },
  {
    icon: <Trophy className="h-5 w-5" />,
    title: "Gelişim + rozetler",
    body: "30 günlük gelişim grafiği, seviye, seri ve konu rozetleriyle motive ol.",
  },
];

function SolveAndGrow() {
  return (
    <section className="bg-card py-20">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center">
          <Badge
            variant="outline"
            className="border-primary/30 bg-accent text-accent-foreground"
          >
            <Sparkles className="mr-1.5 h-3 w-3" />
            Yeni · Çöz &amp; Geliş
          </Badge>
          <h2 className="mt-4 text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            Sadece üretme — site içinde çöz, gelişimini gör
          </h2>
          <p className="mt-4 text-base leading-relaxed text-muted-foreground">
            Üret → test gibi çöz → anında kaç doğru/yanlış → kazanım eksiğine
            göre pratik. Çalışma kağıdı üreticisinin yanında artık tam bir
            öğrenme döngüsü.
          </p>
        </div>
        <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {SOLVE_FEATURES.map((f, i) => (
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
          <Button asChild size="lg" className="gap-2 px-7">
            <Link href="/coz">
              Çözerek çalış <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </section>
  );
}

// ─── SHOWROOM — gerçek örnek çıktı ───────────────────────────────────────────
// "Güçlü motor ama showroom yok" sorununu çözer: Googlebot ve ziyaretçi, sistemin
// GERÇEKTEN ürettiği soruları ana sayfada görür. Veri scripts/gen_samples.py
// (PR #8). Sınıf çeşitliliği için farklı slug'lardan birer temiz soru seçilir.

interface _SampleQ {
  question: string;
  answer: string;
  question_type: string;
  kazanim_kod: string;
}
interface _SampleEntry {
  grade: number;
  topic_id: string;
  difficulty: string;
  questions: _SampleQ[];
}
const _SAMPLES = sampleData as unknown as Record<string, _SampleEntry>;

const _SHOWROOM_SLUGS: [string, string][] = [
  ["2-sinif-dogal-sayilar", "2. sınıf · Doğal sayılar"],
  ["5-sinif-cebir", "5. sınıf · Cebir"],
  ["6-sinif-veri-isleme", "6. sınıf · Veri işleme"],
  ["3-sinif-dogal-sayilar", "3. sınıf · Doğal sayılar"],
  ["4-sinif-olcme", "4. sınıf · Ölçme"],
  ["7-sinif-veri-isleme", "7. sınıf · Veri işleme"],
];

function _pickShowroom(): { label: string; q: _SampleQ }[] {
  const out: { label: string; q: _SampleQ }[] = [];
  for (const [slug, label] of _SHOWROOM_SLUGS) {
    if (out.length >= 3) break;
    const entry = _SAMPLES[slug];
    const q = entry?.questions?.find(
      (x) => !/[$\\]/.test(x.question) && x.question.length <= 220,
    );
    if (q) out.push({ label, q });
  }
  return out;
}

function Showroom() {
  const items = _pickShowroom();
  if (!items.length) return null;
  return (
    <section id="ornekler" className="py-20">
      <div className="container max-w-4xl">
        <SectionHeader
          eyebrow="Gerçek çıktı"
          title="Sistemin ürettiği örnek sorular"
          body="Aşağıdakiler sistemin gerçekten ürettiği sorulardan bir kesit. Hazır PDF'te ayrıca cevap anahtarı ve adım adım çözüm sayfası bulunur."
        />
        <div className="mt-12 grid gap-4 md:grid-cols-3">
          {items.map(({ label, q }, i) => (
            <div
              key={i}
              className="flex flex-col gap-3 rounded-xl border bg-card p-5"
            >
              <span className="text-xs font-semibold uppercase tracking-wider text-primary">
                {label}
              </span>
              <p className="flex-1 text-sm leading-relaxed text-foreground">
                {q.question}
              </p>
              <details className="group">
                <summary className="cursor-pointer list-none text-sm font-medium text-primary hover:underline">
                  Cevabı göster
                </summary>
                <p className="mt-2 rounded-md bg-accent/40 p-3 text-sm text-foreground">
                  {q.answer}
                </p>
              </details>
            </div>
          ))}
        </div>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-muted-foreground">
          <span className="inline-flex items-center gap-1.5">
            <ListChecks className="h-4 w-4 text-primary" /> Sorular
          </span>
          <span className="inline-flex items-center gap-1.5">
            <FileCheck className="h-4 w-4 text-primary" /> Cevap anahtarı
          </span>
          <span className="inline-flex items-center gap-1.5">
            <CheckCircle2 className="h-4 w-4 text-primary" /> Adım adım çözüm
          </span>
        </div>
        <div className="mt-8 flex justify-center">
          <Button asChild size="lg" className="gap-2 px-7">
            <Link href="/sign-up">
              Kendi kağıdını oluştur <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </section>
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
            Öğretmenler ve veliler için MEB uyumlu çalışma kağıdı hazırlayıcı
          </h2>
          <p className="mt-4 text-base leading-relaxed text-muted-foreground">
            1.→7. sınıf MEB matematik müfredatına uygun çalışma kağıtlarını
            dakikalar değil saniyeler içinde hazırlar. Üretilen her soru sana
            gösterilmeden önce <strong>iki kez kontrol edilir</strong>: önce
            matematiği doğru mu, sonra seçtiğin konuya/kazanıma uyuyor mu. Yanlış
            veya konu dışı sorular otomatik elenir — yani elindeki PDF&apos;e
            güvenebilirsin. Çıktı baskıya hazır: sorular, cevap anahtarı ve adım
            adım çözüm.
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
    title: "Sınıf ve konuyu seç",
    body: "Sınıf, konu ve istersen kazanım kodunu seç; zorluk düzeyini ve soru sayısını (5–20) belirle. Hepsi birkaç tıkla.",
    icon: <BookOpen className="h-6 w-6" />,
  },
  {
    n: "2",
    title: "Sorular hazırlansın",
    body: "Sistem MEB kazanımına uygun soruları üretir ve her birinin matematiğini + konuya uygunluğunu otomatik kontrol eder. Hatalı sorular sana hiç gösterilmeden elenir.",
    icon: <Sparkles className="h-6 w-6" />,
  },
  {
    n: "3",
    title: "İndir ve paylaş",
    body: "Sorular, cevap anahtarı ve adım adım çözüm tek bir A4 PDF'te — yaklaşık 30 saniyede. İndir, yazdır, öğrencilerinle paylaş.",
    icon: <Zap className="h-6 w-6" />,
  },
];

function HowItWorks() {
  return (
    <section id="how" className="bg-card py-20">
      <div className="container">
        <SectionHeader
          eyebrow="Nasıl çalışır"
          title="Üç adımda hazır çalışma kağıdı"
          body="Birkaç tıkla, baskıya hazır PDF elinde."
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
            İlk çalışma kağıdını 5 dakikada hazırla
          </h2>
          <p className="text-base text-muted-foreground">
            Hesap açmak için yalnızca e-posta yeterli, ödeme bilgisi istenmez.
            Aylık 100 soru tüm kullanıcılara ücretsiz.
          </p>
          <Button asChild size="lg" className="gap-2 px-8">
            <Link href="/sign-up">
              Ücretsiz dene <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </section>
  );
}
