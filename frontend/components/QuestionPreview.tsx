"use client";

import * as React from "react";
import {
  Download,
  FileText,
  Lightbulb,
  Loader2,
  Sparkles,
  Zap,
} from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

import { downloadBlob, renderPdf } from "@/lib/api";
import { buildPdfFilename } from "@/lib/filename";
import { useGenerateStore } from "@/lib/store";
import { QuestionCard } from "./QuestionCard";

export function QuestionPreview() {
  const { status, result, error, questionCount } = useGenerateStore();

  if (status === "idle") {
    return (
      <Card className="flex h-full min-h-[400px] flex-col items-center justify-center gap-3 border-dashed p-10 text-center">
        <Sparkles className="h-10 w-10 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">
          Soldaki form parametreleri seçildikten sonra{" "}
          <strong>Üretimi başlat</strong> butonu ile üretim başlatılabilir.
        </p>
      </Card>
    );
  }

  if (status === "loading") {
    return <GeneratingState questionCount={questionCount} />;
  }

  if (status === "error") {
    return (
      <Card className="border-destructive/50 bg-destructive/5 p-6 text-sm">
        <p className="font-semibold text-destructive">Üretim başarısız</p>
        <p className="mt-1 text-muted-foreground">{error}</p>
      </Card>
    );
  }

  if (!result) return null;

  const { worksheet, metadata } = result;
  const cacheHit = metadata.trace?.cache_hit ?? false;

  async function onDownloadPdf() {
    if (!result) return;
    const t = toast.loading("PDF hazırlanıyor…");
    try {
      const blob = await renderPdf(result.worksheet);
      downloadBlob(blob, buildPdfFilename(result.worksheet.title));
      toast.success("PDF indirildi", { id: t });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Hata";
      toast.error("PDF başarısız", { id: t, description: msg });
    }
  }

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-card p-4">
        <div>
          <h2 className="text-lg font-semibold">{worksheet.title}</h2>
          <p className="text-xs text-muted-foreground">
            {worksheet.questions.length} soru · {worksheet.difficulty} zorluk · denetimden geçti
          </p>
        </div>
        <div className="flex items-center gap-2">
          {cacheHit && (
            <Badge variant="outline" className="border-primary/40 text-primary">
              <Zap className="mr-1 h-3 w-3" /> Önbellekten
            </Badge>
          )}
          <Button onClick={onDownloadPdf} className="gap-2">
            <Download className="h-4 w-4" /> PDF indir
          </Button>
        </div>
      </div>

      {/* Questions */}
      <div className="space-y-3">
        {worksheet.questions.map((q) => (
          <QuestionCard key={q.number} q={q} />
        ))}
      </div>

      {/* Answer key özeti (PDF'in cevap anahtarı sayfası gibi) */}
      <Card className="p-4">
        <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
          <FileText className="h-4 w-4" /> Cevap anahtarı
        </div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs sm:grid-cols-4">
          {worksheet.answer_key.map((a) => (
            <div key={a.number}>
              <span className="font-mono text-muted-foreground">{a.number}.</span>{" "}
              {a.answer}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

// ─── Generating state — kullanıcıya keyifli bekleme deneyimi ─────────────────

const MATH_FACTS = [
  "0! (sıfır faktöriyel) = 1'dir. Çünkü hiçbir şeyi sıralamanın tek bir yolu vardır: sıralamamak.",
  "Pisagor teoremi, Pisagor'dan 1300 yıl önce Babillilerce zaten biliniyordu — ama isim ona kaldı.",
  "Gauss 9 yaşındayken öğretmeni \"1'den 100'e kadar topla\" dedi. 30 saniyede 5050'yi söyledi — formülü kendi keşfetti.",
  "\"Algoritma\" kelimesi, 9. yüzyıl matematikçisi El-Harezmi'nin Latince adı \"Algoritmi\"den gelir.",
  "Bal arıları peteklerini altıgen yapar — çünkü altıgen, eşit alan için en az malzeme kullanan şekildir.",
  "Sonsuzluk simgesi ∞, John Wallis tarafından 1655'te icat edildi — Roma rakamı M (1000) şeklinin değişimi olabilir.",
  "Pi günü 14 Mart'tır (3.14) ve Albert Einstein'ın doğum günüyle aynı tarih.",
  "Bir A4 kâğıdı insan gücüyle en fazla 7 kez katlanabilir; 8.'sinde fizik durdurur.",
  "2 hariç tüm asal sayılar tektir — çünkü çift sayı zaten 2'ye bölünür.",
  "Fibonacci dizisi (1, 1, 2, 3, 5, 8...) ayçiçeği tohumlarında, deniz kabuğunda, kelebek kanadında doğal olarak çıkar.",
  "Sıfır sayısını matematiksel olarak ilk tanımlayan kişi Hint matematikçi Brahmagupta'dır (7. yüzyıl).",
  "Bir küpün 8 köşesi, 12 kenarı, 6 yüzü vardır. Köşe − Kenar + Yüz = 2 — Euler'in tüm konvex çokyüzlülerde geçerli formülü.",
  "Saniyede 1 sayma hızıyla 1 milyon sayısına 11.5 günde, 1 milyara ise 31.7 yılda ulaşırsın.",
  "0 sayısı çiftdir — 2'ye tam bölünür ve çift sayıların tüm tanımlarını sağlar.",
];

function GeneratingState({ questionCount }: { questionCount: number }) {
  const [factIndex, setFactIndex] = React.useState(() =>
    Math.floor(Math.random() * MATH_FACTS.length),
  );
  const [elapsed, setElapsed] = React.useState(0);

  React.useEffect(() => {
    const factTimer = setInterval(() => {
      setFactIndex((i) => (i + 1) % MATH_FACTS.length);
    }, 6000);
    const tickTimer = setInterval(() => {
      setElapsed((e) => e + 1);
    }, 1000);
    return () => {
      clearInterval(factTimer);
      clearInterval(tickTimer);
    };
  }, []);

  const phase = elapsed < 8
    ? "Sorular üretiliyor"
    : elapsed < 18
      ? "Aritmetik denetimi yapılıyor"
      : elapsed < 28
        ? "Kazanım uyumu denetleniyor"
        : "Çalışma kağıdı hazırlanıyor";

  // 30sn'de %92'ye, 60sn'de %98'e ulaş — hiç %100 olmasın (yanıltıcı olmasın).
  const progress = Math.min(98, Math.round((1 - Math.exp(-elapsed / 14)) * 100));
  const eta = Math.max(0, 30 - elapsed);

  return (
    <div className="space-y-4">
      <Card className="overflow-hidden p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-foreground">{phase}</p>
            <p className="text-xs text-muted-foreground">
              {questionCount} soruluk çalışma kağıdı hazırlanıyor
              {eta > 0 ? ` · ~${eta} sn` : " · birazdan..."}
            </p>
          </div>
        </div>

        <div className="mt-5 h-1.5 overflow-hidden rounded-full bg-muted">
          <div
            className="h-full bg-gradient-to-r from-primary to-indigo-400 transition-all duration-1000 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>

        <div className="mt-6 flex items-start gap-3 rounded-xl border bg-accent/40 p-4">
          <Lightbulb className="mt-0.5 h-5 w-5 flex-shrink-0 text-primary" />
          <div className="min-w-0 flex-1">
            <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-primary">
              Bunu biliyor muydun?
            </p>
            <p
              key={factIndex}
              className="animate-fade-in text-sm leading-relaxed text-foreground"
            >
              {MATH_FACTS[factIndex]}
            </p>
          </div>
        </div>
      </Card>

      {/* Spatial intuition: gelecek soruların hayaleti — 3 ufak iskelet yeter */}
      {Array.from({ length: Math.min(3, questionCount) }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}

function SkeletonCard() {
  return (
    <Card className="space-y-3 p-5">
      <div className="flex items-center gap-2">
        <Skeleton className="h-8 w-8 rounded-full" />
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-4 w-16" />
      </div>
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-5/6" />
      <Skeleton className="h-4 w-4/6" />
    </Card>
  );
}
