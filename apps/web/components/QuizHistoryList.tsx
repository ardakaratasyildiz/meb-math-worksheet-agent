"use client";

import * as React from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { ChevronRight, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

import { listMyAttempts } from "@/lib/api";
import type { AttemptHistoryItem } from "@/lib/types";

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("tr-TR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function QuizHistoryList() {
  const { userId, isLoaded } = useAuth();
  const [items, setItems] = React.useState<AttemptHistoryItem[]>([]);
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
    listMyAttempts(userId)
      .then((d) => {
        if (active) setItems(d);
      })
      .catch((e: unknown) => {
        if (!active) return;
        const msg = e instanceof Error ? e.message : "Geçmiş alınamadı.";
        setError(msg);
        toast.error("Geçmiş yüklenemedi", { description: msg });
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [userId, isLoaded]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
        Geçmiş yükleniyor…
      </div>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <p className="text-sm text-destructive">{error}</p>
      </Card>
    );
  }

  if (items.length === 0) {
    return (
      <Card className="flex flex-col items-center gap-3 p-10 text-center">
        <h2 className="font-semibold">Henüz çözülmüş quiz yok</h2>
        <p className="max-w-sm text-sm text-muted-foreground">
          İlk quizini çöz; burada geçmiş denemelerin ve cevapların birikir.
        </p>
        <Button asChild className="mt-1 gap-2">
          <Link href="/practice/new">
            <Sparkles className="h-4 w-4" />
            İlk quizini çöz
          </Link>
        </Button>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((it) => {
        const pct = it.total ? Math.round((it.score / it.total) * 100) : 0;
        return (
          <Link key={it.attempt_id} href={`/practice/history/${it.attempt_id}`}>
            <Card className="flex items-center justify-between gap-3 p-4 transition-colors hover:border-primary/40 hover:bg-accent/20">
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium">{it.title}</p>
                <p className="text-xs text-muted-foreground">
                  {formatDate(it.completed_at)}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-3">
                <span
                  className={`text-sm font-semibold tabular-nums ${
                    pct >= 60 ? "text-emerald-600 dark:text-emerald-400" : "text-amber-600 dark:text-amber-400"
                  }`}
                >
                  {it.score}/{it.total}
                </span>
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              </div>
            </Card>
          </Link>
        );
      })}
    </div>
  );
}
