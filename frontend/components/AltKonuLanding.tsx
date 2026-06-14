import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  GraduationCap,
  ListChecks,
  Target,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Footer } from "@/components/Footer";
import { JsonLd, learningResourceSchema } from "@/components/JsonLd";
import { TrackedGenerateLink } from "@/components/TrackedGenerateLink";
import type { AltKonu } from "@/lib/altkonular";
import { getAltKonularByTopic, getAltKonuFamily } from "@/lib/altkonular";
import { getCurriculumPageBySlug } from "@/lib/curriculum";

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://soruatolyesi.com";

/**
 * Alt-konu (sub-topic) landing — programatik SEO yüzeyi.
 *
 * SEO-only: CTA, kazanım koduna değil KONU seviyesine deep-link eder
 * (?grade=&topic=). Backend bu parametreleri destekler; üretim hattına dokunmadan
 * o konuda çalışma kağıdı üretir. Benzersiz içerik (intro + alt-beceriler + zorluk
 * ipuçları) thin-content cezasını önler.
 */
export function AltKonuLanding({ ak }: { ak: AltKonu }) {
  const topic = getCurriculumPageBySlug(ak.topicSlug);
  const siblings = getAltKonularByTopic(ak.topicSlug).filter(
    (s) => s.slug !== ak.slug,
  );
  const family = getAltKonuFamily(ak.family, ak.topicSlug);

  // SEO-only → konu seviyesine deep-link (kazanım kodu pinlenmez).
  const generateHref = `/generate?grade=${ak.grade}&topic=${ak.topicId}`;

  return (
    <>
      <JsonLd
        id="altkonu-schema"
        data={learningResourceSchema({
          grade: ak.grade,
          topicName: `${ak.topicName} — ${ak.title}`,
          description: ak.description,
          url: `${SITE_URL}/calismalar/${ak.topicSlug}/${ak.slug}`,
        })}
      />

      <section className="border-b bg-gradient-to-b from-primary/5 to-transparent py-16">
        <div className="container max-w-4xl">
          {/* Breadcrumb — SEO + gezinme */}
          <nav className="mb-6 flex flex-wrap items-center gap-1 text-sm text-muted-foreground">
            <Link
              href="/calismalar"
              className="inline-flex items-center gap-1 hover:text-foreground"
            >
              <GraduationCap className="h-4 w-4" /> Konular
            </Link>
            <ChevronRight className="h-3.5 w-3.5" />
            <Link
              href={`/calismalar/${ak.topicSlug}`}
              className="hover:text-foreground"
            >
              {ak.grade}. Sınıf {ak.topicName}
            </Link>
            <ChevronRight className="h-3.5 w-3.5" />
            <span className="text-foreground">{ak.title}</span>
          </nav>

          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-accent px-3 py-1 text-xs font-medium text-accent-foreground">
            <Target className="h-3 w-3" />
            {ak.grade}. Sınıf · {ak.topicName}
          </div>
          <h1 className="text-balance text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            {ak.grade}. Sınıf {ak.title} —{" "}
            <span className="bg-gradient-to-r from-primary to-coral bg-clip-text text-transparent">
              Çalışma Kağıdı
            </span>
          </h1>
          <p className="mt-5 text-lg text-muted-foreground">{ak.intro}</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <TrackedGenerateLink
              href={generateHref}
              source="altkonu"
              grade={ak.grade}
              topic={ak.topicId}
              size="lg"
              className="gap-2"
            >
              Çalışma kağıdı üret <ArrowRight className="h-4 w-4" />
            </TrackedGenerateLink>
            <Button asChild variant="outline" size="lg">
              <Link href={`/calismalar/${ak.topicSlug}`}>
                {ak.topicName} konusunun tümü
              </Link>
            </Button>
          </div>
        </div>
      </section>

      <section className="py-16">
        <div className="container max-w-4xl">
          <div className="mb-6 flex items-center gap-2">
            <ListChecks className="h-5 w-5 text-primary" />
            <h2 className="text-2xl font-bold tracking-tight text-foreground">
              Bu başlıkta hangi beceriler ölçülür?
            </h2>
          </div>
          <ul className="grid gap-3 sm:grid-cols-2">
            {ak.skills.map((s) => (
              <li
                key={s}
                className="flex items-start gap-2 rounded-lg border bg-card p-4 text-sm text-foreground"
              >
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                {s}
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="bg-card py-16">
        <div className="container max-w-4xl">
          <h2 className="text-2xl font-bold tracking-tight text-foreground">
            Zorluk seviyelerine göre ne sorulur?
          </h2>
          <p className="mt-2 text-muted-foreground">
            Çalışma kağıdını üretirken zorluk seviyesini sen seçersin; her seviyede
            tipik olarak şu beceriler ölçülür:
          </p>
          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {(
              [
                ["Kolay", ak.difficulty.kolay],
                ["Orta", ak.difficulty.orta],
                ["Zor", ak.difficulty.zor],
              ] as const
            ).map(([label, value]) => (
              <div key={label} className="rounded-xl border bg-background p-5">
                <span className="text-xs font-semibold uppercase tracking-wider text-primary">
                  {label}
                </span>
                <p className="mt-2 text-sm leading-relaxed text-foreground">
                  {value}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16">
        <div className="container max-w-3xl text-center">
          <h2 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            {ak.grade}. sınıf {ak.title.toLowerCase()} çalışma kağıdını hemen üret
          </h2>
          <p className="mt-3 text-muted-foreground">
            Soru sayısı, zorluk ve soru tipini sen seç; sistem {ak.topicName.toLowerCase()}
            {" "}konusuna uygun soruları üretir, çift denetimden geçirir ve PDF olarak
            hazırlar.
          </p>
          <TrackedGenerateLink
            href={generateHref}
            source="altkonu_footer"
            grade={ak.grade}
            topic={ak.topicId}
            size="lg"
            className="mt-6 gap-2 px-8"
          >
            Şimdi üret <ArrowRight className="h-4 w-4" />
          </TrackedGenerateLink>
        </div>
      </section>

      {(siblings.length > 0 || family.length > 0 || topic) && (
        <section className="bg-card py-16">
          <div className="container max-w-4xl space-y-10">
            {siblings.length > 0 && (
              <div>
                <h2 className="mb-4 text-xl font-semibold text-foreground">
                  {ak.grade}. Sınıf {ak.topicName} — diğer başlıklar
                </h2>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {siblings.map((s) => (
                    <Link
                      key={s.slug}
                      href={`/calismalar/${s.topicSlug}/${s.slug}`}
                      className="rounded-lg border bg-background p-3 text-sm font-medium hover:border-primary/50 hover:text-primary"
                    >
                      {s.title}
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {family.length > 0 && (
              <div>
                <h2 className="mb-4 text-xl font-semibold text-foreground">
                  &quot;{ak.title}&quot; benzeri başlıklar diğer sınıflarda
                </h2>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {family.map((s) => (
                    <Link
                      key={`${s.topicSlug}-${s.slug}`}
                      href={`/calismalar/${s.topicSlug}/${s.slug}`}
                      className="rounded-lg border bg-background p-3 text-sm font-medium hover:border-primary/50 hover:text-primary"
                    >
                      {s.grade}. Sınıf · {s.title}
                    </Link>
                  ))}
                </div>
              </div>
            )}

            <Link
              href={`/calismalar/${ak.topicSlug}`}
              className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
            >
              ← {ak.grade}. Sınıf {ak.topicName} konusunun tüm çalışma kağıtları
            </Link>
          </div>
        </section>
      )}

      <Footer />
    </>
  );
}
