"use client";

import * as React from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { ArrowLeft, Loader2, Users } from "lucide-react";
import { toast } from "sonner";

import { Card } from "@/components/ui/card";

import { getShareResults } from "@/lib/api";
import type { ShareResultsResponse } from "@/lib/types";

function formatDateTime(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("tr-TR", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function ShareResultsView({ shareId }: { shareId: string }) {
  const { userId, isLoaded } = useAuth();
  const [data, setData] = React.useState<ShareResultsResponse | null>(null);
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
    getShareResults(shareId, userId)
      .then((d) => {
        if (active) setData(d);
      })
      .catch((e: unknown) => {
        if (!active) return;
        setError(e instanceof Error ? e.message : "Sonuçlar alınamadı.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [shareId, userId, isLoaded]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
        Sonuçlar yükleniyor…
      </div>
    );
  }

  if (error || !data) {
    return (
      <Card className="p-6">
        <p className="text-sm text-destructive">
          {error ?? "Paylaşım bulunamadı."}
        </p>
        <Link
          href="/practice/shares"
          className="mt-3 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Paylaşımlarım
        </Link>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Link
          href="/practice/shares"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Paylaşımlarım
        </Link>
        <h1 className="text-2xl font-semibold tracking-tight">{data.title}</h1>
        <p className="flex items-center gap-1 text-sm text-muted-foreground">
          <Users className="h-4 w-4" />
          {data.items.length} kişi çözdü · {data.question_count} soru
        </p>
      </div>

      {data.items.length === 0 ? (
        <Card className="flex flex-col items-center gap-2 p-10 text-center">
          <h2 className="font-semibold">Henüz kimse çözmedi</h2>
          <p className="max-w-sm text-sm text-muted-foreground">
            Paylaştığın link açılıp çözüldükçe sonuçlar burada listelenir.
          </p>
        </Card>
      ) : (
        <Card className="overflow-hidden">
          {/* Başlık satırı (sadece geniş ekran) */}
          <div className="hidden grid-cols-[1fr_auto_auto_auto] gap-4 border-b px-5 py-2.5 text-xs font-medium text-muted-foreground sm:grid">
            <span>Çözen</span>
            <span className="text-right">Skor</span>
            <span className="text-right">Süre</span>
            <span className="text-right">Tarih</span>
          </div>
          <ul className="divide-y">
            {data.items.map((it, i) => {
              const pct = it.total ? Math.round((it.score / it.total) * 100) : 0;
              return (
                <li
                  key={i}
                  className="grid grid-cols-[1fr_auto] gap-x-4 gap-y-1 px-5 py-3 text-sm sm:grid-cols-[1fr_auto_auto_auto] sm:items-center"
                >
                  <span className="truncate font-medium">
                    {it.solver_label || "Misafir"}
                  </span>
                  <span
                    className={`text-right tabular-nums font-semibold ${
                      pct >= 60
                        ? "text-emerald-600 dark:text-emerald-400"
                        : "text-amber-600 dark:text-amber-400"
                    }`}
                  >
                    {it.score}/{it.total}
                    <span className="ml-1 font-normal text-muted-foreground">
                      %{pct}
                    </span>
                  </span>
                  <span className="text-right tabular-nums text-muted-foreground">
                    {it.duration_seconds != null ? `${it.duration_seconds} sn` : "—"}
                  </span>
                  <span className="text-right text-xs text-muted-foreground">
                    {formatDateTime(it.completed_at)}
                  </span>
                </li>
              );
            })}
          </ul>
        </Card>
      )}
    </div>
  );
}
