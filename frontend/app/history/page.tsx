import { HistoryList } from "@/components/HistoryList";

export const metadata = {
  title: "Üretim Geçmişi · Quiz Marketi",
};

export default function HistoryPage() {
  return (
    <div className="container py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Üretim geçmişi</h1>
        <p className="text-sm text-muted-foreground">
          Önceki üretimler. Aynı PDF tekrar indirilebilir veya aynı
          parametrelerle yeniden üretim başlatılabilir.
        </p>
      </div>
      <HistoryList />
    </div>
  );
}
