/**
 * MEB TYMM ünite (tema) snapshot'ı — yeni seçim akışının veri kaynağı.
 *
 * Kaynak: `scripts/build_units.py` (tymm.meb.gov.tr scrape + legacy topic köprüsü).
 * Backend `app/data/units.json` ile aynı veriden üretilir; build-time backend
 * bağımlılığı olmasın diye JSON snapshot'tan okunur (curriculum.ts deseniyle aynı).
 *
 * Müfredat değişince (yeni scrape) TEK komut:
 *   PYTHONIOENCODING=utf-8 python scripts/build_units.py
 */
import data from "./units.json";
import type { KazanimInfo, UnitInfo } from "./types";

export interface UnitKazanim {
  kod: string;
  metin: string;
  legacy_topic_id: string;
}

export interface UnitPage {
  unit_id: string;
  unite_id: number;
  grade: number;
  no: number;
  name: string;
  legacy_topic_id: string;
  kazanimlar: UnitKazanim[];
}

export const UNIT_PAGES = data as unknown as UnitPage[];

// ── Form dropdown verisi (lokal, anında — cold-start'a bağımlı değil) ────────

export function getUnitsLocal(grade: number): UnitInfo[] {
  return UNIT_PAGES.filter((u) => u.grade === grade)
    .sort((a, b) => a.no - b.no)
    .map((u) => ({
      unit_id: u.unit_id,
      name: u.name,
      no: u.no,
      kazanim_count: u.kazanimlar.length,
    }));
}

export function getKazanimlarByUnitLocal(
  grade: number,
  unitId: string,
): KazanimInfo[] {
  const u = UNIT_PAGES.find(
    (x) => x.grade === grade && x.unit_id === unitId,
  );
  if (!u) return [];
  return u.kazanimlar.map((k) => ({ kod: k.kod, metin: k.metin }));
}

// Kazanım kodundan (MAT.*) sınıf/ünite/metin çözer — ilerleme panosu & rollup
// yeni kodları da tanısın diye (mastery_state yalnız kod tutar).
export function findUnitKazanimByKod(
  kod: string,
): { grade: number; unitId: string; unitName: string; metin: string } | undefined {
  for (const u of UNIT_PAGES) {
    for (const k of u.kazanimlar) {
      if (k.kod === kod) {
        return { grade: u.grade, unitId: u.unit_id, unitName: u.name, metin: k.metin };
      }
    }
  }
  return undefined;
}
