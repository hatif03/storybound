import { describe, expect, it } from 'vitest';
import type { Receipt, StoryEvent } from '../api/types';
import { buildScenario } from '../mock/scenarios';
import { allPagesIn, audioStatus, imageStatus, initialStory, isRedraw, keptCounts, storyReducer, type StoryState } from './storyReducer';

const fold = (events: StoryEvent[], from: StoryState = initialStory) => events.reduce((s, ev) => storyReducer(s, { type: 'event', ev }), from);
const upTo = (events: StoryEvent[], pred: (e: StoryEvent) => boolean) => events.slice(0, events.findIndex(pred) + 1);

describe('happy path (recorded bunny run)', () => {
  const events = buildScenario('bunny');
  const s = fold(events);

  it('ends finished with eight pages and a receipt', () => {
    expect(s.phase).toBe('finished');
    expect(s.outcome).toBe('shipped');
    expect(s.pages).toHaveLength(8);
    expect(allPagesIn(s)).toBe(true);
    expect(s.pages.map((p) => p.index)).toEqual([1, 2, 3, 4, 5, 6, 7, 8]);
    expect(s.receipt?.plain).toMatch(/All kept/);
    expect(s.step.kind).toBe('done');
  });

  it('has the hero card and the oath as promises, none left open', () => {
    expect(s.card?.name).toBe('Poppy');
    expect(s.promises.length).toBe(21);
    const c = keptCounts(s);
    expect(c.open).toBe(0);
    expect(c.notKept).toBe(0);
    expect(c.kept + c.keptAfterFix + c.unchecked).toBe(21);
  });

  it('marks a promise that was broken once and fixed as kept after a fix', () => {
    expect(s.promises.find((p) => p.id === 'age_reading_level')?.state).toBe('kept_after_fix');
    expect(s.promises.find((p) => p.id === 'character_named_in_scene')?.state).toBe('kept');
  });

  it('shows pictures and sound once they arrive', () => {
    expect(imageStatus(s, 1)).toBe('ready');
    expect(audioStatus(s, 8)).toBe('ready');
  });

  it('shows a page as soon as it is accepted, while later pages are still coming', () => {
    const mid = fold(upTo(events, (e) => e.type === 'scene.accepted' && e.data.index === 1));
    expect(mid.phase).toBe('running');
    expect(mid.pages).toHaveLength(1);
    expect(mid.step).toEqual({ kind: 'writing', index: 2 });
    expect(imageStatus(mid, 1)).toBe('pending'); // not an error: the picture is still being painted
    expect(mid.receipt).toBeUndefined();
  });
});

describe('repair path', () => {
  const events = buildScenario('repair');

  it('says Pip is fixing page 5 on scene.repair and records why', () => {
    const s = fold(upTo(events, (e) => e.type === 'scene.repair'));
    expect(s.step).toEqual({ kind: 'fixing', index: 5 });
    expect(s.repairs).toHaveLength(1);
    expect(s.repairs[0]).toMatchObject({ index: 5, attempt: 1, failed: ['age_reading_level'] });
    expect(s.promises.find((p) => p.id === 'age_reading_level')?.state).toBe('fixing');
  });

  it('then checks the rewritten page and accepts it', () => {
    const s = fold(events);
    expect(s.attempts[5]).toBe(1);
    expect(s.attempts[4]).toBe(0);
    expect(s.receipt?.pages.find((p) => p.index === 5)?.attempts).toBe(2);
    expect(s.receipt?.plain).toMatch(/1 pages rewritten/);
    expect(s.promises.find((p) => p.id === 'age_reading_level')?.state).toBe('kept_after_fix');
  });
});

describe('refusal', () => {
  it('unsafe drawing: refused, calm message, no pages', () => {
    const s = fold(buildScenario('refuse'));
    expect(s.phase).toBe('refused');
    expect(s.refusal?.reasonCode).toBe('unsafe_image');
    expect(isRedraw(s.refusal?.reasonCode)).toBe(false);
    expect(s.refusal?.message.length).toBeGreaterThan(10);
    expect(s.pages).toHaveLength(0);
  });
  it('too small drawing: a redraw prompt', () => {
    const s = fold(buildScenario('redraw'));
    expect(s.phase).toBe('refused');
    expect(isRedraw(s.refusal?.reasonCode)).toBe(true);
  });
});

describe('degraded media', () => {
  const s = fold(buildScenario('degraded'));
  it('a missing picture or voice is a quiet text-only page, not an error', () => {
    expect(s.phase).toBe('finished');
    expect(imageStatus(s, 4)).toBe('missing');
    expect(imageStatus(s, 3)).toBe('ready');
    expect(audioStatus(s, 6)).toBe('missing');
    expect(s.pages).toHaveLength(8);
  });
  it('keeps the degradations and ignored drawing text for the receipt', () => {
    expect(s.degradations.map((d) => d.what).sort()).toEqual(['audio', 'image', 'judge']);
    expect(s.receipt?.degradations).toHaveLength(3);
    expect(s.receipt?.ignored_drawing_text).toEqual(['Kill fish']);
    expect(s.outcome).toBe('shipped_with_notes');
    expect(s.safety?.ignoredText).toEqual(['Kill fish']);
  });
  it('a page whose media never came is missing once the run is over', () => {
    const early = fold(buildScenario('bunny').slice(0, 30));
    expect(imageStatus(early, 2)).toBe('pending');
    expect(imageStatus({ ...early, phase: 'finished' }, 2)).toBe('missing');
  });
});

describe('reconnect', () => {
  const events = buildScenario('repair');
  it('replayed events (Last-Event-ID or a replay from the start) change nothing', () => {
    const half = fold(events.slice(0, 60));
    const again = fold(events.slice(0, 60), half);
    expect(again).toBe(half);
    const full = fold(events);
    expect(fold(events, full)).toBe(full);
  });
  it('a reconnect that replays from the start ends in the same state', () => {
    const half = fold(events.slice(0, 60));
    expect(fold(events, half)).toEqual(fold(events));
  });
  it('net status is tracked and cleared by the next event', () => {
    let s = storyReducer(fold(events.slice(0, 5)), { type: 'net', net: 'reconnecting' });
    expect(s.net).toBe('reconnecting');
    s = storyReducer(s, { type: 'event', ev: events[5] });
    expect(s.net).toBe('ok');
  });
  it('ignores event types it does not know', () => {
    const odd = { id: 999, t: 1, type: 'future.thing', data: {} } as unknown as StoryEvent;
    expect(fold([odd]).phase).toBe('running');
  });
});

describe('honesty', () => {
  it('a promise the receipt lists as broken is never shown as kept', () => {
    const events = buildScenario('bunny');
    const receipt = events.find((e) => e.type === 'receipt')!;
    const broken: StoryEvent = { ...receipt, data: { ...(receipt.data as Receipt), broken: ['character_named_in_scene'] } } as StoryEvent;
    const s = fold(events.map((e) => (e.type === 'receipt' ? broken : e)));
    expect(s.promises.find((p) => p.id === 'character_named_in_scene')?.state).toBe('not_kept');
    expect(keptCounts(s).notKept).toBe(1);
  });
  it('a promise that never produced a real check is "unchecked", not kept', () => {
    const s = fold(buildScenario('bunny'));
    const unchecked = s.promises.find((p) => p.id === 'lesson_specific_poppy_shares_carrot');
    expect(unchecked?.state).toBe('unchecked');
  });
});
