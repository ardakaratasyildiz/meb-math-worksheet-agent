/**
 * Frontend tarafı geçmiş kaydı — localStorage'a son N üretim saklanır.
 * MVP: tarayıcı başına yerel; cihazlar arası senkron için Sprint 7.5'te
 * backend "user_history" endpoint'i eklenebilir.
 */
import type { GenerateWorksheetResponse } from "./types";

const KEY = "meb-history";
const MAX_ITEMS = 30;

export interface HistoryItem {
  id: string; // timestamp_ms-random
  saved_at: string; // ISO
  request: {
    grade: number;
    topic_id: string;
    kazanim_kod: string | null;
    difficulty: string;
    question_count: number;
  };
  response: GenerateWorksheetResponse;
}

function safeRead(): HistoryItem[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function safeWrite(items: HistoryItem[]): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(KEY, JSON.stringify(items));
  } catch {
    // QuotaExceededError → en eskileri silip tekrar dene
    try {
      window.localStorage.setItem(KEY, JSON.stringify(items.slice(0, 10)));
    } catch {
      // bırak
    }
  }
}

export function listHistory(): HistoryItem[] {
  return safeRead().sort((a, b) => b.saved_at.localeCompare(a.saved_at));
}

export function addHistory(
  request: HistoryItem["request"],
  response: GenerateWorksheetResponse,
): HistoryItem {
  const item: HistoryItem = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    saved_at: new Date().toISOString(),
    request,
    response,
  };
  const next = [item, ...safeRead()].slice(0, MAX_ITEMS);
  safeWrite(next);
  return item;
}

export function removeHistory(id: string): void {
  safeWrite(safeRead().filter((i) => i.id !== id));
}

export function clearHistory(): void {
  safeWrite([]);
}
