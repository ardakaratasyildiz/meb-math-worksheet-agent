import { DeleteAccountView } from "@/components/DeleteAccountView";

export const metadata = {
  title: "Hesabımı Sil · Soru Atölyesi",
  description:
    "Soru Atölyesi hesabını ve tüm verilerini kalıcı olarak silme talimatları.",
};

export default function DeleteAccountPage() {
  return <DeleteAccountView />;
}
