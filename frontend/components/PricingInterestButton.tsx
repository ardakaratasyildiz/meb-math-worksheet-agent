"use client";

import type { VariantProps } from "class-variance-authority";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { track } from "@/lib/analytics";

/**
 * /pricing'deki ücretli plan CTA'sı — tıklanınca GA4 `pricing_plan_interest`
 * event'i (plan adıyla) atar, sonra e-posta ön-kayıt penceresini açar.
 *
 * NEDEN: billing altyapısı henüz kurulmadı ("şimdi tasarla, sonra kur" kararı).
 * Bu buton, ödeme sistemine dokunmadan HANGİ plana talep olduğunu ölçer →
 * north-star GA4 raporunda görünür, billing'i gerçek sinyal gelince kurarız.
 * SEO/pricing sayfası server component olduğu için onClick bu client wrapper'da.
 */
export function PricingInterestButton({
  plan,
  mailtoSubject,
  variant,
  size,
  className,
  children,
}: {
  /** GA4 event'inde ayrışsın diye plan slug'ı, örn. "bireysel" */
  plan: string;
  mailtoSubject: string;
  className?: string;
  children: React.ReactNode;
} & VariantProps<typeof buttonVariants>) {
  const href = `mailto:destek@soruatolyesi.com?subject=${encodeURIComponent(
    mailtoSubject,
  )}`;
  return (
    <a
      href={href}
      onClick={() => track("pricing_plan_interest", { plan })}
      className={cn(buttonVariants({ variant, size }), className)}
    >
      {children}
    </a>
  );
}
