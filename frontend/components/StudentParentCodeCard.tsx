"use client";

import * as React from "react";
import { useAuth } from "@clerk/nextjs";
import { Copy, Loader2, Users } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { getParentCode } from "@/lib/api";

/**
 * Öğrenci tarafı (WS-6b): "Velin seni takip etsin" — öğrenci kalıcı takip kodunu
 * üretir/gösterir, veliyle paylaşır. Veli bu kodu kendi hesabında girip öğrencinin
 * ilerlemesini SALT-OKUNUR takip eder (bkz. ParentDashboard). Öğrenci yüzünde gösterilir.
 */
export function StudentParentCodeCard() {
  const { userId, isLoaded } = useAuth();
  const [code, setCode] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  if (!isLoaded || !userId) return null;

  async function genCode() {
    if (!userId) return;
    setLoading(true);
    try {
      setCode((await getParentCode(userId)).code);
    } catch {
      toast.error("Kod alınamadı");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="space-y-3">
      <div className="flex items-baseline gap-2">
        <Users className="h-4 w-4 self-center text-grape" />
        <h2 className="font-display text-lg font-bold">Velin seni takip etsin</h2>
      </div>
      <Card className="space-y-3 p-4 shadow-pop">
        <p className="text-xs text-muted-foreground">
          Bu kodu velinle paylaş; veli hesabından bu kodu girerek ilerlemeni
          (sadece görüntüleme) takip edebilir.
        </p>
        {code ? (
          <div className="flex items-center gap-2">
            <span className="rounded-lg border bg-accent/40 px-4 py-2 font-mono text-lg font-bold tracking-widest">
              {code}
            </span>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="gap-1.5"
              onClick={() => {
                navigator.clipboard?.writeText(code).then(
                  () => toast.success("Kod kopyalandı"),
                  () => {},
                );
              }}
            >
              <Copy className="h-3.5 w-3.5" /> Kopyala
            </Button>
          </div>
        ) : (
          <Button onClick={genCode} disabled={loading} size="sm" className="gap-2">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            Takip kodumu göster
          </Button>
        )}
      </Card>
    </section>
  );
}
