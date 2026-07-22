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
