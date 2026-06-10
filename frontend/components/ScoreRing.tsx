"use client";

import * as React from "react";

// Skor halkası — yüzdelik görsel. Tailwind conic-gradient üretemediği için inline
// style. Renk eşiğe göre: yeşil (>=70), amber (40-69), kırmızı (<40).
function ringColor(pct: number): string {
  if (pct >= 70) return "#10b981"; // emerald-500
  if (pct >= 40) return "#f59e0b"; // amber-500
  return "#ef4444"; // red-500
}

export function ScoreRing({
  pct,
  label,
  size = 112,
}: {
  pct: number;
  label?: string;
  size?: number;
}) {
  const clamped = Math.max(0, Math.min(100, pct));
  const color = ringColor(clamped);
  return (
    <div
      className="relative shrink-0"
      style={{ width: size, height: size }}
      role="img"
      aria-label={`Skor: yüzde ${clamped}`}
    >
      <div
        className="h-full w-full rounded-full"
        style={{
          background: `conic-gradient(${color} ${clamped * 3.6}deg, hsl(var(--muted)) 0deg)`,
        }}
      />
      <div className="absolute inset-[10px] flex flex-col items-center justify-center rounded-full bg-background">
        <span className="text-2xl font-bold tabular-nums">%{clamped}</span>
        {label ? (
          <span className="text-[10px] text-muted-foreground">{label}</span>
        ) : null}
      </div>
    </div>
  );
}
