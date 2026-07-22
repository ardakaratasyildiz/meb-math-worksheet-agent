import { rollupByTopic } from "./curriculum";
import type { KazanimProgress, TopicBadge } from "./types";

// Konu-bazlı rozetler — mastery'den türetilir (backend kazanım→konu haritası
// kurmaktan kaçınmak için frontend'de). Konu başına en yüksek kademe.
//   Bronz: ≥5 soru & ≥%60   Gümüş: ≥10 & ≥%75   Altın: ≥15 & ≥%90
export function computeBadges(mastery: KazanimProgress[]): TopicBadge[] {
  const badges: TopicBadge[] = [];
  for (const t of rollupByTopic(mastery)) {
    let tier: TopicBadge["tier"] | null = null;
    if (t.total >= 15 && t.ratio >= 0.9) tier = "gold";
    else if (t.total >= 10 && t.ratio >= 0.75) tier = "silver";
    else if (t.total >= 5 && t.ratio >= 0.6) tier = "bronze";
    if (tier) {
      badges.push({
        topicId: t.topicId,
        topicName: t.topicName,
        tier,
        ratio: t.ratio,
        total: t.total,
      });
    }
  }
  return badges;
}
