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
export function PracticeTodayCard() {
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
      <Card className="flex flex-col gap-4 border-0 bg-gradient-to-br from-grape to-sky-500 p-6 text-white shadow-pop sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white/20 text-2xl">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <p className="font-display text-lg font-bold">Hadi başlayalım! ✨</p>
            <p className="text-sm text-white/85">
              İlk quizini çöz; gelişimin ve sana özel öneriler burada belirsin.
            </p>
          </div>
        </div>
        <Button
          asChild
          className="shrink-0 gap-2 rounded-full bg-sun font-display font-semibold text-grape shadow-pop-sun hover:bg-sun/90"
        >
          <Link href="/practice/new">
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
    <Card className="flex flex-col gap-4 border-0 bg-gradient-to-br from-grape to-sky-500 p-6 text-white shadow-pop sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-start gap-3">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white/20 text-2xl">
          <Target className="h-5 w-5" />
        </div>
        <div className="min-w-0">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-0.5 font-display text-xs font-semibold">
            ✨ Günün görevi
          </span>
          <p className="mt-1.5 font-display text-base font-bold leading-snug">
            {label}
          </p>
          <p className="text-sm text-white/80">
            {info ? <span>{info.topicName} · </span> : null}
            <span>şu an %{pct} — birlikte yükseltelim!</span>
          </p>
        </div>
      </div>
      <Button
        asChild
        className="shrink-0 gap-2 rounded-full bg-sun font-display font-semibold text-grape shadow-pop-sun hover:bg-sun/90"
      >
        <Link href={practiceHref(target.kazanim_kod)}>
          Hemen çöz
          <ArrowRight className="h-4 w-4" />
        </Link>
      </Button>
    </Card>
  );
}
