/** Küçük biçimlendirme yardımcıları (tarih/skor). Hermes Intl kısıtlı → elle. */

const MONTHS = [
  "Oca", "Şub", "Mar", "Nis", "May", "Haz",
  "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara",
];

/** ISO tarihi "22 Tem 2026 · 14:30" gibi okunur Türkçe metne çevirir. */
export function formatDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()} · ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/**
 * Denemenin bitmesine kalan GÜN sayısı (bugün biterse 0). Geçmiş/geçersiz → null.
 *
 * Deneme sunucuda tutuluyor (kartsız reverse trial) ve kullanıcı bunu hiçbir yerde
 * görmüyordu: 7 gün Pro+ kalitesi alıp bittiğinde neden kısıtlandığını anlamıyordu.
 * Bu yüzden kalan süre ekranlarda gösterilir.
 */
export function trialDaysLeft(trialEnd: string | null | undefined): number | null {
  if (!trialEnd) return null;
  const end = new Date(trialEnd).getTime();
  if (Number.isNaN(end)) return null;
  const diffMs = end - Date.now();
  if (diffMs <= 0) return null;
  return Math.max(0, Math.ceil(diffMs / 86_400_000));
}

/** "3 gün kaldı" / "bugün bitiyor" — kalan güne göre okunur metin. */
export function trialLeftLabel(daysLeft: number | null): string | null {
  if (daysLeft === null) return null;
  if (daysLeft <= 1) return "bugün bitiyor";
  return `${daysLeft} gün kaldı`;
}

/** Doğru/toplam → yüzde (tam sayı, 0'a bölme güvenli). */
export function scorePct(score: number, total: number): number {
  return Math.round((score / Math.max(total, 1)) * 100);
}

/** Başarı yüzdesine göre renk anahtarı — success (≥70) / warn (≥40) / danger. */
export function scoreTone(pct: number): "good" | "mid" | "low" {
  if (pct >= 70) return "good";
  if (pct >= 40) return "mid";
  return "low";
}
