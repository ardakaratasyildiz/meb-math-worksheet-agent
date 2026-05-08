"use client";

import * as React from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { Question, SolutionStep } from "@/lib/types";

const TYPE_LABELS: Record<string, string> = {
  islem: "İşlem",
  sozel_problem: "Sözel problem",
  kavram_sorusu: "Kavram",
  akil_yurutme: "Akıl yürütme",
  modelleme: "Modelleme",
  gunluk_hayat: "Günlük hayat",
  salt_islem: "Salt işlem",
  tablo_sorusu: "Tablo",
  gorsel_geometri: "Geometri",
  grafik_okuma: "Grafik",
  oruntu_sekil: "Örüntü",
};

function isStepList(v: string | SolutionStep[]): v is SolutionStep[] {
  return Array.isArray(v);
}

export function QuestionCard({ q }: { q: Question }) {
  const [showAnswer, setShowAnswer] = React.useState(false);

  return (
    <Card className="animate-fade-in-up p-5">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
            {q.number}
          </span>
          <Badge variant="outline" className="font-mono text-[10px]">
            {q.kazanim_kod}
          </Badge>
          <Badge variant="secondary" className="text-[10px]">
            {TYPE_LABELS[q.question_type] ?? q.question_type}
          </Badge>
        </div>
      </div>

      <p className="whitespace-pre-wrap text-sm leading-relaxed">{q.question}</p>

      <Separator className="my-3" />

      <Button
        variant="ghost"
        size="sm"
        onClick={() => setShowAnswer((v) => !v)}
        className="-ml-3 gap-1 text-xs text-muted-foreground"
      >
        {showAnswer ? (
          <ChevronUp className="h-3 w-3" />
        ) : (
          <ChevronDown className="h-3 w-3" />
        )}
        {showAnswer ? "Cevabı gizle" : "Cevap & çözümü göster"}
      </Button>

      {showAnswer && (
        <div className="mt-2 space-y-2 rounded-md bg-accent/40 p-3 text-sm">
          <div>
            <span className="font-semibold text-accent-foreground">Cevap: </span>
            {q.answer}
          </div>
          {isStepList(q.solution_steps) ? (
            <ol className="ml-4 list-decimal space-y-1 text-xs text-muted-foreground">
              {q.solution_steps.map((s) => (
                <li key={s.step_no}>
                  {s.description}
                  {s.computation ? (
                    <code className="ml-1 rounded bg-background/60 px-1 py-0.5 font-mono">
                      {s.computation}
                    </code>
                  ) : null}
                </li>
              ))}
            </ol>
          ) : (
            <p className="whitespace-pre-wrap text-xs text-muted-foreground">
              {q.solution_steps}
            </p>
          )}
        </div>
      )}
    </Card>
  );
}
