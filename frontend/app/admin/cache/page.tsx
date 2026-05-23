"use client";

import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface CacheItem {
  cache_key: string;
  question_count: number;
  created_at: number;
  first_question_preview: string;
  first_answer_preview: string;
}

export default function CachePage() {
  const [items, setItems] = useState<CacheItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/admin/cache/recent?limit=50", { cache: "no-store" });
      const json = await res.json();
      setItems(json.items ?? []);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-4">
        <div>
          <CardTitle>Son üretimler</CardTitle>
          <CardDescription>
            Son 50 cache set'i — key, ilk soru/cevap önizleme ve üretim zamanı.
          </CardDescription>
        </div>
        <Button variant="outline" size="sm" onClick={load} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Yenile
        </Button>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="mb-4 rounded-md border border-destructive bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}
        {loading ? (
          <Skeleton className="h-64 w-full" />
        ) : items.length === 0 ? (
          <p className="text-sm text-muted-foreground">Cache boş.</p>
        ) : (
          <div className="space-y-3">
            {items.map((it) => (
              <div key={`${it.cache_key}-${it.created_at}`} className="rounded-md border p-3 text-sm">
                <div className="mb-1 flex items-center justify-between gap-2 text-xs text-muted-foreground">
                  <span className="font-mono truncate">{it.cache_key}</span>
                  <span className="whitespace-nowrap">
                    {it.question_count} soru · {formatTimestamp(it.created_at)}
                  </span>
                </div>
                <p className="font-medium">{it.first_question_preview || "—"}</p>
                {it.first_answer_preview && (
                  <p className="mt-1 text-xs text-muted-foreground">
                    cvp: {it.first_answer_preview}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function formatTimestamp(ts: number | null): string {
  if (!ts) return "—";
  const d = new Date(ts * 1000);
  return d.toLocaleString("tr-TR", { dateStyle: "short", timeStyle: "short" });
}
