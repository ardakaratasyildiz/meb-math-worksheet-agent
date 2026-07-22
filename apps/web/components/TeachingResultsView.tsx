"use client";

import * as React from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import {
  ChevronDown,
  ChevronRight,
  GraduationCap,
  Loader2,
  NotebookPen,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { StudentResultRow } from "@/components/ClassroomDetailView";
import { getAssignmentResults, getTeachingResults } from "@/lib/api";
import type {
  AssignmentResultsResponse,
  TeachingOverviewItem,
} from "@/lib/types";

/** Öğretmen "Ödev Sonuçları" panosu — tüm sınıflardaki ödevler, sınıfa göre gruplu.
 *  Ödeve tıkla → kim çözdü + puan; öğrenciye tıkla → cevapları (StudentResultRow). */
export function TeachingResultsView() {
  const { userId, isLoaded } = useAuth();
  const [items, setItems] = React.useState<TeachingOverviewItem[]>([]);
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
    getTeachingResults(userId)
      .then((d) => active && setItems(d))
      .catch((e: unknown) => {
        if (!active) return;
        const msg = e instanceof Error ? e.message : "Sonuçlar alınamadı.";
        setError(msg);
        toast.error("Ödev sonuçları yüklenemedi", { description: msg });
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
        Ödev sonuçları yükleniyor…
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
        <h2 className="font-semibold">Henüz ödev yok</h2>
        <p className="max-w-sm text-sm text-muted-foreground">
          Bir sınıf aç, öğrencilerini davet et ve ödev ata. Öğrencilerin çözünce
          sonuçları — kim çözdü, kaç aldı, ne cevap verdi — burada birikir.
        </p>
        <Button asChild className="mt-1 gap-1.5">
          <Link href="/practice/classes">
            <GraduationCap className="h-4 w-4" />
            Sınıflarım
          </Link>
        </Button>
      </Card>
    );
  }

  // Sınıfa göre grupla (items zaten sınıf→ödev sırasında geliyor).
  const groups: { classroomId: string; name: string; rows: TeachingOverviewItem[] }[] =
    [];
  for (const it of items) {
    let g = groups.find((x) => x.classroomId === it.classroom_id);
    if (!g) {
      g = { classroomId: it.classroom_id, name: it.classroom_name, rows: [] };
      groups.push(g);
    }
    g.rows.push(it);
  }

  return (
    <div className="space-y-5">
      {groups.map((g) => (
        <Card key={g.classroomId} className="overflow-hidden">
          <div className="flex items-center justify-between gap-2 border-b bg-muted/30 px-5 py-3">
            <h2 className="flex items-center gap-2 font-display font-bold">
              <GraduationCap className="h-4 w-4 text-amber-500" />
              {g.name}
            </h2>
            <Link
              href={`/practice/classes/${g.classroomId}`}
              className="text-xs font-medium text-primary underline-offset-2 hover:underline"
            >
              Sınıfı aç
            </Link>
          </div>
          <ul className="divide-y">
            {g.rows.map((a) => (
              <AssignmentResultsRow
                key={a.assignment_id}
                item={a}
                tenantId={userId as string}
              />
            ))}
          </ul>
        </Card>
      ))}
    </div>
  );
}

/** Bir ödev satırı — tıklayınca sonuç panosunu (roster + skor) açar. */
function AssignmentResultsRow({
  item,
  tenantId,
}: {
  item: TeachingOverviewItem;
  tenantId: string;
}) {
  const [open, setOpen] = React.useState(false);
  const [results, setResults] = React.useState<AssignmentResultsResponse | null>(
    null,
  );
  const [loading, setLoading] = React.useState(false);
  const isPdf = item.assignment_type === "pdf";

  async function toggle() {
    const next = !open;
    setOpen(next);
    if (next && results === null) {
      setLoading(true);
      try {
        setResults(await getAssignmentResults(item.assignment_id, tenantId));
      } catch (e: unknown) {
        toast.error("Sonuçlar alınamadı", {
          description: e instanceof Error ? e.message : undefined,
        });
        setOpen(false);
      } finally {
        setLoading(false);
      }
    }
  }

  return (
    <li className="text-sm">
      <button
        type="button"
        onClick={toggle}
        className="flex w-full items-center gap-2 px-4 py-2.5 text-left transition-colors hover:bg-accent/20"
      >
        {open ? (
          <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
        )}
        <NotebookPen
          className={`h-4 w-4 shrink-0 ${isPdf ? "text-rose-500" : "text-amber-500"}`}
        />
        <span className="min-w-0 truncate font-medium">{item.title}</span>
        {isPdf ? (
          <span className="shrink-0 rounded-full bg-rose-400/15 px-2 py-0.5 text-[11px] font-semibold text-rose-500">
            PDF
          </span>
        ) : null}
        <span className="ml-auto shrink-0 tabular-nums text-muted-foreground">
          {item.solved_count}/{item.member_count} çözdü
        </span>
      </button>

      {open ? (
        <div className="border-t bg-muted/30 px-4 py-3">
          {loading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Sonuçlar yükleniyor…
            </div>
          ) : results && results.items.length > 0 ? (
            <ul className="space-y-1">
              {results.items.map((it) => (
                <StudentResultRow
                  key={it.student_tenant_id}
                  item={it}
                  assignmentId={item.assignment_id}
                  tenantId={tenantId}
                />
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">
              Sınıfta henüz öğrenci yok.
            </p>
          )}
        </div>
      ) : null}
    </li>
  );
}
