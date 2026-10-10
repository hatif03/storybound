// Sound, kept tiny. Nothing plays until the child or grown-up has tapped something (browsers insist, and so do we).
// One shared <audio> element speaks (Pip's lines and page narration, so they never talk over each other); it is "unlocked"
// by the first tap (Welcome's big button), which is what lets later pages read themselves aloud on iOS too.
import { getSettings } from '../state/settings';

const SILENT = '/assets/audio/sfx/silent-100ms.mp3';
const speech = typeof Audio === 'undefined' ? null : new Audio();
const music = typeof Audio === 'undefined' ? null : new Audio('/assets/audio/music/happy-lullaby.mp3');
if (music) { music.loop = true; music.volume = 0.1; music.preload = 'none'; }
let unlocked = false;
let onEnd: (() => void) | null = null;
const listeners = new Set<(url: string | null) => void>();
let playingUrl: string | null = null;

function setPlaying(url: string | null) { playingUrl = url; listeners.forEach((l) => l(url)); }

if (speech) {
  speech.addEventListener('ended', () => { const cb = onEnd; onEnd = null; setPlaying(null); duck(false); cb?.(); });
  speech.addEventListener('error', () => { onEnd = null; setPlaying(null); duck(false); });
}

function duck(on: boolean) { if (music) music.volume = on ? 0.03 : 0.1; }

/** Call inside a tap. Safe to call again. */
export function unlock(): void {
  if (unlocked || !speech) return;
  unlocked = true;
  speech.src = SILENT;
  speech.play().catch(() => { unlocked = false; });
}

export function sfx(name: 'tap' | 'select' | 'page-turn' | 'happy-chime' | 'soft-boop' | 'star-pop' | 'refusal'): void {
  if (!getSettings().sound || typeof Audio === 'undefined') return;
  const a = new Audio(`/assets/audio/sfx/${name}.mp3`);
  a.volume = 0.55;
  a.play().catch(() => {});
}

/** Pip's recorded lines, e.g. say('welcome'). Only when sound is on. */
export function say(id: string): void {
  if (!getSettings().sound) return;
  play(`/assets/audio/voice/${id}.mp3`);
}

/** Play a narration file (a tap on the speaker button works even when sound is off). Resolves when it ends or fails. */
export function play(url: string, done?: () => void): void {
  if (!speech) return;
  speech.pause();
  onEnd = done ?? null;
  speech.src = url;
  setPlaying(url);
  duck(true);
  speech.play().catch(() => { onEnd = null; setPlaying(null); duck(false); });
}

export function stop(): void {
  if (!speech) return;
  speech.pause();
  onEnd = null;
  setPlaying(null);
  duck(false);
}

export function nowPlaying(): string | null { return playingUrl; }
export function subscribePlaying(cb: (url: string | null) => void): () => void { listeners.add(cb); return () => listeners.delete(cb); }

export function setMusic(on: boolean): void {
  if (!music) return;
  if (on) music.play().catch(() => {});
  else music.pause();
}
