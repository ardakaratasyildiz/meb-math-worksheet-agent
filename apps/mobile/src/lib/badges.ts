/**
 * Konu-bazlı rozetler — web frontend/lib/badges.ts port'u.
 * Web müfredat lookup'ı yerine backend'in verdiği `topic_name` alanını kullanır
 * (KazanimProgress'te hazır) → müfredat verisini mobile taşımaya gerek yok.
 * Konu başına en yüksek kademe:
 *   Bronz: ≥5 soru & ≥%60 · Gümüş: ≥10 & ≥%75 · Altın: ≥15 & ≥%90
 */
import type { KazanimProgress } from '@soruatolyesi/shared';

import type { BadgeGlyph } from '@/components/icons';

export type BadgeTier = 'bronze' | 'silver' | 'gold';

export interface TopicBadge {
  topicName: string;
  tier: BadgeTier;
  ratio: number;
  total: number;
}

/** HexBadge renk varyantı (icons.tsx BADGE_COLORS anahtarları). */
export function badgeVariant(tier: BadgeTier): 'bronze' | 'teal' | 'ember' {
  return tier === 'gold' ? 'ember' : tier === 'silver' ? 'teal' : 'bronze';
}

/** Kademeye göre glyph. */
export function badgeGlyph(tier: BadgeTier): BadgeGlyph {
  return tier === 'gold' ? 'trophy' : tier === 'silver' ? 'star' : 'target';
}

export function tierLabel(tier: BadgeTier): string {
  return tier === 'gold' ? 'Altın' : tier === 'silver' ? 'Gümüş' : 'Bronz';
}

export function computeBadges(mastery: KazanimProgress[]): TopicBadge[] {
  const map = new Map<string, { correct: number; total: number }>();
  for (const k of mastery) {
    const name = k.topic_name || k.kazanim_kod;
    const cur = map.get(name) ?? { correct: 0, total: 0 };
    cur.correct += k.correct;
    cur.total += k.total;
    map.set(name, cur);
  }
  const badges: TopicBadge[] = [];
  for (const [topicName, t] of map) {
    const ratio = t.total > 0 ? t.correct / t.total : 0;
    let tier: BadgeTier | null = null;
    if (t.total >= 15 && ratio >= 0.9) tier = 'gold';
    else if (t.total >= 10 && ratio >= 0.75) tier = 'silver';
    else if (t.total >= 5 && ratio >= 0.6) tier = 'bronze';
    if (tier) badges.push({ topicName, tier, ratio, total: t.total });
  }
  // Altın → gümüş → bronz sırala (en iyi önce).
  const order: Record<BadgeTier, number> = { gold: 0, silver: 1, bronze: 2 };
  return badges.sort((a, b) => order[a.tier] - order[b.tier]);
}
