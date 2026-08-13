import { Stack } from 'expo-router';
import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ClassroomsView } from '@/components/classrooms-view';
import { colors, fonts } from '@/theme/tokens';

/**
 * Sınıflarım — itilen ekran (ana ekrandaki "Sınıflarım" kartından açılır).
 * Gövde `components/classrooms-view` içinde; öğretmen rolünde üçüncü sekme de
 * aynı gövdeyi kullanıyor (tek kaynak).
 */
const headerOpts = {
  headerShown: true,
  title: 'Sınıflarım',
  headerStyle: { backgroundColor: colors.bg },
  headerShadowVisible: false,
  headerTintColor: colors.brand,
  headerTitleStyle: { fontFamily: fonts.headingSemi, color: colors.text },
} as const;

export default function ClassroomsScreen() {
  return (
    <View style={styles.root}>
      <Stack.Screen options={headerOpts} />
      <SafeAreaView style={styles.safe} edges={['bottom']}>
        <ClassroomsView />
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  safe: { flex: 1 },
});
