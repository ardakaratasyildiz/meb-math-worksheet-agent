"use client";

import * as React from "react";
import { SignUpButton, useAuth } from "@clerk/nextjs";
import {
  Download,
  FileText,
  Lightbulb,
  Loader2,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ShareButton } from "@/components/ShareButton";

import { track } from "@/lib/analytics";
import { downloadBlob, regenerateQuestion, renderPdf } from "@/lib/api";
import { buildPdfFilename } from "@/lib/filename";
import { MATH_FACTS } from "@/lib/mathFacts";
import { useGenerateStore } from "@/lib/store";
import type { Question } from "@/lib/types";
import { QuestionCard } from "./QuestionCard";

export function QuestionPreview() {
  const {
    status,
    result,
    error,
    questionCount,
    streamedCount,
    includeAnswerKey,
    includeSolutions,
    brandName,
    brandSubtitle,
    brandLogo,
    replaceQuestion,
  } = useGenerateStore();

  const { userId } = useAuth();
  const [regenNumber, setRegenNumber] = React.useState<number | null>(null);

  // Üretim başlatıldığında (idle → loading veya success → loading) preview
  // alanını otomatik görüntüye kaydır — form'un altında olduğu için kullanıcı
  // ekranı kaydırmak zorunda kalmasın. Aynı blok success/error geçişlerini de
  // yumuşatır (ör. cache hit anında sonuç direkt görünür).
  const rootRef = React.useRef<HTMLDivElement>(null);
  React.useEffect(() => {
    if (status === "idle") return;
    // bir tick beklet — DOM güncellensin (loading state'in skeleton'ları)
    const id = window.requestAnimationFrame(() => {
      rootRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    return () => window.cancelAnimationFrame(id);
  }, [status]);

  if (status === "idle") {
    return (
      <div ref={rootRef}>
        <Card className="flex min-h-[280px] flex-col items-center justify-center gap-3 border-dashed p-10 text-center">
          <Sparkles className="h-10 w-10 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            Yukarıdaki parametreleri seçip{" "}
            <strong>Üretimi başlat</strong> butonuna basın. Sonuç bu alanda
            görünecek.
          </p>
        </Card>
      </div>
    );
  }

  if (status === "loading") {
    return (
      <div ref={rootRef}>
        <GeneratingState
          questionCount={questionCount}
          streamedCount={streamedCount}
        />
      </div>
    );
  }

  if (status === "error") {
    return (
      <div ref={rootRef}>
        <Card className="border-destructive/50 bg-destructive/5 p-6 text-sm">
          <p className="font-semibold text-destructive">Üretim başarısız</p>
          <p className="mt-1 text-muted-foreground">{error}</p>
        </Card>
      </div>
    );
  }

  if (!result) return null;

  const { worksheet } = result;

  async function onDownloadPdf() {
    if (!result) return;
    const t = toast.loading("PDF hazırlanıyor…");
    try {
      const blob = await renderPdf(result.worksheet, {
        include_answer_key: includeAnswerKey,
        include_solutions: includeSolutions,
        brand_name: brandName,
        brand_subtitle: brandSubtitle,
        brand_logo: brandLogo,
      });
      downloadBlob(blob, buildPdfFilename(result.worksheet.title));
      // Funnel sonu — kullanıcının somut çıktıyı aldığı an (paylaşım/viral döngü
      // başlangıcı). grade/topic ile hangi içeriğin değer ürettiği görülür.
      track("pdf_download", {
        grade: result.worksheet.grade,
        topic: result.worksheet.topic,
        question_count: result.worksheet.questions.length,
        include_answer_key: includeAnswerKey,
        include_solutions: includeSolutions,
      });
      toast.success("PDF indirildi", { id: t });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Hata";
      toast.error("PDF başarısız", { id: t, description: msg });
    }
  }

  async function handleRegenerate(q: Question) {
    if (!userId) {
      toast.error("Oturum bilgisi henüz yüklenmedi");
      return;
    }
    setRegenNumber(q.number);
    try {
      const nq = await regenerateQuestion({
        grade: worksheet.grade,
        kazanim_kod: q.kazanim_kod,
        difficulty: worksheet.difficulty,
        question_type: q.question_type,
        tenant_id: userId,
      });
      replaceQuestion(q.number, nq);
      track("question_regenerate", {
        grade: worksheet.grade,
        kazanim_kod: q.kazanim_kod,
        question_type: q.question_type,
      });
      toast.success(`${q.number}. soru yenilendi`);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Hata";
      toast.error("Soru yenilenemedi", { description: msg });
    } finally {
      setRegenNumber(null);
    }
  }

  return (
    <div ref={rootRef} className="space-y-3">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-card p-4">
        <div>
          <h2 className="text-lg font-semibold">{worksheet.title}</h2>
          <p className="text-xs text-muted-foreground">
            {worksheet.questions.length} soru · {worksheet.difficulty} zorluk · denetimden geçti
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ShareButton />
          {userId ? (
            <Button onClick={onDownloadPdf} className="gap-2">
              <Download className="h-4 w-4" /> PDF indir
            </Button>
          ) : (
            // Anonim: değeri (sorular + cevap anahtarı) gördü; PDF üyelik kapısında.
            // Clerk modal sayfadan çıkmadan açılır → üretilen kağıt korunur; üyelik
            // bitince userId dolar, buton "PDF indir"e döner.
            <SignUpButton mode="modal">
              <Button
                className="gap-2"
                onClick={() =>
                  track("download_signup_gate", {
                    grade: worksheet.grade,
                    topic: worksheet.topic,
                  })
                }
              >
                <Download className="h-4 w-4" /> Üye ol ve PDF indir
              </Button>
            </SignUpButton>
          )}
        </div>
      </div>

      {/* Questions */}
      <div className="space-y-3">
        {worksheet.questions.map((q) => (
          <QuestionCard
            key={q.number}
            q={q}
            onRegenerate={() => handleRegenerate(q)}
            regenerating={regenNumber === q.number}
          />
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
// Matematik bilgileri @/lib/mathFacts'ten (PDF + quiz üretiminde ortak).

function GeneratingState({
  questionCount,
  streamedCount,
}: {
  questionCount: number;
  streamedCount: number;
}) {
  const [factIndex, setFactIndex] = React.useState(() =>
    Math.floor(Math.random() * MATH_FACTS.length),
  );
  const [elapsed, setElapsed] = React.useState(0);

  React.useEffect(() => {
    const factTimer = setInterval(() => {
      setFactIndex((i) => (i + 1) % MATH_FACTS.length);
    }, 11000);
    const tickTimer = setInterval(() => {
      setElapsed((e) => e + 1);
    }, 1000);
    return () => {
      clearInterval(factTimer);
      clearInterval(tickTimer);
    };
  }, []);

  // Backend soruları üretim BİTTİKTEN sonra teker teker akıtır; ilk soru
  // event'i geldiğinde ağır iş tamam demektir → gerçek sayaca geç.
  const streaming = streamedCount > 0;

  const phase = streaming
    ? "Sorular geliyor"
    : elapsed < 8
      ? "Sorular üretiliyor"
      : elapsed < 18
        ? "Aritmetik denetimi yapılıyor"
        : elapsed < 28
          ? "Kazanım uyumu denetleniyor"
          : "Çalışma kağıdı hazırlanıyor";

  // Akış başladıysa gerçek ilerleme (gelen soru / hedef); değilse zaman-tabanlı
  // tahmin (30sn→%92, 60sn→%98). Hiçbir durumda %100 gösterme — yanıltıcı olmasın.
  const progress = streaming
    ? Math.min(99, Math.round((streamedCount / Math.max(1, questionCount)) * 100))
    : Math.min(98, Math.round((1 - Math.exp(-elapsed / 14)) * 100));
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
              {streaming
                ? `${streamedCount} / ${questionCount} soru hazır`
                : `${questionCount} soruluk çalışma kağıdı hazırlanıyor${
                    eta > 0 ? ` · ~${eta} sn` : " · birazdan..."
                  }`}
            </p>
          </div>
        </div>

        <div className="mt-5 h-1.5 overflow-hidden rounded-full bg-muted">
          <div
            className="h-full bg-gradient-to-r from-primary to-coral transition-all duration-1000 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>

        <div className="mt-6 flex items-start gap-3 rounded-xl border bg-accent/40 p-4">
          <Lightbulb className="mt-0.5 h-5 w-5 flex-shrink-0 text-primary" />
          <div className="min-w-0 flex-1">
            <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-primary">
              Bunu biliyor muydun? 🤔
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
