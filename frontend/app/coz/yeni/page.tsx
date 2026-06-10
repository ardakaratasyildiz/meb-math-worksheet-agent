import { Suspense } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { SolveForm } from "@/components/SolveForm";

export default function CozYeniPage() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Link
          href="/coz"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Çöz & Geliş
        </Link>
        <h1 className="text-2xl font-semibold tracking-tight">Yeni quiz</h1>
        <p className="text-sm text-muted-foreground">
          Sınıf ve konu seç, çözülebilir bir quiz üret. Üretim bitince doğrudan
          çözmeye başlarsın.
        </p>
      </div>

      <div className="rounded-xl border bg-card p-6 shadow-sm">
        <Suspense fallback={null}>
          <SolveForm />
        </Suspense>
      </div>
    </div>
  );
}
