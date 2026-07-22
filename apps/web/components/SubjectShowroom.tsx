"use client";

import * as React from "react";
import Link from "next/link";
import { ArrowRight, CheckCircle2, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { SectionHeader } from "@/components/PageHeader";
import { availableSubjects, subjectStyle } from "@/lib/subjects";
import { SUBJECT_SHOWCASE } from "@/lib/subject-showcase";
import type { Subject } from "@/lib/types";

/**
 * Ders vitrini (sekmeli showroom) — ana sayfada matematik dışı ders(ler) açıkken
 * gösterilir. Bir ders seç → o dersin GERÇEK üretime hizalı örnek sorusu canlı
 * görünür. Renk kodlaması tüm uygulamayla ortak (lib/subjects → subjectStyle).
 *
 * Yalnız tek ders (matematik) açıksa hiç render edilmez → ana sayfa mevcut
 * math-only Showroom'u gösterir (page.tsx bu ayrımı yapar).
 */
export function SubjectShowroom() {
  const subjects = availableSubjects();
  const [active, setActive] = React.useState<Subject>(
    subjects[0]?.value ?? "matematik",
  );
  // Aktif dersin gösterilen örnek indeksi — "başka örnek" ile döner.
  const [idx, setIdx] = React.useState(0);

  const examples = SUBJECT_SHOWCASE[active] ?? [];
  const q = examples[idx] ?? examples[0];
  const st = subjectStyle(active);

  function selectSubject(value: Subject) {
    setActive(value);
    setIdx(0); // ders değişince ilk örnekten başla
  }

  if (!q) return null; // güvenlik (her derste örnek var; TS strict için)

  return (
    <section id="dersler" className="py-20">
      <div className="container max-w-4xl">
        <SectionHeader
          eyebrow="Gerçek çıktı"
          title="Dersini seç, ürettiğimiz soruları gör"
          body="Sistemin her ders için ürettiği sorulardan bir kesittir. Hazırlanan PDF'te ayrıca cevap anahtarı ve adım adım çözüm yer alır."
        />

        {/* Ders sekmeleri */}
        <div
          role="tablist"
          aria-label="Ders seç"
          className="mt-10 flex flex-wrap justify-center gap-2.5"
        >
          {subjects.map((s) => {
            const sst = subjectStyle(s.value);
            const on = s.value === active;
            return (
              <button
                key={s.value}
                type="button"
                role="tab"
                aria-selected={on}
                onClick={() => selectSubject(s.value)}
                className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold transition-colors ${
                  on
                    ? `${sst.bg} ${sst.text} ${sst.border}`
                    : "border-border bg-card text-muted-foreground hover:bg-accent/40"
                }`}
              >
                <span aria-hidden>{sst.emoji}</span>
                {s.label}
              </button>
            );
          })}
        </div>

        {/* Aktif dersin örnek soru kartı */}
        <div className="mt-8">
          <div
            className={`mx-auto max-w-2xl rounded-2xl border-l-4 bg-card p-6 shadow-pop sm:p-7 ${st.border}`}
          >
            <div className="flex flex-wrap items-center gap-2 text-xs font-bold">
              <span className={`inline-flex items-center gap-1.5 ${st.text}`}>
                <span aria-hidden className="text-sm">
                  {st.emoji}
                </span>
                {q.gradeLabel}
              </span>
              <span className="text-muted-foreground">·</span>
              <span className="text-muted-foreground">{q.topic}</span>
              <span
                className={`ml-auto rounded-full px-2.5 py-1 font-mono text-[10px] ${st.bg} ${st.text}`}
              >
                {q.kazanim}
              </span>
            </div>

            <p className="mt-4 text-base leading-relaxed text-foreground">
              {q.question}
            </p>

            {q.options ? (
              <div className="mt-4 grid gap-2 sm:grid-cols-2">
                {q.options.map((opt) => (
                  <div
                    key={opt}
                    className="rounded-lg border bg-background/60 px-3 py-2 text-sm text-foreground"
                  >
                    {opt}
                  </div>
                ))}
              </div>
            ) : null}

            <details className="group mt-4">
              <summary
                className={`cursor-pointer list-none text-sm font-semibold hover:underline ${st.text}`}
              >
                Cevabı göster
              </summary>
              <p className="mt-2 flex items-start gap-2 rounded-md bg-accent/40 p-3 text-sm text-foreground">
                <CheckCircle2
                  className={`mt-0.5 h-4 w-4 flex-shrink-0 ${st.text}`}
                />
                {q.answer}
              </p>
            </details>
          </div>
        </div>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          {examples.length > 1 ? (
            <Button
              type="button"
              variant="outline"
              size="lg"
              className="gap-2"
              onClick={() => setIdx((i) => (i + 1) % examples.length)}
            >
              <RefreshCw className="h-4 w-4" /> Başka örnek
            </Button>
          ) : null}
          <Button asChild size="lg" className="gap-2 px-7">
            <Link
              href={
                active === "matematik"
                  ? "/generate"
                  : `/generate?subject=${active}`
              }
            >
              {subjectStyle(active).emoji} Bu derste üret{" "}
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </section>
  );
}
