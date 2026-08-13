import { Stack } from 'expo-router';
import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ChildrenView } from '@/components/children-view';
import { colors, fonts } from '@/theme/tokens';

/**
 * Çocuklarım — itilen ekran (ana ekrandaki "Çocuklarım" kartından açılır).
 * Gövde `components/children-view` içinde; veli rolünde üçüncü sekme de aynı
 * gövdeyi kullanıyor (tek kaynak).
 */
const headerOpts = {
  headerShown: true,
  title: 'Çocuklarım',
  headerStyle: { backgroundColor: colors.bg },
  headerShadowVisible: false,
  headerTintColor: colors.brand,
  headerTitleStyle: { fontFamily: fonts.headingSemi, color: colors.text },
} as const;

export default function ChildrenScreen() {
  return (
    <View style={styles.root}>
      <Stack.Screen options={headerOpts} />
      <SafeAreaView style={styles.safe} edges={['bottom']}>
        <ChildrenView />
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  safe: { flex: 1 },
});
