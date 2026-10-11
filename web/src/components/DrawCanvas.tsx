// The drawing canvas. Pointer events only (finger, pen, mouse). Strokes are kept as data, so undo is unlimited and the picture is
// re-painted cleanly. Exported at 1024 px on the long edge on a white page (metadata-free PNG).
import { forwardRef, useCallback, useEffect, useImperativeHandle, useRef } from 'react';
import { guard, PALM_PX } from '../lib/touchGuard';

export const W = 1024;
export const H = 768;
const PEN_QUIET_MS = 6000; // after the pencil was last seen, touches on the drawing are a resting hand

interface Stroke { color: string; size: number; pts: { x: number; y: number }[] }

const DRAFT_KEY = 'storybound.draft';
const DRAFT_MAX = 1_500_000; // characters; sessionStorage allows about five million

/** The drawing in progress is kept in this tab only (sessionStorage: gone when the tab closes), so a reload, a crash of the tab or a
 *  stray swipe never costs the child their picture. It is deleted when the story starts and by Forget. */
export function clearDraft(): void { try { sessionStorage.removeItem(DRAFT_KEY); } catch { /* storage blocked */ } }
function saveDraft(strokes: Stroke[]): void {
  try {
    if (!strokes.length) { sessionStorage.removeItem(DRAFT_KEY); return; }
    const json = JSON.stringify(strokes.map((s) => ({ c: s.color, w: s.size, p: s.pts.map((q) => [Math.round(q.x), Math.round(q.y)]) })));
    if (json.length < DRAFT_MAX) sessionStorage.setItem(DRAFT_KEY, json);
  } catch { /* storage blocked or full: the drawing just is not kept */ }
}
function loadDraft(): Stroke[] {
  try {
    const raw = sessionStorage.getItem(DRAFT_KEY);
    if (!raw) return [];
    const a = JSON.parse(raw) as { c: string; w: number; p: [number, number][] }[];
    return a.filter((s) => s && Array.isArray(s.p) && s.p.length).map((s) => ({ color: s.c, size: s.w, pts: s.p.map(([x, y]) => ({ x, y })) }));
  } catch { return []; }
}

export interface DrawHandle {
  undo(): void;
  clear(): void; // soft: the strokes are kept aside until restore() or the next clear()
  restore(): void; // bring back what clear() put aside, under anything drawn since
  hasInk(): boolean;
  toBlob(): Promise<Blob>;
}

interface Props {
  color: string;
  size: number; // brush width in canvas pixels
  onChange(strokes: number, restorable: boolean): void;
  label: string;
}

function paint(ctx: CanvasRenderingContext2D, s: Stroke, from = 0) {
  ctx.strokeStyle = s.color;
  ctx.fillStyle = s.color;
  ctx.lineWidth = s.size;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  const p = s.pts;
  if (p.length === 1) {
    ctx.beginPath();
    ctx.arc(p[0].x, p[0].y, s.size / 2, 0, Math.PI * 2);
    ctx.fill();
    return;
  }
  ctx.beginPath();
  const start = Math.max(1, from);
  ctx.moveTo((p[start - 1].x + (p[start]?.x ?? p[start - 1].x)) / 2, (p[start - 1].y + (p[start]?.y ?? p[start - 1].y)) / 2);
  for (let i = start; i < p.length - 1; i++) {
    const mx = (p[i].x + p[i + 1].x) / 2;
    const my = (p[i].y + p[i + 1].y) / 2;
    ctx.quadraticCurveTo(p[i].x, p[i].y, mx, my);
  }
  ctx.lineTo(p[p.length - 1].x, p[p.length - 1].y);
  ctx.stroke();
}

export const DrawCanvas = forwardRef<DrawHandle, Props>(function DrawCanvas({ color, size, onChange, label }, ref) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const strokes = useRef<Stroke[]>([]);
  const live = useRef<{ id: number; s: Stroke; drawn: number } | null>(null);
  const aside = useRef<Stroke[]>([]); // what "start over" put aside
  const penUntil = useRef(0);
  const props = useRef({ color, size });
  props.current = { color, size };

  const ctx = () => canvas.current!.getContext('2d')!;

  const redraw = useCallback(() => {
    const c = ctx();
    c.fillStyle = '#FFFFFF';
    c.fillRect(0, 0, W, H);
    strokes.current.forEach((s) => paint(c, s));
  }, []);

  const changed = useCallback(() => { saveDraft(strokes.current); onChange(strokes.current.length, aside.current.length > 0); }, [onChange]);

  useEffect(() => {
    strokes.current = loadDraft(); // a picture left behind by a reload or an accidental leave comes back
    redraw();
    if (strokes.current.length) onChange(strokes.current.length, false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [redraw]);

  useImperativeHandle(ref, () => ({
    undo() { strokes.current.pop(); redraw(); changed(); },
    clear() { if (strokes.current.length) aside.current = strokes.current; strokes.current = []; redraw(); changed(); },
    restore() { strokes.current = [...aside.current, ...strokes.current]; aside.current = []; redraw(); changed(); },
    hasInk: () => strokes.current.length > 0,
    toBlob: () => new Promise<Blob>((resolve, reject) => canvas.current!.toBlob((b) => (b ? resolve(b) : reject(new Error('no image'))), 'image/png')),
  }), [changed, redraw]);

  const at = (e: React.PointerEvent) => {
    const r = canvas.current!.getBoundingClientRect();
    return { x: ((e.clientX - r.left) * W) / r.width, y: ((e.clientY - r.top) * H) / r.height };
  };

  const down = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (live.current) return; // a second finger never starts a second stroke
    if (e.pointerType === 'pen') penUntil.current = Date.now() + PEN_QUIET_MS;
    // Palm rejection: ignore large contacts, any touch while the pencil is in use (a resting hand), and a touch when two or more
    // fingers are already down (a hand, not a stroke).
    if (e.pointerType === 'touch' && (Math.max(e.width, e.height) > PALM_PX || Date.now() < penUntil.current || guard.fingers() > 1)) return;
    if (e.button > 0) return;
    e.preventDefault();
    canvas.current!.setPointerCapture(e.pointerId);
    const s: Stroke = { color: props.current.color, size: props.current.size, pts: [at(e)] };
    live.current = { id: e.pointerId, s, drawn: 0 };
    paint(ctx(), s);
  };

  const move = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (e.pointerType === 'pen') penUntil.current = Date.now() + PEN_QUIET_MS; // hovering counts: the hand is on the glass
    const l = live.current;
    if (!l || l.id !== e.pointerId) return;
    const events = e.nativeEvent.getCoalescedEvents?.() ?? [e.nativeEvent];
    const r = canvas.current!.getBoundingClientRect();
    for (const ev of events.length ? events : [e.nativeEvent]) {
      l.s.pts.push({ x: ((ev.clientX - r.left) * W) / r.width, y: ((ev.clientY - r.top) * H) / r.height });
    }
    if (l.s.pts.length > 2) { paint(ctx(), l.s, Math.max(1, l.s.pts.length - events.length - 1)); }
  };

  const up = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const l = live.current;
    if (!l || l.id !== e.pointerId) return;
    live.current = null;
    strokes.current.push(l.s);
    redraw(); // smooth, final version of the stroke
    changed();
  };

  return (
    <canvas
      ref={canvas}
      className="draw-canvas"
      width={W}
      height={H}
      role="img"
      aria-label={label}
      onPointerDown={down}
      onPointerMove={move}
      onPointerUp={up}
      onPointerCancel={up}
    />
  );
});
