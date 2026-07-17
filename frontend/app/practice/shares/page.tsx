import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { currentUser } from "@clerk/nextjs/server";

import { SharesList } from "@/components/SharesList";
import { effectiveRole } from "@/lib/roles";

export default async function PracticeSharesPage() {
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
        <h1 className="text-2xl font-semibold tracking-tight">Paylaşımlarım</h1>
        <p className="text-sm text-muted-foreground">
          Paylaştığın quizleri ve onları çözenlerin sonuçlarını burada gör.
        </p>
      </div>

      <SharesList isTeacher={isTeacher} />
    </div>
  );
}
