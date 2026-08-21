/**
 * White-label PDF markası (kurum/öğretmen adı + logo) — CİHAZDA saklanır.
 *
 * Backend `render.pdf` zaten `brand_name` / `brand_subtitle` / `brand_logo` (base64)
 * kabul ediyor ve ücretli plan kapısı SUNUCUDA (`entitlements.has_paid_access` →
 * ücretsizde alanlar yok sayılır, bkz. worksheets.py). Web'de arayüz vardı, mobilde
 * YOKTU → "Filigransız PDF — kendi logonuzu ekleyin" vaadi mobilde karşılıksızdı
 * (2026-08-21 plan denetimi).
 *
 * Neden SecureStore değil: logo base64'ü onlarca KB, SecureStore'un değer sınırı
 * 2 KB. Neden sunucu değil: marka kişisel bir tercih, hesaba bağlamak için ayrı bir
 * uç/tablo gerekir — ilk tur cihazda yeterli (kullanıcı tek cihazdan üretiyor).
 * Dosya `documentDirectory`'de tutulur → uygulama silinene kadar kalıcı.
 */
import * as FileSystem from "expo-file-system/legacy";

export interface Branding {
  /** Kurum/öğretmen adı — PDF üst bilgisinde solda. */
  name: string;
  /** Alt satır (şube, ders, iletişim) — üst bilgide sağda. */
  subtitle: string;
  /** Logo, `data:image/...;base64,...` biçiminde. Boş = logo yok. */
  logo: string;
}

export const EMPTY_BRANDING: Branding = { name: "", subtitle: "", logo: "" };

/**
 * Logo için üst sınır (base64 karakteri). `render.pdf` gövde tavanı 8 MB ve logo
 * base64'ü ~%33 şişer; 700 KB'lık bir sınır hem tavanın altında kalır hem de
 * 1024px'lik bir amblem için bol bol yeter. Aşarsa kullanıcıya söylenir —
 * sessizce kırpmak "logom neden bozuk" sorusuna yol açar.
 */
export const MAX_LOGO_CHARS = 700_000;

function fileUri(): string {
  // documentDirectory yoksa (beklenmez) kaydetme sessizce devre dışı kalır.
  return `${FileSystem.documentDirectory ?? ""}branding.json`;
}

/** Kayıtlı markayı okur. Dosya yok / bozuk → EMPTY_BRANDING (asla fırlatmaz). */
export async function loadBranding(): Promise<Branding> {
  try {
    const uri = fileUri();
    if (!uri) return EMPTY_BRANDING;
    const info = await FileSystem.getInfoAsync(uri);
    if (!info.exists) return EMPTY_BRANDING;
    const raw = await FileSystem.readAsStringAsync(uri);
    const parsed = JSON.parse(raw) as Partial<Branding>;
    return {
      name: typeof parsed.name === "string" ? parsed.name : "",
      subtitle: typeof parsed.subtitle === "string" ? parsed.subtitle : "",
      logo: typeof parsed.logo === "string" ? parsed.logo : "",
    };
  } catch {
    return EMPTY_BRANDING;
  }
}

/** Markayı kaydeder. Best-effort: hata üretim akışını bozmaz. */
export async function saveBranding(b: Branding): Promise<void> {
  try {
    const uri = fileUri();
    if (!uri) return;
    await FileSystem.writeAsStringAsync(uri, JSON.stringify(b));
  } catch {
    // sessiz — marka kaydedilemese de kağıt üretilebilir
  }
}

/** Markada gösterilecek/gönderilecek bir şey var mı? */
export function hasBranding(b: Branding): boolean {
  return !!(b.name.trim() || b.subtitle.trim() || b.logo);
}
