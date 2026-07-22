import { notFound } from "next/navigation";
import Link from "next/link";
import { Activity, Coins, Database, ScrollText, Users } from "lucide-react";

import { isAdminUser } from "@/lib/admin-proxy";

export const metadata = {
  title: "Admin · Soru Atölyesi",
  robots: "noindex, nofollow",
};

/**
 * Admin layout — server component olarak role check yapar.
 * Admin değilse `notFound()` çağrılır → Next.js default 404 sayfası gösterilir,
 * sayfanın varlığı dışarı sızmaz (`/admin` URL'i index'lenmez ve admin olmayan
 * için hiç render olmaz).
 *
 * Tüm `/admin/*` alt sayfaları bu layout'tan miras alır → tek noktada koruma.
 */
export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const ok = await isAdminUser();
  if (!ok) notFound();
  return (
    <div className="container py-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Admin Paneli</h1>
          <p className="text-sm text-muted-foreground">
            Sistem sağlığı, cache, kullanıcı geçmişi ve audit log.
          </p>
        </div>
        <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-900 dark:bg-amber-900/30 dark:text-amber-200">
          Internal · noindex
        </span>
      </div>
      <nav className="mb-8 flex flex-wrap gap-2 border-b pb-4">
        <AdminNavLink href="/admin" icon={<Activity className="h-4 w-4" />} label="Dashboard" />
        <AdminNavLink href="/admin/costs" icon={<Coins className="h-4 w-4" />} label="Maliyet" />
        <AdminNavLink href="/admin/tenants" icon={<Users className="h-4 w-4" />} label="Kullanıcılar" />
        <AdminNavLink href="/admin/cache" icon={<Database className="h-4 w-4" />} label="Cache" />
        <AdminNavLink href="/admin/audit" icon={<ScrollText className="h-4 w-4" />} label="Audit log" />
      </nav>
      {children}
    </div>
  );
}

function AdminNavLink({
  href,
  icon,
  label,
}: {
  href: string;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <Link
      href={href}
      className="inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground"
    >
      {icon}
      {label}
    </Link>
  );
}
