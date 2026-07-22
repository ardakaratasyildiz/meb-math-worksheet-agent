"use client";

import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface AuditItem {
  id: number;
  clerk_user_id: string | null;
  action: string;
  target: string | null;
  ip: string | null;
  created_at: number;
}

export default function AuditPage() {
  const [items, setItems] = useState<AuditItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/admin/audit?limit=200", { cache: "no-store" });
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
          <CardTitle>Audit log</CardTitle>
          <CardDescription>
            Admin paneline kim, ne zaman, hangi kullanıcının verisine baktı.
            KVKK & güvenlik kanıtı — bu sayfayı görüntülemek de kayıt altına alınır.
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
          <p className="text-sm text-muted-foreground">Henüz kayıt yok.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="py-2 font-medium">Zaman</th>
                  <th className="py-2 font-medium">Kullanıcı (Clerk)</th>
                  <th className="py-2 font-medium">Eylem</th>
                  <th className="py-2 font-medium">Hedef</th>
                  <th className="py-2 font-medium">IP</th>
                </tr>
              </thead>
              <tbody>
                {items.map((it) => (
                  <tr key={it.id} className="border-b last:border-0">
                    <td className="py-2 text-xs text-muted-foreground whitespace-nowrap">
                      {formatTimestamp(it.created_at)}
                    </td>
                    <td className="py-2 font-mono text-xs">
                      {it.clerk_user_id ?? <span className="text-muted-foreground">curl</span>}
                    </td>
                    <td className="py-2">
                      <code className="rounded bg-muted px-1.5 py-0.5 text-xs">{it.action}</code>
                    </td>
                    <td className="py-2 font-mono text-xs">{it.target ?? "—"}</td>
                    <td className="py-2 font-mono text-xs text-muted-foreground">
                      {it.ip ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function formatTimestamp(ts: number): string {
  const d = new Date(ts * 1000);
  return d.toLocaleString("tr-TR", { dateStyle: "short", timeStyle: "medium" });
}
