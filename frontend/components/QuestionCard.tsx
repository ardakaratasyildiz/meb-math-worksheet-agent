"use client";

import * as React from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";

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

// LLM, prompt'ta talimat verildiği üzere `question` alanı içine Markdown blokları
// (kod bloğu, GFM tablo, kalın/italik, inline code) gömüyor. Bunlar ham metin olarak
// render edildiğinde ASCII çubuk grafikler ve geometri şekilleri proportional fontta
// hizalanmıyor, backtick/pipe karakterleri görünür kalıyor. Aşağıdaki components
// haritası kod bloklarını monospace + pre-wrap whitespace ile, tabloları gerçek
// HTML tablo olarak render eder.
const MD_COMPONENTS: Components = {
  pre: ({ children }) => (
    <pre className="my-3 overflow-x-auto whitespace-pre rounded-md border bg-zinc-50 p-3 font-mono text-xs leading-snug text-foreground dark:bg-zinc-900">
      {children}
    </pre>
  ),
  code: ({ className, children, ...props }) => {
    // react-markdown v9: pre'nin içindeki code'da className "language-*" olur.
    // Inline code'da className tanımsızdır → küçük etiket stili.
    const isBlock = typeof className === "string" && className.startsWith("language-");
    if (isBlock) {
      return (
        <code className={`${className} font-mono`} {...props}>
          {children}
        </code>
      );
    }
    return (
      <code
        className="rounded bg-zinc-100 px-1 py-0.5 font-mono text-[0.85em] dark:bg-zinc-800"
        {...props}
      >
        {children}
      </code>
    );
  },
  table: ({ children }) => (
    <div className="my-3 overflow-x-auto">
      <table className="w-full border-collapse text-xs">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="bg-muted/60">{children}</thead>,
  th: ({ children, style }) => (
    <th
      style={style}
      className="border border-border px-2 py-1.5 text-left font-semibold text-foreground"
    >
      {children}
    </th>
  ),
  td: ({ children, style }) => (
    <td style={style} className="border border-border px-2 py-1.5 align-top">
      {children}
    </td>
  ),
  p: ({ children }) => (
    <p className="my-2 leading-relaxed first:mt-0 last:mb-0">{children}</p>
  ),
  ul: ({ children }) => (
    <ul className="my-2 ml-5 list-disc space-y-1">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="my-2 ml-5 list-decimal space-y-1">{children}</ol>
  ),
  strong: ({ children }) => (
    <strong className="font-semibold text-foreground">{children}</strong>
  ),
  em: ({ children }) => <em className="italic">{children}</em>,
};

function MarkdownQuestion({ text }: { text: string }) {
  return (
    <div className="text-sm">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={MD_COMPONENTS}>
        {text}
      </ReactMarkdown>
    </div>
  );
}

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

      <MarkdownQuestion text={q.question} />

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
