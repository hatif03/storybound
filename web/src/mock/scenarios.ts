// Demo mode (?mock=1): the app runs with no backend by replaying a recorded event stream.
// run-bunny.json is the "events" array of evidence/runs/20261010-1318-IST-bunny-sharing-B1-first-full-run.json (verdicts trimmed
// to the fields the page uses). That run had no pictures or audio, so image.ready / audio.ready are synthesised here with local art.
import recording from './run-bunny.json';
import type { Degradation, Receipt, StoryEvent } from '../api/types';

export type ScenarioName = 'bunny' | 'repair' | 'degraded' | 'refuse' | 'redraw';
export const SCENARIOS: ScenarioName[] = ['bunny', 'repair', 'degraded', 'refuse', 'redraw'];

type Raw = { id?: number; type: string; t: number; data: Record<string, unknown> };
const events = recording as unknown as Raw[];

const SCENES = ['meadow', 'forest', 'park', 'playground', 'kitchen', 'school', 'bedroom', 'home'];
const CALM_REFUSAL = "This drawing isn't one I can turn into a story. Could we try a different picture together?";
const CALM_REDRAW = 'I couldn’t quite see a hero in that picture. Could you draw one a little bigger and darker?';

const imageUrl = (i: number) => `/assets/scenes/${SCENES[(i - 1) % SCENES.length]}-4x3.webp`;
const AUDIO_URL = '/assets/audio/sfx/silent-100ms.mp3';

const IMAGE_CHECKS = ['trait_in_image_prompt', 'illustration_present', 'image_matches_card'];

function verdict(t: number, commitment: string, scope: string, status = 'pass'): Raw {
  return { type: 'verdict', t, data: { commitment, scope, status, attempt: 0, verdict_by: 'deterministic' } };
}

/** The recorded run, minus the final receipt, with media events added after the last page. */
function bunnyBase(opts: { skipImage?: number[]; skipAudio?: number[]; ignoredText?: string[]; judgeNote?: boolean; onlyRepair?: number }): { list: Raw[]; degradations: Degradation[] } {
  let list = events.filter((e) => e.type !== 'receipt' && e.type !== 'run.finished').map((e) => ({ ...e, data: { ...e.data } }));
  if (opts.onlyRepair !== undefined) list = keepOneRepair(list, opts.onlyRepair);
  const degradations: Degradation[] = [];
  if (opts.ignoredText) {
    const s = list.find((e) => e.type === 'safety.result');
    if (s) s.data = { ...s.data, tier: 'B', action: 'sanitise', ignored_text: opts.ignoredText };
  }
  const lastAccepted = Math.max(...list.map((e, i) => (e.type === 'scene.accepted' ? i : -1)));
  let t = list[lastAccepted].t + 3;
  const media: Raw[] = [];
  for (let i = 1; i <= 8; i++) {
    t += 1.2;
    if (opts.skipImage?.includes(i)) {
      const d: Degradation = { what: 'image', index: i, why: 'no valid picture returned', fallback: 'text only' };
      degradations.push(d);
      media.push({ type: 'degraded', t, data: { ...d } });
      continue;
    }
    IMAGE_CHECKS.forEach((c) => media.push(verdict(t, c, `image ${i}`)));
    media.push({ type: 'image.ready', t, data: { index: i, url: imageUrl(i), verdict: 'pass' } });
  }
  for (let i = 1; i <= 8; i++) {
    t += 0.9;
    if (opts.skipAudio?.includes(i)) {
      const d: Degradation = { what: 'audio', index: i, why: 'audio did not pass the check', fallback: 'text only' };
      degradations.push(d);
      media.push({ type: 'degraded', t, data: { ...d } });
      continue;
    }
    media.push(verdict(t, 'narration_present', `audio ${i}`));
    media.push({ type: 'audio.ready', t, data: { index: i, url: AUDIO_URL, seconds: 6.5 } });
  }
  if (opts.judgeNote) {
    const d: Degradation = { what: 'judge', why: 'per-story budget reached', fallback: 'quality judging off; safety checks unchanged' };
    degradations.push(d);
    const at = list.findIndex((e) => e.type === 'scene.started' && e.data.index === 6 && e.data.attempt === 0);
    list.splice(at, 0, { type: 'degraded', t: list[at].t, data: { ...d } });
  }
  return { list: [...list, ...media], degradations };
}

/** A shorter, cleaner run: only one page breaks a promise first time. Pages other than `keep` pass on the first try. */
function keepOneRepair(list: Raw[], keep: number): Raw[] {
  const scope = (e: Raw) => String(e.data.scope ?? '');
  const out: Raw[] = [];
  for (const e of list) {
    const idx = Number(e.data.index ?? (scope(e).startsWith('scene ') ? scope(e).split(' ')[1] : 0));
    const isScenePage = idx >= 1 && idx !== keep;
    if (isScenePage && e.type === 'scene.repair') continue;
    if (isScenePage && e.type === 'scene.started' && e.data.attempt === 1) continue;
    if (isScenePage && e.type === 'verdict' && e.data.attempt === 0 && scope(e).startsWith('scene ')) continue;
    if (isScenePage && e.type === 'verdict' && e.data.attempt === 1) {
      out.push({ ...e, data: { ...e.data, attempt: 0 } });
      continue;
    }
    if (isScenePage && e.type === 'scene.accepted') {
      out.push({ ...e, data: { ...e.data, attempts_used: 0 } });
      continue;
    }
    out.push(e);
  }
  return out;
}

function makeReceipt(list: Raw[], degradations: Degradation[], ignored: string[]): Receipt {
  const oath = list.find((e) => e.type === 'oath.ready')!.data as { oath_hash: string; commitments: { id: string }[] };
  const checked = new Set<string>();
  let checks = 0;
  let violations = 0;
  for (const e of list) {
    if (e.type !== 'verdict') continue;
    if (e.data.status !== 'skipped') { checked.add(String(e.data.commitment)); checks++; }
    if (e.data.status === 'violation') violations++;
  }
  const repairs = list.filter((e) => e.type === 'scene.repair');
  const rewritten = new Set(repairs.filter((e) => Number(e.data.index) > 0).map((e) => e.data.index)).size;
  const attempts: Record<number, number> = {};
  for (const e of list) if (e.type === 'scene.accepted') attempts[Number(e.data.index)] = Number(e.data.attempts_used) + 1;
  const original = events.find((e) => e.type === 'receipt')!.data as unknown as Receipt;
  return {
    ...original,
    oath_hash: oath.oath_hash,
    plain: `${checked.size} promises checked. ${rewritten} pages rewritten. All kept.`,
    counts: { ...original.counts, commitments: oath.commitments.length, checked: checked.size, checks, violations_found: violations, repairs: repairs.length, kept: checked.size, shipped_violations: 0 },
    broken: [],
    pages: Object.entries(attempts).map(([i, a]) => ({ index: Number(i), attempts: a, final: 'pass' })),
    degradations,
    ignored_drawing_text: ignored,
  };
}

/** Build the events (with `t` in seconds and sequential `id`s) for a scenario. */
export function buildScenario(name: ScenarioName): StoryEvent[] {
  let list: Raw[];
  if (name === 'refuse' || name === 'redraw') {
    const redraw = name === 'redraw';
    list = [
      { type: 'run.started', t: 0.02, data: { story_id: 'demo', arm: 'B1', lesson_id: 'sharing', age: 6, seed: '1', input_hash: 'demo' } },
      { type: 'safety.result', t: 3.4, data: { tier: redraw ? 'none' : 'A', action: redraw ? 'ask_redraw' : 'refuse', ignored_text: [], reason_code: redraw ? 'too_small' : 'unsafe_image' } },
      { type: 'run.refused', t: 3.41, data: { reason_code: redraw ? 'too_small' : 'unsafe_image', message: redraw ? CALM_REDRAW : CALM_REFUSAL, trace_id: 'demo-trace-no-story-made' } },
    ];
  } else {
    const opt = name === 'degraded'
      ? { skipImage: [4], skipAudio: [6], ignoredText: ['Kill fish'], judgeNote: true }
      : name === 'repair' ? { onlyRepair: 5 } : {};
    const { list: base, degradations } = bunnyBase(opt);
    const ignored = name === 'degraded' ? ['Kill fish'] : [];
    const last = base[base.length - 1].t + 2.2;
    // A small quiz built from the recorded pages, so the quiz and game screens can be tried without a model run.
    const pages = base.filter((e) => e.type === 'scene.accepted').map((e) => (e.data as { page: { index: number; scenario: string } }).page);
    const items = [1, 3, 5, 7].filter((i) => pages[i - 1]).map((i, k) => ({
      index: k + 1, kind: (['recall', 'detail', 'feeling', 'lesson'] as const)[k], question: `What happened on page ${i}?`,
      options: [{ id: 'a', text: 'Something else', is_correct: false }, { id: 'b', text: 'This line is the answer', is_correct: true }, { id: 'c', text: 'Nothing at all', is_correct: false }],
      evidence_page: i, evidence_quote: pages[i - 1].scenario.split(' ').slice(0, 6).join(' '), explain: 'Look: the line on the page.',
    }));
    const quizEvent = { type: 'quiz.ready', t: last - 0.4, data: { items, talk_about: 'What do you like to share with your friends?' } };
    list = [...base, quizEvent as never, { type: 'receipt', t: last, data: makeReceipt(base, degradations, ignored) as never }, { type: 'run.finished', t: last + 0.01, data: { outcome: degradations.length ? 'shipped_with_notes' : 'shipped', story_id: 'demo' } }];
  }
  return list.map((e, id) => ({ ...e, id })) as unknown as StoryEvent[];
}

export function scenarioForFixture(fixtureId: string | undefined, kind: string | undefined): ScenarioName {
  if (kind === 'demo-unsafe') return 'refuse';
  if (kind === 'demo-text') return 'degraded';
  if (fixtureId && /blank|tiny|dot|scribble/.test(fixtureId)) return 'redraw';
  return 'bunny';
}
