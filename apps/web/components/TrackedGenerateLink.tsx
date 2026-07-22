"use client";

import Link from "next/link";
import type { VariantProps } from "class-variance-authority";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { track } from "@/lib/analytics";

/**
 * Generate sayfasına giden CTA — tıklanınca GA4 `cta_generate_click` event'i
 * atar, sonra normal Link gezinmesi yapar. SEO landing'leri (server component)
 * onClick handler taşıyamadığı için bu küçük client wrapper kullanılır.
 *
 * Huni ölçümü: cta_generate_click → generate_page_view → worksheet_generate_start
 * → worksheet_generate_success → pdf_download. cta vs page_view farkı =
 * auth-duvarı (login zorunlu /generate) kaynaklı kayıp.
 */
export function TrackedGenerateLink({
  href,
  source,
  grade,
  topic,
  variant,
  size,
  className,
  children,
}: {
  href: string;
  /** event'te hangi yüzeyden tıklandığını ayırmak için, örn. "lgs_hub" */
  source: string;
  grade?: number;
  topic?: string;
  className?: string;
  children: React.ReactNode;
} & VariantProps<typeof buttonVariants>) {
  return (
    <Link
      href={href}
      onClick={() => track("cta_generate_click", { source, grade, topic })}
      className={cn(buttonVariants({ variant, size }), className)}
    >
      {children}
    </Link>
  );
}
