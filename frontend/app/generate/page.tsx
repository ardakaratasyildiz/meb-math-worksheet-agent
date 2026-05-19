import { GenerateForm } from "@/components/GenerateForm";
import { QuestionPreview } from "@/components/QuestionPreview";

export const metadata = {
  title: "Çalışma Kağıdı Üretimi · Soru Atölyesi",
};

export default function GeneratePage() {
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
        <GenerateForm />
      </div>

      {/* Preview/loading alanı — başlatıldıktan sonra otomatik kaydırma için
          QuestionPreview kendi container'ına ref atıp scrollIntoView çağırır. */}
      <QuestionPreview />
    </div>
  );
}
