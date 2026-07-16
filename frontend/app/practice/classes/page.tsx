import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { ClassesView } from "@/components/ClassesView";

// ?join=KOD → katılma linkinden gelen öğrenci için kod ön-dolu gelir.
export default async function ClassesPage({
  searchParams,
}: {
  searchParams: Promise<{ join?: string }>;
}) {
  const sp = await searchParams;
  const initialJoinCode =
    typeof sp.join === "string" ? sp.join.toUpperCase().slice(0, 12) : "";
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Link
          href="/practice"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Çöz &amp; Geliş
        </Link>
        <h1 className="text-2xl font-semibold tracking-tight">Sınıflarım</h1>
        <p className="text-sm text-muted-foreground">
          Öğretmensen sınıf aç ve ödev ata; öğrenciysen katılma kodunla sınıfına katıl.
        </p>
      </div>

      <ClassesView initialJoinCode={initialJoinCode} />
    </div>
  );
}
