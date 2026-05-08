import { HistoryList } from "@/components/HistoryList";

export const metadata = {
  title: "Geçmiş · SheetGen",
};

export default function HistoryPage() {
  return (
    <div className="container py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Geçmiş</h1>
        <p className="text-sm text-muted-foreground">
          Önceki üretimler — yeniden PDF indir ya da aynı parametrelerle tekrar
          üret.
        </p>
      </div>
      <HistoryList />
    </div>
  );
}
