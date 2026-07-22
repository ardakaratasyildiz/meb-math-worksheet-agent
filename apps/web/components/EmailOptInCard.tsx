"use client";

import * as React from "react";
import { useAuth, useUser } from "@clerk/nextjs";
import { Loader2, Mail } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { getEmailPrefs, setEmailPrefs } from "@/lib/api";

/**
 * KVKK opt-in onay kartı — kullanıcı henüz tercih belirtmediyse (is_set=false)
 * bir kez gösterilir: "bülten + hatırlatma e-postası almak ister misin?".
 * Evet/Hayır → tercih kaydedilir, kart kaybolur. İzin açık + geri alınabilir.
 */
export function EmailOptInCard() {
  const { userId, isLoaded } = useAuth();
  const { user } = useUser();
  const [show, setShow] = React.useState(false);
  const [saving, setSaving] = React.useState(false);

  React.useEffect(() => {
    if (!isLoaded || !userId) return;
    let active = true;
    getEmailPrefs(userId)
      .then((p) => {
        if (active && !p.is_set) setShow(true);
      })
      .catch(() => {
        /* sessiz — onay kartı kritik değil */
      });
    return () => {
      active = false;
    };
  }, [userId, isLoaded]);

  async function choose(optin: boolean) {
    if (!userId) return;
    setSaving(true);
    const email = user?.primaryEmailAddress?.emailAddress ?? null;
    try {
      await setEmailPrefs(userId, email, optin);
      setShow(false);
      toast.success(
        optin ? "Teşekkürler! E-posta ile haberdar edeceğiz." : "Tamam, e-posta göndermeyeceğiz.",
      );
    } catch (e: unknown) {
      toast.error("Tercih kaydedilemedi", {
        description: e instanceof Error ? e.message : undefined,
      });
    } finally {
      setSaving(false);
    }
  }

  if (!show) return null;

  return (
    <Card className="flex flex-col gap-3 border-sky-400/30 bg-sky-400/5 p-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-sky-400/15 text-sky-500">
          <Mail className="h-5 w-5" />
        </div>
        <div>
          <p className="font-display font-bold">E-posta ile haberdar olmak ister misin?</p>
          <p className="mt-0.5 text-sm text-muted-foreground">
            Yeni özellikler, ödev hatırlatmaları ve ipuçlarını e-posta ile gönderelim.
            İstediğin zaman vazgeçebilirsin (her mailde abonelikten çık linki).
          </p>
        </div>
      </div>
      <div className="flex shrink-0 gap-2">
        <Button onClick={() => choose(false)} disabled={saving} variant="ghost" size="sm">
          Hayır
        </Button>
        <Button onClick={() => choose(true)} disabled={saving} size="sm" className="gap-1.5">
          {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Mail className="h-4 w-4" />}
          Evet, gönder
        </Button>
      </div>
    </Card>
  );
}
