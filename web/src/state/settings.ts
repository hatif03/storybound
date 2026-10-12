// Grown-up settings. Kept in sessionStorage only (nothing persists beyond the tab, by design); every access is try/caught
// because storage can be blocked. Sound is ON by default (stories read themselves) but nothing plays before the first tap.
import { useSyncExternalStore } from 'react';

export interface Settings {
  sound: boolean; // tap sounds, Pip's voice, and reading each page aloud on arrival
  music: boolean; // quiet background loop
  textSize: 's' | 'm' | 'l';
  calm: boolean; // reduce motion (also follows the device setting)
  age: number; // the reader's age, 4 to 8, sent with the next story
  pictures: 'auto' | 'full' | 'half' | 'none'; // Pip chooses the pages that matter most (auto), every page, half the pages, or none: sent with the next story
}

const KEY = 'storybound.settings';
const defaults: Settings = { sound: true, music: false, textSize: 'm', calm: false, age: 6, pictures: 'auto' };
let current: Settings = load();
const listeners = new Set<() => void>();

function load(): Settings {
  try {
    const raw = sessionStorage.getItem(KEY);
    if (raw) return { ...defaults, ...JSON.parse(raw) };
  } catch { /* storage blocked: use defaults */ }
  return { ...defaults };
}

export function getSettings(): Settings { return current; }

export function setSettings(patch: Partial<Settings>): void {
  current = { ...current, ...patch };
  try { sessionStorage.setItem(KEY, JSON.stringify(current)); } catch { /* ignore */ }
  applyToDocument();
  listeners.forEach((l) => l());
}

export function applyToDocument(): void {
  const el = document.documentElement;
  el.dataset.text = current.textSize;
  el.dataset.calm = current.calm || window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'true' : 'false';
}

export function useSettings(): Settings {
  return useSyncExternalStore((cb) => { listeners.add(cb); return () => listeners.delete(cb); }, getSettings);
}

export function prefersCalm(): boolean {
  return current.calm || window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}
