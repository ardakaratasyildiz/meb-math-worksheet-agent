"use client";

import * as React from "react";
import { useAuth } from "@clerk/nextjs";
import { Check, Copy, Loader2, Share2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { createShare } from "@/lib/api";
import { track } from "@/lib/analytics";

const SHARE_TEXT =
  "Sana bir matematik quiz'i hazırladım, çözmek ister misin?";

/**
 * Quiz paylaş — link oluşturur (idempotent), kopyalama + WhatsApp paylaşımı sunar.
 * Paylaşılan link login'siz çözülebilir (/q/[code]); viral döngü buradan başlar.
 * Yalnız giriş yapmış sahibi paylaşabilir (quiz kişiseldir).
 */
export function ShareQuizButton({
  quizId,
  variant = "outline",
  className,
}: {
  quizId: string;
  variant?: "default" | "outline" | "secondary" | "ghost";
  className?: string;
}) {
  const { userId } = useAuth();
  const [loading, setLoading] = React.useState(false);
  const [url, setUrl] = React.useState<string | null>(null);
  const [copied, setCopied] = React.useState(false);

  async function onCreate() {
    if (!userId) {
      toast.error("Paylaşmak için giriş yapmalısın.");
      return;
    }
    setLoading(true);
    try {
      const res = await createShare(quizId, userId);
      const origin =
        typeof window !== "undefined" ? window.location.origin : "";
      const full = `${origin}${res.share_url}`;
      setUrl(full);
      track("quiz_share_create", { quiz_id: quizId });
      await copy(full);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Paylaşım oluşturulamadı.";
      toast.error("Paylaşım oluşturulamadı", { description: msg });
    } finally {
      setLoading(false);
    }
  }

  async function copy(value: string) {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      toast.success("Link kopyalandı");
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard yoksa (eski tarayıcı / izin) sessiz geç — link görünür duruyor.
    }
  }

  async function onWhatsApp() {
    if (!url) return;
    const nav = typeof navigator !== "undefined" ? navigator : undefined;
    if (nav && typeof nav.share === "function") {
      try {
        await nav.share({ title: "Soru Atölyesi", text: SHARE_TEXT, url });
        return;
      } catch {
        // iptal / desteklenmiyor → WhatsApp fallback
      }
    }
    const wa = `https://wa.me/?text=${encodeURIComponent(`${SHARE_TEXT} ${url}`)}`;
    window.open(wa, "_blank", "noopener,noreferrer");
  }

  if (!url) {
    return (
      <Button
        type="button"
        onClick={onCreate}
        disabled={loading}
        variant={variant}
        className={`gap-2 ${className ?? ""}`}
      >
        {loading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Share2 className="h-4 w-4" />
        )}
        Paylaş
      </Button>
    );
  }

  return (
    <div className="flex w-full max-w-md flex-col gap-2 rounded-lg border bg-background/60 p-3 sm:flex-row sm:items-center">
      <Input
        readOnly
        value={url}
        onFocus={(e) => e.currentTarget.select()}
        className="text-xs"
      />
      <div className="flex shrink-0 gap-2">
        <Button
          type="button"
          size="sm"
          variant="outline"
          onClick={() => copy(url)}
          className="gap-1.5"
        >
          {copied ? (
            <Check className="h-4 w-4 text-emerald-500" />
          ) : (
            <Copy className="h-4 w-4" />
          )}
          Kopyala
        </Button>
        <Button type="button" size="sm" onClick={onWhatsApp} className="gap-1.5">
          <Share2 className="h-4 w-4" />
          WhatsApp
        </Button>
      </div>
    </div>
  );
}
