import { GenerateForm } from "@/components/GenerateForm";
import { QuestionPreview } from "@/components/QuestionPreview";

export const metadata = {
  title: "Üret · MEB Matematik Üretici",
};

export default function GeneratePage() {
  return (
    <div className="container py-8">
      <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
        {/* Sol pane — form */}
        <aside className="lg:sticky lg:top-20 lg:h-fit">
          <div className="rounded-xl border bg-card p-6">
            <h1 className="mb-1 text-xl font-semibold">Çalışma kağıdı üret</h1>
            <p className="mb-6 text-xs text-muted-foreground">
              MEB müfredatına uygun çalışma kağıdını saniyeler içinde indir.
            </p>
            <GenerateForm />
          </div>
        </aside>

        {/* Sağ pane — preview */}
        <section className="min-w-0">
          <QuestionPreview />
        </section>
      </div>
    </div>
  );
}
