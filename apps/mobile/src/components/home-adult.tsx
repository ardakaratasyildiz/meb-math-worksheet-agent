import { useRouter, type Href } from 'expo-router';
import { type ReactNode } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { IconChart, IconChevron, IconUser, IconWorksheet } from '@/components/icons';
import { colors, fonts, fontSize, radius, shadow, spacing } from '@/theme/tokens';

/**
 * Öğretmen/veli ana ekranı — "yetişkin/sade" ton. Öğrenci ekranının aksine
 * maskot/XP/seri/rozet/kutlama YOK; başlıklar Nunito ExtraBold (Fredoka değil),
 * tek dingin vurgu (öğretmen mavi, veli teal), özet-önce düzen.
 *
 * Öğretmen: birincil "Çalışma Kağıdı Oluştur" + Sınıflarım/Gelişim.
 * Veli: birincil "Çocuğum" (bağla + ilerleme izle) + Oluştur/Gelişim.
 */
export function AdultHome({ role, name }: { role: 'teacher' | 'parent'; name: string }) {
  const router = useRouter();
  const go = (path: string) => () => router.push(path as Href);
  const teacher = role === 'teacher';
  const accent = teacher ? colors.brand : colors.parent;

  return (
    <View style={styles.root}>
      <SafeAreaView edges={['top']} style={styles.safe}>
        <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
          <View>
            <Text style={styles.hello}>Merhaba, {name}</Text>
            <Text style={styles.sub}>
              {teacher ? 'Bugün ne hazırlayalım?' : 'Çocuğunun gelişimini buradan takip et'}
            </Text>
          </View>

          {teacher ? (
            <PrimaryAction
              accent={accent}
              icon={<IconWorksheet size={28} tone="#FFFFFF" />}
              title="Çalışma Kağıdı Oluştur"
              sub="Sınıfın için PDF hazırla"
              onPress={go('/create')}
            />
          ) : (
            <PrimaryAction
              accent={accent}
              icon={<IconUser size={26} color="#FFFFFF" />}
              title="Çocuğum"
              sub="Takip koduyla ekle, gelişimini izle"
              onPress={go('/children')}
            />
          )}

          <View style={styles.twoCol}>
            {teacher ? (
              <MiniCard
                icon={<IconUser size={26} color={colors.brand} />}
                title="Sınıflarım"
                sub="Sınıf & ödev"
                onPress={go('/classrooms')}
              />
            ) : (
              <MiniCard
                icon={<IconWorksheet size={26} tone={colors.parent} />}
                title="Çalışma Kağıdı"
                sub="PDF üret"
                onPress={go('/create')}
              />
            )}
            <MiniCard
              icon={<IconChart size={28} />}
              title="Gelişim"
              sub={teacher ? 'Kendi denemelerin' : 'Özet'}
              onPress={go('/progress')}
            />
          </View>

          {/* Dürüst ipucu kartı */}
          <View style={styles.infoCard}>
            <Text style={styles.infoTitle}>{teacher ? 'İpucu' : 'Nasıl çalışır?'}</Text>
            <Text style={styles.infoText}>
              {teacher
                ? 'Sınıf oluştur, öğrencilerine katılma kodunu ver, ürettiğin quizleri ödev olarak ata ve sonuçları tek ekranda izle.'
                : 'Çocuğun uygulamada Profil ekranındaki takip kodunu sana versin; “Çocuğum”dan ekleyince gelişimini burada görürsün.'}
            </Text>
          </View>
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

function PrimaryAction({
  accent,
  icon,
  title,
  sub,
  onPress,
}: {
  accent: string;
  icon: ReactNode;
  title: string;
  sub: string;
  onPress: () => void;
}) {
  return (
    <Pressable onPress={onPress} style={({ pressed }) => [pressed && styles.pressed]}>
      <View style={[styles.primary, { backgroundColor: accent }, shadow.card]}>
        <View style={styles.primaryIcon}>{icon}</View>
        <View style={styles.primaryBody}>
          <Text style={styles.primaryTitle}>{title}</Text>
          <Text style={styles.primarySub}>{sub}</Text>
        </View>
        <IconChevron size={20} color="#FFFFFF" />
      </View>
    </Pressable>
  );
}

function MiniCard({
  icon,
  title,
  sub,
  onPress,
}: {
  icon: ReactNode;
  title: string;
  sub: string;
  onPress: () => void;
}) {
  return (
    <Pressable onPress={onPress} style={({ pressed }) => [styles.mini, pressed && styles.pressed]}>
      <View style={styles.miniIcon}>{icon}</View>
      <Text style={styles.miniTitle}>{title}</Text>
      <Text style={styles.miniSub}>{sub}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  safe: { flex: 1 },
  content: { padding: spacing.xl, gap: spacing.lg, paddingBottom: 120 },

  hello: { fontFamily: fonts.bodyHeavy, fontSize: fontSize.xxl, color: colors.text },
  sub: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.textMuted, marginTop: spacing.xs },

  pressed: { transform: [{ scale: 0.99 }], opacity: 0.92 },

  primary: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, borderRadius: radius.card, padding: spacing.lg },
  primaryIcon: {
    width: 52,
    height: 52,
    borderRadius: radius.md,
    backgroundColor: 'rgba(255,255,255,0.18)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryBody: { flex: 1 },
  primaryTitle: { fontFamily: fonts.bodyHeavy, fontSize: fontSize.md, color: '#FFFFFF' },
  primarySub: { fontFamily: fonts.body, fontSize: fontSize.xs, color: '#FFFFFF', opacity: 0.92, marginTop: 1 },

  twoCol: { flexDirection: 'row', gap: spacing.md },
  mini: {
    flex: 1,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.card,
    padding: spacing.lg,
    gap: 4,
  },
  miniIcon: { marginBottom: spacing.xs },
  miniTitle: { fontFamily: fonts.bodyBold, fontSize: fontSize.md, color: colors.text },
  miniSub: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textMuted },

  infoCard: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.card,
    padding: spacing.lg,
    gap: spacing.xs,
  },
  infoTitle: { fontFamily: fonts.bodyHeavy, fontSize: fontSize.sm, color: colors.text },
  infoText: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.textMuted, lineHeight: 20 },
});
