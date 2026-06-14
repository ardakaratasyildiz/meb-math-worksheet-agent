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
import { ALTKONU_PAGES } from "@/lib/altkonular";
import { CURRICULUM_PAGES } from "@/lib/curriculum";

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://soruatolyesi.com";

/**
 * LGS hub — head-term landing ("LGS matematik", "LGS hazırlık").
 *
 * 8. sınıf = LGS sınıfı. Bu sayfa 8. sınıf müfredat konularını (CURRICULUM_PAGES)
 * ve LGS-odaklı alt-konu sayfalarını (ALTKONU_PAGES, grade 8) tek bir otorite
 * düğümünde toplar → topical authority + iç-link. Benzersiz içerik + FAQ ile
 * thin-content değil. Üretece /generate?grade=8 ile deep-link.
 */
export const metadata: Metadata = {
  title: "LGS Matematik Çalışma Kağıdı — 8. Sınıf Hazırlık",
  description:
    "LGS matematik hazırlık için 8. sınıf tüm konularına özel ücretsiz çalışma kağıdı üret: üslü ve kareköklü ifadeler, çarpanlar-katlar, özdeşlikler, üçgenler, olasılık ve dahası. PDF, cevap anahtarı ve adım adım çözüm dahil.",
  keywords: [
    "LGS matematik",
    "LGS hazırlık",
    "LGS matematik çalışma kağıdı",
    "8. sınıf matematik",
    "8. sınıf LGS",
    "LGS matematik konuları",
    "LGS matematik soruları",
  ],
  alternates: { canonical: "/lgs-matematik" },
  openGraph: {
    title: "LGS Matematik Çalışma Kağıdı — 8. Sınıf Hazırlık · Soru Atölyesi",
    description:
      "8. sınıf LGS matematik konularına özel, MEB müfredatına uygun ücretsiz çalışma kağıtları. Üslü/kareköklü ifadeler, çarpanlar, özdeşlikler, üçgenler, olasılık ve daha fazlası.",
    url: `${SITE_URL}/lgs-matematik`,
    type: "website",
  },
};

const FAQ = [
  {
    q: "LGS'de matematik kaç soru çıkar?",
    a: "LGS sayısal bölümünde matematikten 20 soru sorulur. Sorular ezbere değil, kazanımları yorumlama ve birden çok adımı birleştirme üzerine kuruludur; bu yüzden her konuda bol soru çözmek belirleyicidir.",
  },
  {
    q: "LGS matematikte hangi konular çıkar?",
    a: "8. sınıf MEB müfredatının tamamı: çarpanlar ve katlar (EBOB-EKOK), üslü ifadeler, kareköklü ifadeler, gerçek sayılar, cebirsel ifadeler ve özdeşlikler, çarpanlara ayırma, doğrusal denklemler, eğim, eşitsizlikler, üçgenler ve Pisagor bağıntısı, dönüşüm geometrisi, geometrik cisimler, veri analizi ve olasılık.",
  },
  {
    q: "Bu çalışma kağıtları LGS'ye uygun mu?",
    a: "Evet. Sayfalardaki içerikler 8. sınıf MEB kazanımlarına göre üretilir ve gerçek çıkmış LGS sorularından oluşan örnek havuzuyla hizalanır. Her kağıt PDF, cevap anahtarı ve adım adım çözüm içerir.",
  },
  {
    q: "Çalışma kağıtları ücretsiz mi?",
    a: "Evet, konu seçip ücretsiz çalışma kağıdı üretebilirsin. Soru sayısını, zorluk seviyesini ve soru tipini sen belirlersin; sistem soruları üretir, denetimden geçirir ve PDF olarak hazırlar.",
  },
];

function collectionPageSchema(topics: typeof CURRICULUM_PAGES) {
  return {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: "LGS Matematik Çalışma Kağıtları — 8. Sınıf Hazırlık",
    url: `${SITE_URL}/lgs-matematik`,
    inLanguage: "tr-TR",
    isPartOf: { "@type": "WebSite", name: "Soru Atölyesi", url: SITE_URL },
    hasPart: topics.map((p) => ({
      "@type": "LearningResource",
      name: `8. Sınıf ${p.topicName}`,
      url: `${SITE_URL}/calismalar/${p.slug}`,
      educationalLevel: "Grade 8",
      learningResourceType: "Worksheet",
    })),
  };
}

function faqSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: FAQ.map((f) => ({
      "@type": "Question",
      name: f.q,
      acceptedAnswer: { "@type": "Answer", text: f.a },
    })),
  };
}

export default function LgsHubPage() {
  const topics = CURRICULUM_PAGES.filter((p) => p.grade === 8);
  const altKonular = ALTKONU_PAGES.filter((a) => a.grade === 8);

  return (
    <>
      <JsonLd id="lgs-collection-schema" data={collectionPageSchema(topics)} />
      <JsonLd id="lgs-faq-schema" data={faqSchema()} />

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
            <span className="text-foreground">LGS Matematik</span>
          </nav>

          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-accent px-3 py-1 text-xs font-medium text-accent-foreground">
            <Sparkles className="h-3 w-3" />
            8. Sınıf · LGS Hazırlık · MEB Müfredatı
          </div>
          <h1 className="text-balance text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            LGS Matematik Çalışma Kağıdı —{" "}
            <span className="bg-gradient-to-r from-primary to-coral bg-clip-text text-transparent">
              8. Sınıf Hazırlık
            </span>
          </h1>
          <p className="mt-5 text-lg text-muted-foreground">
            LGS matematikte fark, çok soru çözmekle açılır. 8. sınıf MEB
            müfredatının her konusu için saniyeler içinde özgün çalışma kağıdı
            üret: soru sayısını, zorluk seviyesini ve soru tipini sen seç; sistem
            soruları üretir, çift denetimden geçirir ve PDF olarak hazırlar.
            Cevap anahtarı ve adım adım çözüm dahil.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild size="lg" className="gap-2">
              <Link href="/generate?grade=8">
                LGS çalışma kağıdı üret <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link href="/calismalar">Tüm sınıflar ve konular</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Ana konular — 8. sınıf müfredat sayfaları */}
      <section className="py-16">
        <div className="container max-w-4xl">
          <div className="mb-6 flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-primary" />
            <h2 className="text-2xl font-bold tracking-tight text-foreground">
              LGS matematik konuları
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

      {/* LGS alt-konular — long-tail landing'lere iç-link */}
      {altKonular.length > 0 && (
        <section className="bg-card py-16">
          <div className="container max-w-4xl">
            <div className="mb-6 flex items-center gap-2">
              <Target className="h-5 w-5 text-primary" />
              <h2 className="text-2xl font-bold tracking-tight text-foreground">
                LGS'de en çok çıkan alt-konular
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
            LGS matematik hakkında sık sorulanlar
          </h2>
          <div className="space-y-6">
            {FAQ.map((f) => (
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
            LGS matematik çalışma kağıdını hemen üret
          </h2>
          <p className="mt-3 text-muted-foreground">
            8. sınıf konusunu seç, gerisini sisteme bırak — kazanıma hizalı
            sorular, cevap anahtarı ve adım adım çözümle PDF olarak hazır.
          </p>
          <Button asChild size="lg" className="mt-6 gap-2 px-8">
            <Link href="/generate?grade=8">
              Şimdi üret <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </section>

      <Footer />
    </>
  );
}
