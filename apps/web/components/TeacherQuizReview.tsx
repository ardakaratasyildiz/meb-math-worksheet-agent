"use client";

import * as React from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { GraduationCap, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { QuestionCard } from "@/components/QuestionCard";
import { ShareQuizButton } from "@/components/ShareQuizButton";
import { getQuizReview, regenerateQuizQuestion } from "@/lib/api";
import type { Question, QuizReview } from "@/lib/types";

/**
 * Öğretmene ürettiği quiz'in sorularını CEVAPLI gösterir; beğenmediği soruyu tek
 * tıkla yeniden üretir (kalıcı). İsteğe bağlı "Paylaş" (link) ve "Sınıfıma ata"
 * kısayolları. Hem "Quiz oluşturuldu" ekranında hem ödev picker önizlemesinde kullanılır.
 */
export function TeacherQuizReview({
  quizId,
  showShare = true,
  showAssign = true,
}: {
  quizId: string;
  showShare?: boolean;
  showAssign?: boolean;
}) {
  const { userId } = useAuth();
  const [data, setData] = React.useState<QuizReview | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [regenNumber, setRegenNumber] = React.useState<number | null>(null);

  React.useEffect(() => {
    if (!userId) return;
    let active = true;
    setLoading(true);
    getQuizReview(quizId, userId)
      .then((d) => active && setData(d))
      .catch((e: unknown) =>
        active && setError(e instanceof Error ? e.message : "Sorular yüklenemedi."),
      )
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [quizId, userId]);

  async function handleRegenerate(q: Question) {
    if (!userId || regenNumber !== null) return;
    setRegenNumber(q.number);
    try {
      const nq = await regenerateQuizQuestion(quizId, q.number, userId);
      setData((prev) =>
        prev
          ? {
              ...prev,
              questions: prev.questions.map((x) =>
                x.number === q.number ? nq : x,
              ),
            }
          : prev,
      );
      toast.success(`${q.number}. soru yenilendi`);
    } catch (e: unknown) {
      toast.error("Soru yenilenemedi", {
        description: e instanceof Error ? e.message : undefined,
      });
    } finally {
      setRegenNumber(null);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-6 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" /> Sorular yükleniyor…
      </div>
    );
  }

  if (error || !data) {
    return (
      <Card className="p-4">
        <p className="text-sm text-destructive">{error ?? "Sorular bulunamadı."}</p>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {(showShare || showAssign) ? (
        <div className="flex flex-wrap items-center gap-2">
          {showAssign ? (
            <Button asChild size="sm" className="gap-1.5">
              <Link href="/practice/classes">
                <GraduationCap className="h-4 w-4" />
                Sınıfıma ata
              </Link>
            </Button>
          ) : null}
          {showShare ? <ShareQuizButton quizId={quizId} variant="outline" /> : null}
        </div>
      ) : null}

      <div className="space-y-3">
        {data.questions.map((q) => (
          <QuestionCard
            key={q.number}
            q={q}
            onRegenerate={() => handleRegenerate(q)}
            regenerating={regenNumber === q.number}
          />
        ))}
      </div>
    </div>
  );
}
