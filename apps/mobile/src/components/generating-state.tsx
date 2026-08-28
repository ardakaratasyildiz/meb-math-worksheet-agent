import { useEffect, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { IconSpark } from '@/components/icons';
import { Card, ProgressBar } from '@/components/ui';
import { Mascot } from '@/components/mascot';
import { factsForSubject } from '@/lib/facts';
import { colors, fonts, fontSize, radius, spacing } from '@/theme/tokens';

/**
 * Üretim beklerken (30-90 sn) gösterilen ekran — web'deki "Bunu biliyor muydun?"
 * bekleme ekranının mobil karşılığı (frontend/components/SolveForm.tsx).
 *
 * Neden: boş bir iskelet 60 saniye boyunca "takıldı mı?" hissi veriyordu. Ders
 * bilgisi hem bekleyişi kısaltıyor hem ürünün eğitim kimliğini pekiştiriyor.
 * Bilgi 7 sn'de bir döner, başlangıç rastgele → her üretimde farklı içerik.
 */

const FACT_MS = 7000;
const TICK_MS = 500;
/**
 * Üretim bitmeden önceki bölüm için zaman-tabanlı TAHMİN tavanı. Bu aralıkta
 * sunucudan gerçek ilerleme sinyali gelmez (üretim blocking, yalnız keepalive
 * akar), o yüzden çubuk buranın ötesine GEÇMEZ — kalan %40 gerçek sorular
 * geldikçe dolar. Eskiden çubuk 75 sn'ye lineer yayılıyordu; üretim 25 sn'de
 * bittiğinde çubuk %30'dayken ekran birden sonuca atlıyordu ("orantısız" şikayeti).
 */
const ESTIMATE_CEILING = 0.6;
/** Tahmin eğrisinin zaman sabiti — 35 sn'de tavanın ~%63'üne gelir, hiç durmaz. */
const ESTIMATE_TAU_MS = 35_000;

export function GeneratingState({
  subject,
  questionCount,
  sober = false,
  connected = false,
  produced = 0,
}: {
  subject: string;
  questionCount: number;
  /** Yetişkin tonu: maskot gösterilmez. */
  sober?: boolean;
  /** Sunucu isteği kabul etti (SSE `meta` event'i geldi). */
  connected?: boolean;
  /** Akıştan gelen soru sayısı — çubuğun GERÇEK ilerleme kısmını besler. */
  produced?: number;
}) {
  const facts = factsForSubject(subject);
  const [factIdx, setFactIdx] = useState(() => Math.floor(Math.random() * facts.length));
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setFactIdx((i) => (i + 1) % facts.length), FACT_MS);
    return () => clearInterval(t);
  }, [facts.length]);

  useEffect(() => {
    const t = setInterval(() => setElapsed((e) => e + TICK_MS), TICK_MS);
    return () => clearInterval(t);
  }, []);

  // İki bölümlü ilerleme: (1) sorular gelmeden önce zaman-tabanlı TAHMİN, tavanı
  // aşamaz; (2) sorular geldikçe GERÇEK oran. Böylece çubuk hiçbir zaman işin
  // önüne geçmez, üretim erken biterse de anında dolar.
  const estimate = ESTIMATE_CEILING * (1 - Math.exp(-elapsed / ESTIMATE_TAU_MS));
  const real = questionCount > 0 ? Math.min(1, produced / questionCount) : 0;
  const progress = produced > 0 ? Math.min(0.99, ESTIMATE_CEILING + (1 - ESTIMATE_CEILING) * real) : estimate;

  const phase =
    produced > 0
      ? `Sorular geliyor (${Math.min(produced, questionCount)}/${questionCount})`
      : connected
        ? 'Sorular yazılıyor…'
        : 'Sunucuya bağlanılıyor…';

  return (
    <View style={styles.wrap}>
      <View style={styles.head}>
        {sober ? null : <Mascot variant="thinking" size={72} />}
        <View style={styles.headText}>
          <Text style={styles.title}>{questionCount} soru hazırlanıyor</Text>
          <Text style={styles.phase}>{phase}</Text>
        </View>
      </View>

      <ProgressBar progress={progress} color={colors.brand} />
      <Text style={styles.hint}>
        Bu işlem 30-90 saniye sürebilir. Uygulamadan çıkmazsan en hızlısı bu; çıkman
        gerekirse üretim sunucuda sürer, geri döndüğünde kağıdını getiririz.
      </Text>

      <Card style={styles.factCard}>
        <View style={styles.factHead}>
          <IconSpark size={16} />
          <Text style={styles.factKicker}>Bunu biliyor muydun?</Text>
        </View>
        <Text style={styles.factText}>{facts[factIdx]}</Text>
      </Card>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: spacing.md },
  head: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  headText: { flex: 1, gap: 2 },
  title: { fontFamily: fonts.heading, fontSize: fontSize.lg, color: colors.text },
  phase: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.textMuted },
  hint: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textFaint, textAlign: 'center' },

  factCard: { gap: spacing.sm, backgroundColor: colors.tintBlue, borderRadius: radius.card },
  factHead: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  factKicker: {
    fontFamily: fonts.bodyBold,
    fontSize: fontSize.xs,
    color: colors.brandDark,
    letterSpacing: 0.5,
  },
  factText: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.text, lineHeight: 21 },
});
