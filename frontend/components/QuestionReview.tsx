"use client";

import * as React from "react";
import { Check, X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { MarkdownQuestion } from "@/components/MarkdownQuestion";
import type {
  QuestionType,
  SolutionStep,
  SubmittedAnswer,
} from "@/lib/types";

export const OPTION_LETTERS = ["A", "B", "C", "D", "E"];

// MCQ soru metni şıkları gömülü içerebilir ("... A) 4 B) 5"). Tekrar göstermemek
// için, en az 2 şık işareti varsa metni ilk işaretten keser.
export function stripInlineOptions(text: string): string {
  const marker = /\s+[A-E]\s*[\)\.]\s+/g;
  const matches = text.match(marker);
  if (!matches || matches.length < 2) return text;
  const idx = text.search(/\s+[A-E]\s*[\)\.]\s+/);
  return idx > 0 ? text.slice(0, idx).trim() : text;
}

export function SolutionView({ steps }: { steps: string | SolutionStep[] }) {
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

// Kullanıcının verdiği cevabı okunabilir metne çevirir (tipe göre).
export function formatSubmittedAnswer(
  questionType: QuestionType,
  submitted: SubmittedAnswer | null | undefined,
  options?: string[] | null,
): string {
  if (!submitted) return "Boş bırakıldı";
  if (questionType === "coktan_secmeli") {
    const i = submitted.selected_index;
    if (i == null) return "Boş bırakıldı";
    const letter = OPTION_LETTERS[i] ?? String(i + 1);
    const opt = options?.[i];
    return opt ? `${letter}) ${opt}` : letter;
  }
  if (questionType === "dogru_yanlis") {
    if (submitted.bool_answer == null) return "Boş bırakıldı";
    return submitted.bool_answer ? "Doğru" : "Yanlış";
  }
  const texts = (submitted.texts ?? []).map((t) => t.trim()).filter(Boolean);
  return texts.length ? texts.join(", ") : "Boş bırakıldı";
}

export interface QuestionReviewProps {
  number: number;
  question: string;
  questionType: QuestionType;
  options?: string[] | null;
  isCorrect: boolean;
  correctAnswer: string;
  solutionSteps: string | SolutionStep[];
  submitted?: SubmittedAnswer | null;
}

// Tek sorunun gözden geçirme kartı: ✓/✗ + soru + senin cevabın + doğru cevap +
// çözüm. Hem canlı sonuç ekranında hem geçmiş detayında kullanılır.
export function QuestionReview({
  number,
  question,
  questionType,
  options,
  isCorrect,
  correctAnswer,
  solutionSteps,
  submitted,
}: QuestionReviewProps) {
  const yourAnswer = formatSubmittedAnswer(questionType, submitted, options);
  return (
    <div className="space-y-2">
      <div className="flex items-start gap-2">
        <span
          className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-white ${
            isCorrect ? "bg-emerald-500" : "bg-red-500"
          }`}
        >
          {isCorrect ? (
            <Check className="h-4 w-4" />
          ) : (
            <X className="h-4 w-4" />
          )}
        </span>
        <div className="min-w-0 flex-1">
          <MarkdownQuestion
            text={
              questionType === "coktan_secmeli" && options?.length
                ? stripInlineOptions(question)
                : question
            }
          />
        </div>
      </div>
      <div className="space-y-1.5 pl-8 text-sm">
        <p className="text-xs">
          <span className="text-muted-foreground">Senin cevabın: </span>
          <span className={isCorrect ? "" : "text-red-600 dark:text-red-400"}>
            {yourAnswer}
          </span>
        </p>
        <Badge variant={isCorrect ? "secondary" : "outline"}>
          Doğru cevap: {correctAnswer}
        </Badge>
        <SolutionView steps={solutionSteps} />
      </div>
    </div>
  );
}
