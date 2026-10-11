// Touch safety for small hands. A child on a tablet rests a palm, an elbow or a sleeve on the screen, taps twice, swipes from the
// edge, pinches, or taps where a button just was (the screen changed under the finger). None of that may change the story.
//
// What this does, and what it cannot:
//  - Ghost taps: for a moment after the screen changes, clicks are dropped (a tap meant for the last screen must not hit the next one).
//  - Palms and elbows: a contact reported as big (more than PALM_PX) is not a tap, and neither is a click while three or more
//    fingers are down. Safari on iPad does not report contact size, so there the protection is the other rules (hold to confirm,
//    undo, drafts that survive a reload), not this one.
//  - Pinch and long-press: zooming gestures and the press-and-hold menu are switched off outside text fields.
//  - Keyboard and screen-reader clicks (detail 0) are never blocked: they are deliberate.
//  - The app's own back arrows work; the browser's back swipe is held in place (see keepInApp), because an edge swipe by a palm
//    would otherwise leave the story.

export const PALM_PX = 60; // a fingertip is about 40 px wide on a tablet; a palm or an elbow is much larger
export const GHOST_MS = 350; // clicks right after a screen change are dropped
export const PALM_MS = 800; // clicks shortly after a palm landed are dropped
export const MAX_FINGERS = 3; // this many contacts at once is a hand resting, not a tap

export interface Contact { pointerType: string; width: number; height: number }

export function isPalm(c: Contact): boolean {
  return c.pointerType === 'touch' && Math.max(c.width || 0, c.height || 0) > PALM_PX;
}

export type Block = '' | 'ghost' | 'palm' | 'hand';

export function createGuard(now: () => number = () => Date.now()) {
  let lockedUntil = 0;
  let palmAt = -Infinity;
  const down = new Set<number>();

  return {
    /** Call when the screen changes. */
    lock(ms = GHOST_MS) { lockedUntil = Math.max(lockedUntil, now() + ms); },
    pointerDown(id: number, c: Contact) {
      if (c.pointerType === 'touch') down.add(id);
      if (isPalm(c)) palmAt = now();
    },
    pointerUp(id: number) { down.delete(id); },
    /** Why a click should be dropped ('' = let it through). `detail` is the click count: 0 means keyboard or assistive technology. */
    blockClick(detail: number): Block {
      if (detail === 0) return '';
      if (now() < lockedUntil) return 'ghost';
      if (down.size >= MAX_FINGERS) return 'hand';
      if (now() - palmAt < PALM_MS) return 'palm';
      return '';
    },
    fingers: () => down.size,
  };
}

export const guard = createGuard();

const TEXTY = 'input, textarea, select, [contenteditable="true"]';

/** Install the page-wide rules once. Returns a function that removes them. `onHidden` runs when the tab is hidden (stop talking). */
export function installTouchGuard(onHidden?: () => void): () => void {
  if (typeof document === 'undefined') return () => {};
  const on = (t: Document | Window, k: string, fn: (e: never) => void, opts?: AddEventListenerOptions) => {
    t.addEventListener(k, fn as EventListener, opts);
    return () => t.removeEventListener(k, fn as EventListener, opts);
  };
  const offs = [
    on(document, 'pointerdown', (e: PointerEvent) => guard.pointerDown(e.pointerId, e), { capture: true }),
    on(document, 'pointerup', (e: PointerEvent) => guard.pointerUp(e.pointerId), { capture: true }),
    on(document, 'pointercancel', (e: PointerEvent) => guard.pointerUp(e.pointerId), { capture: true }),
    on(document, 'click', (e: MouseEvent) => {
      if (guard.blockClick(e.detail)) { e.preventDefault(); e.stopPropagation(); }
    }, { capture: true }),
    // iOS Safari ignores user-scalable=no; its pinch gesture events can still be cancelled.
    on(document, 'gesturestart', (e: Event) => e.preventDefault()),
    on(document, 'gesturechange', (e: Event) => e.preventDefault()),
    on(document, 'contextmenu', (e: Event) => { if (!(e.target as HTMLElement)?.closest?.(TEXTY)) e.preventDefault(); }),
    on(document, 'dragstart', (e: Event) => { if (!(e.target as HTMLElement)?.closest?.(TEXTY)) e.preventDefault(); }),
    on(document, 'visibilitychange', () => { if (document.hidden) onHidden?.(); }),
  ];
  return () => offs.forEach((f) => f());
}

/** Keep the browser's back swipe or button from leaving the app: put the same entry back. The app's own arrows do the going back. */
export function keepInApp(): () => void {
  if (typeof window === 'undefined' || !window.history?.pushState) return () => {};
  try { window.history.pushState({ storybound: true }, ''); } catch { return () => {}; }
  const pop = () => { try { window.history.pushState({ storybound: true }, ''); } catch { /* ignore */ } };
  window.addEventListener('popstate', pop);
  return () => window.removeEventListener('popstate', pop);
}
