"use client";

import * as React from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { Check, ChevronRight, Copy, Loader2, Share2, Users } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

import { listMyShares } from "@/lib/api";
import type { ShareSummary } from "@/lib/types";

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("tr-TR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

function CopyLinkButton({ shareCode }: { shareCode: string }) {
  const [copied, setCopied] = React.useState(false);
  async function onCopy(e: React.MouseEvent) {
    // Kart bir Link içinde — kopyalama tıklaması sayfaya gitmesin.
    e.preventDefault();
    e.stopPropagation();
    const origin = typeof window !== "undefined" ? window.location.origin : "";
    try {
      await navigator.clipboard.writeText(`${origin}/q/${shareCode}`);
      setCopied(true);
      toast.success("Link kopyalandı");
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Link kopyalanamadı");
    }
  }
  return (
    <Button
      type="button"
      size="sm"
      variant="outline"
      onClick={onCopy}
      className="gap-1.5"
    >
      {copied ? (
        <Check className="h-4 w-4 text-emerald-500" />
      ) : (
        <Copy className="h-4 w-4" />
      )}
      Linki kopyala
    </Button>
  );
}

export function SharesList({ isTeacher = false }: { isTeacher?: boolean }) {
  const { userId, isLoaded } = useAuth();
  const [items, setItems] = React.useState<ShareSummary[]>([]);
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
    listMyShares(userId)
      .then((d) => {
        if (active) setItems(d);
      })
      .catch((e: unknown) => {
        if (!active) return;
        const msg = e instanceof Error ? e.message : "Paylaşımlar alınamadı.";
        setError(msg);
        toast.error("Paylaşımlar yüklenemedi", { description: msg });
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
        Paylaşımlar yükleniyor…
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
        <Share2 className="h-8 w-8 text-muted-foreground" />
        <h2 className="font-semibold">Henüz paylaşım yok</h2>
        <p className="max-w-sm text-sm text-muted-foreground">
          {isTeacher ? (
            <>
              Bir quiz üret; oluşturma ekranındaki <strong>Paylaş</strong> ile link
              oluştur. Paylaştığın kişilerin sonuçları burada birikir.
            </>
          ) : (
            <>
              Bir quiz çöz, sonuç ekranındaki <strong>Paylaş</strong> ile link oluştur;
              paylaştığın kişilerin sonuçları burada birikir.
            </>
          )}
        </p>
        <Button asChild className="mt-1">
          <Link href="/practice/new">{isTeacher ? "Quiz üret" : "Yeni quiz çöz"}</Link>
        </Button>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((s) => (
        <Card key={s.share_id} className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
          <Link
            href={`/practice/shares/${s.share_id}`}
            className="min-w-0 flex-1"
          >
            <p className="truncate font-medium">{s.title}</p>
            <p className="mt-0.5 flex items-center gap-3 text-xs text-muted-foreground">
              <span className="inline-flex items-center gap-1">
                <Users className="h-3.5 w-3.5" />
                {s.attempt_count} çözüm
              </span>
              {s.avg_score_pct != null ? (
                <span>ort. %{s.avg_score_pct}</span>
              ) : null}
              <span>{formatDate(s.created_at)}</span>
            </p>
          </Link>
          <div className="flex shrink-0 items-center gap-2">
            <CopyLinkButton shareCode={s.share_code} />
            <Button asChild size="sm" variant="ghost" className="gap-1">
              <Link href={`/practice/shares/${s.share_id}`}>
                Sonuçlar
                <ChevronRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </Card>
      ))}
    </div>
  );
}
