"use client";

import * as React from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import {
  ArrowLeft,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Circle,
  Copy,
  Loader2,
  NotebookPen,
  Plus,
  Users,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  assignPdf,
  assignQuiz,
  getAssignmentResults,
  getClassroom,
  listMyQuizzes,
  listWorksheetHistory,
} from "@/lib/api";
import type { HistoryItem } from "@/lib/history";
import type {
  AssignmentResultsResponse,
  AssignmentSummary,
  ClassroomDetail,
  MyQuizItem,
} from "@/lib/types";

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
  const [pickerSource, setPickerSource] = React.useState<"quiz" | "pdf">("quiz");
  const [myQuizzes, setMyQuizzes] = React.useState<MyQuizItem[] | null>(null);
  const [myWorksheets, setMyWorksheets] = React.useState<HistoryItem[] | null>(null);
  const [assigningId, setAssigningId] = React.useState<string | null>(null);
  const [dueDate, setDueDate] = React.useState(""); // YYYY-MM-DD, opsiyonel

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
    setPickerSource("quiz");
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

  async function selectPdfSource() {
    setPickerSource("pdf");
    if (!userId || myWorksheets !== null) return;
    try {
      setMyWorksheets(await listWorksheetHistory(userId));
    } catch (e: unknown) {
      toast.error("Çalışma kağıtların alınamadı", {
        description: e instanceof Error ? e.message : undefined,
      });
      setMyWorksheets([]);
    }
  }

  async function finishAssign(label: string) {
    toast.success(label);
    setPicking(false);
    setDueDate("");
    await reload();
  }

  async function onAssign(quizId: string) {
    if (!userId) return;
    setAssigningId(quizId);
    try {
      await assignQuiz(classroomId, userId, quizId, dueDate || null);
      await finishAssign("Ödev atandı");
    } catch (e: unknown) {
      toast.error("Ödev atanamadı", {
        description: e instanceof Error ? e.message : undefined,
      });
    } finally {
      setAssigningId(null);
    }
  }

  async function onAssignPdf(item: HistoryItem) {
    if (!userId) return;
    setAssigningId(item.id);
    try {
      await assignPdf(classroomId, userId, item.response.worksheet, dueDate || null);
      await finishAssign("PDF ödev atandı");
    } catch (e: unknown) {
      toast.error("PDF ödev atanamadı", {
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

          {/* Ödev kaynağı: çözülebilir Quiz veya PDF çalışma kağıdı */}
          {picking ? (
            <div className="space-y-3">
              <div className="inline-flex gap-1 rounded-lg bg-muted p-1 text-sm">
                <button
                  type="button"
                  onClick={() => setPickerSource("quiz")}
                  className={`rounded-md px-3 py-1.5 font-medium transition-colors ${
                    pickerSource === "quiz"
                      ? "bg-background shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Quiz (çözülebilir)
                </button>
                <button
                  type="button"
                  onClick={selectPdfSource}
                  className={`rounded-md px-3 py-1.5 font-medium transition-colors ${
                    pickerSource === "pdf"
                      ? "bg-background shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Çalışma kağıdı (PDF)
                </button>
              </div>

              <label className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                Son teslim (opsiyonel):
                <Input
                  type="date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="h-9 w-auto"
                />
                {dueDate ? (
                  <button
                    type="button"
                    onClick={() => setDueDate("")}
                    className="text-xs underline hover:text-foreground"
                  >
                    temizle
                  </button>
                ) : null}
              </label>

              {pickerSource === "quiz" ? (
                myQuizzes === null ? (
                  <p className="flex items-center gap-2 py-3 text-sm text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" /> Quizlerin yükleniyor…
                  </p>
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
              ) : myWorksheets === null ? (
                <p className="flex items-center gap-2 py-3 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" /> Çalışma kağıtların yükleniyor…
                </p>
              ) : myWorksheets.length === 0 ? (
                <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
                  Henüz çalışma kağıdı üretmedin.{" "}
                  <Link href="/generate" className="font-medium text-primary underline">
                    Çalışma kağıdı üret
                  </Link>{" "}
                  sonra PDF ödev olarak ata.
                </div>
              ) : (
                <ul className="divide-y rounded-lg border">
                  {myWorksheets.map((it) => (
                    <li
                      key={it.id}
                      className="flex items-center justify-between gap-2 px-4 py-2.5 text-sm"
                    >
                      <span className="min-w-0 truncate">
                        {it.response.worksheet.title}
                      </span>
                      <Button
                        onClick={() => onAssignPdf(it)}
                        disabled={assigningId !== null}
                        size="sm"
                        variant="outline"
                        className="shrink-0 gap-1"
                      >
                        {assigningId === it.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Plus className="h-4 w-4" />
                        )}
                        Ata
                      </Button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ) : null}

          {/* Atanmış ödevler */}
          {data.assignments.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Henüz ödev atamadın. Quizlerinden birini sınıfa ata.
            </p>
          ) : (
            <ul className="divide-y rounded-lg border">
              {data.assignments.map((a) => (
                <AssignmentRow
                  key={a.id}
                  assignment={a}
                  tenantId={userId as string}
                />
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

/** Ödev satırı — tıklayınca sonuç panosunu (sınıf roster'ı) açar. */
function AssignmentRow({
  assignment,
  tenantId,
}: {
  assignment: AssignmentSummary;
  tenantId: string;
}) {
  const [open, setOpen] = React.useState(false);
  const [results, setResults] = React.useState<AssignmentResultsResponse | null>(
    null,
  );
  const [loading, setLoading] = React.useState(false);
  const isPdf = assignment.assignment_type === "pdf";

  // PDF ödev: site içi çözüm/sonuç yok → genişlemeyen sade satır.
  if (isPdf) {
    return (
      <li className="flex items-center gap-2 px-4 py-2.5 text-sm">
        <NotebookPen className="h-4 w-4 shrink-0 text-rose-500" />
        <span className="min-w-0 truncate font-medium">{assignment.title}</span>
        <span className="shrink-0 rounded-full bg-rose-400/15 px-2 py-0.5 text-[11px] font-semibold text-rose-500">
          PDF
        </span>
        {assignment.due_at ? (
          <span className="shrink-0 text-[11px] text-muted-foreground">
            son: {formatDate(assignment.due_at)}
          </span>
        ) : null}
        <span className="ml-auto shrink-0 text-xs text-muted-foreground">
          indirilebilir · takip yok
        </span>
      </li>
    );
  }

  async function toggle() {
    const next = !open;
    setOpen(next);
    if (next && results === null) {
      setLoading(true);
      try {
        setResults(await getAssignmentResults(assignment.id, tenantId));
      } catch (e: unknown) {
        toast.error("Sonuçlar alınamadı", {
          description: e instanceof Error ? e.message : undefined,
        });
        setOpen(false);
      } finally {
        setLoading(false);
      }
    }
  }

  return (
    <li className="text-sm">
      <button
        type="button"
        onClick={toggle}
        className="flex w-full items-center gap-2 px-4 py-2.5 text-left transition-colors hover:bg-accent/20"
      >
        {open ? (
          <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
        )}
        <NotebookPen className="h-4 w-4 shrink-0 text-amber-500" />
        <span className="min-w-0 truncate font-medium">{assignment.title}</span>
        {assignment.due_at ? (
          <span
            className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-semibold ${
              new Date(assignment.due_at) < new Date()
                ? "bg-rose-400/15 text-rose-500"
                : "bg-amber-400/15 text-amber-600 dark:text-amber-400"
            }`}
          >
            son: {formatDate(assignment.due_at)}
          </span>
        ) : null}
        <span className="ml-auto shrink-0 text-xs text-muted-foreground">
          {results
            ? `${results.solved_count}/${results.member_count} çözdü`
            : formatDate(assignment.created_at)}
        </span>
      </button>

      {open ? (
        <div className="border-t bg-muted/30 px-4 py-3">
          {loading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Sonuçlar yükleniyor…
            </div>
          ) : results && results.items.length > 0 ? (
            <ul className="space-y-1.5">
              {results.items.map((it) => {
                const pct =
                  it.solved && it.total
                    ? Math.round(((it.score ?? 0) / it.total) * 100)
                    : 0;
                return (
                  <li
                    key={it.student_tenant_id}
                    className="flex items-center gap-2"
                  >
                    {it.solved ? (
                      <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-500" />
                    ) : (
                      <Circle className="h-4 w-4 shrink-0 text-muted-foreground/40" />
                    )}
                    <span className="min-w-0 truncate">{it.display_name}</span>
                    <span className="ml-auto shrink-0 tabular-nums text-muted-foreground">
                      {it.solved ? (
                        <>
                          {it.score}/{it.total} · %{pct}
                        </>
                      ) : (
                        "çözmedi"
                      )}
                    </span>
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">
              Sınıfta henüz öğrenci yok.
            </p>
          )}
        </div>
      ) : null}
    </li>
  );
}
