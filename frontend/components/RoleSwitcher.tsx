"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useUser } from "@clerk/nextjs";
import { Check, ChevronDown, Loader2, UserCog } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { effectiveRole, ROLE_META, roleLabel, type SelectableRole } from "@/lib/roles";

/**
 * Profil (rol) değiştirici — onboarding'den sonra kullanıcı rolünü değiştirebilir.
 * unsafeMetadata.role'ü günceller, ardından router.refresh() ile sunucuda render edilen
 * yüzü (PracticeHub) tazeler. Admin'e gösterilmez (admin publicMetadata'dan gelir, değişmez);
 * rolü olmayan kullanıcıda da gösterilmez (RoleGate zaten seçim ister).
 */
export function RoleSwitcher() {
  const { isLoaded, user } = useUser();
  const router = useRouter();
  const [saving, setSaving] = React.useState(false);

  if (!isLoaded || !user) return null;
  const current = effectiveRole(user);
  if (current === null || current === "admin") return null;

  async function switchTo(role: SelectableRole) {
    if (!user || role === current || saving) return;
    setSaving(true);
    try {
      await user.update({ unsafeMetadata: { ...user.unsafeMetadata, role } });
      toast.success(`Profil değişti: ${roleLabel(role)}`);
      router.refresh(); // sunucu-render yüzü (PracticeHub) yeni role göre tazele
    } catch (e: unknown) {
      toast.error("Değiştirilemedi", {
        description: e instanceof Error ? e.message : "Lütfen tekrar dene.",
      });
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex justify-end">
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="gap-1.5">
          {saving ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <UserCog className="h-3.5 w-3.5" />
          )}
          {roleLabel(current)}
          <ChevronDown className="h-3.5 w-3.5 opacity-60" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel>Profilini değiştir</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {ROLE_META.map((r) => (
          <DropdownMenuItem
            key={r.value}
            disabled={saving}
            onClick={() => switchTo(r.value)}
            className="gap-2"
          >
            <span aria-hidden>{r.emoji}</span>
            <span className="flex-1">{r.label}</span>
            {r.value === current ? <Check className="h-4 w-4 text-primary" /> : null}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
    </div>
  );
}
