import { GenerateForm } from "@/components/GenerateForm";
import { QuestionPreview } from "@/components/QuestionPreview";
import { isSubjectEnabled } from "@/lib/subjects";
import type { Subject } from "@/lib/types";

export const metadata = {
  title: "Çalışma Kağıdı Üretimi · Soru Atölyesi",
};

/**
 * SEO landing CTA'ları buraya ?grade=8&topic=dogal_sayilar&kazanim=... ile
 * deep-link eder. searchParams'ı server component'te okuyup forma prop geçeriz
 * (useSearchParams + Suspense karmaşası yok). Form bu değerlerle açılır →
 * kullanıcı SEO'dan geldiği sınıf/konuyu yeniden seçmek zorunda kalmaz.
 */
export default async function GeneratePage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const gradeRaw = typeof sp.grade === "string" ? parseInt(sp.grade, 10) : NaN;
  const initialGrade =
    Number.isInteger(gradeRaw) && gradeRaw >= 1 && gradeRaw <= 8
      ? gradeRaw
      : undefined;
  // Yeni akış: ?unit=<unit_id>. (Eski ?topic= artık kullanılmıyor — SEO sayfaları
  // ayrı bir işte ünite-bazlı yenilenecek; o zamana dek grade+kazanım taşınır.)
  const initialUnitId = typeof sp.unit === "string" ? sp.unit : undefined;
  const initialKazanim = typeof sp.kazanim === "string" ? sp.kazanim : undefined;
  // Ders deep-link: /generate?subject=<slug>. Yalnız FLAG'İ AÇIK matematik-dışı ders
  // kabul edilir; kapalı/geçersiz → undefined (form matematik'e düşer, GenerateForm guard'ı).
  const spSubject = typeof sp.subject === "string" ? sp.subject.toLowerCase() : "";
  const initialSubject: Subject | undefined =
    spSubject && spSubject !== "matematik" && isSubjectEnabled(spSubject as Subject)
      ? (spSubject as Subject)
      : undefined;

  return (
    <div className="container space-y-6 py-8">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">
          Çalışma kağıdı üretimi
        </h1>
        <p className="text-sm text-muted-foreground">
          Aşağıdaki parametreleri seçip üretimi başlatın. Sistem, seçilen MEB
          kazanımına hizalanmış bir çalışma kağıdı üretir ve PDF olarak indirir.
        </p>
      </header>

      {/* Sprint 12-A UI v2: yatay form (mobile'da stack, lg+ yatay).
          Üretim butonu form'un sonunda → her zaman görünür. */}
      <div className="rounded-xl border bg-card p-6 shadow-sm">
        <GenerateForm
          initialGrade={initialGrade}
          initialUnitId={initialUnitId}
          initialKazanim={initialKazanim}
          initialSubject={initialSubject}
        />
      </div>

      {/* Preview/loading alanı — başlatıldıktan sonra otomatik kaydırma için
          QuestionPreview kendi container'ına ref atıp scrollIntoView çağırır. */}
      <QuestionPreview />
    </div>
  );
}
