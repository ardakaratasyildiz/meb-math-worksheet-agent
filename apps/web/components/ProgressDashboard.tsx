"use client";

import * as React from "react";
import Link from "next/link";
import { useAuth, useUser } from "@clerk/nextjs";
import { Flame, Loader2, Sparkles, Target, TrendingUp } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

import { getGamification, getProgress } from "@/lib/api";
import { practiceHref } from "@/lib/curriculum";
import { subjectLabel, subjectStyle } from "@/lib/subjects";
import type {
  DailyTrendPoint,
  GamificationResponse,
  KazanimProgress,
  ProgressResponse,
  Subject,
} from "@/lib/types";

// ── Yardımcılar ──────────────────────────────────────────────────────────────

const pct = (r: number) => Math.round(r * 100);

/** Zayıf/eksik kazanım için "Çalış" derin-linki — ders farkında. */
function hrefFor(k: KazanimProgress): string {
  const subject = (k.subject ?? "matematik") as Subject;
  if (subject === "matematik") return practiceHref(k.kazanim_kod);
  const p = new URLSearchParams({ subject });
  if (k.grade) p.set("grade", String(k.grade));
  p.set("kazanim", k.kazanim_kod);
  return `/practice/new?${p.toString()}`;
}

interface TopicAgg {
  name: string;
  correct: number;
  total: number;
  ratio: number;
}
interface SubjectGroup {
  subject: Subject;
  correct: number;
  total: number;
  ratio: number;
  topics: TopicAgg[];
  weakest: KazanimProgress | null;
}

/** mastery satırlarını derse göre grupla; her ders için konu kırılımı + en zayıf kazanım. */
function groupBySubject(mastery: KazanimProgress[]): SubjectGroup[] {
  const bySub = new Map<Subject, KazanimProgress[]>();
  for (const m of mastery) {
    const s = (m.subject ?? "matematik") as Subject;
    const arr = bySub.get(s);
    if (arr) arr.push(m);
    else bySub.set(s, [m]);
  }
  const groups: SubjectGroup[] = [];
  for (const [subject, items] of bySub) {
    const byTopic = new Map<string, { correct: number; total: number }>();
    let correct = 0;
    let total = 0;
    for (const it of items) {
      correct += it.correct;
      total += it.total;
      const name = it.topic_name || "Genel";
      const cur = byTopic.get(name) ?? { correct: 0, total: 0 };
      cur.correct += it.correct;
      cur.total += it.total;
      byTopic.set(name, cur);
    }
    const topics: TopicAgg[] = [...byTopic.entries()]
      .map(([name, v]) => ({
        name,
        correct: v.correct,
        total: v.total,
        ratio: v.total ? v.correct / v.total : 0,
      }))
      .sort((a, b) => b.total - a.total);
    const weakest =
      items
        .filter((i) => i.total >= 3)
        .sort((a, b) => a.ratio - b.ratio)[0] ?? null;
    groups.push({
      subject,
      correct,
      total,
      ratio: total ? correct / total : 0,
      topics,
      weakest,
    });
  }
  return groups.sort((a, b) => b.total - a.total);
}

type BadgeTier = "gold" | "silver" | "bronze";
interface SubjectBadgeItem {
  subject: Subject;
  topic: string;
  tier: BadgeTier;
}
const TIER_EMOJI: Record<BadgeTier, string> = {
  gold: "🥇",
  silver: "🥈",
  bronze: "🥉",
};
const TIER_LABEL: Record<BadgeTier, string> = {
  gold: "Altın",
  silver: "Gümüş",
  bronze: "Bronz",
};

/** Konu-bazlı rozetler (ders farkında). Bronz ≥5&%60, Gümüş ≥10&%75, Altın ≥15&%90. */
function computeSubjectBadges(groups: SubjectGroup[]): SubjectBadgeItem[] {
  const out: SubjectBadgeItem[] = [];
  for (const g of groups) {
    for (const t of g.topics) {
      let tier: BadgeTier | null = null;
      if (t.total >= 15 && t.ratio >= 0.9) tier = "gold";
      else if (t.total >= 10 && t.ratio >= 0.75) tier = "silver";
      else if (t.total >= 5 && t.ratio >= 0.6) tier = "bronze";
      if (tier) out.push({ subject: g.subject, topic: t.name, tier });
    }
  }
  return out;
}

// ── Küçük görsel parçalar ────────────────────────────────────────────────────

/** Renkli conic-gradient doğruluk halkası (ders rengiyle). */
function Ring({ value, color }: { value: number; color: string }) {
  return (
    <div
      className="relative h-[72px] w-[72px] shrink-0 rounded-full"
      style={{
        background: `conic-gradient(${color} ${value * 3.6}deg, hsl(var(--muted)) 0deg)`,
      }}
      role="img"
      aria-label={`Doğruluk %${value}`}
    >
      <div className="absolute inset-[7px] flex items-center justify-center rounded-full bg-card">
        <span className="font-display text-base font-bold" style={{ color }}>
          %{value}
        </span>
      </div>
    </div>
  );
}

// ── Bölümler ───────────────────────────────────────────────────────────────

function SubjectCard({ g }: { g: SubjectGroup }) {
  const st = subjectStyle(g.subject);
  const wrong = g.total - g.correct;
  const top = g.topics.slice(0, 3);
  return (
    <Card className="space-y-3 p-4 shadow-pop">
      <div className="flex items-center gap-3">
        <Ring value={pct(g.ratio)} color={st.hex} />
        <div className="min-w-0">
          <div className="flex items-center gap-2 font-display text-base font-bold">
            <span
              className={`grid h-6 w-6 place-items-center rounded-md text-sm ${st.bg}`}
              aria-hidden
            >
              {st.emoji}
            </span>
            {subjectLabel(g.subject)}
          </div>
          <p className="mt-1 text-xs font-semibold text-muted-foreground">
            <span className="text-emerald-600 dark:text-emerald-400">
              {g.correct} ✓
            </span>{" "}
            <span className="text-rose-600 dark:text-rose-400">{wrong} ✕</span> ·{" "}
            {g.total} soru
          </p>
        </div>
      </div>

      <div className="space-y-1.5">
        {top.map((t) => (
          <div key={t.name} className="text-xs">
            <div className="flex items-center justify-between gap-2">
              <span className="min-w-0 truncate font-medium">{t.name}</span>
              <span className="shrink-0 tabular-nums text-muted-foreground">
                %{pct(t.ratio)}
              </span>
            </div>
            <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full"
                style={{ width: `${pct(t.ratio)}%`, background: st.hex }}
              />
            </div>
          </div>
        ))}
      </div>

      {g.weakest ? (
        <div className="flex items-center justify-between gap-2 pt-1">
          <span
            className={`min-w-0 truncate rounded-full px-2.5 py-1 text-[11px] font-semibold ${st.bg} ${st.text}`}
          >
            Zayıf: {g.weakest.topic_name || "Genel"}
          </span>
          <Button asChild size="sm" className="h-8 shrink-0 gap-1">
            <Link href={hrefFor(g.weakest)}>Çalış →</Link>
          </Button>
        </div>
      ) : null}
    </Card>
  );
}

function formatDay(iso: string): string {
  const p = iso.split("-");
  return p.length === 3 ? `${p[2]}.${p[1]}` : iso;
}

function TrendChart({ trend }: { trend: DailyTrendPoint[] }) {
  if (trend.length < 2) return null;
  return (
    <section className="space-y-3">
      <div className="flex items-baseline gap-2">
        <h2 className="font-display text-lg font-bold">Son 30 gün</h2>
        <span className="text-xs text-muted-foreground">
          günlük doğruluk — yeşil ≥%60
        </span>
      </div>
      <Card className="p-4 shadow-pop">
        <div className="flex items-end gap-1.5" style={{ height: 120 }}>
          {trend.map((d) => {
            const p = d.total ? Math.round((d.score / d.total) * 100) : 0;
            const strong = p >= 60;
            return (
              <div
                key={d.date}
                className="flex flex-1 items-end"
                style={{ height: "100%" }}
                title={`${formatDay(d.date)} · ${d.score}/${d.total} · %${p}`}
              >
                <div
                  className={`w-full rounded-t ${strong ? "bg-emerald-500" : "bg-amber-500"}`}
                  style={{ height: `${Math.max(6, p)}%` }}
                />
              </div>
            );
          })}
        </div>
        <div className="mt-2 flex justify-between text-[11px] font-semibold text-muted-foreground">
          <span>{trend.length} aktif gün</span>
          <span>bugün →</span>
        </div>
      </Card>
    </section>
  );
}

// ── Ana bileşen ──────────────────────────────────────────────────────────────

export function ProgressDashboard() {
  const { userId, isLoaded } = useAuth();
  const { user } = useUser();
  const [data, setData] = React.useState<ProgressResponse | null>(null);
  const [game, setGame] = React.useState<GamificationResponse | null>(null);
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
    // Oyunlaştırma kritik değil — sessizce dener, hero olmadan da çalışır.
    getGamification(userId)
      .then((g) => {
        if (active) setGame(g);
      })
      .catch(() => {});
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

  if (data.summary.total_answered === 0) {
    return (
      <Card className="flex flex-col items-center gap-3 p-10 text-center shadow-pop">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
          <TrendingUp className="h-6 w-6" />
        </div>
        <h2 className="font-display font-bold">Henüz çözüm yok</h2>
        <p className="max-w-sm text-sm text-muted-foreground">
          İlk quizini çöz; ders bazlı gelişimin, doğru/yanlış dağılımın ve zayıf
          konuların burada görünmeye başlar.
        </p>
        <Button asChild className="mt-1 gap-2">
          <Link href="/practice/new">
            <Sparkles className="h-4 w-4" />
            İlk quizini çöz
          </Link>
        </Button>
      </Card>
    );
  }

  const { summary } = data;
  const correct = summary.total_correct;
  const wrong = summary.total_answered - correct;
  const accuracy = pct(summary.accuracy);
  const groups = groupBySubject(data.mastery);
  const badges = computeSubjectBadges(groups);
  const firstName = user?.firstName;
  const xpBar =
    game && game.xp_for_next > 0
      ? Math.min(100, Math.round((game.xp_in_level / game.xp_for_next) * 100))
      : 0;

  return (
    <div className="space-y-8">
      {/* HERO — selamlama + seviye/seri/XP (oyunlaştırma varsa) */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-grape to-sky-500 p-6 text-white shadow-pop-grape">
        <span
          aria-hidden
          className="pointer-events-none absolute -top-2 right-3 animate-bob text-6xl drop-shadow-md"
        >
          🦊
        </span>
        <h1 className="font-display text-2xl font-bold">
          {firstName ? `Harika gidiyorsun, ${firstName}!` : "Harika gidiyorsun!"}
        </h1>
        <p className="text-sm font-semibold text-white/85">
          {groups.length > 1
            ? `${groups.length} derste çalıştın 🎯`
            : "Çözmeye devam et 🎯"}
        </p>

        {game ? (
          <div className="mt-4 flex flex-wrap items-center gap-4">
            <div
              className="relative h-[76px] w-[76px] shrink-0 rounded-full"
              style={{
                background: `conic-gradient(#FFD54A ${xpBar * 3.6}deg, rgba(255,255,255,.25) 0deg)`,
              }}
            >
              <div className="absolute inset-[7px] flex flex-col items-center justify-center rounded-full bg-grape text-center">
                <span className="text-[9px] uppercase tracking-wider text-white/80">
                  Seviye
                </span>
                <span className="font-display text-xl font-bold leading-none">
                  {game.level}
                </span>
              </div>
            </div>
            <div className="min-w-[200px] flex-1">
              <div className="flex flex-wrap gap-2">
                <span className="inline-flex items-center gap-1.5 rounded-2xl bg-white/16 px-3 py-1.5 text-sm font-semibold">
                  <Flame className="h-4 w-4 text-orange-300" />
                  {game.streak_current} gün seri
                </span>
                <span className="rounded-2xl bg-white/16 px-3 py-1.5 text-sm font-semibold tabular-nums">
                  {summary.quizzes_solved} quiz
                </span>
              </div>
              <div className="mt-3 h-2.5 overflow-hidden rounded-full bg-white/20">
                <div
                  className="h-full rounded-full bg-yellow-300"
                  style={{ width: `${xpBar}%` }}
                />
              </div>
              <p className="mt-1.5 text-xs font-semibold text-white/85 tabular-nums">
                {game.xp} XP · sonraki seviyeye{" "}
                {Math.max(0, game.xp_for_next - game.xp_in_level)} XP
              </p>
            </div>
          </div>
        ) : null}
      </div>

      {/* DOĞRU / YANLIŞ net gösterim */}
      <section className="space-y-3">
        <div className="flex items-baseline gap-2">
          <h2 className="font-display text-lg font-bold">Doğru &amp; yanlış</h2>
          <span className="text-xs text-muted-foreground">
            çözdüğün tüm sorular
          </span>
        </div>
        <Card className="flex flex-col gap-4 p-5 shadow-pop sm:flex-row sm:items-center">
          <div className="flex gap-6">
            <div className="flex items-center gap-2.5">
              <span className="grid h-9 w-9 place-items-center rounded-xl bg-emerald-500 text-lg font-black text-white">
                ✓
              </span>
              <div>
                <div className="font-display text-2xl font-bold leading-none tabular-nums">
                  {correct}
                </div>
                <div className="text-xs font-semibold text-muted-foreground">
                  doğru
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2.5">
              <span className="grid h-9 w-9 place-items-center rounded-xl bg-rose-500 text-lg font-black text-white">
                ✕
              </span>
              <div>
                <div className="font-display text-2xl font-bold leading-none tabular-nums">
                  {wrong}
                </div>
                <div className="text-xs font-semibold text-muted-foreground">
                  yanlış
                </div>
              </div>
            </div>
          </div>
          <div className="flex-1">
            <div className="flex h-7 overflow-hidden rounded-xl border">
              {correct > 0 ? (
                <div
                  className="flex items-center justify-center bg-emerald-500 text-xs font-bold text-white"
                  style={{ width: `${accuracy}%` }}
                >
                  {accuracy >= 12 ? `%${accuracy}` : ""}
                </div>
              ) : null}
              {wrong > 0 ? (
                <div
                  className="flex flex-1 items-center justify-center bg-rose-500 text-xs font-bold text-white"
                >
                  {100 - accuracy >= 12 ? `%${100 - accuracy}` : ""}
                </div>
              ) : null}
            </div>
            <p className="mt-2 text-xs font-semibold text-muted-foreground tabular-nums">
              Toplam {summary.total_answered} soru · %{accuracy} doğruluk
            </p>
          </div>
        </Card>
      </section>

      {/* DERSLERE GÖRE */}
      {groups.length ? (
        <section className="space-y-3">
          <div className="flex items-baseline gap-2">
            <h2 className="font-display text-lg font-bold">Derslerine göre</h2>
            <span className="text-xs text-muted-foreground">
              her ders için doğruluk ve en zayıf konun
            </span>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {groups.map((g) => (
              <SubjectCard key={g.subject} g={g} />
            ))}
          </div>
        </section>
      ) : null}

      {/* EKSİKLER */}
      {data.weak.length ? (
        <section className="space-y-3">
          <div className="flex items-baseline gap-2">
            <Target className="h-4 w-4 self-center text-rose-500" />
            <h2 className="font-display text-lg font-bold">
              Önce bunları kapatalım
            </h2>
            <span className="text-xs text-muted-foreground">
              en çok zorlandığın kazanımlar
            </span>
          </div>
          <div className="space-y-2.5">
            {data.weak.map((k) => {
              const subject = (k.subject ?? "matematik") as Subject;
              const st = subjectStyle(subject);
              const p = pct(k.ratio);
              const sev = p < 50 ? "#F0563F" : "#E9A100";
              return (
                <Card
                  key={k.kazanim_kod}
                  className="flex items-center gap-3 border-l-4 p-3.5 shadow-pop"
                  style={{ borderLeftColor: sev }}
                >
                  <span
                    className={`grid h-9 w-9 shrink-0 place-items-center rounded-lg text-lg ${st.bg}`}
                    aria-hidden
                  >
                    {st.emoji}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-bold">
                      {k.topic_name || subjectLabel(subject)}{" "}
                      <span className="font-mono text-[11px] font-normal text-muted-foreground">
                        {k.kazanim_kod}
                      </span>
                    </div>
                    <div className="mt-1.5 flex items-center gap-2">
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full rounded-full"
                          style={{ width: `${p}%`, background: sev }}
                        />
                      </div>
                      <span
                        className="shrink-0 text-xs font-bold tabular-nums"
                        style={{ color: sev }}
                      >
                        %{p}
                      </span>
                    </div>
                  </div>
                  <Button asChild size="sm" className="h-8 shrink-0 gap-1">
                    <Link href={hrefFor(k)}>Çalış</Link>
                  </Button>
                </Card>
              );
            })}
          </div>
        </section>
      ) : null}

      {/* TREND */}
      <TrendChart trend={data.daily_trend ?? []} />

      {/* ROZETLER */}
      <section className="space-y-3">
        <div className="flex items-baseline gap-2">
          <h2 className="font-display text-lg font-bold">Rozetlerin</h2>
          <span className="text-xs text-muted-foreground">
            bir konuda ustalaştıkça kazanırsın
          </span>
        </div>
        {badges.length ? (
          <div className="flex flex-wrap gap-2">
            {badges.map((b, i) => {
              const st = subjectStyle(b.subject);
              return (
                <div
                  key={`${b.subject}-${b.topic}-${i}`}
                  className="flex items-center gap-2 rounded-2xl border bg-card px-3.5 py-2 shadow-pop"
                  title={`${TIER_LABEL[b.tier]} · ${subjectLabel(b.subject)}`}
                >
                  <span className="text-xl">{TIER_EMOJI[b.tier]}</span>
                  <div>
                    <div className="text-sm font-bold">{b.topic}</div>
                    <div className={`text-[11px] font-semibold ${st.text}`}>
                      {subjectLabel(b.subject)} · {TIER_LABEL[b.tier]}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <Card className="p-5 text-sm text-muted-foreground shadow-pop">
            Henüz rozet yok — bir konuda en az 5 soru çözüp %60 başarıyla ilk
            rozetini kazan. 🏅
          </Card>
        )}
      </section>
    </div>
  );
}
