"use client";

import * as React from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import {
  ArrowLeft,
  Check,
  Copy,
  Loader2,
  NotebookPen,
  Plus,
  Users,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { assignQuiz, getClassroom, listMyQuizzes } from "@/lib/api";
import type { ClassroomDetail, MyQuizItem } from "@/lib/types";

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("tr-TR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

export function ClassroomDetailView({ classroomId }: { classroomId: string }) {
  const { userId, isLoaded } = useAuth();
  const [data, setData] = React.useState<ClassroomDetail | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [copied, setCopied] = React.useState(false);

  // Ödev atama paneli
  const [picking, setPicking] = React.useState(false);
  const [myQuizzes, setMyQuizzes] = React.useState<MyQuizItem[] | null>(null);
  const [assigningId, setAssigningId] = React.useState<string | null>(null);

  const reload = React.useCallback(async () => {
    if (!userId) return;
    const d = await getClassroom(classroomId, userId);
    setData(d);
  }, [classroomId, userId]);

  React.useEffect(() => {
    if (!isLoaded) return;
    if (!userId) {
      setError("Oturum bulunamadı.");
      setLoading(false);
      return;
    }
    let active = true;
    setLoading(true);
    getClassroom(classroomId, userId)
      .then((d) => active && setData(d))
      .catch((e: unknown) =>
        active && setError(e instanceof Error ? e.message : "Sınıf yüklenemedi."),
      )
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [classroomId, userId, isLoaded]);

  async function openPicker() {
    if (!userId) return;
    setPicking(true);
    if (myQuizzes === null) {
      try {
        setMyQuizzes(await listMyQuizzes(userId));
      } catch (e: unknown) {
        toast.error("Quizlerin alınamadı", {
          description: e instanceof Error ? e.message : undefined,
        });
        setMyQuizzes([]);
      }
    }
  }

  async function onAssign(quizId: string) {
    if (!userId) return;
    setAssigningId(quizId);
    try {
      await assignQuiz(classroomId, userId, quizId);
      toast.success("Ödev atandı");
      setPicking(false);
      await reload();
    } catch (e: unknown) {
      toast.error("Ödev atanamadı", {
        description: e instanceof Error ? e.message : undefined,
      });
    } finally {
      setAssigningId(null);
    }
  }

  async function copyCode() {
    if (!data?.join_code) return;
    try {
      await navigator.clipboard.writeText(data.join_code);
      setCopied(true);
      toast.success("Kod kopyalandı");
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Kopyalanamadı");
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
        Sınıf yükleniyor…
      </div>
    );
  }

  if (error || !data) {
    return (
      <Card className="p-6">
        <p className="text-sm text-destructive">{error ?? "Sınıf bulunamadı."}</p>
        <Button asChild variant="outline" size="sm" className="mt-3">
          <Link href="/practice/classes">Sınıflarım</Link>
        </Button>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Link
          href="/practice/classes"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Sınıflarım
        </Link>
        <h1 className="text-2xl font-semibold tracking-tight">{data.name}</h1>
        <p className="flex items-center gap-1 text-sm text-muted-foreground">
          <Users className="h-4 w-4" />
          {data.member_count} öğrenci
          {data.is_owner ? " · öğretmenisin" : " · katıldığın sınıf"}
        </p>
      </div>

      {/* Sahip: katılma kodu paylaşımı */}
      {data.is_owner && data.join_code ? (
        <Card className="space-y-2 p-5">
          <h2 className="font-display font-bold">Katılma kodu</h2>
          <p className="text-sm text-muted-foreground">
            Öğrencilerin <strong>Sınıfa katıl</strong> ekranına bu kodu girsin.
          </p>
          <div className="flex items-center gap-3">
            <span className="rounded-lg bg-muted px-4 py-2 font-mono text-2xl font-bold tracking-[0.3em]">
              {data.join_code}
            </span>
            <Button onClick={copyCode} variant="outline" size="sm" className="gap-1.5">
              {copied ? (
                <Check className="h-4 w-4 text-emerald-500" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
              Kopyala
            </Button>
          </div>
        </Card>
      ) : null}

      {/* Sahip: ödevler (ata + liste) */}
      {data.is_owner ? (
        <Card className="space-y-3 p-5">
          <div className="flex items-center justify-between gap-2">
            <h2 className="font-display font-bold">
              Ödevler ({data.assignments.length})
            </h2>
            {!picking ? (
              <Button onClick={openPicker} size="sm" className="gap-1.5">
                <Plus className="h-4 w-4" />
                Ödev ata
              </Button>
            ) : (
              <Button onClick={() => setPicking(false)} size="sm" variant="ghost">
                Kapat
              </Button>
            )}
          </div>

          {/* Quiz seçici (kendi quizlerinden ata) */}
          {picking ? (
            myQuizzes === null ? (
              <div className="flex items-center gap-2 py-3 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Quizlerin yükleniyor…
              </div>
            ) : myQuizzes.length === 0 ? (
              <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
                Henüz quiz üretmedin.{" "}
                <Link href="/practice/new" className="font-medium text-primary underline">
                  Yeni quiz üret
                </Link>{" "}
                sonra buradan ödev olarak ata.
              </div>
            ) : (
              <ul className="divide-y rounded-lg border">
                {myQuizzes.map((q) => (
                  <li
                    key={q.id}
                    className="flex items-center justify-between gap-2 px-4 py-2.5 text-sm"
                  >
                    <span className="min-w-0 truncate">{q.title}</span>
                    <Button
                      onClick={() => onAssign(q.id)}
                      disabled={assigningId !== null}
                      size="sm"
                      variant="outline"
                      className="shrink-0 gap-1"
                    >
                      {assigningId === q.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Plus className="h-4 w-4" />
                      )}
                      Ata
                    </Button>
                  </li>
                ))}
              </ul>
            )
          ) : null}

          {/* Atanmış ödevler */}
          {data.assignments.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Henüz ödev atamadın. Quizlerinden birini sınıfa ata.
            </p>
          ) : (
            <ul className="divide-y">
              {data.assignments.map((a) => (
                <li key={a.id} className="flex items-center gap-2 py-2.5 text-sm">
                  <NotebookPen className="h-4 w-4 shrink-0 text-amber-500" />
                  <span className="min-w-0 truncate font-medium">{a.title}</span>
                  <span className="ml-auto shrink-0 text-xs text-muted-foreground">
                    {formatDate(a.created_at)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      ) : null}

      {/* Sahip: öğrenci listesi */}
      {data.is_owner ? (
        <Card className="overflow-hidden">
          <div className="border-b px-5 py-3">
            <h2 className="font-display font-bold">Öğrenciler ({data.member_count})</h2>
          </div>
          {data.members.length === 0 ? (
            <p className="px-5 py-6 text-sm text-muted-foreground">
              Henüz katılan yok. Katılma kodunu öğrencilerinle paylaş.
            </p>
          ) : (
            <ul className="divide-y">
              {data.members.map((m) => (
                <li
                  key={m.student_tenant_id}
                  className="flex items-center justify-between px-5 py-3 text-sm"
                >
                  <span className="font-medium">{m.display_name}</span>
                  <span className="text-xs text-muted-foreground">
                    {formatDate(m.joined_at)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      ) : (
        <Card className="p-5 text-sm text-muted-foreground">
          Bu sınıfa katıldın. Öğretmenin verdiği ödevler{" "}
          <Link href="/practice/assignments" className="font-medium text-primary underline">
            Ödevlerim
          </Link>{" "}
          sayfanda görünür.
        </Card>
      )}
    </div>
  );
}
