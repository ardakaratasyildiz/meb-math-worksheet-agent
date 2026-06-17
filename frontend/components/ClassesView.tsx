"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth, useUser } from "@clerk/nextjs";
import { ChevronRight, GraduationCap, Loader2, Plus, Users } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { createClassroom, joinClassroom, listClassrooms } from "@/lib/api";
import type { ClassroomSummary } from "@/lib/types";

export function ClassesView() {
  const { userId, isLoaded } = useAuth();
  const { user } = useUser();
  const router = useRouter();

  const [teaching, setTeaching] = React.useState<ClassroomSummary[]>([]);
  const [enrolled, setEnrolled] = React.useState<ClassroomSummary[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const [newName, setNewName] = React.useState("");
  const [joinCode, setJoinCode] = React.useState("");
  const [joinName, setJoinName] = React.useState("");
  const [creating, setCreating] = React.useState(false);
  const [joining, setJoining] = React.useState(false);

  const defaultName = user?.fullName ?? user?.firstName ?? "";

  const load = React.useCallback(() => {
    if (!userId) return;
    setLoading(true);
    listClassrooms(userId)
      .then((d) => {
        setTeaching(d.teaching);
        setEnrolled(d.enrolled);
      })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : "Sınıflar alınamadı.");
      })
      .finally(() => setLoading(false));
  }, [userId]);

  React.useEffect(() => {
    if (!isLoaded) return;
    if (!userId) {
      setError("Oturum bulunamadı.");
      setLoading(false);
      return;
    }
    load();
  }, [isLoaded, userId, load]);

  async function onCreate() {
    if (!userId || !newName.trim()) return;
    setCreating(true);
    try {
      const c = await createClassroom(userId, newName.trim());
      toast.success("Sınıf oluşturuldu", { description: `Katılma kodu: ${c.join_code}` });
      setNewName("");
      router.push(`/practice/classes/${c.id}`);
    } catch (e: unknown) {
      toast.error("Sınıf oluşturulamadı", {
        description: e instanceof Error ? e.message : undefined,
      });
    } finally {
      setCreating(false);
    }
  }

  async function onJoin() {
    if (!userId || !joinCode.trim()) return;
    const name = (joinName || defaultName).trim();
    if (!name) {
      toast.error("Adını gir (öğretmenin sonucunu bu isimle görür).");
      return;
    }
    setJoining(true);
    try {
      const r = await joinClassroom(userId, joinCode.trim(), name);
      toast.success(`"${r.name}" sınıfına katıldın`);
      setJoinCode("");
      router.push(`/practice/classes/${r.classroom_id}`);
    } catch (e: unknown) {
      toast.error("Katılınamadı", {
        description: e instanceof Error ? e.message : "Kodu kontrol et.",
      });
    } finally {
      setJoining(false);
    }
  }

  return (
    <div className="space-y-7">
      {/* Aksiyonlar: oluştur + katıl */}
      <div className="grid gap-4 sm:grid-cols-2">
        <Card className="space-y-3 p-5">
          <div className="flex items-center gap-2">
            <GraduationCap className="h-5 w-5 text-grape" />
            <h2 className="font-display font-bold">Sınıf oluştur</h2>
          </div>
          <p className="text-sm text-muted-foreground">
            Öğretmen/veli olarak sınıf aç; öğrenciler katılma koduyla katılır.
          </p>
          <div className="flex gap-2">
            <Input
              placeholder="Sınıf adı (ör. 5/A Matematik)"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && onCreate()}
            />
            <Button onClick={onCreate} disabled={creating || !newName.trim()} className="shrink-0 gap-1">
              {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
              Oluştur
            </Button>
          </div>
        </Card>

        <Card className="space-y-3 p-5">
          <div className="flex items-center gap-2">
            <Users className="h-5 w-5 text-coral" />
            <h2 className="font-display font-bold">Sınıfa katıl</h2>
          </div>
          <p className="text-sm text-muted-foreground">
            Öğretmeninin verdiği katılma kodunu gir.
          </p>
          <div className="grid gap-2 sm:grid-cols-2">
            <Input
              placeholder="Katılma kodu"
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
              className="uppercase"
            />
            <Input
              placeholder={defaultName ? `Adın (${defaultName})` : "Adın"}
              value={joinName}
              onChange={(e) => setJoinName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && onJoin()}
            />
          </div>
          <Button onClick={onJoin} disabled={joining || !joinCode.trim()} variant="outline" className="gap-1">
            {joining ? <Loader2 className="h-4 w-4 animate-spin" /> : <Users className="h-4 w-4" />}
            Katıl
          </Button>
        </Card>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16 text-muted-foreground">
          <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          Sınıflar yükleniyor…
        </div>
      ) : error ? (
        <Card className="p-6">
          <p className="text-sm text-destructive">{error}</p>
        </Card>
      ) : (
        <>
          <ClassroomGroup
            title="Öğretmeni olduğun sınıflar"
            empty="Henüz sınıf açmadın."
            items={teaching}
            showCode
          />
          <ClassroomGroup
            title="Katıldığın sınıflar"
            empty="Henüz bir sınıfa katılmadın."
            items={enrolled}
          />
        </>
      )}
    </div>
  );
}

function ClassroomGroup({
  title,
  empty,
  items,
  showCode = false,
}: {
  title: string;
  empty: string;
  items: ClassroomSummary[];
  showCode?: boolean;
}) {
  return (
    <section className="space-y-3">
      <h2 className="font-display text-lg font-bold">{title}</h2>
      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground">{empty}</p>
      ) : (
        <div className="space-y-2">
          {items.map((c) => (
            <Link key={c.id} href={`/practice/classes/${c.id}`}>
              <Card className="flex items-center justify-between gap-3 p-4 transition-colors hover:border-primary/40 hover:bg-accent/20">
                <div className="min-w-0">
                  <p className="truncate font-medium">{c.name}</p>
                  <p className="mt-0.5 flex items-center gap-3 text-xs text-muted-foreground">
                    <span className="inline-flex items-center gap-1">
                      <Users className="h-3.5 w-3.5" />
                      {c.member_count} öğrenci
                    </span>
                    {showCode && c.join_code ? (
                      <span className="font-mono tracking-wider">Kod: {c.join_code}</span>
                    ) : null}
                  </p>
                </div>
                <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
              </Card>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}
