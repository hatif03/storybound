// The drawing canvas. Pointer events only (finger, pen, mouse). Strokes are kept as data, so undo is unlimited and the picture is
// re-painted cleanly. Exported at 1024 px on the long edge on a white page (metadata-free PNG).
import { forwardRef, useCallback, useEffect, useImperativeHandle, useRef } from 'react';

export const W = 1024;
export const H = 768;

interface Stroke { color: string; size: number; pts: { x: number; y: number }[] }

export interface DrawHandle {
  undo(): void;
  clear(): void;
  hasInk(): boolean;
  toBlob(): Promise<Blob>;
}

interface Props {
  color: string;
  size: number; // brush width in canvas pixels
  onChange(strokes: number): void;
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

  useEffect(() => { redraw(); }, [redraw]);

  useImperativeHandle(ref, () => ({
    undo() { strokes.current.pop(); redraw(); onChange(strokes.current.length); },
    clear() { strokes.current = []; redraw(); onChange(0); },
    hasInk: () => strokes.current.length > 0,
    toBlob: () => new Promise<Blob>((resolve, reject) => canvas.current!.toBlob((b) => (b ? resolve(b) : reject(new Error('no image'))), 'image/png')),
  }), [onChange, redraw]);

  const at = (e: React.PointerEvent) => {
    const r = canvas.current!.getBoundingClientRect();
    return { x: ((e.clientX - r.left) * W) / r.width, y: ((e.clientY - r.top) * H) / r.height };
  };

  const down = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (live.current) return; // a second finger never starts a second stroke
    if (e.pointerType === 'pen') penUntil.current = Date.now() + 2000;
    // Palm rejection: ignore large contacts, and any touch just after the pen was used.
    if (e.pointerType === 'touch' && (Math.max(e.width, e.height) > 48 || Date.now() < penUntil.current)) return;
    if (e.button > 0) return;
    e.preventDefault();
    canvas.current!.setPointerCapture(e.pointerId);
    const s: Stroke = { color: props.current.color, size: props.current.size, pts: [at(e)] };
    live.current = { id: e.pointerId, s, drawn: 0 };
    paint(ctx(), s);
  };

  const move = (e: React.PointerEvent<HTMLCanvasElement>) => {
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
    onChange(strokes.current.length);
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
