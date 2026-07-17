"use client";

import * as React from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { ChevronDown, ChevronRight, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { TeacherQuizReview } from "@/components/TeacherQuizReview";
import { listMyQuizzes } from "@/lib/api";
import type { MyQuizItem } from "@/lib/types";

/** "Ürettiğim Quizler" sayfası — öğretmenin ürettiği tüm quizler; her biri açılıp
 *  cevaplarıyla incelenir ve beğenilmeyen soru yeniden üretilir (düzenleme). */
export function MyQuizzesView() {
  const { userId, isLoaded } = useAuth();
  const [quizzes, setQuizzes] = React.useState<MyQuizItem[] | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!isLoaded) return;
    if (!userId) {
      setError("Oturum bulunamadı.");
      return;
    }
    let active = true;
    listMyQuizzes(userId)
      .then((d) => active && setQuizzes(d))
      .catch((e: unknown) => {
        if (!active) return;
        const msg = e instanceof Error ? e.message : "Quizler alınamadı.";
        setError(msg);
        toast.error("Quizler yüklenemedi", { description: msg });
      });
    return () => {
      active = false;
    };
  }, [userId, isLoaded]);

  if (error) {
    return (
      <Card className="p-6">
        <p className="text-sm text-destructive">{error}</p>
      </Card>
    );
  }

  if (quizzes === null) {
    return (
      <div className="flex items-center justify-center py-16 text-muted-foreground">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
        Quizler yükleniyor…
      </div>
    );
  }

  if (quizzes.length === 0) {
    return (
      <Card className="flex flex-col items-center gap-3 p-10 text-center">
        <Sparkles className="h-8 w-8 text-muted-foreground" />
        <h2 className="font-semibold">Henüz quiz üretmedin</h2>
        <p className="max-w-sm text-sm text-muted-foreground">
          &quot;Quiz üret&quot; ile çözülebilir quizler oluştur; ürettiklerin burada
          listelenir, inceleyip düzenleyebilir ve sınıflarına ödev olarak
          atayabilirsin.
        </p>
        <Button asChild className="mt-1 gap-1.5">
          <Link href="/practice/new">
            <Sparkles className="h-4 w-4" />
            Quiz üret
          </Link>
        </Button>
      </Card>
    );
  }

  return (
    <ul className="divide-y rounded-lg border">
      {quizzes.map((q) => (
        <MyQuizRow key={q.id} quiz={q} />
      ))}
    </ul>
  );
}

/** Quiz satırı — tıklayınca cevaplı önizleme + soru yenileme (düzenleme) açılır. */
function MyQuizRow({ quiz }: { quiz: MyQuizItem }) {
  const [open, setOpen] = React.useState(false);
  return (
    <li className="text-sm">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center gap-2 px-4 py-3 text-left transition-colors hover:bg-accent/20"
      >
        {open ? (
          <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
        )}
        <span className="min-w-0 truncate font-medium">{quiz.title}</span>
        <span className="ml-auto shrink-0 text-xs text-muted-foreground">
          {quiz.grade ? `${quiz.grade}. sınıf · ` : ""}
          {quiz.difficulty}
        </span>
      </button>
      {open ? (
        <div className="border-t bg-muted/20 px-4 py-3">
          {/* Düzenleme = soru yenileme. Ödev atama sınıf detayındaki picker'da. */}
          <TeacherQuizReview quizId={quiz.id} showAssign={false} showShare={false} />
        </div>
      ) : null}
    </li>
  );
}
