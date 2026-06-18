"use client";

import * as React from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { Bell } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { listMyAssignments } from "@/lib/api";

/**
 * Uygulama-içi bildirim (sıfır altyapı): öğrencinin çözülmemiş ödevlerini hub'ın
 * tepesinde gösterir. Gecikmiş / yakında-son ödevleri ayrıca vurgular.
 * Çözülmemiş ödev yoksa hiçbir şey render etmez.
 */
export function AssignmentAlert() {
  const { userId, isLoaded } = useAuth();
  const [unsolved, setUnsolved] = React.useState(0);
  const [overdue, setOverdue] = React.useState(0);
  const [dueSoon, setDueSoon] = React.useState(0);
  const [ready, setReady] = React.useState(false);

  React.useEffect(() => {
    if (!isLoaded || !userId) return;
    let active = true;
    listMyAssignments(userId)
      .then((items) => {
        if (!active) return;
        const now = Date.now();
        const open = items.filter((a) => !a.solved);
        let od = 0;
        let soon = 0;
        for (const a of open) {
          if (!a.due_at) continue;
          const t = new Date(a.due_at).getTime();
          if (t < now) od += 1;
          else if (t - now < 48 * 3600 * 1000) soon += 1;
        }
        setUnsolved(open.length);
        setOverdue(od);
        setDueSoon(soon);
        setReady(true);
      })
      .catch(() => {
        /* sessiz — bildirim kritik değil */
      });
    return () => {
      active = false;
    };
  }, [userId, isLoaded]);

  if (!ready || unsolved === 0) return null;

  const parts: string[] = [];
  if (overdue) parts.push(`${overdue} tanesinin süresi doldu`);
  if (dueSoon) parts.push(`${dueSoon} tanesi yakında son`);

  return (
    <Card className="flex items-center gap-3 border-rose-400/30 bg-rose-400/5 p-4">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-rose-400/15 text-rose-500">
        <Bell className="h-5 w-5" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="font-display font-bold">
          {unsolved} çözülmemiş ödevin var
        </p>
        {parts.length ? (
          <p className="text-sm text-muted-foreground">{parts.join(" · ")}</p>
        ) : null}
      </div>
      <Button asChild size="sm" className="shrink-0">
        <Link href="/practice/assignments">Ödevlerime git</Link>
      </Button>
    </Card>
  );
}
