"use client";

import * as React from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { Loader2, Sparkles, Target, TrendingUp } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

import { getProgress } from "@/lib/api";
import { findKazanimByKod } from "@/lib/curriculum";
import type { KazanimProgress, ProgressResponse } from "@/lib/types";

function practiceHref(kod: string): string {
  const info = findKazanimByKod(kod);
  if (!info) return "/coz/yeni";
  const p = new URLSearchParams({
    grade: String(info.grade),
    topic: info.topicId,
    kazanim: kod,
  });
  return `/coz/yeni?${p.toString()}`;
}

function MasteryRow({ k }: { k: KazanimProgress }) {
  const info = findKazanimByKod(k.kazanim_kod);
  const pct = Math.round(k.ratio * 100);
  const strong = pct >= 60;
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between gap-2 text-xs">
        <span className="min-w-0 truncate">
          <span className="font-mono text-primary">{k.kazanim_kod}</span>
          {info ? (
            <span className="text-muted-foreground"> · {info.metin}</span>
          ) : null}
        </span>
        <span className="shrink-0 tabular-nums text-muted-foreground">
          {k.correct}/{k.total} · %{pct}
        </span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-muted">
        <div
          className={`h-full ${strong ? "bg-emerald-500" : "bg-amber-500"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function ProgressDashboard() {
  const { userId, isLoaded } = useAuth();
  const [data, setData] = React.useState<ProgressResponse | null>(null);
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
    getProgress(userId)
      .then((d) => {
        if (active) setData(d);
      })
      .catch((e: unknown) => {
        if (!active) return;
        const msg = e instanceof Error ? e.message : "İlerleme alınamadı.";
        setError(msg);
        toast.error("İlerleme yüklenemedi", { description: msg });
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
        İlerleme yükleniyor…
      </div>
    );
  }

  if (error || !data) {
    return (
      <Card className="p-6">
        <p className="text-sm text-destructive">{error ?? "Veri yok."}</p>
      </Card>
    );
  }

  // Boş durum — henüz hiç çözüm yok.
  if (data.summary.total_answered === 0) {
    return (
      <Card className="flex flex-col items-center gap-3 p-10 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
          <TrendingUp className="h-6 w-6" />
        </div>
        <h2 className="font-semibold">Henüz çözüm yok</h2>
        <p className="max-w-sm text-sm text-muted-foreground">
          İlk quizini çöz; kazanım bazlı gelişimin, doğru oranın ve zayıf
          konuların burada görünmeye başlar.
        </p>
        <Button asChild className="mt-1 gap-2">
          <Link href="/coz/yeni">
            <Sparkles className="h-4 w-4" />
            İlk quizini çöz
          </Link>
        </Button>
      </Card>
    );
  }

  const accuracyPct = Math.round(data.summary.accuracy * 100);

  return (
    <div className="space-y-6">
      {/* Özet kartları */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="p-5">
          <p className="text-xs text-muted-foreground">Genel doğru oranı</p>
          <p className="mt-1 text-3xl font-bold tabular-nums">%{accuracyPct}</p>
          <p className="text-xs text-muted-foreground">
            {data.summary.total_correct}/{data.summary.total_answered} doğru
          </p>
        </Card>
        <Card className="p-5">
          <p className="text-xs text-muted-foreground">Çözülen quiz</p>
          <p className="mt-1 text-3xl font-bold tabular-nums">
            {data.summary.quizzes_solved}
          </p>
        </Card>
        <Card className="p-5">
          <p className="text-xs text-muted-foreground">Çalışılan kazanım</p>
          <p className="mt-1 text-3xl font-bold tabular-nums">
            {data.summary.kazanim_count}
          </p>
        </Card>
      </div>

      {/* Zayıf kazanımlar + hedefli öneri */}
      {data.weak.length ? (
        <Card className="space-y-4 p-5">
          <div className="flex items-center gap-2">
            <Target className="h-4 w-4 text-amber-500" />
            <h2 className="text-sm font-semibold">
              Geliştirmen gereken kazanımlar
            </h2>
          </div>
          <div className="space-y-4">
            {data.weak.map((k) => (
              <div key={k.kazanim_kod} className="space-y-2">
                <MasteryRow k={k} />
                <Button asChild size="sm" variant="outline" className="gap-1.5">
                  <Link href={practiceHref(k.kazanim_kod)}>
                    <Sparkles className="h-3.5 w-3.5" />
                    Bu kazanımda pratik yap
                  </Link>
                </Button>
              </div>
            ))}
          </div>
        </Card>
      ) : (
        <Card className="p-5 text-sm text-muted-foreground">
          Henüz belirgin bir zayıf kazanım yok. Çözmeye devam ettikçe burada
          hedefli öneriler belirir.
        </Card>
      )}

      {/* Tüm kazanım ustalığı */}
      <Card className="space-y-4 p-5">
        <h2 className="text-sm font-semibold">Kazanım ustalığı</h2>
        <div className="space-y-3">
          {data.mastery.map((k) => (
            <MasteryRow key={k.kazanim_kod} k={k} />
          ))}
        </div>
      </Card>
    </div>
  );
}
