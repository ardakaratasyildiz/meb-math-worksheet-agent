"use client";

import { useCallback, useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchTenantUsers, tenantDisplay, type TenantUser } from "@/lib/tenant-label";

interface CostItem {
  id: string;
  tenant_id: string;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  cost_usd: number;
  grade: number | null;
  topic: string | null;
  question_count: number;
  cache_hit: boolean;
  created_at: number;
}

const usd = (n: number) =>
  `$${(n ?? 0).toLocaleString("en-US", { minimumFractionDigits: 4, maximumFractionDigits: 4 })}`;

function ts(t: number | null): string {
  if (!t) return "—";
  return new Date(t * 1000).toLocaleString("tr-TR", { dateStyle: "short", timeStyle: "short" });
}

// Ucuz (2.5) yeşil, güçlü (3.5) amber — hızlı göz taraması için.
function modelBadge(model: string) {
  const strong = model.includes("3.5") || model.includes("pro");
  const cache = model === "cache";
  const cls = cache
    ? "bg-muted text-muted-foreground"
    : strong
      ? "bg-amber-100 text-amber-900 dark:bg-amber-900/30 dark:text-amber-200"
      : "bg-emerald-100 text-emerald-900 dark:bg-emerald-900/30 dark:text-emerald-200";
  return <span className={`rounded px-1.5 py-0.5 font-mono text-[10px] ${cls}`}>{model}</span>;
}

export default function AdminCostsPage() {
  const [items, setItems] = useState<CostItem[]>([]);
  const [users, setUsers] = useState<Record<string, TenantUser>>({});
  const [usersLoaded, setUsersLoaded] = useState(false);
  const [days, setDays] = useState(7);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/admin/costs/recent?limit=200&days=${days}`, {
        cache: "no-store",
      });
      const json = await res.json();
      const list: CostItem[] = json.items ?? [];
      setItems(list);
      setUsersLoaded(false);
      fetchTenantUsers(list.map((i) => i.tenant_id))
        .then(setUsers)
        .finally(() => setUsersLoaded(true));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => {
    load();
  }, [load]);

  const total = items.reduce((s, i) => s + (i.cost_usd || 0), 0);

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle>Üretim başına maliyet detayı</CardTitle>
            <CardDescription>
              Her satır bir üretim: hangi kağıt/quiz (sınıf + konu), hangi model, ne kadar token
              ve maliyet. Kaynak: usage_ledger (tahmini; Google faturasıyla mutabakat için
              Dashboard&apos;daki model/gün toplamına bakın). Son {days} gün, en fazla 200 kayıt.
            </CardDescription>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex gap-1">
              {[1, 7, 30].map((d) => (
                <Button
                  key={d}
                  size="sm"
                  variant={days === d ? "default" : "outline"}
                  onClick={() => setDays(d)}
                >
                  {d}g
                </Button>
              ))}
            </div>
            <Button variant="outline" size="sm" onClick={load} disabled={loading}>
              <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              Yenile
            </Button>
          </div>
        </div>
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
          <p className="text-sm text-muted-foreground">Bu dönemde kayıt yok.</p>
        ) : (
          <>
            <div className="mb-3 text-sm text-muted-foreground">
              {items.length} üretim · toplam <span className="font-medium text-foreground">{usd(total)}</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="py-2 pr-3 font-medium">Tarih</th>
                    <th className="py-2 pr-3 font-medium">Kullanıcı</th>
                    <th className="py-2 pr-3 font-medium">Sınıf</th>
                    <th className="py-2 pr-3 font-medium">Konu</th>
                    <th className="py-2 pr-3 font-medium">Model</th>
                    <th className="py-2 pr-3 text-right font-medium">Soru</th>
                    <th className="py-2 pr-3 text-right font-medium">Girdi/Çıktı tok</th>
                    <th className="py-2 pr-3 text-right font-medium">Maliyet</th>
                    <th className="py-2 font-medium">Cache</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((it) => (
                    <tr key={it.id} className="border-b last:border-0">
                      <td className="whitespace-nowrap py-2 pr-3 text-xs text-muted-foreground">
                        {ts(it.created_at)}
                      </td>
                      <td className="max-w-[160px] py-2 pr-3">
                        <span className="block truncate text-xs">
                          {tenantDisplay(it.tenant_id, users, usersLoaded)}
                        </span>
                      </td>
                      <td className="py-2 pr-3 tabular-nums">{it.grade ?? "—"}</td>
                      <td className="max-w-[200px] py-2 pr-3">
                        <span className="block truncate">{it.topic || "—"}</span>
                      </td>
                      <td className="py-2 pr-3">{modelBadge(it.model)}</td>
                      <td className="py-2 pr-3 text-right tabular-nums">{it.question_count}</td>
                      <td className="py-2 pr-3 text-right tabular-nums text-muted-foreground">
                        {it.prompt_tokens.toLocaleString("tr-TR")}/
                        {it.completion_tokens.toLocaleString("tr-TR")}
                      </td>
                      <td className="py-2 pr-3 text-right font-medium tabular-nums">
                        {usd(it.cost_usd)}
                      </td>
                      <td className="py-2">
                        {it.cache_hit ? (
                          <span className="rounded bg-muted px-1.5 py-0.5 text-[10px]">hit</span>
                        ) : (
                          ""
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-4 text-xs text-muted-foreground">
              Not: Karışık-zorluk kağıtta farklı bucket&apos;lar farklı model kullanabilir; Model
              sütunu birincil bucket&apos;ı, Maliyet ise tüm bucket&apos;ların toplamını gösterir.
            </p>
          </>
        )}
      </CardContent>
    </Card>
  );
}
