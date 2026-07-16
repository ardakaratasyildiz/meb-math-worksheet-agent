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
import { HeroSubjectFan } from "@/components/HeroSubjectFan";
import { SectionHeader } from "@/components/PageHeader";
import { SubjectShowroom } from "@/components/SubjectShowroom";
import { availableSubjects, hasMultipleSubjects, subjectStyle } from "@/lib/subjects";
import sampleData from "@/lib/sample-questions.json";

export default function LandingPage() {
  // Çok-ders açıksa (flag) ders-bazlı sekmeli vitrin; değilse mevcut math-only
  // Showroom. Flag kapalıyken (bugünkü canlı) ana sayfa birebir eskisi gibi kalır.
  const multi = hasMultipleSubjects();
  return (
    <>
      <JsonLd id="org-schema" data={organizationSchema()} />
      <JsonLd id="website-schema" data={websiteSchema()} />
      <Hero />
      {multi ? <SubjectShowroom /> : <Showroom />}
      <SolveAndGrow />
      <ClassroomCta />
      <SystemSummary />
      <BrowseByGrade />
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

// ─── ÖĞRETMEN / VELİ CTA — sınıf modeli kapısı (keşfedilebilirlik + SEO) ─────

function ClassroomCta() {
  return (
    <section className="py-16">
      <div className="container">
        <div className="relative overflow-hidden rounded-3xl border bg-card p-8 shadow-pop sm:p-10">
          <div className="grid items-center gap-6 sm:grid-cols-[1fr_auto]">
            <div className="space-y-3">
              <span className="inline-flex items-center gap-2 rounded-full bg-amber-400/15 px-3 py-1 font-display text-sm font-semibold text-amber-600 dark:text-amber-400">
                <GraduationCap className="h-4 w-4" />
                Öğretmen &amp; veli
              </span>
              <h2 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">
                Öğretmen veya veli misin? Sınıfını aç.
              </h2>
              <p className="max-w-xl text-muted-foreground">
                Sınıf oluştur, öğrencilerini katılma koduyla davet et, çözülebilir
                quizleri ödev olarak ata; kimin çözdüğünü ve kaç doğru yaptığını tek
                ekrandan izle.
              </p>
            </div>
            <Button asChild size="lg" className="gap-2 sm:shrink-0">
              <Link href="/practice">
                <Users className="h-4 w-4" />
                Sınıf oluştur
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── HERO ────────────────────────────────────────────────────────────────────

function Hero() {
  const multi = hasMultipleSubjects();
  return (
    <section className="relative overflow-hidden">
      <div
        aria-hidden
        className="pointer-events-none absolute -right-40 -top-40 -z-10 h-[520px] w-[520px] rounded-full bg-primary/10 blur-3xl"
      />
      {/* Süzülen matematik sembolleri — oyunsu hava (sadece geniş ekran) */}
      <div
        aria-hidden
        className="pointer-events-none absolute right-[7%] top-24 hidden animate-bob font-display text-4xl text-primary/25 lg:block"
        style={{ animationDelay: "0.4s" }}
      >
        ÷
      </div>
      <div
        aria-hidden
        className="pointer-events-none absolute left-[46%] bottom-14 hidden animate-bob font-display text-5xl text-coral/25 lg:block"
        style={{ animationDelay: "1.1s" }}
      >
        π
      </div>
      <div className="container grid gap-12 pb-16 pt-8 sm:pb-20 sm:pt-12 lg:grid-cols-12 lg:items-start">
        {/* Sol — metin */}
        <div className="lg:col-span-7">
          <Badge
            variant="outline"
            className="border-primary/30 bg-accent text-accent-foreground"
          >
            <Sparkles className="mr-1.5 h-3 w-3" />
            {multi
              ? "1.→8. sınıf · LGS hazırlık · MEB müfredatı"
              : "1.→8. sınıf · LGS hazırlık · MEB matematik müfredatı"}
          </Badge>
          <h1 className="mt-6 max-w-2xl text-balance text-4xl font-bold tracking-tight text-foreground sm:text-5xl md:text-6xl">
            {multi ? "Çalışma kağıtlarını" : "Matematik çalışma kağıtlarını"}{" "}
            <span className="bg-gradient-to-r from-primary to-coral bg-clip-text text-transparent">
              saniyeler içinde
            </span>{" "}
            hazırlayın
          </h1>
          <p className="mt-6 max-w-xl text-balance text-lg text-muted-foreground sm:text-xl">
            {multi ? "Sınıf, ders ve kazanımı seçin" : "Sınıf ve kazanımı seçin"};
            MEB kazanımlarına uygun sorular, cevap anahtarı ve adım adım
            çözümüyle hazırlanan PDF saniyeler içinde elinizde. İndirin, yazdırın,
            öğrencilerinizle paylaşın.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
            <Button asChild size="lg" className="gap-2 px-7">
              <Link href="/sign-up">
                Ücretsiz dene <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>
          <div className="mt-7 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-muted-foreground">
            <TrustBullet>Aylık 100 soru ücretsiz</TrustBullet>
            <TrustBullet>Kayıt için yalnızca e-posta</TrustBullet>
            <TrustBullet>Ödeme bilgisi alınmaz</TrustBullet>
          </div>
        </div>

        {/* Sağ — çok-ders: ders kartı fanı (maskotlu); tek-ders: statik matematik kartı */}
        <div className="lg:col-span-5">
          {multi ? (
            <HeroSubjectFan />
          ) : (
            <div className="relative mx-auto max-w-sm">
              {/* Zıplayan maskot — demolardaki oyunsu dokunuş */}
              <div
                aria-hidden
                className="absolute -left-6 -top-9 z-10 animate-bob text-5xl drop-shadow-md"
              >
                🦊
              </div>
              <div
                aria-hidden
                className="absolute inset-0 translate-x-3 translate-y-3 rounded-3xl bg-primary/10"
              />
              <div className="relative rounded-3xl border bg-card p-6 shadow-pop">
                <div className="flex items-center justify-between border-b pb-3">
                  <span className="font-display text-base font-bold text-foreground">
                    5. sınıf · Cebir
                  </span>
                  <span className="rounded-full bg-accent px-2.5 py-1 text-[10px] font-bold text-accent-foreground">
                    M.5.2.1
                  </span>
                </div>
                <ol className="mt-4 space-y-3 text-sm text-muted-foreground">
                  <li>
                    <span className="font-bold text-foreground">1.</span> 3a + 5
                    ifadesinin a = 4 için değeri kaçtır?
                  </li>
                  <li>
                    <span className="font-bold text-foreground">2.</span> x − 7 = 12
                    denkleminde x kaçtır?
                  </li>
                  <li>
                    <span className="font-bold text-foreground">3.</span> Bir sayının
                    2 katının 6 fazlası 20 ise sayı kaçtır?
                  </li>
                </ol>
                <div className="mt-5 flex items-center gap-2 border-t pt-3 text-[11px] font-bold text-mint">
                  <CheckCircle2 className="h-3.5 w-3.5" /> Cevap anahtarı · adım adım
                  çözüm
                </div>
              </div>
            </div>
          )}
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

// ─── ÇÖZ & GELİŞ TANITIMI — öğrenme döngüsü ──────────────────────────────────

const SOLVE_FEATURES = [
  {
    icon: <PencilLine className="h-5 w-5" />,
    title: "Site içinde çöz",
    body: "Üretilen quizi site içinde çöz: çoktan seçmeli, doğru/yanlış, boşluk doldurma ve açık uçlu.",
  },
  {
    icon: <BarChart3 className="h-5 w-5" />,
    title: "Anında puan + konu raporu",
    body: "Kaç doğru kaç yanlış — konu bazında kazanım eksiğini hemen gör.",
  },
  {
    icon: <Target className="h-5 w-5" />,
    title: "Eksiğine göre pratik",
    body: "Zayıf kazanımına yönelik tek tıkla yeni sorular oluştur ve kazanım eksiğini kapat.",
  },
  {
    icon: <Trophy className="h-5 w-5" />,
    title: "Gelişim + rozetler",
    body: "30 günlük gelişim grafiği, seviye, seri ve konu rozetleriyle motive ol.",
  },
];

function SolveAndGrow() {
  return (
    <section className="py-20">
      <div className="container">
        {/* Öğrenciler için — gradyan vitrin + oyunlaştırma önizlemesi (alıcıya
            çocuğun eğleneceği deneyimi gösteren köprü). Statik temsilî veri. */}
        <div className="overflow-hidden rounded-3xl bg-gradient-to-br from-primary to-sky-500 p-8 text-primary-foreground shadow-pop sm:p-10">
          <div className="grid items-center gap-8 lg:grid-cols-2">
            <div>
              <span className="inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold uppercase tracking-wider">
                <Sparkles className="h-3 w-3" /> Yeni · Öğrenciler için
              </span>
              <h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">
                Sadece kağıt değil — çocuğunuz için eğlenceli bir öğrenme döngüsü
              </h2>
              <p className="mt-3 text-base leading-relaxed text-white/85">
                Üret → Çöz → Geliş: anında kaç doğru/yanlış, eksik kazanıma göre
                pratik. Öğrenci rozet kazanır, seri yapar, seviye atlar; siz
                gelişimini takip edersiniz.
              </p>
              <Button
                asChild
                size="lg"
                className="mt-6 gap-2 bg-white text-primary hover:bg-white/90"
              >
                <Link href="/practice">
                  Çöz &amp; Geliş&apos;i keşfet <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
            </div>
            {/* oyunlaştırma önizlemesi */}
            <div className="rounded-2xl bg-white/12 p-5 ring-1 ring-white/20 backdrop-blur">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-sun font-display text-lg font-bold text-primary">
                    7
                  </div>
                  <div>
                    <p className="text-sm font-semibold">Seviye 7</p>
                    <p className="text-xs text-white/70">1.840 XP</p>
                  </div>
                </div>
                <span className="rounded-full bg-white/15 px-3 py-1 text-sm font-semibold">
                  🔥 12 gün
                </span>
              </div>
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/20">
                <div className="h-full w-[47%] rounded-full bg-sun" />
              </div>
              <div className="mt-3 flex flex-wrap gap-2 text-xs">
                <span className="rounded-full bg-white/15 px-2.5 py-1 font-medium">🥇 Doğal sayılar</span>
                <span className="rounded-full bg-white/15 px-2.5 py-1 font-medium">🥈 Cebir</span>
                <span className="rounded-full bg-white/15 px-2.5 py-1 font-medium">🥉 Geometri</span>
              </div>
            </div>
          </div>
        </div>

        {/* Çöz & Geliş özellikleri */}
        <div className="mt-10 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {SOLVE_FEATURES.map((f, i) => (
            <div
              key={i}
              className="flex flex-col gap-3 rounded-xl border bg-card p-5 shadow-pop"
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
  ["8-sinif-cebir", "8. sınıf · LGS hazırlık"],
  ["2-sinif-dogal-sayilar", "2. sınıf · Doğal sayılar"],
  ["5-sinif-cebir", "5. sınıf · Cebir"],
  ["8-sinif-geometri", "8. sınıf · LGS geometri"],
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
          body="Aşağıdakiler sistemin ürettiği sorulardan bir kesittir. Hazırlanan PDF'te ayrıca cevap anahtarı ve adım adım çözüm sayfası yer alır."
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
  const multi = hasMultipleSubjects();
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
            {multi
              ? "1.→8. sınıf MEB müfredatına (Matematik, Fen Bilimleri, Türkçe, Sosyal Bilgiler ve İngilizce; 8. sınıfta LGS hazırlık dahil) "
              : "1.→8. sınıf MEB matematik müfredatına (8. sınıfta LGS hazırlık dahil) "}
            uygun çalışma kağıtlarını dakikalar değil saniyeler içinde hazırlar. Üretilen her soru sana
            gösterilmeden önce <strong>iki kez kontrol edilir</strong>: önce
            {multi ? " içeriği doğru mu" : " matematiği doğru mu"}, sonra seçtiğin
            konuya/kazanıma uyuyor mu. Yanlış veya konu dışı sorular otomatik
            elenir — yani elindeki PDF&apos;e güvenebilirsin. Çıktı baskıya hazır:
            sorular, cevap anahtarı ve adım adım çözüm.
          </p>
        </div>
      </div>
    </section>
  );
}

// ─── SINIFA GÖRE GÖZ AT — içerik ağacına iç link (SEO) ───────────────────────
// Ana sayfa sitenin TEK güçlü indeksli/otoriteli sayfası; buradan sınıf hub'larına
// crawlable link vererek otoritenin içerik ağacına (hub → konu → kazanım) akmasını
// sağlıyoruz. Bu blok olmadan 300+ SEO sayfası yalnızca sitemap'ten keşfediliyordu
// (otorite taşımaz) → "unknown to Google" / "crawled - not indexed".

const GRADE_HUBS: { label: string; sub: string; href: string }[] = [
  { label: "1. Sınıf", sub: "Matematik", href: "/1-sinif-matematik" },
  { label: "2. Sınıf", sub: "Matematik", href: "/2-sinif-matematik" },
  { label: "3. Sınıf", sub: "Matematik", href: "/3-sinif-matematik" },
  { label: "4. Sınıf", sub: "Matematik", href: "/4-sinif-matematik" },
  { label: "5. Sınıf", sub: "Matematik", href: "/5-sinif-matematik" },
  { label: "6. Sınıf", sub: "Matematik", href: "/6-sinif-matematik" },
  { label: "7. Sınıf", sub: "Matematik", href: "/7-sinif-matematik" },
  { label: "8. Sınıf", sub: "LGS hazırlık", href: "/lgs-matematik" },
];

function BrowseByGrade() {
  const multi = hasMultipleSubjects();
  const subjects = multi ? availableSubjects() : [];
  return (
    <section className="py-20">
      <div className="container">
        <SectionHeader
          eyebrow="Sınıf ve derse göre göz at"
          title="Sınıf ve konu bazlı çalışma kağıtları"
          body={
            multi
              ? "Dersini ve sınıfını seç; o sınıfın MEB kazanımlarına uygun hazır çalışma kağıtlarına göz at."
              : "Sınıfını seç; o sınıfın MEB matematik konularına ve kazanımlarına uygun hazır çalışma kağıtlarına göz at."
          }
        />

        {/* Derse göre — renkli ders çipleri (Konular'daki ilgili bölüme köprü) */}
        {multi ? (
          <div className="mt-10 flex flex-wrap justify-center gap-2.5">
            {subjects.map((s) => {
              const st = subjectStyle(s.value);
              return (
                <Link
                  key={s.value}
                  href={`/calismalar#${s.value}`}
                  className="inline-flex items-center gap-1.5 rounded-full border bg-card px-4 py-2 text-sm font-semibold shadow-pop transition-colors hover:bg-accent/40"
                  style={{ borderColor: `${st.hex}55`, color: st.hex }}
                >
                  <span aria-hidden>{st.emoji}</span>
                  {s.label}
                </Link>
              );
            })}
          </div>
        ) : null}

        {/* Sınıf hub'ları — matematik SEO iç linki (indeksleme kaldıracı, korunur) */}
        {multi ? (
          <p className="mt-10 text-center text-sm font-medium text-muted-foreground">
            Sınıf bazlı matematik hub&apos;ları:
          </p>
        ) : null}
        <div className={`grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 ${multi ? "mt-4" : "mt-12"}`}>
          {GRADE_HUBS.map((g) => (
            <Link
              key={g.href}
              href={g.href}
              className="group flex items-center justify-between gap-3 rounded-xl border bg-card p-5 shadow-pop transition-colors hover:border-primary/40"
            >
              <span className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                  <GraduationCap className="h-5 w-5" />
                </span>
                <span>
                  <span className="block font-display text-base font-bold text-foreground">
                    {g.label}
                  </span>
                  <span className="block text-xs text-muted-foreground">
                    {g.sub}
                  </span>
                </span>
              </span>
              <ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-primary" />
            </Link>
          ))}
        </div>
        <div className="mt-8 flex justify-center">
          <Button asChild variant="outline" className="gap-2">
            <Link href="/calismalar">
              Tüm sınıf ve konular <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </section>
  );
}

// ─── HOW IT WORKS ────────────────────────────────────────────────────────────

const STEPS = [
  {
    n: "1",
    title: "Sınıf, ders ve konuyu seç",
    body: "Sınıf, ders, konu ve istersen kazanım kodunu seç; zorluk düzeyini ve soru sayısını (5–20) belirle. Hepsi birkaç tıkla.",
    icon: <BookOpen className="h-6 w-6" />,
  },
  {
    n: "2",
    title: "Sorular hazırlansın",
    body: "Sistem MEB kazanımına uygun soruları üretir ve her birinin içeriğini/doğruluğunu + konuya uygunluğunu otomatik kontrol eder. Hatalı sorular sana hiç gösterilmeden elenir.",
    icon: <Sparkles className="h-6 w-6" />,
  },
  {
    n: "3",
    title: "İndir ve paylaş",
    body: "Sorular, cevap anahtarı ve adım adım çözüm tek bir A4 PDF'te — saniyeler içinde. İndir, yazdır, öğrencilerinle paylaş.",
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
    body: "Ders öncesi ilgili kazanım kodu seçilir; sistem 5–20 soruluk çalışma kağıdı ile cevap anahtarını hazırlar. Konu eksiği gözlendiğinde aynı kazanım için farklı yeni sorular üretilebilir.",
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
          body="Öğretmen, veli ve öğrenci kullanımlarında adımlar farklıdır; sistem her üç durumu da destekler."
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

function getFeatures(multi: boolean) {
  return [
  {
    icon: <BookOpen className="h-5 w-5" />,
    title: "Kazanım kodu bazlı üretim",
    body: multi
      ? "1.→8. sınıf MEB kazanımları — Matematik, Fen, Türkçe, Sosyal ve İngilizce (8. sınıf LGS hazırlık dahil); her sorunun yanında ilgili kazanım kodu görünür."
      : "1.→8. sınıf MEB matematik kazanımları (8. sınıf LGS hazırlık dahil); her sorunun yanında ilgili kazanım kodu görünür.",
  },
  {
    icon: <ShieldCheck className="h-5 w-5" />,
    title: "İki aşamalı denetim",
    body: multi
      ? "İçerik doğruluğu denetimi (matematikte sembolik aritmetik) ve kazanım uyumu denetimi. Denetim geçmeyen sorular yeniden üretilir."
      : "Sembolik aritmetik denetim ve kazanım uyumu denetimi. Denetim geçmeyen sorular yeniden üretilir.",
  },
  {
    icon: <FileCheck className="h-5 w-5" />,
    title: "Cevap anahtarı ve çözüm",
    body: "Her PDF içinde cevap anahtarı ve adım adım çözüm sayfası yer alır.",
  },
  {
    icon: <Sparkles className="h-5 w-5" />,
    title: "Anlamsal benzerlik denetimi",
    body: "Aynı parametrelerle tekrar üretimde önceki sorulara çok benzeyen sorular üretim havuzundan elenir.",
  },
  {
    icon: <Hash className="h-5 w-5" />,
    title: "İzlenebilir kazanım kodları",
    body: multi
      ? "Her çıktıda MEB kazanım kodu (örn. M.8.2.1, F.6.1.2) açıkça görünür — sınıf ve ders bazlı takip yapılabilir."
      : "Her çıktıda M.X.Y.Z formatında kazanım kodu açıkça görünür — sınıf bazlı takip yapılabilir.",
  },
  {
    icon: <Zap className="h-5 w-5" />,
    title: "Önbellek destekli yeniden indirme",
    body: "Aynı parametrelerle yapılan tekrar talepler önbellekten döner ve aylık kotadan düşmez.",
  },
  ];
}

function Features() {
  const multi = hasMultipleSubjects();
  const FEATURES = getFeatures(multi);
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
      className="relative overflow-hidden bg-gradient-to-br from-primary to-coral py-20 text-primary-foreground"
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

function getFaqs(multi: boolean) {
  return [
  {
    q: multi ? "Hangi dersler ve sınıflar destekleniyor?" : "Hangi sınıflar destekleniyor?",
    a: multi
      ? "1.→8. sınıf için Matematik, Fen Bilimleri, Türkçe, Sosyal Bilgiler ve İngilizce derslerinin MEB müfredatı desteklenmektedir (her dersin sınıf aralığı farklıdır). 8. sınıf, LGS hazırlık kapsamını da içerir."
      : "1.→8. sınıf MEB matematik müfredatının tamamı desteklenmektedir. 8. sınıf, LGS hazırlık kapsamını da içerir — gerçek çıkmış LGS soruları örnek havuzunda kullanılır.",
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
}

function Faq() {
  const FAQS = getFaqs(hasMultipleSubjects());
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
        <div className="mx-auto flex max-w-3xl flex-col items-center gap-6 rounded-2xl border bg-card p-12 text-center shadow-pop">
          <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            İlk çalışma kağıdını saniyeler içinde hazırla
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
