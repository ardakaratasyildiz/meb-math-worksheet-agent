import Link from "next/link";
import { ArrowRight, History, Sparkles, TrendingUp } from "lucide-react";

import { Card } from "@/components/ui/card";
import { CozTodayCard } from "@/components/CozTodayCard";

export default function CozHubPage() {
  return (
    <div className="space-y-8">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Çöz & Geliş</h1>
        <p className="text-sm text-muted-foreground">
          Soru üret, site içinde test gibi çöz, anında kaç doğru kaç yanlış
          yaptığını gör. Eksik kazanımlarına göre pratiğe yönlen.
        </p>
      </header>

      <CozTodayCard />

      <div className="grid gap-4 sm:grid-cols-3">
        <Link href="/coz/yeni" className="group">
          <Card className="flex h-full flex-col gap-3 p-6 transition-colors hover:border-primary/40 hover:bg-accent/20">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary/10 text-primary">
              <Sparkles className="h-5 w-5" />
            </div>
            <div className="space-y-1">
              <h2 className="font-semibold">Yeni quiz çöz</h2>
              <p className="text-sm text-muted-foreground">
                Sınıf ve konu seç, çözülebilir bir quiz üret ve hemen çözmeye
                başla.
              </p>
            </div>
            <span className="mt-auto inline-flex items-center gap-1 text-sm font-medium text-primary">
              Başla
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </span>
          </Card>
        </Link>

        <Link href="/coz/ilerleme" className="group">
          <Card className="flex h-full flex-col gap-3 p-6 transition-colors hover:border-primary/40 hover:bg-accent/20">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary/10 text-primary">
              <TrendingUp className="h-5 w-5" />
            </div>
            <div className="space-y-1">
              <h2 className="font-semibold">İlerlemem</h2>
              <p className="text-sm text-muted-foreground">
                Kazanım bazlı gelişimin, zayıf konuların ve genel doğru oranın.
              </p>
            </div>
            <span className="mt-auto inline-flex items-center gap-1 text-sm font-medium text-primary">
              Görüntüle
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </span>
          </Card>
        </Link>

        <Link href="/coz/history" className="group">
          <Card className="flex h-full flex-col gap-3 p-6 transition-colors hover:border-primary/40 hover:bg-accent/20">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary/10 text-primary">
              <History className="h-5 w-5" />
            </div>
            <div className="space-y-1">
              <h2 className="font-semibold">Geçmiş quizlerim</h2>
              <p className="text-sm text-muted-foreground">
                Çözdüğün quizleri, doğru cevapları ve kendi cevaplarını incele.
              </p>
            </div>
            <span className="mt-auto inline-flex items-center gap-1 text-sm font-medium text-primary">
              Aç
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </span>
          </Card>
        </Link>
      </div>
    </div>
  );
}
