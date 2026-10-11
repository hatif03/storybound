import { describe, expect, it, beforeEach } from 'vitest';
import { createGuard, GHOST_MS, isPalm, MAX_FINGERS, PALM_MS, PALM_PX } from './touchGuard';
import { loadActive, saveActive, clearActive } from './resume';

const touch = (w = 10, h = 10) => ({ pointerType: 'touch', width: w, height: h });

describe('touch guard', () => {
  it('treats a big touch contact as a palm, never a pen or a mouse', () => {
    expect(isPalm(touch(PALM_PX + 1, 20))).toBe(true);
    expect(isPalm(touch(20, PALM_PX + 1))).toBe(true);
    expect(isPalm(touch(PALM_PX, PALM_PX))).toBe(false); // a fingertip
    expect(isPalm({ pointerType: 'pen', width: 200, height: 200 })).toBe(false);
    expect(isPalm({ pointerType: 'mouse', width: 200, height: 200 })).toBe(false);
  });

  it('drops a tap that lands just after the screen changed, then lets taps through', () => {
    let t = 1000;
    const g = createGuard(() => t);
    expect(g.blockClick(1)).toBe('');
    g.lock();
    expect(g.blockClick(1)).toBe('ghost');
    t += GHOST_MS + 1;
    expect(g.blockClick(1)).toBe('');
  });

  it('never blocks a keyboard or screen-reader click (detail 0)', () => {
    const g = createGuard(() => 0);
    g.lock(10_000);
    expect(g.blockClick(0)).toBe('');
  });

  it('drops clicks while a whole hand is down, and just after a palm landed', () => {
    let t = 5000;
    const g = createGuard(() => t);
    for (let i = 0; i < MAX_FINGERS; i++) g.pointerDown(i, touch());
    expect(g.blockClick(1)).toBe('hand');
    g.pointerUp(0);
    expect(g.blockClick(1)).toBe('');
    g.pointerDown(9, touch(120, 120));
    g.pointerUp(9);
    expect(g.blockClick(1)).toBe('palm');
    t += PALM_MS + 1;
    expect(g.blockClick(1)).toBe('');
  });

  it('counts only touch contacts as fingers', () => {
    const g = createGuard(() => 0);
    g.pointerDown(1, { pointerType: 'mouse', width: 1, height: 1 });
    g.pointerDown(2, { pointerType: 'pen', width: 1, height: 1 });
    expect(g.fingers()).toBe(0);
  });
});

describe('resume', () => {
  const store: Record<string, string> = {};
  beforeEach(() => {
    for (const k of Object.keys(store)) delete store[k];
    (globalThis as unknown as { sessionStorage: Storage }).sessionStorage = {
      getItem: (k: string) => store[k] ?? null, setItem: (k: string, v: string) => { store[k] = v; }, removeItem: (k: string) => { delete store[k]; },
    } as Storage;
  });

  it('keeps only an id and a title, and forgets on clear', () => {
    saveActive({ storyId: 'ab12cd34ef56', lessonTitle: 'Sharing' });
    expect(loadActive()).toEqual({ storyId: 'ab12cd34ef56', lessonTitle: 'Sharing' });
    clearActive();
    expect(loadActive()).toBeNull();
  });

  it('refuses a story id that is not a plain token', () => {
    store['storybound.active'] = JSON.stringify({ storyId: '../etc/passwd' });
    expect(loadActive()).toBeNull();
    store['storybound.active'] = 'not json';
    expect(loadActive()).toBeNull();
  });
});
