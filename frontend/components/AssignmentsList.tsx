"use client";

import * as React from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { CheckCircle2, ChevronRight, Loader2, NotebookPen } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { listMyAssignments } from "@/lib/api";
import type { MyAssignmentItem } from "@/lib/types";

export function AssignmentsList() {
  const { userId, isLoaded } = useAuth();
  const [items, setItems] = React.useState<MyAssignmentItem[]>([]);
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
    listMyAssignments(userId)
      .then((d) => active && setItems(d))
      .catch((e: unknown) => {
        if (!active) return;
        const msg = e instanceof Error ? e.message : "Ödevler alınamadı.";
        setError(msg);
        toast.error("Ödevler yüklenemedi", { description: msg });
      })
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [userId, isLoaded]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
        Ödevler yükleniyor…
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
        <NotebookPen className="h-8 w-8 text-muted-foreground" />
        <h2 className="font-semibold">Henüz ödevin yok</h2>
        <p className="max-w-sm text-sm text-muted-foreground">
          Bir sınıfa katıldığında öğretmenin verdiği ödevler burada görünür.
        </p>
        <Button asChild className="mt-1" variant="outline">
          <Link href="/practice/classes">Sınıfa katıl</Link>
        </Button>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((a) => {
        const pct =
          a.solved && a.total ? Math.round(((a.score ?? 0) / a.total) * 100) : 0;
        return (
          <Link key={a.assignment_id} href={`/practice/assignments/${a.assignment_id}`}>
            <Card className="flex items-center justify-between gap-3 p-4 transition-colors hover:border-primary/40 hover:bg-accent/20">
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium">{a.title}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {a.classroom_name}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-3">
                {a.solved ? (
                  <span className="inline-flex items-center gap-1 text-sm font-semibold text-emerald-600 dark:text-emerald-400">
                    <CheckCircle2 className="h-4 w-4" />
                    {a.score}/{a.total}
                    <span className="font-normal text-muted-foreground">
                      · %{pct}
                    </span>
                  </span>
                ) : (
                  <span className="rounded-full bg-coral/15 px-2.5 py-0.5 text-xs font-semibold text-coral">
                    Çöz
                  </span>
                )}
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              </div>
            </Card>
          </Link>
        );
      })}
    </div>
  );
}
