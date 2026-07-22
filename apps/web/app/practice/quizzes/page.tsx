import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { currentUser } from "@clerk/nextjs/server";

import { MyQuizzesView } from "@/components/MyQuizzesView";
import { effectiveRole } from "@/lib/roles";

// "Ürettiğim Quizler" — öğretmenin ürettiği quizler; incele + soru yenile (düzenle).
export default async function MyQuizzesPage() {
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
        <h1 className="text-2xl font-semibold tracking-tight">Ürettiğim Quizler</h1>
        <p className="text-sm text-muted-foreground">
          Ürettiğin quizleri incele, beğenmediğin soruyu tek tıkla yeniden üret;
          sınıflarına ödev olarak atamak için sınıf sayfasını kullan.
        </p>
      </div>

      <MyQuizzesView />
    </div>
  );
}
