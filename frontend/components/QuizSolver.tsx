"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { FileText, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { MarkdownQuestion } from "@/components/MarkdownQuestion";
import { ScoreRing } from "@/components/ScoreRing";
import {
  OPTION_LETTERS,
  QuestionReview,
  stripInlineOptions,
} from "@/components/QuestionReview";

import { getQuiz, submitAttempt } from "@/lib/api";
import { findKazanimByKod, practiceHref, rollupByTopic } from "@/lib/curriculum";
import { useGenerateStore } from "@/lib/store";
import type {
  AttemptResult,
  QuestionResult,
  QuizPublic,
  SubmittedAnswer,
} from "@/lib/types";

interface AnswerState {
  selectedIndex?: number;
  boolAnswer?: boolean;
  texts?: string[];
}

export function QuizSolver({ quizId }: { quizId: string }) {
  const { userId, isLoaded } = useAuth();

  const [quiz, setQuiz] = React.useState<QuizPublic | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [loadError, setLoadError] = React.useState<string | null>(null);
  const [answers, setAnswers] = React.useState<Record<number, AnswerState>>({});
  const [submitting, setSubmitting] = React.useState(false);
  const [result, setResult] = React.useState<AttemptResult | null>(null);
  const [submittedPayload, setSubmittedPayload] = React.useState<
    SubmittedAnswer[]
  >([]);
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
      setSubmittedPayload(payload);
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
    return (
      <ResultsView quiz={quiz} result={result} submitted={submittedPayload} />
    );
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
  submitted,
}: {
  quiz: QuizPublic;
  result: AttemptResult;
  submitted: SubmittedAnswer[];
}) {
  const pct = result.total
    ? Math.round((result.score / result.total) * 100)
    : 0;
  const byNumber = new Map<number, QuestionResult>(
    result.results.map((r): [number, QuestionResult] => [r.number, r]),
  );
  const submittedByNumber = new Map<number, SubmittedAnswer>(
    submitted.map((s): [number, SubmittedAnswer] => [s.number, s]),
  );

  const router = useRouter();
  const setForm = useGenerateStore((s) => s.setForm);

  // Kazanım kodları yerine KONU bazında kırılım (anlaşılırlık).
  const topics = rollupByTopic(result.per_kazanim).sort((a, b) => a.ratio - b.ratio);
  const wrongCount = result.total - result.score;
  // Bu quiz'te en çok zorlanılan konu(lar) — "neyi yanlış yaptın" özeti.
  const weakTopics = topics.filter((t) => t.ratio < 1 && t.total > 0);

  // En zayıf kazanım (eksik olan) — hedefli aksiyonlar için. Mükemmel skorda null.
  const weakest = [...result.per_kazanim]
    .filter((k) => k.total > 0)
    .sort(
      (a, b) => a.correct / a.total - b.correct / b.total || b.total - a.total,
    )[0];
  const weakestKod =
    weakest && weakest.correct < weakest.total ? weakest.kazanim_kod : null;

  function onCreateWorksheet() {
    // Çöz→PDF köprüsü: zayıf konuyu PDF üreticiye ön-doldur (Zustand deseni).
    const info = weakestKod ? findKazanimByKod(weakestKod) : null;
    setForm({
      grade: quiz.grade,
      topicId: info?.topicId ?? quiz.topic_id,
      kazanimKod: weakestKod ?? null,
      difficulty: quiz.difficulty,
    });
    router.push("/generate");
  }

  return (
    <div className="space-y-6">
      {/* Skor halkası + özet */}
      <Card className="flex flex-col items-center gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <ScoreRing pct={pct} label="doğru" />
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">{quiz.title}</p>
            <p className="text-2xl font-bold tabular-nums">
              {result.score}
              <span className="text-lg text-muted-foreground">
                /{result.total}
              </span>{" "}
              <span className="text-base font-normal text-muted-foreground">
                doğru
              </span>
            </p>
            <p className="text-xs text-muted-foreground">
              {wrongCount} yanlış
              {result.duration_seconds != null
                ? ` · ${result.duration_seconds} sn`
                : ""}
            </p>
          </div>
        </div>
        {weakTopics.length ? (
          <div className="w-full max-w-xs rounded-md bg-amber-50 p-3 text-xs dark:bg-amber-950/30 sm:w-auto">
            <p className="font-medium text-amber-700 dark:text-amber-400">
              En çok zorlandığın:
            </p>
            <p className="mt-0.5 text-amber-700/90 dark:text-amber-400/90">
              {weakTopics
                .slice(0, 2)
                .map((t) => `${t.topicName} (${t.correct}/${t.total})`)
                .join(", ")}
            </p>
          </div>
        ) : null}
      </Card>

      {/* Konu bazlı kırılım */}
      {topics.length ? (
        <Card className="space-y-3 p-5">
          <h2 className="text-sm font-semibold">Konu bazında</h2>
          <div className="space-y-2.5">
            {topics.map((t) => {
              const tpct = Math.round(t.ratio * 100);
              return (
                <div key={t.topicId} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium">{t.topicName}</span>
                    <span className="tabular-nums text-muted-foreground">
                      {t.correct}/{t.total} · %{tpct}
                    </span>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                    <div
                      className={`h-full ${tpct >= 60 ? "bg-emerald-500" : "bg-amber-500"}`}
                      style={{ width: `${tpct}%` }}
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
          if (!r) return null;
          return (
            <Card key={q.number} className="p-5">
              <QuestionReview
                number={q.number}
                question={q.question}
                questionType={r.question_type}
                options={r.options}
                isCorrect={r.is_correct}
                correctAnswer={r.correct_answer}
                solutionSteps={r.solution_steps}
                submitted={submittedByNumber.get(q.number)}
              />
            </Card>
          );
        })}
      </ol>

      <div className="flex flex-wrap gap-3">
        {weakestKod ? (
          <Button asChild className="gap-2">
            <Link href={practiceHref(weakestKod)}>
              <Sparkles className="h-4 w-4" />
              Eksiklerine göre yeni test
            </Link>
          </Button>
        ) : (
          <Button asChild className="gap-2">
            <Link href="/coz/yeni">
              <Sparkles className="h-4 w-4" />
              Yeni quiz çöz
            </Link>
          </Button>
        )}
        <Button onClick={onCreateWorksheet} variant="outline" className="gap-2">
          <FileText className="h-4 w-4" />
          Bu konuda çalışma kağıdı
        </Button>
        <Button asChild variant="ghost">
          <Link href="/coz">Çöz &amp; Geliş&apos;e dön</Link>
        </Button>
      </div>
    </div>
  );
}
