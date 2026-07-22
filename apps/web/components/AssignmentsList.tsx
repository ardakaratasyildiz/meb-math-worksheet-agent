"use client";

import * as React from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import {
  CheckCircle2,
  ChevronRight,
  Download,
  Loader2,
  NotebookPen,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  downloadBlob,
  getAssignmentWorksheet,
  listMyAssignments,
  renderPdf,
} from "@/lib/api";
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
        if (a.assignment_type === "pdf") {
          return (
            <PdfAssignmentRow
              key={a.assignment_id}
              a={a}
              tenantId={userId as string}
            />
          );
        }
        const pct =
          a.solved && a.total ? Math.round(((a.score ?? 0) / a.total) * 100) : 0;
        return (
          <Link key={a.assignment_id} href={`/practice/assignments/${a.assignment_id}`}>
            <Card className="flex items-center justify-between gap-3 p-4 transition-colors hover:border-primary/40 hover:bg-accent/20">
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium">{a.title}</p>
                <p className="mt-0.5 flex flex-wrap items-center gap-x-2 text-xs text-muted-foreground">
                  <span>{a.classroom_name}</span>
                  {a.due_at && !a.solved ? <DueChip dueAt={a.due_at} /> : null}
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

/** PDF (worksheet) ödev satırı — sistem-içi çöz (deterministik puanlama) VEYA PDF indir. */
function PdfAssignmentRow({
  a,
  tenantId,
}: {
  a: MyAssignmentItem;
  tenantId: string;
}) {
  const [downloading, setDownloading] = React.useState(false);
  const pct =
    a.solved && a.total ? Math.round(((a.score ?? 0) / a.total) * 100) : 0;

  async function onDownload() {
    setDownloading(true);
    try {
      const res = await getAssignmentWorksheet(a.assignment_id, tenantId);
      const blob = await renderPdf(res.worksheet, {
        include_answer_key: false,
        include_solutions: false,
      });
      const safe = (res.title || "odev").replace(/[^\w.-]+/g, "_");
      downloadBlob(blob, `${safe}.pdf`);
    } catch (e: unknown) {
      toast.error("PDF indirilemedi", {
        description: e instanceof Error ? e.message : undefined,
      });
    } finally {
      setDownloading(false);
    }
  }

  return (
    <Card className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0 flex-1">
        <p className="truncate font-medium">{a.title}</p>
        <p className="mt-0.5 flex flex-wrap items-center gap-x-2 text-xs text-muted-foreground">
          <span>{a.classroom_name}</span>
          <span className="rounded-full bg-rose-400/15 px-2 py-0.5 font-semibold text-rose-500">
            PDF
          </span>
          {a.due_at && !a.solved ? <DueChip dueAt={a.due_at} /> : null}
        </p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {a.solved ? (
          <span className="inline-flex items-center gap-1 text-sm font-semibold text-emerald-600 dark:text-emerald-400">
            <CheckCircle2 className="h-4 w-4" />
            {a.score}/{a.total}
            <span className="font-normal text-muted-foreground">· %{pct}</span>
          </span>
        ) : null}
        <Button asChild size="sm" className="gap-1.5">
          <Link href={`/practice/assignments/${a.assignment_id}`}>
            {a.solved ? "Tekrar çöz" : "Çöz"}
          </Link>
        </Button>
        <Button
          onClick={onDownload}
          disabled={downloading}
          size="sm"
          variant="outline"
          className="gap-1.5"
        >
          {downloading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Download className="h-4 w-4" />
          )}
          İndir
        </Button>
      </div>
    </Card>
  );
}

/** Son teslim rozeti — geçmişse "süresi doldu" (kırmızı), 48 saat içindeyse amber. */
function DueChip({ dueAt }: { dueAt: string }) {
  const due = new Date(dueAt);
  const now = new Date();
  const overdue = due.getTime() < now.getTime();
  const soon = !overdue && due.getTime() - now.getTime() < 48 * 3600 * 1000;
  const label = due.toLocaleDateString("tr-TR", { day: "2-digit", month: "short" });
  const cls = overdue
    ? "text-rose-500"
    : soon
      ? "text-amber-600 dark:text-amber-400"
      : "text-muted-foreground";
  return (
    <span className={`font-semibold ${cls}`}>
      {overdue ? "⏰ süresi doldu" : `son: ${label}`}
    </span>
  );
}
