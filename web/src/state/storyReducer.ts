// One small pure reducer: folds the backend's event stream (docs/API.md "Events") into UI state.
// No I/O, no timers. Replayed events (reconnect with Last-Event-ID, or a late join) are ignored by `id`.
import type { CharacterCard, Commitment, Degradation, Page, Quiz, Receipt, SafetyAction, StoryEvent, VerdictStatus } from '../api/types';

export type Step =
  | 'start' | 'looking' | 'meeting' | 'promise' | 'planning' | 'writing' | 'checking' | 'fixing' | 'painting' | 'voice' | 'wrapping' | 'done';

export type PromiseKind = 'waiting' | 'checking' | 'fixing' | 'kept' | 'kept_after_fix' | 'not_kept' | 'unchecked';

export interface PromiseState extends Commitment {
  state: PromiseKind;
  done: number; // how many of `expected` places have a passing latest verdict
  expected: number;
  everBad: boolean; // a check failed at some point (so "kept" means "kept after a fix")
}

export interface MediaState { image?: string; audio?: string; seconds?: number; imageMissing?: boolean; audioMissing?: boolean }
export interface RepairNote { index: number; attempt: number; failed: string[]; because: string }

export type Net = 'ok' | 'reconnecting' | 'lost';

export interface StoryState {
  phase: 'idle' | 'running' | 'finished' | 'refused' | 'error';
  net: Net;
  lastId: number; // highest event id folded so far (-1 = none)
  storyId?: string; lessonId?: string; arm?: string;
  safety?: { tier: string; action: SafetyAction; ignoredText: string[]; reasonCode: string };
  card?: CharacterCard;
  oathHash?: string;
  promises: PromiseState[];
  beats: string[];
  totalPages: number;
  step: { kind: Step; index?: number };
  pages: Page[]; // accepted pages, in order
  final: boolean; // the whole-story check is done: no page will change any more
  attempts: Record<number, number>; // page index -> attempts used (0 = first try)
  media: Record<number, MediaState>;
  repairs: RepairNote[];
  degradations: Degradation[];
  verdicts: Record<string, Record<string, { status: VerdictStatus; attempt: number }>>; // commitment -> scope -> latest
  everBad: Record<string, boolean>; // commitment -> a check failed at some point (run-level checks come before the oath)
  receipt?: Receipt;
  quiz?: Quiz; // only questions that passed every quiz promise
  outcome?: 'shipped' | 'shipped_with_notes';
  refusal?: { reasonCode: string; message: string; traceId: string };
  error?: { code: string; message: string };
  eventCount: number;
}

export const DEFAULT_PAGES = 8;

export const initialStory: StoryState = {
  phase: 'idle', net: 'ok', lastId: -1, promises: [], beats: [], totalPages: DEFAULT_PAGES, step: { kind: 'start' },
  pages: [], final: false, attempts: {}, media: {}, repairs: [], degradations: [], verdicts: {}, everBad: {}, eventCount: 0,
};

export type StoryAction = { type: 'reset' } | { type: 'event'; ev: StoryEvent } | { type: 'net'; net: Net };

const BAD: VerdictStatus[] = ['violation', 'critical'];
const OK: VerdictStatus[] = ['pass', 'warning', 'skipped'];

function expectedPlaces(scope: Commitment['scope'], totalPages: number): number {
  return scope === 'run' || scope === 'story' ? 1 : totalPages;
}

/** Work out one promise's state from the latest verdict per place. Pure; used after every verdict. */
function refreshPromise(p: PromiseState, places: Record<string, { status: VerdictStatus }> | undefined, totalPages: number): PromiseState {
  if (p.state === 'not_kept' || p.state === 'unchecked') return p;
  const entries = Object.values(places ?? {});
  const expected = expectedPlaces(p.scope, totalPages);
  const done = entries.filter((e) => OK.includes(e.status)).length;
  const anyPass = entries.some((e) => e.status === 'pass' || e.status === 'warning');
  let state: PromiseKind = 'waiting';
  if (entries.some((e) => BAD.includes(e.status))) state = 'fixing';
  else if (done >= expected && anyPass) state = p.everBad ? 'kept_after_fix' : 'kept';
  else if (entries.length) state = 'checking';
  return { ...p, state, done, expected };
}

function finalise(state: StoryState, receipt: Receipt): PromiseState[] {
  const broken = new Set(receipt.broken ?? []);
  return state.promises.map((p) => {
    const places = Object.values(state.verdicts[p.id] ?? {});
    if (broken.has(p.id)) return { ...p, state: 'not_kept' as const };
    if (!places.some((e) => e.status !== 'skipped')) return { ...p, state: 'unchecked' as const };
    return { ...p, state: p.everBad ? ('kept_after_fix' as const) : ('kept' as const) };
  });
}

/** Where is the run now? Recomputed whenever media events change what is outstanding. */
function mediaStep(s: StoryState): Step {
  const n = s.totalPages;
  const imagesLeft = Array.from({ length: n }, (_, i) => i + 1).some((i) => !s.media[i]?.image && !s.media[i]?.imageMissing);
  if (imagesLeft) return 'painting';
  const audioLeft = Array.from({ length: n }, (_, i) => i + 1).some((i) => !s.media[i]?.audio && !s.media[i]?.audioMissing);
  return audioLeft ? 'voice' : 'wrapping';
}

export function storyReducer(state: StoryState, action: StoryAction): StoryState {
  if (action.type === 'reset') return initialStory;
  if (action.type === 'net') return state.net === action.net ? state : { ...state, net: action.net };
  const ev = action.ev;
  if (ev.id !== undefined) {
    if (ev.id <= state.lastId) return state; // replay after a reconnect
  }
  const base: StoryState = { ...state, net: 'ok', lastId: ev.id ?? state.lastId, eventCount: state.eventCount + 1, phase: state.phase === 'idle' ? 'running' : state.phase };

  switch (ev.type) {
    case 'run.started':
      return { ...base, phase: 'running', storyId: ev.data.story_id, lessonId: ev.data.lesson_id, arm: ev.data.arm, step: { kind: 'looking' } };

    case 'safety.result':
      return {
        ...base,
        safety: { tier: ev.data.tier, action: ev.data.action, ignoredText: ev.data.ignored_text ?? [], reasonCode: ev.data.reason_code },
        step: { kind: ev.data.action === 'refuse' || ev.data.action === 'ask_redraw' ? 'looking' : 'meeting' },
      };

    case 'character.ready':
      return { ...base, card: ev.data.card, step: { kind: 'promise' } };

    case 'oath.ready': {
      const promises = ev.data.commitments.map((c) => {
        const places = state.verdicts[c.id];
        return refreshPromise({ ...c, state: 'waiting', done: 0, expected: expectedPlaces(c.scope, state.totalPages), everBad: !!state.everBad[c.id] }, places, state.totalPages);
      });
      return { ...base, oathHash: ev.data.oath_hash, promises, step: { kind: 'planning' } };
    }

    case 'plan.ready': {
      const totalPages = ev.data.beats.length || DEFAULT_PAGES;
      return { ...base, beats: ev.data.beats, totalPages, step: { kind: 'writing', index: 1 } };
    }

    case 'scene.started':
      return { ...base, step: ev.data.attempt > 0 ? { kind: 'checking', index: ev.data.index } : { kind: 'writing', index: ev.data.index } };

    case 'verdict': {
      const v = ev.data;
      const places = { ...(state.verdicts[v.commitment] ?? {}), [v.scope]: { status: v.status, attempt: v.attempt } };
      const verdicts = { ...state.verdicts, [v.commitment]: places };
      const bad = BAD.includes(v.status);
      const everBad = bad ? { ...state.everBad, [v.commitment]: true } : state.everBad;
      const promises = state.promises.map((p) => (p.id === v.commitment ? refreshPromise({ ...p, everBad: p.everBad || bad }, places, state.totalPages) : p));
      const m = /^scene (\d+)$/.exec(v.scope);
      const step = m && state.step.kind !== 'fixing' ? { kind: 'checking' as const, index: Number(m[1]) } : state.step;
      return { ...base, verdicts, everBad, promises, step };
    }

    case 'scene.repair':
      return {
        ...base,
        repairs: [...state.repairs, { index: ev.data.index, attempt: ev.data.attempt, failed: ev.data.failed, because: ev.data.because }],
        // a picture that failed its check is painted again: that is painting, not fixing the page's words
        step: /picture/.test(ev.data.because ?? '') ? { kind: 'painting' } : { kind: 'fixing', index: ev.data.index },
      };

    case 'scene.accepted': {
      const page = ev.data.page;
      const pages = [...state.pages.filter((p) => p.index !== page.index), page].sort((a, b) => a.index - b.index);
      const attempts = { ...state.attempts, [page.index]: ev.data.attempts_used };
      const all = pages.length >= state.totalPages;
      // all pages are in but the whole-story check is still to come (a page may still be rewritten): that is checking, not painting
      return { ...base, pages, attempts, step: all ? { kind: 'checking' } : { kind: 'writing', index: page.index + 1 } };
    }

    case 'story.verified': {
      const next = { ...base, final: true };
      return { ...next, step: state.pages.length >= state.totalPages ? { kind: mediaStep(next) } : state.step };
    }

    case 'image.ready': {
      const media = { ...state.media, [ev.data.index]: { ...state.media[ev.data.index], image: ev.data.url, imageMissing: false } };
      const next = { ...base, media };
      return { ...next, step: state.pages.length >= state.totalPages ? { kind: mediaStep(next) } : state.step };
    }

    case 'audio.ready': {
      const media = { ...state.media, [ev.data.index]: { ...state.media[ev.data.index], audio: ev.data.url, seconds: ev.data.seconds, audioMissing: false } };
      const next = { ...base, media };
      return { ...next, step: state.pages.length >= state.totalPages ? { kind: mediaStep(next) } : state.step };
    }

    case 'quiz.ready':
      return { ...base, quiz: ev.data };

    case 'degraded': {
      const d = ev.data;
      let media = state.media;
      if (d.index && d.what === 'image') media = { ...media, [d.index]: { ...media[d.index], imageMissing: true } };
      if (d.index && d.what === 'audio') media = { ...media, [d.index]: { ...media[d.index], audioMissing: true } };
      const next = { ...base, media, degradations: [...state.degradations, d] };
      return d.index && state.pages.length >= state.totalPages ? { ...next, step: { kind: mediaStep(next) } } : next;
    }

    case 'receipt':
      return { ...base, final: true, receipt: ev.data, promises: finalise(state, ev.data), step: { kind: 'wrapping' } };

    case 'run.finished':
      return { ...base, phase: 'finished', outcome: ev.data.outcome, step: { kind: 'done' } };

    case 'run.refused':
      return { ...base, phase: 'refused', refusal: { reasonCode: ev.data.reason_code, message: ev.data.message, traceId: ev.data.trace_id } };

    case 'error':
      return { ...base, phase: 'error', error: ev.data };

    default:
      return base; // unknown event types are ignored: additions to the contract must never break the page
  }
}

// ---- selectors (pure helpers the screens use) ----------------------------------------------------------------------------------

export type MediaKind = 'ready' | 'pending' | 'missing';

export function imageStatus(s: StoryState, index: number): MediaKind {
  const m = s.media[index];
  if (m?.image) return 'ready';
  if (m?.imageMissing) return 'missing';
  return s.phase === 'running' ? 'pending' : 'missing';
}

export function audioStatus(s: StoryState, index: number): MediaKind {
  const m = s.media[index];
  if (m?.audio) return 'ready';
  if (m?.audioMissing) return 'missing';
  return s.phase === 'running' ? 'pending' : 'missing';
}

/** A page is shown only when everything for it exists: its final words, its picture (or the decision to go without) and its voice (or the same). */
export function pageReady(s: StoryState, index: number): boolean {
  if (!s.pages.some((p) => p.index === index)) return false;
  if (!s.final && s.phase === 'running') return false; // a page may still be rewritten by the whole-story check
  return imageStatus(s, index) !== 'pending' && audioStatus(s, index) !== 'pending';
}

export function isDone(s: StoryState): boolean {
  return s.phase === 'finished' || s.phase === 'refused' || s.phase === 'error';
}

/** Pages are all here and the run is over: the child can reach the end screen. */
export function allPagesIn(s: StoryState): boolean {
  return s.pages.length >= s.totalPages;
}

export const REDRAW_CODES = ['too_small', 'blank', 'no_character'];
export function isRedraw(reasonCode: string | undefined): boolean {
  return !!reasonCode && REDRAW_CODES.includes(reasonCode);
}

/** Final status of the oath for the parent: only meaningful once the receipt arrived. */
export function keptCounts(s: StoryState) {
  const c = { kept: 0, keptAfterFix: 0, notKept: 0, unchecked: 0, open: 0 };
  for (const p of s.promises) {
    if (p.state === 'kept') c.kept++;
    else if (p.state === 'kept_after_fix') c.keptAfterFix++;
    else if (p.state === 'not_kept') c.notKept++;
    else if (p.state === 'unchecked') c.unchecked++;
    else c.open++;
  }
  return c;
}
