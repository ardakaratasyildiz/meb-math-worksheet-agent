/*
 * SATICI (şirket) bilgileri — TEK KAYNAK.
 *
 * ⚠️ TASLAK: Aşağıdaki alanlar şahıs şirketi kurulduktan sonra doldurulacaktır.
 * Şirket bilgisi tüm yasal sayfalarda (mesafeli satış, ön bilgilendirme, iptal/iade,
 * künye) buradan okunur → tek yeri güncellemek yeterlidir.
 *
 * Kuruluş sonrası doldur: ticari unvan, T.C./VKN, vergi dairesi, adres, telefon.
 * Bir hukuk danışmanının metinleri gözden geçirmesi önerilir.
 */

export const SELLER = {
  /** Ticari unvan (şahıs şirketinde genelde: "Ad Soyad" veya "Ad Soyad - İşletme adı") */
  unvan: "[TİCARİ UNVAN — kuruluş sonrası]",
  /** Markanın kullanıcıya görünen adı */
  markaAdi: "Soru Atölyesi",
  /** Vergi kimlik / T.C. kimlik no */
  vergiNo: "[VKN / T.C. KİMLİK NO]",
  /** Bağlı olunan vergi dairesi */
  vergiDairesi: "[VERGİ DAİRESİ]",
  /** Açık adres */
  adres: "[AÇIK ADRES — kuruluş sonrası]",
  /** İletişim */
  eposta: "destek@soruatolyesi.com",
  telefon: "[TELEFON]",
  /** Web sitesi */
  web: "https://soruatolyesi.com",
  /** Ödeme altyapısı sağlayıcısı */
  odemeKurulusu: "iyzico (İyzi Ödeme ve Elektronik Para Hizmetleri A.Ş.)",
} as const;

/** Sözleşme metinlerinde tekrar eden satıcı kimlik bloğu (bullet listesi). */
export const SELLER_BULLETS: string[] = [
  `Satıcı / Hizmet Sağlayıcı: ${SELLER.unvan} (“${SELLER.markaAdi}”)`,
  `Vergi Dairesi / No: ${SELLER.vergiDairesi} / ${SELLER.vergiNo}`,
  `Adres: ${SELLER.adres}`,
  `E-posta: ${SELLER.eposta}`,
  `Telefon: ${SELLER.telefon}`,
  `Web: ${SELLER.web}`,
];
