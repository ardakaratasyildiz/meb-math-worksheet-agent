import { Suspense } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { currentUser } from "@clerk/nextjs/server";

import { SolveForm } from "@/components/SolveForm";
import { hasMultipleSubjects } from "@/lib/subjects";
import { effectiveRole } from "@/lib/roles";

// Öğretmen bu sayfaya "Quiz üret" (ödev için) ile gelir → üret+kaydet, çözmeye sokma.
// Öğrenci "Yeni quiz" ile gelir → üret ve doğrudan çöz. Rol Clerk'ten (server) okunur.
export default async function CozYeniPage() {
  const multi = hasMultipleSubjects();
  const role = effectiveRole(await currentUser());
  const isTeacher = role === "teacher";
  const mode = isTeacher ? "create" : "solve";

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
        <h1 className="text-2xl font-semibold tracking-tight">
          {isTeacher ? "Quiz üret (ödev için)" : "Yeni quiz"}
        </h1>
        <p className="text-sm text-muted-foreground">
          {isTeacher
            ? `${multi ? "Ders, sınıf ve konu seç" : "Sınıf ve konu seç"}, çözülebilir bir quiz üret. Üretilen quiz "Sınıflarım"da ödev olarak atanmaya hazır olur.`
            : `${multi ? "Ders, sınıf ve konu seç" : "Sınıf ve konu seç"}, çözülebilir bir quiz üret. Üretim bitince doğrudan çözmeye başlarsın.`}
        </p>
      </div>

      <div className="rounded-xl border bg-card p-6 shadow-sm">
        <Suspense fallback={null}>
          <SolveForm mode={mode} />
        </Suspense>
      </div>
    </div>
  );
}
