"use client";

import { useEffect, useState } from "react";
import { AlertCircle, CheckCircle2, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

// ─── Tipler — backend'in döndürdüğü JSON ile birebir ─────────────────────────

interface HealthCheck {
  ready: boolean;
  checks: {
    gemini_api_key: boolean;
    db_backend: string;
    worksheet_history_rows: number | { ok: false; error: string };
    chroma: { ok: boolean; count?: number; error?: string };
  };
}

interface CacheStats {
  total_sets?: number;
  distinct_keys?: number;
  runtime_hits?: number;
  runtime_misses?: number;
  top_keys: Array<{ key: string; set_count: number }>;
}

// ─── Dashboard ───────────────────────────────────────────────────────────────

export default function AdminDashboard() {
  const [health, setHealth] = useState<HealthCheck | null>(null);
  const [cache, setCache] = useState<CacheStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [h, c] = await Promise.all([
        fetch("/api/admin/health", { cache: "no-store" }).then((r) => r.json()),
        fetch("/api/admin/cache/stats", { cache: "no-store" }).then((r) => r.json()),
      ]);
      setHealth(h);
      setCache(c);
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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Dashboard</h2>
        <Button variant="outline" size="sm" onClick={load} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Yenile
        </Button>
      </div>

      {error && (
        <div className="rounded-md border border-destructive bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <HealthCard health={health} loading={loading} />
        <DbBackendCard health={health} loading={loading} />
        <ChromaCard health={health} loading={loading} />
        <WorksheetCard health={health} loading={loading} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Cache istatistikleri</CardTitle>
          <CardDescription>
            En sık üretilen 20 cache key — aynı parametrelere kaç kez kağıt üretildi.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading && <Skeleton className="h-32 w-full" />}
          {cache && !loading && (
            <>
              <div className="mb-4 grid grid-cols-2 gap-4 sm:grid-cols-4 text-sm">
                <Stat label="Distinct keys" value={cache.distinct_keys ?? "—"} />
                <Stat label="Toplam set" value={cache.total_sets ?? "—"} />
                <Stat label="Hit" value={cache.runtime_hits ?? 0} />
                <Stat label="Miss" value={cache.runtime_misses ?? 0} />
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left text-muted-foreground">
                      <th className="py-2 font-medium">Cache key</th>
                      <th className="py-2 text-right font-medium">Set count</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cache.top_keys?.length ? (
                      cache.top_keys.map((k) => (
                        <tr key={k.key} className="border-b last:border-0">
                          <td className="truncate py-2 font-mono text-xs">{k.key}</td>
                          <td className="py-2 text-right">{k.set_count}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={2} className="py-4 text-center text-muted-foreground">
                          Henüz kayıt yok.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ─── Yardımcı kartlar ────────────────────────────────────────────────────────

function HealthCard({ health, loading }: { health: HealthCheck | null; loading: boolean }) {
  if (loading) return <SkeletonCard />;
  const ok = health?.ready;
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>Genel sağlık</CardDescription>
        <CardTitle className="flex items-center gap-2">
          {ok ? (
            <>
              <CheckCircle2 className="h-5 w-5 text-emerald-600" />
              <span>Hazır</span>
            </>
          ) : (
            <>
              <AlertCircle className="h-5 w-5 text-amber-600" />
              <span>Sorun var</span>
            </>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="text-xs text-muted-foreground">
        Gemini key: {health?.checks.gemini_api_key ? "✓" : "✗"}
      </CardContent>
    </Card>
  );
}

function DbBackendCard({ health, loading }: { health: HealthCheck | null; loading: boolean }) {
  if (loading) return <SkeletonCard />;
  const backend = health?.checks.db_backend ?? "—";
  const isTurso = backend === "turso";
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>DB backend</CardDescription>
        <CardTitle className={isTurso ? "text-emerald-600" : "text-amber-600"}>
          {backend}
        </CardTitle>
      </CardHeader>
      <CardContent className="text-xs text-muted-foreground">
        {isTurso ? "Kalıcı (restart-proof)" : "Ephemeral disk — restart'ta sıfırlanır"}
      </CardContent>
    </Card>
  );
}

function ChromaCard({ health, loading }: { health: HealthCheck | null; loading: boolean }) {
  if (loading) return <SkeletonCard />;
  const chroma = health?.checks.chroma;
  const count = chroma?.count ?? 0;
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>ChromaDB</CardDescription>
        <CardTitle>{count.toLocaleString("tr-TR")}</CardTitle>
      </CardHeader>
      <CardContent className="text-xs text-muted-foreground">
        Embedding'li örnek soru sayısı
      </CardContent>
    </Card>
  );
}

function WorksheetCard({ health, loading }: { health: HealthCheck | null; loading: boolean }) {
  if (loading) return <SkeletonCard />;
  const rows = health?.checks.worksheet_history_rows;
  const value = typeof rows === "number" ? rows.toLocaleString("tr-TR") : "—";
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>Üretilen kağıtlar</CardDescription>
        <CardTitle>{value}</CardTitle>
      </CardHeader>
      <CardContent className="text-xs text-muted-foreground">
        Tüm tenant'lar toplamı (Sprint 13)
      </CardContent>
    </Card>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div>
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="text-lg font-semibold">{value}</div>
    </div>
  );
}

function SkeletonCard() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-6 w-24" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-3 w-32" />
      </CardContent>
    </Card>
  );
}
