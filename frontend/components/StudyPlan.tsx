"use client";

import * as React from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { CalendarDays, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { createStudyPlan, getStudyPlan } from "@/lib/api";
import { practiceHref } from "@/lib/curriculum";
import { subjectLabel, subjectStyle } from "@/lib/subjects";
import type { StudyPlanDay, StudyPlanResponse, Subject } from "@/lib/types";

/** Gün türü rozeti — odak (eksik) / tekrar / karışık. */
const KIND_META: Record<string, { label: string; cls: string }> = {
  focus: { label: "Odak", cls: "bg-grape/10 text-grape" },
  review: { label: "Tekrar", cls: "bg-mint/20 text-emerald-600 dark:text-emerald-400" },
  mixed: { label: "Karışık", cls: "bg-sun/25 text-amber-600 dark:text-amber-400" },
};

/** Programdaki bir günün kazanımı için "Çalış" derin-linki (ders-farkında). */
function hrefForDay(d: StudyPlanDay): string {
  const subject = (d.subject ?? "matematik") as Subject;
  const kod = d.kazanim_kod ?? "";
  if (subject === "matematik") return kod ? practiceHref(kod) : "/practice/new";
  const p = new URLSearchParams({ subject });
  if (d.grade) p.set("grade", String(d.grade));
  if (kod) p.set("kazanim", kod);
  return `/practice/new?${p.toString()}`;
}

function formatDate(iso?: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? ""
    : d.toLocaleDateString("tr-TR", { day: "numeric", month: "long" });
}

/**
 * AI haftalık çalışma programı (WS-6a) — kullanıcı bazlı KALICI ("Çalışma Programım"
 * sekmesi). Mount'ta kayıtlı program getirilir; yoksa "oluştur" CTA'sı gösterilir.
 * "Yenile" yeni program üretip kaydeder. 7 gün · odak (eksik) + tekrar + karışık.
 */
export function StudyPlan() {
  const { userId, isLoaded } = useAuth();
  const [plan, setPlan] = React.useState<StudyPlanResponse | null>(null);
  const [loading, setLoading] = React.useState(false); // üretim in-flight
  const [initializing, setInitializing] = React.useState(true);

  // Kayıtlı programı getir (created_at boşsa henüz yok → CTA).
  React.useEffect(() => {
    if (!userId) {
      setInitializing(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const p = await getStudyPlan(userId);
        if (!cancelled) setPlan(p.created_at ? p : null);
      } catch {
        // sessiz — CTA gösterilir
      } finally {
        if (!cancelled) setInitializing(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [userId]);

  async function generate() {
    if (!userId) return;
    setLoading(true);
    try {
      setPlan(await createStudyPlan(userId));
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Program oluşturulamadı.";
      toast.error("Program oluşturulamadı", { description: msg });
    } finally {
      setLoading(false);
    }
  }

  if (!isLoaded || !userId) return null;

  const hasPlan = !!plan?.created_at;

  return (
    <section className="space-y-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div className="flex items-baseline gap-2">
          <CalendarDays className="h-4 w-4 self-center text-grape" />
          <h2 className="font-display text-lg font-bold">Haftalık çalışma programı</h2>
          <span className="text-xs text-muted-foreground">
            7 gün · eksik + tekrar + karışık, yapay zeka destekli
          </span>
        </div>
        {hasPlan ? (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={generate}
            disabled={loading}
            className="gap-1.5 text-xs"
          >
            {loading ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Sparkles className="h-3.5 w-3.5" />
            )}
            Yenile
          </Button>
        ) : null}
      </div>

      {initializing ? (
        <Card className="flex items-center gap-2 p-5 text-sm text-muted-foreground shadow-pop">
          <Loader2 className="h-4 w-4 animate-spin" /> Programın yükleniyor…
        </Card>
      ) : !hasPlan ? (
        <Card className="flex flex-col items-start gap-3 p-5 shadow-pop">
          <p className="text-sm text-muted-foreground">
            Haftaya yayılmış, dengeli bir program: eksik konularını pekiştir,
            öğrendiklerini tekrar et ve karışık sorularla kendini dene. Program
            oluşturunca burada kalır.
          </p>
          <Button onClick={generate} disabled={loading} className="gap-2">
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" /> Hazırlanıyor…
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" /> AI ile programımı oluştur
              </>
            )}
          </Button>
        </Card>
      ) : (
        <div className="space-y-3">
          <Card className="flex flex-wrap items-center justify-between gap-2 p-4 shadow-pop">
            <p className="text-sm">{plan!.summary}</p>
            {plan!.created_at ? (
              <span className="shrink-0 text-[11px] text-muted-foreground">
                {formatDate(plan!.created_at)} tarihinde hazırlandı
              </span>
            ) : null}
          </Card>

          {plan!.days.map((d) => {
            const subject = (d.subject ?? "matematik") as Subject;
            const st = subjectStyle(subject);
            return (
              <Card
                key={d.day_no}
                className="flex items-start gap-3 border-l-4 p-4 shadow-pop"
                style={{ borderLeftColor: st.hex }}
              >
                <span
                  className="grid h-9 w-9 shrink-0 place-items-center rounded-xl font-display text-sm font-bold text-white"
                  style={{ background: st.hex }}
                >
                  {d.day_no}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    {d.weekday ? (
                      <span className="text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
                        {d.weekday}
                      </span>
                    ) : null}
                    {d.kind && KIND_META[d.kind] ? (
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${KIND_META[d.kind].cls}`}
                      >
                        {KIND_META[d.kind].label}
                      </span>
                    ) : null}
                  </div>
                  <div className="mt-0.5 flex flex-wrap items-center gap-2">
                    <span className="font-display text-sm font-bold">{d.title}</span>
                    <span
                      className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${st.bg} ${st.text}`}
                    >
                      {st.emoji} {subjectLabel(subject)}
                      {d.grade ? ` · ${d.grade}. sınıf` : ""}
                    </span>
                  </div>
                  {d.tip ? (
                    <p className="mt-1 text-xs text-muted-foreground">{d.tip}</p>
                  ) : null}
                  <div className="mt-2 flex items-center justify-between gap-2">
                    <span className="text-[11px] font-semibold text-muted-foreground">
                      {d.topic_name} · {d.question_count} soru
                    </span>
                    <Button asChild size="sm" className="h-8 shrink-0 gap-1">
                      <Link href={hrefForDay(d)}>Çalış →</Link>
                    </Button>
                  </div>
                </div>
              </Card>
            );
          })}

          {plan!.ai_generated ? (
            <p className="text-[11px] text-muted-foreground">
              ✨ Bu haftalık program yapay zeka ile hazırlandı (eksik + tekrar + karışık).
            </p>
          ) : null}
        </div>
      )}
    </section>
  );
}
