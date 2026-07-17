import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { currentUser } from "@clerk/nextjs/server";

import { TeachingResultsView } from "@/components/TeachingResultsView";
import { effectiveRole } from "@/lib/roles";

// "Ödev Sonuçları" — öğretmenin tüm sınıflarındaki ödevleri + kim çözdü + puanları +
// (öğrenci cevaplarını) gösteren pano. (Rota /practice/shares tarihsel; içerik değişti.)
export default async function TeachingResultsPage() {
  const isTeacher = effectiveRole(await currentUser()) === "teacher";
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Link
          href="/practice"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          {isTeacher ? "Sınıfım" : "Çöz & Geliş"}
        </Link>
        <h1 className="text-2xl font-semibold tracking-tight">Ödev Sonuçları</h1>
        <p className="text-sm text-muted-foreground">
          Tüm sınıflarına attığın ödevler; hangi sınıfta kimin çözdüğünü, kaç puan
          aldığını ve verdiği cevapları buradan gör.
        </p>
      </div>

      <TeachingResultsView />
    </div>
  );
}
