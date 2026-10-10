import type { Degradation, Receipt } from '../api/types';

export function duration(seconds: number): string {
  const s = Math.round(seconds);
  if (s < 60) return `${s} s`;
  return `${Math.floor(s / 60)} min ${String(s % 60).padStart(2, '0')} s`;
}

/** The backend sends `usd_estimate` (API.md says `usd`): accept both. Always labelled an estimate. */
export function cost(b: Receipt['budget']): string {
  const v = b.usd_estimate ?? b.usd;
  if (v === undefined) return 'not reported';
  return `about $${v < 0.1 ? v.toFixed(3) : v.toFixed(2)} (estimate)`;
}

const WHAT: Record<string, string> = {
  image: 'a picture could not be made', audio: 'the narration could not be made', judge: 'quality judging was turned off for part of the run',
  check: 'a check could not run',
};

/** One plain sentence per degradation, for the parent. */
export function degradeLine(d: Degradation): string {
  const where = d.index ? `Page ${d.index}` : 'The story';
  const what = WHAT[d.what] ?? `${d.what} was reduced`;
  return `${where}: ${what} (${d.why}). Fallback: ${d.fallback}.`;
}

const FIELD: Record<string, string> = {
  drawing: 'the drawing', character_card: 'the hero card', scenario: 'the page text', question: 'the questions', choices: 'the choices',
  image_prompt: 'the picture request', image: 'the pictures', audio: 'the narration', safety_screen: 'the safety screen',
  illustrate: 'picture making', narrate: 'narration making',
};
export const fieldName = (f: string): string => FIELD[f] ?? f.replace(/_/g, ' ');

export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    try {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.setAttribute('readonly', '');
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.append(ta);
      ta.select();
      const ok = document.execCommand('copy');
      ta.remove();
      return ok;
    } catch {
      return false;
    }
  }
}
