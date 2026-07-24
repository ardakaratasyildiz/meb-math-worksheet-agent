/**
 * RevenueCat (react-native-purchases) — GUARD'LI sarmalayıcı.
 *
 * react-native-purchases bir NATIVE modüldür → Expo Go'da native derlenmez, import/çağrı
 * anında patlar (aynen @clerk/expo ClerkExpo krizi gibi). Bu modül her erişimi lazy-require
 * + try/catch ile korur: native modül yok VEYA RevenueCat anahtarı boş ise `available=false`
 * olur ve tüm çağrılar zararsızca no-op / PurchasesUnavailableError döner. Böylece Expo Go
 * çalışır (paywall "yakında" durumu gösterir); gerçek satın-alma yalnız EAS dev/prod build'de
 * (native + EXPO_PUBLIC_REVENUECAT_* anahtarı + App Store/Play ürünleri) devreye girer.
 *
 * Faz 5b (28 Tem dev build): anahtarları .env/EAS'e koy + store ürünlerini (pro-aylik,
 * proplus-aylik, topup-25, topup-75) tanımla → bu sarmalayıcı otomatik "ready" olur.
 */
import { Platform } from "react-native";

import { ENV } from "./env";

/** Native modül JS sarmalayıcısı (varsa). Tipler pakete bağlanmasın diye `any`. */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let Purchases: any = null;
let nativeLoaded = false;

function loadNative(): boolean {
  if (nativeLoaded) return !!Purchases;
  nativeLoaded = true;
  try {
    // Lazy require: Expo Go'da native modül yoksa burada değil, çağrıda korunuruz.
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const mod = require("react-native-purchases");
    Purchases = mod?.default ?? mod ?? null;
  } catch {
    Purchases = null;
  }
  return !!Purchases;
}

function platformKey(): string {
  return Platform.OS === "ios" ? ENV.revenueCatIosKey : ENV.revenueCatAndroidKey;
}

let configured = false;

/** Satın-alma bu ortamda mümkün mü (native modül + platform anahtarı var). */
export function purchasesSupported(): boolean {
  return loadNative() && !!platformKey();
}

export class PurchasesUnavailableError extends Error {
  constructor() {
    super("Satın alma bu ortamda kullanılamıyor (uygulama mağaza sürümü gerekir).");
    this.name = "PurchasesUnavailableError";
  }
}

/**
 * RevenueCat'i Clerk kullanıcı kimliğiyle bir kez yapılandırır (idempotent).
 * appUserID = Clerk userId → webhook backend'te aynı tenant_id'ye eşlenir.
 * Desteklenmiyorsa sessizce döner (Expo Go).
 */
export function configurePurchases(appUserID: string): void {
  if (configured || !purchasesSupported() || !appUserID) return;
  try {
    Purchases.configure({ apiKey: platformKey(), appUserID });
    configured = true;
  } catch {
    // native yapılandırma hatası — satın-alma kapalı kalır
  }
}

/** Normalize edilmiş mağaza ürünü (fiyat mağazadan gelir; yerelleştirilmiş). */
export interface StoreProduct {
  productId: string;
  priceString: string; // "₺199,00" (mağaza yerelleştirmesi)
  title: string;
}

/** Verilen SKU'lar için mağaza ürünlerini getirir (yoksa boş). */
export async function fetchProducts(skus: string[]): Promise<StoreProduct[]> {
  if (!purchasesSupported()) return [];
  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const products: any[] = await Purchases.getProducts(skus);
    return (products ?? []).map((p) => ({
      productId: p.identifier,
      priceString: p.priceString,
      title: p.title,
    }));
  } catch {
    return [];
  }
}

/**
 * Bir SKU'yu satın alır. Başarılıysa true (entitlement RevenueCat + webhook üzerinden
 * backend'e yazılır → çağıran getEntitlements'i yenilemeli). Kullanıcı iptal ederse false.
 * Desteklenmiyorsa PurchasesUnavailableError fırlatır (UI kullanıcıya bunu göstermeli).
 */
export async function purchaseSku(sku: string): Promise<boolean> {
  if (!purchasesSupported()) throw new PurchasesUnavailableError();
  const products = await fetchProducts([sku]);
  if (!products.length) throw new Error("Ürün mağazada bulunamadı.");
  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const raw: any[] = await Purchases.getProducts([sku]);
    await Purchases.purchaseStoreProduct(raw[0]);
    return true;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } catch (e: any) {
    if (e?.userCancelled) return false;
    throw new Error(e?.message ?? "Satın alma tamamlanamadı.");
  }
}

/**
 * Önceki satın-almaları geri yükler (yeni cihaz / yeniden kurulum). Aktif entitlement
 * varsa true. Desteklenmiyorsa PurchasesUnavailableError.
 */
export async function restorePurchases(): Promise<boolean> {
  if (!purchasesSupported()) throw new PurchasesUnavailableError();
  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const info: any = await Purchases.restorePurchases();
    const active = info?.entitlements?.active ?? {};
    return Object.keys(active).length > 0;
  } catch {
    return false;
  }
}
