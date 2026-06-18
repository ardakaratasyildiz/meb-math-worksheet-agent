import { PracticeHub } from "@/components/PracticeHub";

// /practice hub — rol toggle (öğrenci / öğretmen-veli). Navbar "Sınıfım" kapısı
// ?role=teacher ile öğretmen yüzünü açar; aksi halde son seçim (localStorage) /
// öğrenci varsayılır. Login zorunlu (middleware /practice).
export default async function PracticePage({
  searchParams,
}: {
  searchParams: Promise<{ role?: string }>;
}) {
  const sp = await searchParams;
  const roleParam =
    sp.role === "teacher" ? "teacher" : sp.role === "student" ? "student" : null;
  return <PracticeHub roleParam={roleParam} />;
}
