"use client";

import * as React from "react";
import { Download, RefreshCw, Trash2, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

import { downloadBlob, renderPdf } from "@/lib/api";
import {
  clearHistory,
  listHistory,
  removeHistory,
  type HistoryItem,
} from "@/lib/history";
import { useGenerateStore } from "@/lib/store";

export function HistoryList() {
  const router = useRouter();
  const setForm = useGenerateStore((s) => s.setForm);

  const [items, setItems] = React.useState<HistoryItem[]>([]);
  const [mounted, setMounted] = React.useState(false);

  const refresh = React.useCallback(() => setItems(listHistory()), []);

  React.useEffect(() => {
    setMounted(true);
    refresh();
  }, [refresh]);

  if (!mounted) return null;

  if (items.length === 0) {
    return (
      <Card className="flex flex-col items-center justify-center gap-3 border-dashed py-16 text-center">
        <Sparkles className="h-10 w-10 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">
          Henüz üretim kaydı yok.
        </p>
        <Button asChild>
          <a href="/generate">Üretime başla</a>
        </Button>
      </Card>
    );
  }

  async function onDownload(item: HistoryItem) {
    const t = toast.loading("PDF hazırlanıyor…");
    try {
      const blob = await renderPdf(item.response.worksheet);
      const safe = item.response.worksheet.title
        .replace(/\s+/g, "_")
        .replace(/[^\w_-]/g, "");
      downloadBlob(blob, `${safe || "worksheet"}.pdf`);
      toast.success("PDF indirildi", { id: t });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Hata";
      toast.error("PDF başarısız", { id: t, description: msg });
    }
  }

  function onRegenerate(item: HistoryItem) {
    setForm({
      grade: item.request.grade,
      topicId: item.request.topic_id,
      kazanimKod: item.request.kazanim_kod,
      difficulty: item.request.difficulty as "kolay" | "orta" | "zor",
      questionCount: item.request.question_count,
    });
    router.push("/generate");
  }

  function onRemove(id: string) {
    removeHistory(id);
    refresh();
  }

  function onClearAll() {
    if (!confirm("Tüm üretim geçmişi silinecek. Devam edilsin mi?")) return;
    clearHistory();
    refresh();
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {items.length} kayıt · cihaza yerel olarak saklanır
        </p>
        <Button variant="ghost" size="sm" onClick={onClearAll}>
          <Trash2 className="mr-1 h-3 w-3" /> Tümünü sil
        </Button>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {items.map((item) => {
          const ws = item.response.worksheet;
          const cacheHit = item.response.metadata.trace?.cache_hit;
          const date = new Date(item.saved_at).toLocaleString("tr-TR", {
            dateStyle: "short",
            timeStyle: "short",
          });
          return (
            <Card key={item.id} className="flex flex-col gap-3 p-4">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <h3 className="truncate text-sm font-semibold">{ws.title}</h3>
                  <p className="text-xs text-muted-foreground">{date}</p>
                </div>
                {cacheHit && (
                  <Badge variant="outline" className="border-primary/40 text-primary">
                    Önbellek
                  </Badge>
                )}
              </div>
              <div className="flex flex-wrap gap-1">
                <Badge variant="secondary" className="text-[10px]">
                  {ws.grade}. sınıf
                </Badge>
                <Badge variant="secondary" className="text-[10px]">
                  {ws.difficulty}
                </Badge>
                <Badge variant="secondary" className="text-[10px]">
                  {ws.questions.length} soru
                </Badge>
              </div>
              <div className="mt-auto flex gap-2">
                <Button
                  size="sm"
                  variant="default"
                  className="flex-1 gap-1"
                  onClick={() => onDownload(item)}
                >
                  <Download className="h-3 w-3" /> PDF
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="flex-1 gap-1"
                  onClick={() => onRegenerate(item)}
                >
                  <RefreshCw className="h-3 w-3" /> Yeniden üret
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => onRemove(item.id)}
                  aria-label="Sil"
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
