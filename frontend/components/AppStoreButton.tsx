"use client";

import type { VariantProps } from "class-variance-authority";
import { ArrowRight, Smartphone } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { track } from "@/lib/analytics";
import { IOS_APP_URL } from "@/lib/app-links";

/**
 * Ücretli planların GERÇEK satın alma kapısı — App Store.
 *
 * Abonelik yalnız uygulama içinden (Apple IAP) satılıyor, web'de ödeme yok.
 * Ücretli planlarda PricingInterestButton'ın (mailto ön-kaydı) yerini aldı:
 * talep artık ölçülecek bir niyet değil, tamamlanabilir bir satın alma.
 * GA4'e `app_store_click` olarak plan adıyla düşer, böylece hangi plan
 * kartının indirmeye götürdüğü huni raporunda ayrışır.
 */
export function AppStoreButton({
  plan,
  label = "App Store'dan indir",
  variant,
  size,
  className,
}: {
  /** GA4 event'inde ayrışsın diye plan slug'ı ya da CTA konumu, örn. "pro" */
  plan: string;
  label?: string;
  className?: string;
} & VariantProps<typeof buttonVariants>) {
  return (
    <a
      href={IOS_APP_URL}
      target="_blank"
      rel="noopener noreferrer"
      onClick={() => track("app_store_click", { plan })}
      className={cn(buttonVariants({ variant, size }), className)}
    >
      <Smartphone className="h-4 w-4" />
      {label}
      <ArrowRight className="h-4 w-4" />
    </a>
  );
}
