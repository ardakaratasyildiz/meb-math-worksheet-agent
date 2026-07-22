"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { ArrowLeft, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchTenantUsers, tenantDisplay, type TenantUser } from "@/lib/tenant-label";

interface HistoryItem {
  key: string;
  normalized_question: string;
  contexts: string[];
}

interface TenantHistoryResponse {
  tenant_id: string;
  count: number;
  items: HistoryItem[];
}

export default function TenantDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [data, setData] = useState<TenantHistoryResponse | null>(null);
  const [users, setUsers] = useState<Record<string, TenantUser>>({});
  const [usersLoaded, setUsersLoaded] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    // Kullanıcı ad/e-posta çözümü (Clerk) — best-effort, geçmişle paralel.
    setUsersLoaded(false);
    fetchTenantUsers([id])
      .then(setUsers)
      .finally(() => setUsersLoaded(true));
    try {
      const res = await fetch(
        `/api/admin/tenants/${encodeURIComponent(id)}?limit=200`,
        { cache: "no-store" },
      );
      if (!res.ok) {
        throw new Error(`${res.status} ${res.statusText}`);
      }
      const json = await res.json();
      setData(json);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Link
          href="/admin/tenants"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Tüm kullanıcılar
        </Link>
        <Button variant="outline" size="sm" onClick={load} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Yenile
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardDescription>Kullanıcı</CardDescription>
          <CardTitle className="break-words text-lg">
            {tenantDisplay(id, users, usersLoaded)}
          </CardTitle>
          <p className="break-all font-mono text-xs text-muted-foreground">{id}</p>
          {data && (
            <p className="text-sm text-muted-foreground">
              {data.count} soru kaydı gösteriliyor (en yeni 200 ile sınırlı).
            </p>
          )}
        </CardHeader>
        <CardContent>
          {error && (
            <div className="mb-4 rounded-md border border-destructive bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}
          {loading && <Skeleton className="h-64 w-full" />}
          {data && !loading && (
            <div className="space-y-3">
              {data.items.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  Bu tenant için kayıt bulunamadı.
                </p>
              ) : (
                data.items.map((it, idx) => (
                  <div
                    key={`${it.key}-${idx}`}
                    className="rounded-md border bg-card p-3 text-sm"
                  >
                    <p className="whitespace-pre-wrap break-words">
                      {it.normalized_question || (
                        <span className="text-muted-foreground italic">
                          (boş normalize)
                        </span>
                      )}
                    </p>
                    {it.contexts.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {it.contexts.map((c, i) => (
                          <span
                            key={i}
                            className="rounded bg-muted px-2 py-0.5 text-xs text-muted-foreground"
                          >
                            {c}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
