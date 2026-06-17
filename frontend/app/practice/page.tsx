import Link from "next/link";
import { ArrowRight, History, Share2, Sparkles, TrendingUp } from "lucide-react";

import { Card } from "@/components/ui/card";
import { PracticeTodayCard } from "@/components/PracticeTodayCard";

export default function CozHubPage() {
  return (
    <div className="space-y-7">
      <header className="relative overflow-hidden rounded-3xl bg-card p-6 shadow-pop sm:p-7">
        <span
          aria-hidden
          className="pointer-events-none absolute -right-1 -top-2 hidden animate-bob text-6xl sm:block"
        >
          🦊
        </span>
        <p className="font-display text-sm font-semibold text-grape">
          Çöz &amp; Geliş 👋
        </p>
        <h1 className="mt-1 font-display text-3xl font-bold tracking-tight">
          Bugün de matematiğe devam!
        </h1>
        <p className="mt-2 max-w-md text-muted-foreground">
          Soru üret, site içinde test gibi çöz, anında kaç doğru kaç yanlış
          yaptığını gör. Eksik kazanımlarına göre pratiğe yönlen.
        </p>
      </header>

      <PracticeTodayCard />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Link href="/practice/new" className="group">
          <Card className="flex h-full flex-col gap-3 p-6 shadow-pop transition-transform hover:-translate-y-1">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-coral/15 text-2xl">
              <Sparkles className="h-6 w-6 text-coral" />
            </div>
            <div className="space-y-1">
              <h2 className="font-display text-lg font-bold">Yeni quiz çöz</h2>
              <p className="text-sm text-muted-foreground">
                Sınıf ve konu seç, çözülebilir bir quiz üret ve hemen çözmeye
                başla.
              </p>
            </div>
            <span className="mt-auto inline-flex items-center gap-1 font-display text-sm font-semibold text-coral">
              Başla
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </span>
          </Card>
        </Link>

        <Link href="/practice/progress" className="group">
          <Card className="flex h-full flex-col gap-3 p-6 shadow-pop transition-transform hover:-translate-y-1">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-sky-400/15 text-2xl">
              <TrendingUp className="h-6 w-6 text-sky-500" />
            </div>
            <div className="space-y-1">
              <h2 className="font-display text-lg font-bold">İlerlemem</h2>
              <p className="text-sm text-muted-foreground">
                Kazanım bazlı gelişimin, zayıf konuların ve genel doğru oranın.
              </p>
            </div>
            <span className="mt-auto inline-flex items-center gap-1 font-display text-sm font-semibold text-sky-500">
              Görüntüle
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </span>
          </Card>
        </Link>

        <Link href="/practice/history" className="group">
          <Card className="flex h-full flex-col gap-3 p-6 shadow-pop transition-transform hover:-translate-y-1">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-mint/15 text-2xl">
              <History className="h-6 w-6 text-mint" />
            </div>
            <div className="space-y-1">
              <h2 className="font-display text-lg font-bold">Geçmiş quizlerim</h2>
              <p className="text-sm text-muted-foreground">
                Çözdüğün quizleri, doğru cevapları ve kendi cevaplarını incele.
              </p>
            </div>
            <span className="mt-auto inline-flex items-center gap-1 font-display text-sm font-semibold text-mint">
              Aç
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </span>
          </Card>
        </Link>

        <Link href="/practice/shares" className="group">
          <Card className="flex h-full flex-col gap-3 p-6 shadow-pop transition-transform hover:-translate-y-1">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-grape/15 text-2xl">
              <Share2 className="h-6 w-6 text-grape" />
            </div>
            <div className="space-y-1">
              <h2 className="font-display text-lg font-bold">Paylaşımlarım</h2>
              <p className="text-sm text-muted-foreground">
                Paylaştığın quizleri ve onları çözenlerin sonuçlarını gör.
              </p>
            </div>
            <span className="mt-auto inline-flex items-center gap-1 font-display text-sm font-semibold text-grape">
              Aç
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </span>
          </Card>
        </Link>
      </div>
    </div>
  );
}
