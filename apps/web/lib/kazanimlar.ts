/**
 * Kazanım-seviyesi landing page verisi (programatik SEO).
 *
 * Kaynak: scripts/export_seo_data.py (backend müfredatından OTOMATİK üretir).
 * Her kazanım benzersiz içerik (resmi metin + zorluk ipuçları) taşır → thin/
 * doorway içerik değil. 1-8. sınıf = 166 long-tail landing.
 */
import data from "./kazanimlar.json";

export interface KazanimPage {
  topicSlug: string;
  grade: number;
  topicId: string;
  topicName: string;
  kazanimSlug: string;
  kod: string;
  metin: string;
  hints: { kolay?: string; orta?: string; zor?: string };
}

export const KAZANIM_PAGES = data as unknown as KazanimPage[];

export function getKazanim(
  topicSlug: string,
  kazanimSlug: string,
): KazanimPage | undefined {
  return KAZANIM_PAGES.find(
    (k) => k.topicSlug === topicSlug && k.kazanimSlug === kazanimSlug,
  );
}

export function getKazanimlarByTopic(topicSlug: string): KazanimPage[] {
  return KAZANIM_PAGES.filter((k) => k.topicSlug === topicSlug);
}
