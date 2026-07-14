"use client";

import * as React from "react";
import { useUser } from "@clerk/nextjs";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import { effectiveRole, ROLE_META, type SelectableRole } from "@/lib/roles";

/**
 * Zorunlu rol seçimi (onboarding). Giriş yapmış ama rolü OLMAYAN kullanıcıya —
 * hem yeni üye hem tekrar giren mevcut kullanıcı — atlanamayan bir modal gösterir.
 * Seçim Clerk `unsafeMetadata.role`'e yazılır; sonra bir daha çıkmaz. Admin (publicMetadata)
 * ve rolü olanlar hiç görmez. Rol sonradan profilden değiştirilebilir (RoleSwitcher).
 *
 * Layout'a global monte edilir → kullanıcı hangi sayfada olursa olsun önce rolünü seçer.
 */
export function RoleGate() {
  const { isLoaded, isSignedIn, user } = useUser();
  const [saving, setSaving] = React.useState<SelectableRole | null>(null);

  if (!isLoaded || !isSignedIn || !user) return null;
  if (effectiveRole(user) !== null) return null; // rol var / admin → gösterme

  async function choose(role: SelectableRole) {
    if (!user) return;
    setSaving(role);
    try {
      await user.update({ unsafeMetadata: { ...user.unsafeMetadata, role } });
      // user.update sonrası useUser yeniden render eder → effectiveRole dolar → modal kapanır.
    } catch (e: unknown) {
      toast.error("Kaydedilemedi", {
        description: e instanceof Error ? e.message : "Lütfen tekrar dene.",
      });
      setSaving(null);
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Profilini seç"
      className="fixed inset-0 z-[100] flex items-center justify-center bg-background/80 p-4 backdrop-blur-sm"
    >
      <div className="w-full max-w-lg rounded-3xl border bg-card p-6 shadow-pop sm:p-8">
        <div className="space-y-1 text-center">
          <span aria-hidden className="text-4xl">
            👋
          </span>
          <h2 className="font-display text-2xl font-bold">Hoş geldin! Kimsin?</h2>
          <p className="text-sm text-muted-foreground">
            Sana doğru ekranları göstermemiz için profilini seç. Sonradan
            değiştirebilirsin.
          </p>
        </div>

        <div className="mt-6 grid gap-3">
          {ROLE_META.map((r) => {
            const busy = saving === r.value;
            const disabled = saving !== null;
            return (
              <button
                key={r.value}
                type="button"
                disabled={disabled}
                onClick={() => choose(r.value)}
                className="group flex items-center gap-4 rounded-2xl border p-4 text-left transition-colors hover:border-primary/50 hover:bg-accent/40 disabled:opacity-60"
              >
                <span
                  aria-hidden
                  className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-accent text-2xl"
                >
                  {busy ? <Loader2 className="h-5 w-5 animate-spin" /> : r.emoji}
                </span>
                <span className="min-w-0">
                  <span className="block font-display text-lg font-bold">
                    {r.label}
                  </span>
                  <span className="block text-sm text-muted-foreground">
                    {r.desc}
                  </span>
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
