"use client";

import * as React from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { Check, Loader2, Sparkles, X } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { MarkdownQuestion } from "@/components/MarkdownQuestion";

import { getQuiz, submitAttempt } from "@/lib/api";
import type {
  AttemptResult,
  QuestionResult,
  QuizPublic,
  SolutionStep,
  SubmittedAnswer,
} from "@/lib/types";

interface AnswerState {
  selectedIndex?: number;
  boolAnswer?: boolean;
  texts?: string[];
}

const OPTION_LETTERS = ["A", "B", "C", "D", "E"];

// MCQ soru metni şıkları gömülü içerebilir ("... A) 4 B) 5"). Radio butonlarla
// tekrar göstermemek için, en az 2 şık işareti varsa metni ilk işaretten keser.
function stripInlineOptions(text: string): string {
  const marker = /\s+[A-E]\s*[\)\.]\s+/g;
  const matches = text.match(marker);
  if (!matches || matches.length < 2) return text;
  const idx = text.search(/\s+[A-E]\s*[\)\.]\s+/);
  return idx > 0 ? text.slice(0, idx).trim() : text;
}

function SolutionView({
  steps,
}: {
  steps: string | SolutionStep[];
}) {
  if (typeof steps === "string") {
    if (!steps.trim()) return null;
    return (
      <div className="mt-2 rounded-md bg-muted/50 p-3 text-xs">
        <MarkdownQuestion text={steps} />
      </div>
    );
  }
  if (!steps.length) return null;
  return (
    <ol className="mt-2 space-y-1 rounded-md bg-muted/50 p-3 text-xs">
      {steps.map((s) => (
        <li key={s.step_no} className="flex gap-2">
          <span className="font-medium text-muted-foreground">{s.step_no}.</span>
          <span>
            {s.description}
            {s.computation ? (
              <span className="ml-1 font-mono text-primary">{s.computation}</span>
            ) : null}
          </span>
        </li>
      ))}
    </ol>
  );
}

export function QuizSolver({ quizId }: { quizId: string }) {
  const { userId, isLoaded } = useAuth();

  const [quiz, setQuiz] = React.useState<QuizPublic | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [loadError, setLoadError] = React.useState<string | null>(null);
  const [answers, setAnswers] = React.useState<Record<number, AnswerState>>({});
  const [submitting, setSubmitting] = React.useState(false);
  const [result, setResult] = React.useState<AttemptResult | null>(null);
  const startedAtRef = React.useRef<number>(0);

  React.useEffect(() => {
    if (!isLoaded) return;
    if (!userId) {
      setLoadError("Oturum bulunamadı.");
      setLoading(false);
      return;
    }
    let active = true;
    setLoading(true);
    getQuiz(quizId, userId)
      .then((q) => {
        if (!active) return;
        setQuiz(q);
        startedAtRef.current = Date.now();
      })
      .catch((e: unknown) => {
        if (!active) return;
        setLoadError(e instanceof Error ? e.message : "Quiz yüklenemedi.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [quizId, userId, isLoaded]);

  function setAnswer(num: number, patch: AnswerState) {
    setAnswers((prev) => ({ ...prev, [num]: { ...prev[num], ...patch } }));
  }

  async function onSubmit() {
    if (!quiz || !userId) return;
    const payload: SubmittedAnswer[] = quiz.questions.map((q) => {
      const a = answers[q.number] ?? {};
      return {
        number: q.number,
        selected_index: a.selectedIndex ?? null,
        bool_answer: a.boolAnswer ?? null,
        texts: a.texts ?? null,
      };
    });
    setSubmitting(true);
    try {
      const duration = Math.round((Date.now() - startedAtRef.current) / 1000);
      const res = await submitAttempt(quiz.id, {
        tenant_id: userId,
        answers: payload,
        duration_seconds: duration,
      });
      setResult(res);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Bilinmeyen hata";
      toast.error("Cevaplar gönderilemedi", { description: msg });
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
        Quiz yükleniyor…
      </div>
    );
  }

  if (loadError || !quiz) {
    return (
      <Card className="p-6">
        <p className="text-sm text-destructive">
          {loadError ?? "Quiz bulunamadı."}
        </p>
        <Button asChild variant="outline" size="sm" className="mt-3">
          <Link href="/coz">Çöz & Geliş&apos;e dön</Link>
        </Button>
      </Card>
    );
  }

  if (result) {
    return <ResultsView quiz={quiz} result={result} />;
  }

  const answeredCount = quiz.questions.filter((q) => {
    const a = answers[q.number];
    if (!a) return false;
    return (
      a.selectedIndex !== undefined ||
      a.boolAnswer !== undefined ||
      (a.texts?.some((t) => t.trim()) ?? false)
    );
  }).length;

  return (
    <div className="space-y-5">
      <ol className="space-y-4">
        {quiz.questions.map((q) => {
          const a = answers[q.number] ?? {};
          return (
            <Card key={q.number} className="space-y-3 p-5">
              <div className="flex items-start gap-2">
                <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                  {q.number}
                </span>
                <div className="min-w-0 flex-1">
                  <MarkdownQuestion
                    text={
                      q.question_type === "coktan_secmeli" && q.options?.length
                        ? stripInlineOptions(q.question)
                        : q.question
                    }
                  />
                </div>
              </div>

              {/* Çoktan seçmeli */}
              {q.question_type === "coktan_secmeli" && q.options ? (
                <div className="grid gap-2 pl-8">
                  {q.options.map((opt, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => setAnswer(q.number, { selectedIndex: i })}
                      className={`flex items-center gap-2 rounded-md border px-3 py-2 text-left text-sm transition-colors hover:bg-accent/30 ${
                        a.selectedIndex === i
                          ? "border-primary bg-accent/30"
                          : ""
                      }`}
                    >
                      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-xs font-medium">
                        {OPTION_LETTERS[i] ?? i + 1}
                      </span>
                      <span>{opt}</span>
                    </button>
                  ))}
                </div>
              ) : null}

              {/* Doğru / Yanlış */}
              {q.question_type === "dogru_yanlis" ? (
                <div className="flex gap-2 pl-8">
                  <Button
                    type="button"
                    variant={a.boolAnswer === true ? "default" : "outline"}
                    size="sm"
                    onClick={() => setAnswer(q.number, { boolAnswer: true })}
                  >
                    Doğru
                  </Button>
                  <Button
                    type="button"
                    variant={a.boolAnswer === false ? "default" : "outline"}
                    size="sm"
                    onClick={() => setAnswer(q.number, { boolAnswer: false })}
                  >
                    Yanlış
                  </Button>
                </div>
              ) : null}

              {/* Boşluk doldurma */}
              {q.question_type === "bosluk_doldurma" ? (
                <div className="grid gap-2 pl-8 sm:grid-cols-2">
                  {Array.from({ length: q.blank_count ?? 1 }).map((_, i) => (
                    <Input
                      key={i}
                      placeholder={
                        (q.blank_count ?? 1) > 1
                          ? `${i + 1}. boşluk`
                          : "Cevabınız"
                      }
                      value={a.texts?.[i] ?? ""}
                      onChange={(e) => {
                        const texts = [...(a.texts ?? [])];
                        texts[i] = e.target.value;
                        setAnswer(q.number, { texts });
                      }}
                    />
                  ))}
                </div>
              ) : null}

              {/* Salt işlem (sayısal) */}
              {q.question_type === "salt_islem" ? (
                <div className="pl-8 sm:max-w-xs">
                  <Input
                    placeholder="Sonuç (ör. 3/4 veya 0,75)"
                    value={a.texts?.[0] ?? ""}
                    onChange={(e) =>
                      setAnswer(q.number, { texts: [e.target.value] })
                    }
                  />
                </div>
              ) : null}
            </Card>
          );
        })}
      </ol>

      <div className="sticky bottom-4 flex items-center justify-between gap-3 rounded-lg border bg-background/90 p-3 shadow-sm backdrop-blur">
        <span className="text-sm text-muted-foreground">
          {answeredCount}/{quiz.questions.length} cevaplandı
        </span>
        <Button onClick={onSubmit} disabled={submitting} className="gap-2">
          {submitting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Puanlanıyor…
            </>
          ) : (
            "Cevapları gönder"
          )}
        </Button>
      </div>
    </div>
  );
}

function ResultsView({
  quiz,
  result,
}: {
  quiz: QuizPublic;
  result: AttemptResult;
}) {
  const pct = result.total
    ? Math.round((result.score / result.total) * 100)
    : 0;
  const byNumber = new Map<number, QuestionResult>(
    result.results.map((r): [number, QuestionResult] => [r.number, r]),
  );

  return (
    <div className="space-y-6">
      <Card className="space-y-3 p-6 text-center">
        <p className="text-sm text-muted-foreground">{quiz.title}</p>
        <p className="text-4xl font-bold tabular-nums">
          {result.score}
          <span className="text-2xl text-muted-foreground">/{result.total}</span>
        </p>
        <p className="text-sm font-medium">
          %{pct} doğru
          {result.duration_seconds != null
            ? ` · ${result.duration_seconds} sn`
            : ""}
        </p>
      </Card>

      {result.per_kazanim.length ? (
        <Card className="space-y-3 p-5">
          <h2 className="text-sm font-semibold">Kazanım kırılımı</h2>
          <div className="space-y-2">
            {result.per_kazanim.map((k) => {
              const kpct = k.total ? Math.round((k.correct / k.total) * 100) : 0;
              return (
                <div key={k.kazanim_kod} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono text-primary">{k.kazanim_kod}</span>
                    <span className="tabular-nums text-muted-foreground">
                      {k.correct}/{k.total}
                    </span>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                    <div
                      className={`h-full ${kpct >= 60 ? "bg-emerald-500" : "bg-amber-500"}`}
                      style={{ width: `${kpct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      ) : null}

      <ol className="space-y-3">
        {quiz.questions.map((q) => {
          const r = byNumber.get(q.number);
          const correct = r?.is_correct ?? false;
          return (
            <Card key={q.number} className="space-y-2 p-5">
              <div className="flex items-start gap-2">
                <span
                  className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-white ${
                    correct ? "bg-emerald-500" : "bg-red-500"
                  }`}
                >
                  {correct ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    <X className="h-4 w-4" />
                  )}
                </span>
                <div className="min-w-0 flex-1">
                  <MarkdownQuestion text={q.question} />
                </div>
              </div>
              {r ? (
                <div className="pl-8 text-sm">
                  <Badge variant={correct ? "secondary" : "outline"}>
                    Doğru cevap: {r.correct_answer}
                  </Badge>
                  <SolutionView steps={r.solution_steps} />
                </div>
              ) : null}
            </Card>
          );
        })}
      </ol>

      <div className="flex flex-wrap gap-3">
        <Button asChild className="gap-2">
          <Link href="/coz/yeni">
            <Sparkles className="h-4 w-4" />
            Yeni quiz çöz
          </Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/coz">Çöz &amp; Geliş&apos;e dön</Link>
        </Button>
      </div>
    </div>
  );
}
