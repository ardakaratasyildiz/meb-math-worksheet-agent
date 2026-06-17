import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { AssignmentsList } from "@/components/AssignmentsList";

export default function AssignmentsPage() {
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
        <h1 className="text-2xl font-semibold tracking-tight">Ödevlerim</h1>
        <p className="text-sm text-muted-foreground">
          Katıldığın sınıflardaki ödevleri çöz; sonucun hem sana hem öğretmenine işlenir.
        </p>
      </div>

      <AssignmentsList />
    </div>
  );
}
