"use client";

import * as React from "react";
import Image from "next/image";
import Link from "next/link";
import { History, Menu, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { UserButton, useAuth, useUser } from "@clerk/nextjs";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { effectiveRole, type Role } from "@/lib/roles";

// Uygulamanın "kendi alanı" linki role göre etiketlenir (hepsi /practice'e gider;
// hub yüzü kalıcı role göre render edilir). Admin ek olarak /admin görür.
function appLink(role: Role | null): { href: string; label: string } {
  switch (role) {
    case "teacher":
      return { href: "/practice", label: "Sınıfım" };
    case "parent":
      return { href: "/practice", label: "Çocuğum" };
    default: // student / admin / rolü yok / çıkış yapmış
      return { href: "/practice", label: "Çöz & Geliş" };
  }
}

// Genel (tanıtım + ana iş akışı) navigasyon. "Geçmiş" buraya KONULMAZ —
// kişisel/korumalı bir görünüm olduğu için UserButton açılır menüsünde.
function buildNavLinks(role: Role | null): { href: string; label: string }[] {
  const app = appLink(role);
  const links = [
    { href: "/generate", label: "Üretim" },
    { href: app.href, label: app.label },
    // Sınıf/konu SEO ağacının site-geneli girişi (orphan-ada fix'i — indeksleme).
    { href: "/calismalar", label: "Konular" },
    { href: "/features", label: "Özellikler" },
    { href: "/pricing", label: "Fiyatlandırma" },
    { href: "/faq", label: "Sıkça Sorulanlar" },
  ];
  if (role === "admin") links.push({ href: "/admin", label: "Admin" });
  return links;
}

const TopNavBar = () => {
  const { setTheme } = useTheme();
  const { isLoaded, isSignedIn } = useAuth();
  const { user } = useUser();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  const role = effectiveRole(user);
  const NAV_LINKS = buildNavLinks(role);

  return (
    <nav className="sticky top-0 z-40 border-b bg-background/85 backdrop-blur supports-[backdrop-filter]:bg-background/70">
      <div className="container flex h-16 items-center justify-between">
        <Link href="/" className="flex items-center" aria-label="Soru Atölyesi">
          <Image
            src="/logo.png"
            alt="Soru Atölyesi"
            width={706}
            height={173}
            priority
            className="h-8 w-auto rounded-md [filter:hue-rotate(32deg)_saturate(1.3)]"
          />
        </Link>
        <div className="hidden items-center gap-7 md:flex">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              {link.label}
            </Link>
          ))}
        </div>
        <div className="flex items-center gap-2">
          {/* Mobil menü — navbar linkleri md altında gizli; burada açılır. */}
          <div className="md:hidden">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" aria-label="Menü">
                  <Menu className="h-5 w-5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                {NAV_LINKS.map((link) => (
                  <DropdownMenuItem key={link.href} asChild>
                    <Link href={link.href}>{link.label}</Link>
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
          {mounted && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" aria-label="Tema değiştir">
                  <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
                  <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => setTheme("light")}>
                  Açık
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme("dark")}>
                  Koyu
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
          {isLoaded && isSignedIn && (
            <UserButton appearance={{ elements: { avatarBox: "h-8 w-8" } }}>
              {/* "Geçmiş" kişisel görünüm → genel navbar yerine avatar menüsünde.
                  Mobilde de erişilebilir (navbar linkleri md altında gizli). */}
              <UserButton.MenuItems>
                <UserButton.Link
                  label="Geçmiş"
                  labelIcon={<History className="h-4 w-4" />}
                  href="/history"
                />
              </UserButton.MenuItems>
            </UserButton>
          )}
          {isLoaded && !isSignedIn && (
            <>
              <Button asChild variant="ghost" size="sm" className="hidden sm:inline-flex">
                <Link href="/sign-in">Giriş</Link>
              </Button>
              <Button asChild size="sm">
                <Link href="/sign-up">Hesap aç</Link>
              </Button>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

export default TopNavBar;
