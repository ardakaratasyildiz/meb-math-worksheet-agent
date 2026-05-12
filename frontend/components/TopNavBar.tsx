"use client";

import * as React from "react";
import Image from "next/image";
import Link from "next/link";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { UserButton, useAuth } from "@clerk/nextjs";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const NAV_LINKS = [
  { href: "/generate", label: "Üretim" },
  { href: "/features", label: "Özellikler" },
  { href: "/pricing", label: "Fiyatlandırma" },
  { href: "/faq", label: "Sıkça Sorulanlar" },
];

const TopNavBar = () => {
  const { setTheme, resolvedTheme } = useTheme();
  const { isLoaded, isSignedIn } = useAuth();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  // Logo PNG beyaz zeminde tasarlandı; dark mode'da invert filtresi ile
  // hızlı çözüm (ideal: ayrı dark PNG/SVG).
  const isDark = mounted && resolvedTheme === "dark";

  return (
    <nav className="sticky top-0 z-40 border-b bg-background/85 backdrop-blur supports-[backdrop-filter]:bg-background/70">
      <div className="container flex h-16 items-center justify-between">
        <Link href="/" className="flex items-center" aria-label="Soru Atölyesi">
          <Image
            src="/logo.png"
            alt="Soru Atölyesi"
            width={386}
            height={256}
            priority
            className={`h-9 w-auto ${isDark ? "brightness-0 invert" : ""}`}
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
                <DropdownMenuItem onClick={() => setTheme("system")}>
                  Sistem
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
          {isLoaded && isSignedIn && (
            <UserButton appearance={{ elements: { avatarBox: "h-8 w-8" } }} />
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
