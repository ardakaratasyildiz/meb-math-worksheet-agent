/**
 * MEB kaynak künyesi + "resmi kurum değiliz" uyarısı.
 *
 * Google Play "Misleading Claims" politikası, devlet kaynaklı bilgi gösteren
 * uygulamalardan iki şey istiyor: (1) bilginin resmi kaynağına açık ve çalışan
 * bağlantı, (2) kurumu temsil etmediğine dair kolay görülen bir uyarı.
 * 18 Ağustos 2026'daki Play reddinin gerekçesi tam olarak buydu
 * (bkz. docs/PLAY_POLICY_FIX.md) — aynı metinler mağaza açıklamasında da geçer.
 */

/** Tek satırlık uyarı (ekran altı, profil dipnotu). */
export const MEB_DISCLAIMER_SHORT =
  'Soru Atölyesi bağımsız bir eğitim uygulamasıdır. T.C. Milli Eğitim Bakanlığı (MEB) ile ' +
  'bağlantılı, ortaklı veya MEB tarafından onaylı değildir; MEB’i temsil etmez.';

/** Uzun sürüm — Hakkında ekranı ve mağaza açıklaması için. */
export const MEB_DISCLAIMER_LONG =
  'Soru Atölyesi bağımsız bir eğitim uygulamasıdır. T.C. Milli Eğitim Bakanlığı (MEB), ' +
  'Talim ve Terbiye Kurulu Başkanlığı ya da başka bir resmi kurumla bağlantılı, ortaklı veya ' +
  'bu kurumlarca onaylı değildir; hiçbirini temsil etmez ve resmi bir hizmet sunmaz.\n\n' +
  'Uygulamadaki ünite, konu ve kazanım başlıkları MEB’in kamuya açık öğretim programlarına ' +
  'dayanır; sorular ve çözümler yapay zeka ile üretilir, MEB’in resmi yayını veya sınav ' +
  'materyali değildir. Güncel ve bağlayıcı bilgi için aşağıdaki resmi kaynaklara başvurun.';

export type SourceLink = {
  label: string;
  url: string;
  /** Bağlantının ne içerdiği — kullanıcı hangi bilginin kaynağı olduğunu görsün. */
  note: string;
};

/** Uygulamada gösterilen müfredat bilgisinin resmi kaynakları (.gov.tr). */
export const MEB_SOURCES: SourceLink[] = [
  {
    label: 'meb.gov.tr',
    url: 'https://www.meb.gov.tr',
    note: 'T.C. Milli Eğitim Bakanlığı resmi sitesi',
  },
  {
    label: 'tymm.meb.gov.tr',
    url: 'https://tymm.meb.gov.tr',
    note: 'Türkiye Yüzyılı Maarif Modeli — güncel öğretim programları ve ders materyalleri',
  },
  {
    label: 'mufredat.meb.gov.tr',
    url: 'https://mufredat.meb.gov.tr',
    note: 'Talim ve Terbiye Kurulu Başkanlığı — öğretim programları ve kazanım listeleri',
  },
];
