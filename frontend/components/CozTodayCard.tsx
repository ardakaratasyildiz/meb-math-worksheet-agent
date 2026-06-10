"use client";

import * as React from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { ArrowRight, Sparkles, Target } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

import { getProgress } from "@/lib/api";
import { findKazanimByKod, practiceHref } from "@/lib/curriculum";
import type { ProgressResponse } from "@/lib/types";

// Hub'da "Bugün ne çözmeliyim?" önerisi — kullanıcının en zayıf kazanımından
// mini-test önerir. Ek backend yok (mevcut getProgress'ten türetilir). Sessiz:
// veri yoksa/hata olursa hiçbir şey göstermez (hub yine çalışır).
export function CozTodayCard() {
  const { userId, isLoaded } = useAuth();
  const [data, setData] = React.useState<ProgressResponse | null>(null);
  const [ready, setReady] = React.useState(false);

  React.useEffect(() => {
    if (!isLoaded || !userId) return;
    let active = true;
    getProgress(userId)
      .then((d) => {
        if (active) setData(d);
      })
      .catch(() => {
        /* sessiz — öneri kartı kritik değil */
      })
      .finally(() => {
        if (active) setReady(true);
      });
    return () => {
      active = false;
    };
  }, [userId, isLoaded]);

  if (!ready || !data) return null;

  // Yeni kullanıcı — ilk quiz çağrısı.
  if (data.summary.total_answered === 0) {
    return (
      <Card className="flex flex-col gap-3 border-primary/30 bg-accent/20 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <p className="text-sm font-semibold">Hadi başlayalım</p>
            <p className="text-sm text-muted-foreground">
              İlk quizini çöz; gelişimin ve sana özel öneriler burada belirsin.
            </p>
          </div>
        </div>
        <Button asChild className="shrink-0 gap-2">
          <Link href="/coz/yeni">
            İlk quizini çöz
            <ArrowRight className="h-4 w-4" />
          </Link>
        </Button>
      </Card>
    );
  }

  // En zayıf kazanım (yoksa mastery'nin en zayıfı — zaten zayıf→güçlü sıralı).
  const target = data.weak[0] ?? data.mastery[0] ?? null;
  if (!target) return null;

  const info = findKazanimByKod(target.kazanim_kod);
  const label = info?.metin ?? target.kazanim_kod;
  const pct = Math.round(target.ratio * 100);

  return (
    <Card className="flex flex-col gap-3 border-primary/30 bg-accent/20 p-5 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-amber-500/15 text-amber-600 dark:text-amber-400">
          <Target className="h-5 w-5" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold">Bugün şunu çöz</p>
          <p className="text-sm text-muted-foreground">
            <span className="text-foreground">{label}</span>
            {info ? (
              <span className="text-muted-foreground">
                {" "}
                · {info.topicName}
              </span>
            ) : null}{" "}
            <span className="text-xs">(şu an %{pct})</span>
          </p>
        </div>
      </div>
      <Button asChild className="shrink-0 gap-2">
        <Link href={practiceHref(target.kazanim_kod)}>
          Hemen çöz
          <ArrowRight className="h-4 w-4" />
        </Link>
      </Button>
    </Card>
  );
}
