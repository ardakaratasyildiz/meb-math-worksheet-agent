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
/** Zaman-tabanlı ilerleme (gerçek streaming yok) — kullanıcı ilerlediğini görsün. */
const PROGRESS_MS = 75_000;
const TICK_MS = 500;

const PHASES = [
  'Kazanımlar seçiliyor…',
  'Sorular yazılıyor…',
  'Çözümler hazırlanıyor…',
  'Son kontroller…',
];

export function GeneratingState({
  subject,
  questionCount,
  sober = false,
}: {
  subject: string;
  questionCount: number;
  /** Yetişkin tonu: maskot gösterilmez. */
  sober?: boolean;
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

  // %95'te durur — iş bitmeden "tamamlandı" göstermek güveni bozar.
  const progress = Math.min(0.95, elapsed / PROGRESS_MS);
  const phase = PHASES[Math.min(PHASES.length - 1, Math.floor(progress * PHASES.length))];

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
      <Text style={styles.hint}>Bu işlem 30-90 saniye sürebilir, ekranda kalman yeterli.</Text>

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
