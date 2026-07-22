import { currentUser } from "@clerk/nextjs/server";

import { PracticeHub } from "@/components/PracticeHub";
import { effectiveRole } from "@/lib/roles";

// /practice hub — KALICI role göre yüz gösterir (öğrenci/öğretmen/veli); admin hepsini
// görür. Rol Clerk metadata'da (onboarding → unsafeMetadata.role; admin publicMetadata).
// Rol yoksa RoleGate (layout) zaten zorunlu seçim modalını gösterir. Login zorunlu.
export default async function PracticePage() {
  const user = await currentUser();
  const role = effectiveRole(user);
  return <PracticeHub role={role} />;
}
