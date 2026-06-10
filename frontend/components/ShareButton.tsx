"use client";

import * as React from "react";
import { Share2 } from "lucide-react";

import { Button } from "@/components/ui/button";

const SITE_URL = "https://soruatolyesi.com";
const DEFAULT_TEXT =
  "Soru Atölyesi ile MEB matematik çalışma kağıdı hazırla, site içinde test gibi çöz:";

type Variant =
  | "default"
  | "outline"
  | "secondary"
  | "ghost"
  | "link"
  | "destructive";

// Paylaş — mobilde native paylaşım sayfası (WhatsApp dahil), yoksa doğrudan
// WhatsApp'a düşer. PDF büyüme döngüsü: "WhatsApp'a at" → arkadaş da üretir.
export function ShareButton({
  text = DEFAULT_TEXT,
  url = SITE_URL,
  label = "WhatsApp'a at",
  variant = "outline",
  className,
}: {
  text?: string;
  url?: string;
  label?: string;
  variant?: Variant;
  className?: string;
}) {
  async function onShare() {
    const nav = typeof navigator !== "undefined" ? navigator : undefined;
    if (nav && typeof nav.share === "function") {
      try {
        await nav.share({ title: "Soru Atölyesi", text, url });
        return;
      } catch {
        // Kullanıcı iptal etti ya da desteklenmiyor → WhatsApp fallback.
      }
    }
    const wa = `https://wa.me/?text=${encodeURIComponent(`${text} ${url}`)}`;
    if (typeof window !== "undefined") {
      window.open(wa, "_blank", "noopener,noreferrer");
    }
  }

  return (
    <Button
      type="button"
      onClick={onShare}
      variant={variant}
      className={`gap-2 ${className ?? ""}`}
    >
      <Share2 className="h-4 w-4" />
      {label}
    </Button>
  );
}
