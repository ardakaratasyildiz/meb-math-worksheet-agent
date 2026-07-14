"use client";

import * as React from "react";
import { useAuth } from "@clerk/nextjs";
import { Loader2, UserPlus } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getChildProgress, linkChild, listChildren } from "@/lib/api";
import { subjectLabel, subjectStyle } from "@/lib/subjects";
import type { ChildItem, ProgressResponse, Subject } from "@/lib/types";

const pct = (r: number) => Math.round(r * 100);

/**
 * Veli tarafı (WS-6b): çocuğun takip kodunu gir → ekle → ilerlemesini (salt-okunur) gör.
 * Öğrenci onayı KODDADIR (öğrenci kodu paylaşmadıkça kimse bağlanamaz). Veli yüzünde
 * gösterilir. Öğrenci kendi kodunu StudentParentCodeCard'dan alır.
 */
export function ParentDashboard() {
  const { userId, isLoaded } = useAuth();
  const [childCode, setChildCode] = React.useState("");
  const [childLabel, setChildLabel] = React.useState("");
  const [children, setChildren] = React.useState<ChildItem[]>([]);
  const [linking, setLinking] = React.useState(false);
  const [selected, setSelected] = React.useState<ChildItem | null>(null);
  const [childProgress, setChildProgress] = React.useState<ProgressResponse | null>(null);
  const [progressLoading, setProgressLoading] = React.useState(false);

  React.useEffect(() => {
    if (isLoaded && userId) {
      listChildren(userId).then(setChildren).catch(() => {});
    }
  }, [userId, isLoaded]);

  if (!isLoaded || !userId) return null;

  async function addChild() {
    if (!userId || !childCode.trim()) return;
    setLinking(true);
    try {
      await linkChild(userId, childCode.trim(), childLabel.trim() || undefined);
      setChildCode("");
      setChildLabel("");
      setChildren(await listChildren(userId));
      toast.success("Çocuk eklendi");
    } catch (e: unknown) {
      toast.error("Bağlanamadı", {
        description: e instanceof Error ? e.message : "Kod geçersiz olabilir.",
      });
    } finally {
      setLinking(false);
    }
  }

  async function openChild(c: ChildItem) {
    if (!userId) return;
    setSelected(c);
    setChildProgress(null);
    setProgressLoading(true);
    try {
      setChildProgress(await getChildProgress(userId, c.student_id));
    } catch {
      toast.error("İlerleme alınamadı");
    } finally {
      setProgressLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <Card className="space-y-3 p-4 shadow-pop">
        <p className="text-sm font-semibold">Çocuğunu ekle</p>
        <p className="text-xs text-muted-foreground">
          Çocuğun kendi hesabından aldığı takip kodunu gir. Kodu yalnızca çocuğun
          paylaşabilir (onay koddadır).
        </p>
        <div className="flex flex-wrap items-end gap-2">
          <div className="flex-1 space-y-1">
            <label className="text-xs text-muted-foreground">Çocuğun takip kodu</label>
            <Input
              value={childCode}
              onChange={(e) => setChildCode(e.target.value.toUpperCase())}
              placeholder="ör. CNRZX8"
              className="font-mono uppercase"
            />
          </div>
          <div className="flex-1 space-y-1">
            <label className="text-xs text-muted-foreground">Ad (isteğe bağlı)</label>
            <Input
              value={childLabel}
              onChange={(e) => setChildLabel(e.target.value)}
              placeholder="ör. Ayşe"
            />
          </div>
          <Button onClick={addChild} disabled={linking || !childCode.trim()} className="gap-2">
            {linking ? <Loader2 className="h-4 w-4 animate-spin" /> : <UserPlus className="h-4 w-4" />}
            Ekle
          </Button>
        </div>

        {children.length ? (
          <div className="flex flex-wrap gap-2 pt-1">
            {children.map((c) => (
              <button
                key={c.student_id}
                type="button"
                onClick={() => openChild(c)}
                className={`rounded-full border px-3 py-1.5 text-sm font-semibold transition-colors ${
                  selected?.student_id === c.student_id
                    ? "border-grape bg-grape/10 text-grape"
                    : "border-border hover:bg-accent/40"
                }`}
              >
                {c.label}
              </button>
            ))}
          </div>
        ) : null}
      </Card>

      {selected ? (
        <Card className="space-y-3 p-4 shadow-pop">
          <p className="text-sm font-semibold">{selected.label} · ilerleme</p>
          {progressLoading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" /> Yükleniyor…
            </div>
          ) : childProgress && childProgress.summary.total_answered > 0 ? (
            <ChildSummary data={childProgress} />
          ) : (
            <p className="text-sm text-muted-foreground">Bu öğrenci henüz quiz çözmemiş.</p>
          )}
        </Card>
      ) : null}
    </div>
  );
}

function ChildSummary({ data }: { data: ProgressResponse }) {
  const s = data.summary;
  const wrong = s.total_answered - s.total_correct;
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-4 text-sm">
        <span>
          Doğruluk: <b className="tabular-nums">%{pct(s.accuracy)}</b>
        </span>
        <span className="text-emerald-600 dark:text-emerald-400">{s.total_correct} doğru</span>
        <span className="text-rose-600 dark:text-rose-400">{wrong} yanlış</span>
        <span className="tabular-nums text-muted-foreground">{s.quizzes_solved} quiz</span>
      </div>
      {data.weak.length ? (
        <div className="space-y-1.5">
          <p className="text-xs font-semibold text-muted-foreground">Geliştirilecek konular</p>
          {data.weak.slice(0, 5).map((k) => {
            const subject = (k.subject ?? "matematik") as Subject;
            const st = subjectStyle(subject);
            return (
              <div key={k.kazanim_kod} className="flex items-center gap-2 text-sm">
                <span className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${st.bg} ${st.text}`}>
                  {st.emoji} {subjectLabel(subject)}
                </span>
                <span className="min-w-0 flex-1 truncate">
                  {k.topic_name || k.kazanim_kod}
                </span>
                <span className="shrink-0 tabular-nums text-rose-600 dark:text-rose-400">
                  %{pct(k.ratio)}
                </span>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">Belirgin zayıf konu yok 👏</p>
      )}
    </div>
  );
}
