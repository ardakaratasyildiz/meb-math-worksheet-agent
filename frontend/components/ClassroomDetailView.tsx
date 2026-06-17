"use client";

import * as React from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { ArrowLeft, Check, Copy, Loader2, Users } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { getClassroom } from "@/lib/api";
import type { ClassroomDetail } from "@/lib/types";

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
          Bu sınıfa katıldın. Öğretmenin ödev verdiğinde{" "}
          <strong>Ödevlerim</strong> sayfanda görünecek (yakında).
        </Card>
      )}
    </div>
  );
}
