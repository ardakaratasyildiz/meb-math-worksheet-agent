"use client";

import * as React from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { ChevronDown, Loader2, Sparkles, Target, TrendingUp } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ScoreRing } from "@/components/ScoreRing";

import { getProgress } from "@/lib/api";
import {
  findKazanimByKod,
  practiceHref,
  rollupByTopic,
  type TopicRollup,
} from "@/lib/curriculum";
import type {
  AttemptSummary,
  KazanimProgress,
  ProgressResponse,
} from "@/lib/types";

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

function TopicBar({ t }: { t: TopicRollup }) {
  const pct = Math.round(t.ratio * 100);
  const strong = pct >= 60;
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="font-medium">{t.topicName}</span>
        <span className="tabular-nums text-muted-foreground">
          {t.correct}/{t.total} · %{pct}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <div
          className={`h-full ${strong ? "bg-emerald-500" : "bg-amber-500"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function TrendChart({ recent }: { recent: AttemptSummary[] }) {
  if (recent.length < 2) return null;
  return (
    <Card className="space-y-3 p-5">
      <h2 className="text-sm font-semibold">Son denemeler</h2>
      <div className="flex items-end gap-1.5">
        {recent.map((a, i) => {
          const pct = a.total ? Math.round((a.score / a.total) * 100) : 0;
          return (
            <div
              key={i}
              className="flex flex-1 flex-col items-center gap-1"
              title={`${a.score}/${a.total} · %${pct}`}
            >
              <div
                className={`w-full rounded-t ${pct >= 60 ? "bg-emerald-500" : "bg-amber-500"}`}
                style={{ height: Math.max(4, Math.round(pct * 0.6)) }}
              />
              <span className="text-[9px] tabular-nums text-muted-foreground">
                %{pct}
              </span>
            </div>
          );
        })}
      </div>
      <p className="text-[11px] text-muted-foreground">
        Soldan sağa: eski → yeni. Her çubuk bir quiz&apos;in doğruluğu.
      </p>
    </Card>
  );
}

function buildInsight(topics: TopicRollup[]): string | null {
  const withData = topics.filter((t) => t.total >= 2);
  if (withData.length === 0) return null;
  const sorted = [...withData].sort((a, b) => b.ratio - a.ratio);
  const best = sorted[0];
  const worst = sorted[sorted.length - 1];
  if (best.topicId === worst.topicId) {
    return `${best.topicName} konusunda %${Math.round(best.ratio * 100)} başarıdasın.`;
  }
  return `${best.topicName} konusunda güçlüsün (%${Math.round(
    best.ratio * 100,
  )}); ${worst.topicName} konusunda zorlanıyorsun (%${Math.round(
    worst.ratio * 100,
  )}).`;
}

export function ProgressDashboard() {
  const { userId, isLoaded } = useAuth();
  const [detailOpen, setDetailOpen] = React.useState(false);
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
  // Kazanım kodları yerine KONU bazında ustalık (anlaşılırlık), zayıf→güçlü.
  const topics = rollupByTopic(data.mastery).sort((a, b) => a.ratio - b.ratio);
  const insight = buildInsight(topics);

  return (
    <div className="space-y-6">
      {/* Üst: skor halkası + özet + sade-dil içgörü */}
      <Card className="flex flex-col gap-4 p-6 sm:flex-row sm:items-center">
        <ScoreRing pct={accuracyPct} label="doğru" />
        <div className="flex-1 space-y-3">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-xs text-muted-foreground">Çözülen quiz</p>
              <p className="text-xl font-bold tabular-nums">
                {data.summary.quizzes_solved}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Toplam soru</p>
              <p className="text-xl font-bold tabular-nums">
                {data.summary.total_answered}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Konu</p>
              <p className="text-xl font-bold tabular-nums">{topics.length}</p>
            </div>
          </div>
          {insight ? (
            <p className="rounded-md bg-accent/30 px-3 py-2 text-sm">
              {insight}
            </p>
          ) : null}
        </div>
      </Card>

      {/* Trend */}
      <TrendChart recent={data.recent} />

      {/* Konu bazında ustalık (birincil görünüm) */}
      {topics.length ? (
        <Card className="space-y-3 p-5">
          <h2 className="text-sm font-semibold">Konu bazında ustalık</h2>
          <div className="space-y-3">
            {topics.map((t) => (
              <TopicBar key={t.topicId} t={t} />
            ))}
          </div>
        </Card>
      ) : null}

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
      ) : null}

      {/* Kazanım detayı — ikincil, katlanır (kod karmaşası öne çıkmasın) */}
      <Card className="p-5">
        <button
          type="button"
          onClick={() => setDetailOpen((v) => !v)}
          aria-expanded={detailOpen}
          className="flex w-full items-center justify-between gap-2 text-sm font-semibold"
        >
          <span>Kazanım detayı ({data.mastery.length})</span>
          <ChevronDown
            className={`h-4 w-4 transition-transform ${detailOpen ? "rotate-180" : ""}`}
          />
        </button>
        {detailOpen ? (
          <div className="mt-4 space-y-3">
            {data.mastery.map((k) => (
              <MasteryRow key={k.kazanim_kod} k={k} />
            ))}
          </div>
        ) : null}
      </Card>
    </div>
  );
}
