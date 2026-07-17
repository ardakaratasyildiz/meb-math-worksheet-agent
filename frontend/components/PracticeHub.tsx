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
import { ParentDashboard } from "@/components/ParentDashboard";
import { PracticeTodayCard } from "@/components/PracticeTodayCard";
import { hasMultipleSubjects } from "@/lib/subjects";
import type { Role } from "@/lib/roles";

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
        <div className={`flex h-12 w-12 items-center justify-center rounded-2xl text-2xl ${c.bg}`}>
          {icon}
        </div>
        <div className="space-y-1">
          <h2 className="font-display text-lg font-bold">{title}</h2>
          <p className="text-sm text-muted-foreground">{desc}</p>
        </div>
        <span className={`mt-auto inline-flex items-center gap-1 font-display text-sm font-semibold ${c.text}`}>
          {cta}
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
        </span>
      </Card>
    </Link>
  );
}

/** Admin görünümünde bölümleri ayıran başlık (tek-rol kullanıcıda gizli). */
function SectionDivider({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 pt-2">
      <span className="font-display text-sm font-bold uppercase tracking-wide text-grape">
        {label}
      </span>
      <span className="h-px flex-1 bg-border" />
    </div>
  );
}

function StudentSection() {
  return (
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
  );
}

function TeacherSection() {
  return (
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
        desc="Herkese açık link (/q/…) ile paylaştığın quizler ve çözenleri. Sınıf ödevleri burada değil — Sınıflarım'da."
        cta="Aç"
      />
    </div>
  );
}

const HEADER: Record<Role, { eyebrow: string; title: string; body: string; emoji: string }> = {
  student: {
    eyebrow: "Çöz & Geliş 👋",
    title: "Bugün de çalışmaya devam!",
    body: "Soru üret, site içinde test gibi çöz, anında kaç doğru kaç yanlış yaptığını gör.",
    emoji: "🦊",
  },
  teacher: {
    eyebrow: "Sınıfım 🎓",
    title: "Sınıfını yönet",
    body: "Sınıf aç, öğrencilerini katılma koduyla davet et, ödev ata ve sonuçlarını izle.",
    emoji: "🎓",
  },
  parent: {
    eyebrow: "Çocuğum 👨‍👩‍👧",
    title: "Çocuğunun gelişimini takip et",
    body: "Çocuğunun takip koduyla ekle; ilerlemesini, doğru oranını ve eksik konularını gör.",
    emoji: "👨‍👩‍👧",
  },
  admin: {
    eyebrow: "Yönetici 🛠️",
    title: "Tüm görünümler",
    body: "Öğrenci, öğretmen ve veli ekranlarının tümünü buradan görürsün.",
    emoji: "🛠️",
  },
};

/**
 * /practice hub — KALICI role göre yüz gösterir. Öğrenci: çöz&geliş kartları; öğretmen:
 * sınıf/ödev; veli: çocuk takibi. Admin hepsini görür (bölüm başlıklarıyla). Rol
 * server'da okunur (practice/page.tsx) → flash yok. null (rol henüz yok) → RoleGate
 * modalı zaten zorunlu seçim ister; arka planda öğrenci yüzü gösterilir.
 */
export function PracticeHub({ role }: { role: Role | null }) {
  const effective: Role = role ?? "student";
  const isAdmin = effective === "admin";
  const h = HEADER[effective];

  const showStudent = effective === "student" || isAdmin;
  const showTeacher = effective === "teacher" || isAdmin;
  const showParent = effective === "parent" || isAdmin;

  return (
    <div className="space-y-7">
      <header className="relative overflow-hidden rounded-3xl bg-card p-6 shadow-pop sm:p-7">
        <span
          aria-hidden
          className="pointer-events-none absolute -right-1 -top-2 hidden animate-bob text-6xl sm:block"
        >
          {h.emoji}
        </span>
        <p className="font-display text-sm font-semibold text-grape">{h.eyebrow}</p>
        <h1 className="mt-1 font-display text-3xl font-bold tracking-tight">
          {effective === "student" && hasMultipleSubjects()
            ? "Bugün de çalışmaya devam!"
            : h.title}
        </h1>
        <p className="mt-2 max-w-md text-muted-foreground">{h.body}</p>
      </header>

      <EmailOptInCard />

      {showStudent ? (
        <>
          {isAdmin ? <SectionDivider label="Öğrenci" /> : null}
          <StudentSection />
        </>
      ) : null}

      {showTeacher ? (
        <>
          {isAdmin ? <SectionDivider label="Öğretmen" /> : null}
          <TeacherSection />
        </>
      ) : null}

      {showParent ? (
        <>
          {isAdmin ? <SectionDivider label="Veli" /> : null}
          <ParentDashboard />
        </>
      ) : null}
    </div>
  );
}
