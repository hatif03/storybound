// Demo mode switches and fake answers for the HTTP calls. Replay of the event stream is in api/events.ts.
import type { Fixture, Lesson, StartRequest, StoryEvent } from '../api/types';
import { buildScenario, SCENARIOS, scenarioForFixture, type ScenarioName } from './scenarios';

const params = typeof location === 'undefined' ? new URLSearchParams() : new URLSearchParams(location.search);

/** ?mock=1 turns demo mode on: no backend needed. */
export const MOCK = params.get('mock') === '1' || params.get('mock') === 'true';
/** ?speed=10 plays the recorded run ten times faster (default 1: the real pace, about five minutes). */
export const MOCK_SPEED = Math.max(0.1, Number(params.get('speed')) || 1);
const forced = params.get('scenario') as ScenarioName | null;

let current: ScenarioName = 'bunny';

// The four lessons the backend has today (src/storybound/lessons.py).
export const mockLessons = (): Lesson[] => [
  { id: 'sharing', title: 'Sharing', blurb: 'Sharing makes good things better for everyone.', icon: 'gift' },
  { id: 'honesty', title: 'Telling the truth', blurb: 'Saying what really happened, even when it is hard.', icon: 'star' },
  { id: 'kindness', title: 'Being kind', blurb: "Small kind acts can change someone's whole day.", icon: 'heart' },
  { id: 'patience', title: 'Being patient', blurb: 'Good things come to those who wait and try again.', icon: 'clock' },
];

const SAMPLES: [string, string][] = [
  ['bunny-bow-carrot', 'Bunny bow carrot'], ['rabbit-tree-rainbow', 'Rabbit tree rainbow'], ['rhinoceros-crayon', 'Rhinoceros crayon'],
  ['van-crayon', 'Van crayon'], ['chameleon-hummingbird', 'Chameleon hummingbird'], ['christmas-tree-digital', 'Christmas tree digital'],
];

/** Same shape as GET /api/fixtures. Unsafe and caption samples have no picture in demo mode: the drawer lists them by name only. */
export const mockFixtures = (): Fixture[] => [
  ...SAMPLES.map(([id, label]) => ({ id: `benign/${id}`, label, url: `/assets/samples/${id}.webp`, kind: 'benign' })),
  { id: 'tier-a-unsafe/evil-cat-knife-blood', label: 'Evil cat knife blood', url: '', kind: 'demo-unsafe' },
  { id: 'tier-b-text/fish-kill-fish-caption', label: 'Fish kill fish caption', url: '', kind: 'demo-text' },
  { id: 'synthetic/blank-white-page', label: 'Blank white page', url: '', kind: 'synthetic' },
  { id: 'synthetic/bunny-tiny-64px', label: 'Bunny tiny 64px', url: '', kind: 'synthetic' },
];

export function mockStart(req: StartRequest): { storyId: string } {
  const fid = req.drawing.kind === 'fixture' ? req.drawing.id : undefined;
  const kind = fid ? mockFixtures().find((f) => f.id === fid)?.kind : undefined;
  current = forced && SCENARIOS.includes(forced) ? forced : scenarioForFixture(fid, kind);
  return { storyId: 'demo' };
}

export const mockEvents = (): StoryEvent[] => buildScenario(current);
