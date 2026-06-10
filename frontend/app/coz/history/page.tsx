import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { QuizHistoryList } from "@/components/QuizHistoryList";

export default function CozHistoryPage() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Link
          href="/coz"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Çöz &amp; Geliş
        </Link>
        <h1 className="text-2xl font-semibold tracking-tight">
          Geçmiş quizlerim
        </h1>
        <p className="text-sm text-muted-foreground">
          Çözdüğün quizleri aç; soruları, doğru cevapları ve kendi cevaplarını
          incele.
        </p>
      </div>

      <QuizHistoryList />
    </div>
  );
}
