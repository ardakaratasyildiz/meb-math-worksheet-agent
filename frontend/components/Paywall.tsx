"use client";

import Link from "next/link";
import { ArrowRight, Check, Sparkles } from "lucide-react";

import type { QuotaInfo } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

/**
 * Kota aşımı paywall'ı (MONETIZATION_PLAN §8 — güven-önce, jarring değil).
 *
 * Generate akışı `QuotaExceededError` yakalayınca açılır. billing_enabled canlı
 * olana kadar backend 402 döndürmediği için pratikte görünmez (forward-compat).
 * Kayıp-kaçınma + yıllık/aylık çerçeve yerine sade "Pro'ya geç" + güven sinyalleri.
 */
export function Paywall({
  open,
  onOpenChange,
  info,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  info: QuotaInfo | null;
}) {
  const limit = info?.limit ?? null;
  // Günlük tavan GEÇİCİ (yarın açılır) — "hakkın bitti, satın al" demek yanlış olur.
  const daily = info?.error === "daily_limit_reached";
  const dailyLimit = info?.daily_limit ?? null;
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-accent text-accent-foreground">
            <Sparkles className="h-6 w-6" />
          </div>
          <DialogTitle className="text-center text-xl">
            {daily ? "Bugünlük hakkın doldu" : "Bu ayki ücretsiz hakkın doldu"}
          </DialogTitle>
          <DialogDescription className="text-center">
            {daily ? (
              <>
                {dailyLimit
                  ? `Ücretsiz planda günde ${dailyLimit} çalışma kağıdı üretebilirsin.`
                  : "Günlük ücretsiz üretim hakkını kullandın."}{" "}
                Hakkın yarın yenilenir — beklemek istemezsen Pro ile hemen devam edebilirsin.
              </>
            ) : (
              <>
                {limit
                  ? `Aylık ${limit} çalışma kağıdı hakkını kullandın.`
                  : "Aylık ücretsiz üretim hakkını kullandın."}{" "}
                Pro ile kaldığın yerden devam et — üretimin durmasın.
              </>
            )}
          </DialogDescription>
        </DialogHeader>

        <ul className="mx-auto space-y-2 py-2 text-sm text-foreground">
          {[
            "Pro ₺199/ay — ayda 50 çalışma kağıdı",
            "Pro+ ₺349/ay — ayda 120 kağıt + veli/öğretmen takibi",
            "Günlük sınır yok · yeni nesil kalite + filigransız PDF",
          ].map((f) => (
            <li key={f} className="flex items-start gap-2">
              <Check className="mt-0.5 h-4 w-4 shrink-0 text-mint" />
              <span>{f}</span>
            </li>
          ))}
        </ul>

        <DialogFooter className="flex-col gap-2 sm:flex-col">
          <Button asChild size="lg" className="w-full gap-2">
            <Link href="/pricing">
              Planları gör <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
          <button
            type="button"
            onClick={() => onOpenChange(false)}
            className="text-xs text-muted-foreground underline-offset-2 hover:underline"
          >
            Sonra devam ederim
          </button>
          <p className="text-center text-[11px] text-muted-foreground">
            İstediğin an iptal edebilirsin · Kota her ay başında sıfırlanır
          </p>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
