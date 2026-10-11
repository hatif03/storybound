// A button that only counts when it is held down for a moment (default 0.9 s), with a ring that fills while you hold.
// For anything that throws work away: a palm or a stray finger lands for a tap's length, never for a whole second.
// Keyboard and screen-reader activation (Enter, Space, "activate") works at once: those are deliberate.
import { useEffect, useRef, useState, type ReactNode } from 'react';
import { Icon } from './Icon';
import { sfx } from '../lib/sound';

export const HOLD_MS = 900;

interface Props { onHold(): void; ms?: number; icon?: string; variant?: 'sun' | 'sky' | 'leaf' | 'paper' | 'grape'; children: ReactNode; className?: string; 'data-testid'?: string }

export function HoldButton({ onHold, ms = HOLD_MS, icon, variant = 'leaf', children, className = '', ...rest }: Props) {
  const [p, setP] = useState(0); // 0..1
  const start = useRef(0);
  const raf = useRef(0);
  const fired = useRef(false);

  const cancel = () => { cancelAnimationFrame(raf.current); start.current = 0; if (!fired.current) setP(0); };
  useEffect(() => () => cancelAnimationFrame(raf.current), []);

  const tick = () => {
    if (!start.current) return;
    const t = Math.min(1, (performance.now() - start.current) / ms);
    setP(t);
    if (t >= 1) { fired.current = true; start.current = 0; sfx('select'); navigator.vibrate?.(20); onHold(); return; }
    raf.current = requestAnimationFrame(tick);
  };

  return (
    <button
      type="button"
      className={`btn btn-${variant} btn-hold ${className}`}
      style={{ ['--hold' as string]: p }}
      data-holding={p > 0 && p < 1}
      aria-label={typeof children === 'string' ? `${children}. Hold the button for a moment.` : undefined}
      onPointerDown={(e) => { if (e.button > 0) return; fired.current = false; start.current = performance.now(); raf.current = requestAnimationFrame(tick); }}
      onPointerUp={cancel}
      onPointerLeave={cancel}
      onPointerCancel={cancel}
      onContextMenu={(e) => e.preventDefault()}
      onClick={(e) => { if (e.detail === 0 && !fired.current) { fired.current = true; onHold(); } }} // keyboard and assistive technology
      {...rest}
    >
      {icon && <Icon name={icon} />}
      <span className="btn-label">{children}</span>
      <span className="hold-hint" aria-hidden="true">hold</span>
    </button>
  );
}
