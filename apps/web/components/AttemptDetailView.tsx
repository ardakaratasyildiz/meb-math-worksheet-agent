"use client";

import * as React from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { ArrowLeft, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ScoreRing } from "@/components/ScoreRing";
import { QuestionReview } from "@/components/QuestionReview";

import { getMyAttempt } from "@/lib/api";
import type { AttemptDetail } from "@/lib/types";

export function AttemptDetailView({ attemptId }: { attemptId: string }) {
  const { userId, isLoaded } = useAuth();
  const [detail, setDetail] = React.useState<AttemptDetail | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!isLoaded) return;
    if (!userId) {
      setError("Oturum bulunamadı.");
      setLoading(false);
      return;
    }
    let active = true;
    setLoading(true);
    getMyAttempt(attemptId, userId)
      .then((d) => {
        if (active) setDetail(d);
      })
      .catch((e: unknown) => {
        if (!active) return;
        const msg = e instanceof Error ? e.message : "Deneme alınamadı.";
        setError(msg);
        toast.error("Deneme yüklenemedi", { description: msg });
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [attemptId, userId, isLoaded]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
        Deneme yükleniyor…
      </div>
    );
  }

  if (error || !detail) {
    return (
      <Card className="p-6">
        <p className="text-sm text-destructive">{error ?? "Deneme bulunamadı."}</p>
        <Button asChild variant="outline" size="sm" className="mt-3">
          <Link href="/practice/history">Geçmişe dön</Link>
        </Button>
      </Card>
    );
  }

  const pct = detail.total
    ? Math.round((detail.score / detail.total) * 100)
    : 0;

  return (
    <div className="space-y-6">
      <Link
        href="/practice/history"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Geçmiş quizlerim
      </Link>

      <Card className="flex items-center gap-4 p-6">
        <ScoreRing pct={pct} label="doğru" />
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">{detail.title}</p>
          <p className="text-2xl font-bold tabular-nums">
            {detail.score}
            <span className="text-lg text-muted-foreground">/{detail.total}</span>{" "}
            <span className="text-base font-normal text-muted-foreground">
              doğru
            </span>
          </p>
          {detail.duration_seconds != null ? (
            <p className="text-xs text-muted-foreground">
              {detail.duration_seconds} sn
            </p>
          ) : null}
        </div>
      </Card>

      {detail.has_detail ? (
        <ol className="space-y-3">
          {detail.review.map((item) => (
            <Card key={item.number} className="p-5">
              <QuestionReview
                number={item.number}
                question={item.question}
                questionType={item.question_type}
                options={item.options}
                isCorrect={item.is_correct}
                correctAnswer={item.correct_answer}
                solutionSteps={item.solution_steps}
                submitted={item.submitted}
              />
            </Card>
          ))}
        </ol>
      ) : (
        <Card className="p-5 text-sm text-muted-foreground">
          Bu eski deneme için soru detayı saklanmadı; yalnızca skor gösteriliyor.
        </Card>
      )}
    </div>
  );
}
