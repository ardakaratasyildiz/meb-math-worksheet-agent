"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ArrowUpDown, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";

interface HistoryTenant {
  tenant_id: string;
  question_count: number;
}

interface WorksheetTenant {
  tenant_id: string;
  worksheet_count: number;
  last_at: number | null;
}

type SortBy = "questions" | "worksheets" | "last";

export default function TenantsPage() {
  const [history, setHistory] = useState<HistoryTenant[]>([]);
  const [worksheets, setWorksheets] = useState<WorksheetTenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<SortBy>("questions");

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [h, w] = await Promise.all([
        fetch("/api/admin/tenants", { cache: "no-store" }).then((r) => r.json()),
        fetch("/api/admin/worksheets", { cache: "no-store" }).then((r) => r.json()),
      ]);
      setHistory(h.tenants ?? []);
      setWorksheets(w.tenants ?? []);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  // İki listeyi tenant_id üzerinden birleştir — bazı tenant'lar yalnızca
  // birinde olabilir (history var ama PDF üretmemiş, vs).
  const merged = useMemo(() => {
    const byId = new Map<
      string,
      { tenant_id: string; questions: number; worksheets: number; last_at: number | null }
    >();
    for (const h of history) {
      byId.set(h.tenant_id, {
        tenant_id: h.tenant_id,
        questions: h.question_count,
        worksheets: 0,
        last_at: null,
      });
    }
    for (const w of worksheets) {
      const existing = byId.get(w.tenant_id);
      if (existing) {
        existing.worksheets = w.worksheet_count;
        existing.last_at = w.last_at;
      } else {
        byId.set(w.tenant_id, {
          tenant_id: w.tenant_id,
          questions: 0,
          worksheets: w.worksheet_count,
          last_at: w.last_at,
        });
      }
    }
    let arr = Array.from(byId.values());
    if (search.trim()) {
      const q = search.toLowerCase();
      arr = arr.filter((t) => t.tenant_id.toLowerCase().includes(q));
    }
    arr.sort((a, b) => {
      if (sortBy === "questions") return b.questions - a.questions;
      if (sortBy === "worksheets") return b.worksheets - a.worksheets;
      return (b.last_at ?? 0) - (a.last_at ?? 0);
    });
    return arr;
  }, [history, worksheets, search, sortBy]);

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-4">
        <div>
          <CardTitle>Kullanıcılar</CardTitle>
          <CardDescription>
            Tenant başına gördüğü soru sayısı + ürettiği PDF sayısı. Detay için satıra tıkla.
          </CardDescription>
        </div>
        <Button variant="outline" size="sm" onClick={load} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Yenile
        </Button>
      </CardHeader>
      <CardContent>
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <Input
            placeholder="Tenant ID ile ara…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-sm"
          />
          <span className="text-xs text-muted-foreground">{merged.length} kayıt</span>
        </div>

        {error && (
          <div className="mb-4 rounded-md border border-destructive bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {loading ? (
          <Skeleton className="h-64 w-full" />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="py-2 font-medium">Tenant ID</th>
                  <SortableHeader
                    label="Sorular"
                    active={sortBy === "questions"}
                    onClick={() => setSortBy("questions")}
                  />
                  <SortableHeader
                    label="Kağıtlar"
                    active={sortBy === "worksheets"}
                    onClick={() => setSortBy("worksheets")}
                  />
                  <SortableHeader
                    label="Son üretim"
                    active={sortBy === "last"}
                    onClick={() => setSortBy("last")}
                  />
                </tr>
              </thead>
              <tbody>
                {merged.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-6 text-center text-muted-foreground">
                      Kayıt bulunamadı.
                    </td>
                  </tr>
                ) : (
                  merged.map((t) => (
                    <tr key={t.tenant_id} className="border-b last:border-0 hover:bg-muted/50">
                      <td className="py-2">
                        <Link
                          href={`/admin/tenants/${encodeURIComponent(t.tenant_id)}`}
                          className="font-mono text-xs text-primary hover:underline"
                        >
                          {t.tenant_id}
                        </Link>
                      </td>
                      <td className="py-2 text-right">{t.questions}</td>
                      <td className="py-2 text-right">{t.worksheets}</td>
                      <td className="py-2 text-right text-xs text-muted-foreground">
                        {formatTimestamp(t.last_at)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function SortableHeader({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <th className="py-2 text-right font-medium">
      <button
        onClick={onClick}
        className={`inline-flex items-center gap-1 hover:text-foreground ${active ? "text-foreground" : ""}`}
      >
        {label}
        <ArrowUpDown className="h-3 w-3" />
      </button>
    </th>
  );
}

function formatTimestamp(ts: number | null): string {
  if (!ts) return "—";
  const d = new Date(ts * 1000);
  return d.toLocaleString("tr-TR", { dateStyle: "short", timeStyle: "short" });
}
