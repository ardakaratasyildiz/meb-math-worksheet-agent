"use client";

import * as React from "react";
import { useAuth } from "@clerk/nextjs";
import { Flame } from "lucide-react";

import { Card } from "@/components/ui/card";

import { getGamification } from "@/lib/api";
import { computeBadges } from "@/lib/badges";
import type {
  BadgeTier,
  GamificationResponse,
  KazanimProgress,
} from "@/lib/types";

const TIER_STYLE: Record<BadgeTier, { ring: string; emoji: string; label: string }> = {
  bronze: { ring: "border-amber-700/40 bg-amber-700/10", emoji: "🥉", label: "Bronz" },
  silver: { ring: "border-slate-400/40 bg-slate-400/10", emoji: "🥈", label: "Gümüş" },
  gold: { ring: "border-yellow-500/40 bg-yellow-500/10", emoji: "🥇", label: "Altın" },
};

export function GamificationPanel({
  mastery,
}: {
  mastery: KazanimProgress[];
}) {
  const { userId, isLoaded } = useAuth();
  const [data, setData] = React.useState<GamificationResponse | null>(null);

  React.useEffect(() => {
    if (!isLoaded || !userId) return;
    let active = true;
    getGamification(userId)
      .then((d) => {
        if (active) setData(d);
      })
      .catch(() => {
        /* sessiz — oyunlaştırma kritik değil */
      });
    return () => {
      active = false;
    };
  }, [userId, isLoaded]);

  if (!data) return null;

  const badges = computeBadges(mastery);
  const barPct =
    data.xp_for_next > 0
      ? Math.min(100, Math.round((data.xp_in_level / data.xp_for_next) * 100))
      : 0;

  return (
    <Card className="space-y-4 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-primary/10 text-lg font-bold text-primary">
            {data.level}
          </div>
          <div>
            <p className="text-sm font-semibold">Seviye {data.level}</p>
            <p className="text-xs text-muted-foreground">{data.xp} XP</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 text-sm">
          <Flame
            className={`h-4 w-4 ${data.streak_current > 0 ? "text-orange-500" : "text-muted-foreground"}`}
          />
          <span className="font-medium tabular-nums">{data.streak_current}</span>
          <span className="text-muted-foreground">gün seri</span>
          {data.streak_longest > data.streak_current ? (
            <span className="text-xs text-muted-foreground">
              (en uzun {data.streak_longest})
            </span>
          ) : null}
        </div>
      </div>

      {/* Seviye barı */}
      <div className="space-y-1">
        <div className="flex items-center justify-between text-[11px] text-muted-foreground">
          <span>Seviye {data.level}</span>
          <span className="tabular-nums">
            {data.xp_in_level}/{data.xp_for_next} XP
          </span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-muted">
          <div
            className="h-full bg-primary"
            style={{ width: `${barPct}%` }}
          />
        </div>
      </div>

      {/* Rozetler */}
      {badges.length ? (
        <div className="flex flex-wrap gap-2">
          {badges.map((b) => {
            const s = TIER_STYLE[b.tier];
            return (
              <div
                key={b.topicId}
                className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs ${s.ring}`}
                title={`${s.label} · ${b.total} soru · %${Math.round(b.ratio * 100)}`}
              >
                <span>{s.emoji}</span>
                <span className="font-medium">{b.topicName}</span>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="text-xs text-muted-foreground">
          Henüz rozet yok — bir konuda en az 5 soru çözüp %60 başarıyla ilk
          rozetini kazan.
        </p>
      )}
    </Card>
  );
}
