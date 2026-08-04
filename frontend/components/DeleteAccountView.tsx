"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { AlertTriangle, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { DeleteAccountError, deleteAccount } from "@/lib/api";

const CONFIRM_PHRASE = "HESABIMI SIL";

const WHAT_GETS_DELETED = [
  "Ürettiğin çalışma kağıtları ve quizler",
  "Çözüm geçmişin",
  "İlerlemen ve rozetlerin",
  "Oluşturduğun sınıflar ve ödevler",
  "Veli-öğrenci bağlantıların",
  "Hesap bilgilerin",
];

function errorMessage(e: unknown): string {
  if (e instanceof DeleteAccountError) {
    switch (e.status) {
      case 401:
        return "Oturumun sona ermiş görünüyor. Tekrar giriş yapıp dene.";
      case 502:
        return "Verilerin silindi ama hesabı kapatma adımı tamamlanamadı. Lütfen tekrar dene.";
      case 503:
        return "Sunucu şu anda bu işlemi yapamıyor. Birazdan tekrar dene.";
      case 400:
        return e.message || "Onay metni eşleşmedi. Lütfen tam olarak yazdığından emin ol.";
      default:
        return e.message || "Hesap silinemedi. Lütfen tekrar dene.";
    }
  }
  return e instanceof Error ? e.message : "Hesap silinemedi. Lütfen tekrar dene.";
}

export function DeleteAccountView() {
  // Repo genelinde Clerk `useAuth()` ile kullanılıyor (SignedIn/SignedOut kontrol
  // bileşenleri @clerk/nextjs v7'de dışa aktarılmıyor). `isLoaded` beklenmezse
  // sayfa bir an "giriş yap" gösterip sonra forma atlıyor.
  const { isLoaded, isSignedIn, signOut } = useAuth();
  const router = useRouter();
  const [confirmText, setConfirmText] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const canSubmit = confirmText.trim() === CONFIRM_PHRASE && !busy;

  async function onDelete() {
    if (!canSubmit || busy) return;
    setBusy(true);
    setError(null);
    try {
      await deleteAccount();
      await signOut();
      router.replace("/");
    } catch (e) {
      setError(errorMessage(e));
      setBusy(false);
    }
  }

  return (
    <div className="container max-w-2xl space-y-6 py-10">
      <div>
        <h1 className="text-2xl font-semibold">Hesabımı Sil</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Hesabını ve tüm verilerini kalıcı olarak silebilirsin.
        </p>
      </div>

      <Card className="border-destructive/30 bg-destructive/5">
        <CardContent className="flex gap-3 p-4">
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-destructive" />
          <p className="text-sm text-foreground">
            <span className="font-semibold">Bu işlem geri alınamaz.</span> Hesabını sildiğinde tüm
            verilerin kalıcı olarak kaybolur.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Silinecekler</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="ml-5 list-disc space-y-1.5 text-sm text-muted-foreground">
            {WHAT_GETS_DELETED.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <Card className="border-amber-400/30 bg-amber-400/10">
        <CardContent className="p-4">
          <p className="text-sm text-foreground">
            Aboneliğin varsa App Store / Google Play üzerinden ayrıca iptal etmelisin —
            hesabını silmek aboneliği durdurmaz.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Onayla</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {!isLoaded ? (
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          ) : isSignedIn ? (
            <>
              <p className="text-sm text-muted-foreground">
                Devam etmek için aşağıya tam olarak <span className="font-semibold text-foreground">{CONFIRM_PHRASE}</span> yaz.
              </p>
              <Input
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value)}
                placeholder={CONFIRM_PHRASE}
                autoComplete="off"
                disabled={busy}
              />
              {error ? <p className="text-sm text-destructive">{error}</p> : null}
              <Button
                variant="destructive"
                disabled={!canSubmit}
                onClick={() => void onDelete()}
                className="gap-1.5"
              >
                {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                Hesabımı kalıcı olarak sil
              </Button>
            </>
          ) : (
            <>
              <p className="text-sm text-muted-foreground">
                Hesabını silmek için önce giriş yapmalısın.
              </p>
              <Button asChild>
                <Link href="/sign-in">Giriş yap</Link>
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
