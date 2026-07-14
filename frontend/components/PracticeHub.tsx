import Link from "next/link";
import {
  ArrowRight,
  CalendarDays,
  GraduationCap,
  History,
  NotebookPen,
  Share2,
  Sparkles,
  TrendingUp,
} from "lucide-react";

import { Card } from "@/components/ui/card";
import { AssignmentAlert } from "@/components/AssignmentAlert";
import { EmailOptInCard } from "@/components/EmailOptInCard";
import { PracticeTodayCard } from "@/components/PracticeTodayCard";
import { hasMultipleSubjects } from "@/lib/subjects";

type Role = "student" | "teacher";

const COLORS: Record<string, { bg: string; text: string }> = {
  coral: { bg: "bg-coral/15", text: "text-coral" },
  sky: { bg: "bg-sky-400/15", text: "text-sky-500" },
  mint: { bg: "bg-mint/15", text: "text-mint" },
  grape: { bg: "bg-grape/15", text: "text-grape" },
  amber: { bg: "bg-amber-400/15", text: "text-amber-500" },
  rose: { bg: "bg-rose-400/15", text: "text-rose-500" },
};

function HubCard({
  href,
  icon,
  title,
  desc,
  cta,
  color,
}: {
  href: string;
  icon: React.ReactNode;
  title: string;
  desc: string;
  cta: string;
  color: keyof typeof COLORS;
}) {
  const c = COLORS[color];
  return (
    <Link href={href} className="group">
      <Card className="flex h-full flex-col gap-3 p-6 shadow-pop transition-transform hover:-translate-y-1">
        <div
          className={`flex h-12 w-12 items-center justify-center rounded-2xl text-2xl ${c.bg}`}
        >
          {icon}
        </div>
        <div className="space-y-1">
          <h2 className="font-display text-lg font-bold">{title}</h2>
          <p className="text-sm text-muted-foreground">{desc}</p>
        </div>
        <span
          className={`mt-auto inline-flex items-center gap-1 font-display text-sm font-semibold ${c.text}`}
        >
          {cta}
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
        </span>
      </Card>
    </Link>
  );
}

/**
 * /practice hub — "iki yüz, tek hesap" (LEARNING_PLATFORM_PLAN §2).
 * Hangi yüz açılacağı GİRİŞ KAPISINA göre belirlenir (navbar'da iki link):
 *   "Çöz & Geliş" → /practice            → öğrenci yüzü
 *   "Sınıfım"     → /practice?role=teacher → öğretmen/veli yüzü
 * Sayfa içi toggle yok (kafa karışıklığını önlemek için); kapılar arası geçiş
 * navbar'dan yapılır.
 */
export function PracticeHub({ roleParam }: { roleParam: Role | null }) {
  const isStudent = roleParam !== "teacher";

  return (
    <div className="space-y-7">
      <header className="relative overflow-hidden rounded-3xl bg-card p-6 shadow-pop sm:p-7">
        <span
          aria-hidden
          className="pointer-events-none absolute -right-1 -top-2 hidden animate-bob text-6xl sm:block"
        >
          {isStudent ? "🦊" : "🎓"}
        </span>
        <p className="font-display text-sm font-semibold text-grape">
          {isStudent ? "Çöz & Geliş 👋" : "Sınıfım 🎓"}
        </p>
        <h1 className="mt-1 font-display text-3xl font-bold tracking-tight">
          {isStudent
            ? hasMultipleSubjects()
              ? "Bugün de çalışmaya devam!"
              : "Bugün de matematiğe devam!"
            : "Sınıfını yönet"}
        </h1>
        <p className="mt-2 max-w-md text-muted-foreground">
          {isStudent
            ? "Soru üret, site içinde test gibi çöz, anında kaç doğru kaç yanlış yaptığını gör."
            : "Sınıf aç, öğrencilerini katılma koduyla davet et, ödev ata ve sonuçlarını izle."}
        </p>
      </header>

      <EmailOptInCard />

      {isStudent ? (
        <>
          <AssignmentAlert />
          <PracticeTodayCard />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <HubCard
              href="/practice/new"
              color="coral"
              icon={<Sparkles className="h-6 w-6 text-coral" />}
              title="Yeni quiz çöz"
              desc="Sınıf ve konu seç, çözülebilir bir quiz üret ve hemen çözmeye başla."
              cta="Başla"
            />
            <HubCard
              href="/practice/assignments"
              color="rose"
              icon={<NotebookPen className="h-6 w-6 text-rose-500" />}
              title="Ödevlerim"
              desc="Katıldığın sınıflardaki ödevleri çöz; sonucun öğretmenine işlenir."
              cta="Aç"
            />
            <HubCard
              href="/practice/progress"
              color="sky"
              icon={<TrendingUp className="h-6 w-6 text-sky-500" />}
              title="İlerlemem"
              desc="Kazanım bazlı gelişimin, zayıf konuların ve genel doğru oranın."
              cta="Görüntüle"
            />
            <HubCard
              href="/practice/study-plan"
              color="grape"
              icon={<CalendarDays className="h-6 w-6 text-grape" />}
              title="Çalışma Programım"
              desc="Eksiklerine göre haftalık, gün gün AI çalışma programı — oluştur, kalıcı olsun."
              cta="Aç"
            />
            <HubCard
              href="/practice/history"
              color="mint"
              icon={<History className="h-6 w-6 text-mint" />}
              title="Geçmiş quizlerim"
              desc="Çözdüğün quizleri, doğru cevapları ve kendi cevaplarını incele."
              cta="Aç"
            />
          </div>
        </>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <HubCard
            href="/practice/classes"
            color="amber"
            icon={<GraduationCap className="h-6 w-6 text-amber-500" />}
            title="Sınıflarım"
            desc="Sınıf aç, öğrencilerini katılma koduyla davet et, ödev ata ve sonuçları gör."
            cta="Aç"
          />
          <HubCard
            href="/practice/new"
            color="coral"
            icon={<Sparkles className="h-6 w-6 text-coral" />}
            title="Quiz üret"
            desc="Ödev olarak atayacağın çözülebilir quizleri üret."
            cta="Üret"
          />
          <HubCard
            href="/practice/shares"
            color="grape"
            icon={<Share2 className="h-6 w-6 text-grape" />}
            title="Paylaşımlarım"
            desc="Paylaştığın quizleri ve onları çözenlerin sonuçlarını gör."
            cta="Aç"
          />
        </div>
      )}
    </div>
  );
}
