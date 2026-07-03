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

interface CostSummary {
  window_days?: number;
  total?: {
    generations: number;
    cost_usd: number;
    prompt_tokens: number;
    completion_tokens: number;
    cache_hits: number;
  };
  by_tenant?: Array<{
    tenant_id: string;
    generations: number;
    cost_usd: number;
    prompt_tokens: number;
    completion_tokens: number;
  }>;
  by_model?: Array<{ model: string; generations: number; cost_usd: number }>;
  by_day?: Array<{ day: string; generations: number; cost_usd: number }>;
}

const usd = (n: number | undefined) =>
  `$${(n ?? 0).toLocaleString("en-US", { minimumFractionDigits: 4, maximumFractionDigits: 4 })}`;

// ─── Dashboard ───────────────────────────────────────────────────────────────

export default function AdminDashboard() {
  const [health, setHealth] = useState<HealthCheck | null>(null);
  const [cache, setCache] = useState<CacheStats | null>(null);
  const [cost, setCost] = useState<CostSummary | null>(null);
  const [costDays, setCostDays] = useState(30);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [h, c, cs] = await Promise.all([
        fetch("/api/admin/health", { cache: "no-store" }).then((r) => r.json()),
        fetch("/api/admin/cache/stats", { cache: "no-store" }).then((r) => r.json()),
        fetch(`/api/admin/costs/summary?days=${costDays}`, { cache: "no-store" }).then((r) =>
          r.json(),
        ),
      ]);
      setHealth(h);
      setCache(c);
      setCost(cs);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [costDays]);

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

      {/* ── Gemini maliyet ── */}
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <CardTitle>Gemini maliyeti — kim ne kadar harcadı</CardTitle>
              <CardDescription>
                Gerçek Gemini harcaması (üretim + retry + top-up + critic + embedding).
                Anonim üretimler dahil. Son {cost?.window_days ?? costDays} gün.
              </CardDescription>
            </div>
            <div className="flex gap-1">
              {[1, 7, 30].map((d) => (
                <Button
                  key={d}
                  size="sm"
                  variant={costDays === d ? "default" : "outline"}
                  onClick={() => setCostDays(d)}
                >
                  {d}g
                </Button>
              ))}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading && <Skeleton className="h-40 w-full" />}
          {cost && !loading && (
            <>
              <div className="mb-5 grid grid-cols-2 gap-4 sm:grid-cols-4 text-sm">
                <Stat label="Toplam maliyet" value={usd(cost.total?.cost_usd)} />
                <Stat label="Üretim sayısı" value={cost.total?.generations ?? 0} />
                <Stat
                  label="Girdi / çıktı token"
                  value={`${(cost.total?.prompt_tokens ?? 0).toLocaleString("tr-TR")} / ${(
                    cost.total?.completion_tokens ?? 0
                  ).toLocaleString("tr-TR")}`}
                />
                <Stat label="Cache hit" value={cost.total?.cache_hits ?? 0} />
              </div>

              <div className="grid gap-6 lg:grid-cols-2">
                {/* Tenant kırılımı */}
                <div>
                  <div className="mb-2 text-sm font-medium">Kullanıcı (tenant) bazında</div>
                  <div className="max-h-72 overflow-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b text-left text-muted-foreground">
                          <th className="py-2 font-medium">Tenant</th>
                          <th className="py-2 text-right font-medium">Üretim</th>
                          <th className="py-2 text-right font-medium">Maliyet</th>
                        </tr>
                      </thead>
                      <tbody>
                        {cost.by_tenant?.length ? (
                          cost.by_tenant.map((t) => (
                            <tr key={t.tenant_id} className="border-b last:border-0">
                              <td className="max-w-[180px] truncate py-2 font-mono text-xs">
                                {t.tenant_id === "anon" ? "🕶️ anonim" : t.tenant_id}
                              </td>
                              <td className="py-2 text-right tabular-nums">{t.generations}</td>
                              <td className="py-2 text-right font-medium tabular-nums">
                                {usd(t.cost_usd)}
                              </td>
                            </tr>
                          ))
                        ) : (
                          <tr>
                            <td colSpan={3} className="py-4 text-center text-muted-foreground">
                              Henüz kayıt yok.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Model + gün kırılımı */}
                <div className="space-y-5">
                  <div>
                    <div className="mb-2 text-sm font-medium">Model bazında</div>
                    <table className="w-full text-sm">
                      <tbody>
                        {cost.by_model?.map((m) => (
                          <tr key={m.model} className="border-b last:border-0">
                            <td className="py-2 font-mono text-xs">{m.model}</td>
                            <td className="py-2 text-right tabular-nums text-muted-foreground">
                              {m.generations}
                            </td>
                            <td className="py-2 text-right font-medium tabular-nums">
                              {usd(m.cost_usd)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div>
                    <div className="mb-2 text-sm font-medium">Günlük</div>
                    <div className="max-h-40 overflow-auto">
                      <table className="w-full text-sm">
                        <tbody>
                          {cost.by_day?.map((d) => (
                            <tr key={d.day} className="border-b last:border-0">
                              <td className="py-1.5 font-mono text-xs">{d.day}</td>
                              <td className="py-1.5 text-right tabular-nums text-muted-foreground">
                                {d.generations}
                              </td>
                              <td className="py-1.5 text-right tabular-nums">{usd(d.cost_usd)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

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
        Embedding&apos;li örnek soru sayısı
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
        Tüm tenant&apos;lar toplamı (Sprint 13)
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
