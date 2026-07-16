"use client";

import * as React from "react";
import { useUser } from "@clerk/nextjs";

import { isSelectableRole } from "@/lib/roles";

/**
 * Legacy rol migrasyonu: eski kullanıcılarda rol `unsafeMetadata.role`'de (client-writable)
 * tutuluyordu. Bu bileşen, publicMetadata.role YOK ama unsafeMetadata.role VAR olan
 * kullanıcıda bir kez `/api/role`'ü çağırıp rolü SUNUCU-set publicMetadata'ya taşır
 * (kalıcılaştırır). Sonra effectiveRole publicMetadata'yı okur; eski unsafe değeri
 * yok sayılır. Görünmez; layout'a global monte edilir.
 */
export function RoleSync() {
  const { isLoaded, isSignedIn, user } = useUser();
  const done = React.useRef(false);

  React.useEffect(() => {
    if (!isLoaded || !isSignedIn || !user || done.current) return;
    const pub = (user.publicMetadata as { role?: string } | null)?.role;
    const legacy = (user.unsafeMetadata as { role?: string } | null)?.role;
    if (pub || !isSelectableRole(legacy)) return; // zaten kalıcı ya da taşınacak rol yok

    done.current = true; // oturum başına tek deneme
    void fetch("/api/role", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role: legacy }),
    })
      .then((r) => (r.ok ? user.reload() : null))
      .catch(() => {});
  }, [isLoaded, isSignedIn, user]);

  return null;
}
