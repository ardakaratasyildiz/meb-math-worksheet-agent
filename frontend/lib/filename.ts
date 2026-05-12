// Türkçe karakter -> ASCII transliterasyonu. Backend app/routers/worksheets.py
// içindeki _TURKISH_TRANSLIT ile birebir eşleşmeli (PDF dosya adı tutarlılığı).
const TURKISH_TRANSLIT: Record<string, string> = {
  "ş": "s", "Ş": "S",
  "ı": "i", "İ": "I",
  "ğ": "g", "Ğ": "G",
  "ç": "c", "Ç": "C",
  "ö": "o", "Ö": "O",
  "ü": "u", "Ü": "U",
};

export function buildPdfFilename(title: string): string {
  const transliterated = Array.from(title)
    .map((c) => TURKISH_TRANSLIT[c] ?? c)
    .join("");
  const cleaned = transliterated.replace(/[^A-Za-z0-9 \-_]/g, " ");
  const parts = cleaned.split(/\s+/).filter(Boolean);
  const slug = parts.length > 0 ? parts.join("_") : "Calisma_Kagidi";
  const today = new Date().toISOString().slice(0, 10);
  return `QuizMarketi_${slug}_${today}.pdf`;
}
