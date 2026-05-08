"use client";

import * as React from "react";
import { Download, FileText, Sparkles, Zap } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

import { downloadBlob, renderPdf } from "@/lib/api";
import { useGenerateStore } from "@/lib/store";
import { QuestionCard } from "./QuestionCard";

export function QuestionPreview() {
  const { status, result, error, questionCount } = useGenerateStore();

  if (status === "idle") {
    return (
      <Card className="flex h-full min-h-[400px] flex-col items-center justify-center gap-3 border-dashed p-10 text-center">
        <Sparkles className="h-10 w-10 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">
          Soldan parametreleri seç ve <strong>Üret</strong> butonuna bas.
        </p>
      </Card>
    );
  }

  if (status === "loading") {
    return (
      <div className="space-y-3">
        <PreviewHeaderSkeleton />
        {Array.from({ length: questionCount }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
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
  const cost = metadata.trace?.estimated_cost_usd ?? 0;

  async function onDownloadPdf() {
    if (!result) return;
    const t = toast.loading("PDF hazırlanıyor…");
    try {
      const blob = await renderPdf(result.worksheet);
      const safe = result.worksheet.title
        .replace(/\s+/g, "_")
        .replace(/[^\w_-]/g, "");
      downloadBlob(blob, `${safe || "worksheet"}.pdf`);
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
            {worksheet.questions.length} soru · {worksheet.difficulty} · {metadata.model}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {cacheHit ? (
            <Badge variant="outline" className="border-primary/40 text-primary">
              <Zap className="mr-1 h-3 w-3" /> Cache hit
            </Badge>
          ) : (
            <Badge variant="outline" className="text-muted-foreground">
              ~${cost.toFixed(4)}
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

function PreviewHeaderSkeleton() {
  return (
    <div className="flex items-center justify-between gap-3 rounded-lg border bg-card p-4">
      <div className="space-y-2">
        <Skeleton className="h-5 w-64" />
        <Skeleton className="h-3 w-40" />
      </div>
      <Skeleton className="h-9 w-28" />
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
