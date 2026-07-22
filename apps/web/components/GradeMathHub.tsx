import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  BookOpen,
  ChevronRight,
  GraduationCap,
  Sparkles,
  Target,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Footer } from "@/components/Footer";
import { JsonLd } from "@/components/JsonLd";
import { TrackedGenerateLink } from "@/components/TrackedGenerateLink";
import { ALTKONU_PAGES } from "@/lib/altkonular";
import { CURRICULUM_PAGES } from "@/lib/curriculum";

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://soruatolyesi.com";

/**
 * Sınıf-bazlı matematik hub'ı (1-7) — head-term landing ("5. sınıf matematik",
 * "6. sınıf matematik çalışma kağıdı"). /lgs-matematik (8) deseninin çoğaltması.
 * O sınıfın müfredat konularını + alt-konu sayfalarını tek otorite düğümünde
 * toplar (topical authority + iç-link) + FAQ (rich result). Benzersiz içerik
 * (konu adları sınıfa göre) → thin-content değil.
 */

function slug(grade: number): string {
  return `${grade}-sinif-matematik`;
}

/** Statik sayfa başına metadata — her grade page'i bunu re-export eder. */
export function gradeMathMetadata(grade: number): Metadata {
  const url = `${SITE_URL}/${slug(grade)}`;
  const topics = CURRICULUM_PAGES.filter((p) => p.grade === grade)
    .map((p) => p.topicName)
    .join(", ");
  return {
    title: `${grade}. Sınıf Matematik Çalışma Kağıdı — Ücretsiz, MEB Müfredatı`,
    description: `${grade}. sınıf matematik konularına özel ücretsiz çalışma kağıdı üret: ${topics}. PDF, cevap anahtarı ve adım adım çözüm dahil. MEB müfredatına uygun.`,
    keywords: [
      `${grade}. sınıf matematik`,
      `${grade}. sınıf matematik çalışma kağıdı`,
      `${grade}. sınıf matematik soruları`,
      `${grade}. sınıf matematik testi`,
      `${grade}. sınıf matematik konuları`,
    ],
    alternates: { canonical: `/${slug(grade)}` },
    openGraph: {
      title: `${grade}. Sınıf Matematik Çalışma Kağıdı · Soru Atölyesi`,
      description: `${grade}. sınıf matematik konularına özel, MEB müfredatına uygun ücretsiz çalışma kağıtları. Cevap anahtarı ve adım adım çözüm dahil.`,
      url,
      type: "website",
    },
  };
}

function buildFaq(grade: number, topicNames: string[]) {
  return [
    {
      q: `${grade}. sınıfta matematik hangi konular var?`,
      a: `${grade}. sınıf MEB matematik müfredatı şu öğrenme alanlarını kapsar: ${topicNames.join(", ")}. Her konu için ayrı çalışma kağıdı üretebilir, soru sayısı ve zorluk seviyesini kendin seçebilirsin.`,
    },
    {
      q: `${grade}. sınıf matematik çalışma kağıtları ücretsiz mi?`,
      a: "Evet. Konu seçip ücretsiz çalışma kağıdı üretebilirsin; sistem soruları üretir, denetimden geçirir ve cevap anahtarı + adım adım çözümle PDF olarak hazırlar.",
    },
    {
      q: "Çalışma kağıtları MEB müfredatına uygun mu?",
      a: `Evet, tüm sorular ${grade}. sınıf MEB kazanımlarına göre üretilir ve içerik ders kitabı + örnek soru havuzuyla hizalanır.`,
    },
    {
      q: "Nasıl çalışma kağıdı üretirim?",
      a: "Sınıf ve konuyu seç, soru sayısı/zorluk/soru tipini belirle; sistem saniyeler içinde özgün soruları üretip PDF olarak hazırlar.",
    },
  ];
}

function collectionSchema(grade: number, topics: typeof CURRICULUM_PAGES) {
  return {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: `${grade}. Sınıf Matematik Çalışma Kağıtları`,
    url: `${SITE_URL}/${slug(grade)}`,
    inLanguage: "tr-TR",
    isPartOf: { "@type": "WebSite", name: "Soru Atölyesi", url: SITE_URL },
    hasPart: topics.map((p) => ({
      "@type": "LearningResource",
      name: `${grade}. Sınıf ${p.topicName}`,
      url: `${SITE_URL}/calismalar/${p.slug}`,
      educationalLevel: `Grade ${grade}`,
      learningResourceType: "Worksheet",
    })),
  };
}

function faqSchema(faq: { q: string; a: string }[]) {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faq.map((f) => ({
      "@type": "Question",
      name: f.q,
      acceptedAnswer: { "@type": "Answer", text: f.a },
    })),
  };
}

export function GradeMathHub({ grade }: { grade: number }) {
  const topics = CURRICULUM_PAGES.filter((p) => p.grade === grade);
  const altKonular = ALTKONU_PAGES.filter((a) => a.grade === grade);
  const faq = buildFaq(
    grade,
    topics.map((t) => t.topicName),
  );
  const genHref = `/generate?grade=${grade}`;

  return (
    <>
      <JsonLd id={`grade-${grade}-collection`} data={collectionSchema(grade, topics)} />
      <JsonLd id={`grade-${grade}-faq`} data={faqSchema(faq)} />

      <section className="border-b bg-gradient-to-b from-primary/5 to-transparent py-16">
        <div className="container max-w-4xl">
          <nav className="mb-6 flex flex-wrap items-center gap-1 text-sm text-muted-foreground">
            <Link
              href="/calismalar"
              className="inline-flex items-center gap-1 hover:text-foreground"
            >
              <GraduationCap className="h-4 w-4" /> Konular
            </Link>
            <ChevronRight className="h-3.5 w-3.5" />
            <span className="text-foreground">{grade}. Sınıf Matematik</span>
          </nav>

          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-accent px-3 py-1 text-xs font-medium text-accent-foreground">
            <Sparkles className="h-3 w-3" />
            {grade}. Sınıf · MEB Müfredatı · Ücretsiz
          </div>
          <h1 className="text-balance text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            {grade}. Sınıf Matematik Çalışma Kağıdı —{" "}
            <span className="bg-gradient-to-r from-primary to-coral bg-clip-text text-transparent">
              Ücretsiz Üret
            </span>
          </h1>
          <p className="mt-5 text-lg text-muted-foreground">
            {grade}. sınıf MEB matematik müfredatının her konusu için saniyeler
            içinde özgün çalışma kağıdı üret: soru sayısını, zorluk seviyesini ve
            soru tipini sen seç; sistem soruları üretir, çift denetimden geçirir ve
            PDF olarak hazırlar. Cevap anahtarı ve adım adım çözüm dahil.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <TrackedGenerateLink
              href={genHref}
              source="grade_hub"
              grade={grade}
              size="lg"
              className="gap-2"
            >
              {grade}. sınıf çalışma kağıdı üret <ArrowRight className="h-4 w-4" />
            </TrackedGenerateLink>
            <Button asChild variant="outline" size="lg">
              <Link href="/calismalar">Tüm sınıflar ve konular</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Ana konular — sınıf müfredat sayfaları */}
      <section className="py-16">
        <div className="container max-w-4xl">
          <div className="mb-6 flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-primary" />
            <h2 className="text-2xl font-bold tracking-tight text-foreground">
              {grade}. sınıf matematik konuları
            </h2>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {topics.map((p) => (
              <Link
                key={p.slug}
                href={`/calismalar/${p.slug}`}
                className="group rounded-xl border bg-card p-5 transition hover:border-primary/50"
              >
                <h3 className="font-semibold text-foreground group-hover:text-primary">
                  {p.topicName}
                </h3>
                <p className="mt-1.5 text-sm text-muted-foreground">
                  {p.description}
                </p>
                <span className="mt-3 inline-flex items-center gap-1 text-sm text-primary">
                  Konuyu aç <ArrowRight className="h-3.5 w-3.5" />
                </span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Alt-konular — long-tail landing'lere iç-link */}
      {altKonular.length > 0 && (
        <section className="bg-card py-16">
          <div className="container max-w-4xl">
            <div className="mb-6 flex items-center gap-2">
              <Target className="h-5 w-5 text-primary" />
              <h2 className="text-2xl font-bold tracking-tight text-foreground">
                {grade}. sınıf matematik alt-konuları
              </h2>
            </div>
            <p className="mb-8 text-muted-foreground">
              Her başlık, o konuya özel benzersiz bir çalışma sayfasıdır. İncele,
              becerileri gör ve doğrudan o konuda çalışma kağıdı üret.
            </p>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {altKonular.map((a) => (
                <Link
                  key={`${a.topicSlug}-${a.slug}`}
                  href={`/calismalar/${a.topicSlug}/${a.slug}`}
                  className="rounded-lg border bg-background p-4 text-sm font-medium hover:border-primary/50 hover:text-primary"
                >
                  {a.title}
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* SSS — FAQPage rich-result */}
      <section className="py-16">
        <div className="container max-w-3xl">
          <h2 className="mb-8 text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            {grade}. sınıf matematik hakkında sık sorulanlar
          </h2>
          <div className="space-y-6">
            {faq.map((f) => (
              <div key={f.q} className="rounded-xl border bg-card p-6">
                <h3 className="font-semibold text-foreground">{f.q}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  {f.a}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-card py-16">
        <div className="container max-w-3xl text-center">
          <h2 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            {grade}. sınıf matematik çalışma kağıdını hemen üret
          </h2>
          <p className="mt-3 text-muted-foreground">
            Konuyu seç, gerisini sisteme bırak — kazanıma hizalı sorular, cevap
            anahtarı ve adım adım çözümle PDF olarak hazır.
          </p>
          <TrackedGenerateLink
            href={genHref}
            source="grade_hub_footer"
            grade={grade}
            size="lg"
            className="mt-6 gap-2 px-8"
          >
            Şimdi üret <ArrowRight className="h-4 w-4" />
          </TrackedGenerateLink>
        </div>
      </section>

      <Footer />
    </>
  );
}
