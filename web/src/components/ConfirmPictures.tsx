// A confirm that never needs reading: two big picture buttons (a tick and a "keep going" arrow), with Pip asking. Esc keeps going.
// The "yes" must be HELD for a moment, so a palm or a stray tap can never throw work away; "keep going" is a plain tap and has focus.
import { useEffect, useRef, type ReactNode } from 'react';
import { Btn } from './Btn';
import { HoldButton } from './HoldButton';
import { Pip, type Pose } from './Pip';

interface Props { title: string; yesLabel: string; noLabel: string; pose?: Pose; onYes(): void; onNo(): void; children?: ReactNode }

export function ConfirmPictures({ title, yesLabel, noLabel, pose = 'wink', onYes, onNo, children }: Props) {
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    box.current?.querySelector<HTMLElement>('[data-autofocus]')?.focus(); // the safe choice (keep going) gets focus first
    const key = (e: KeyboardEvent) => { if (e.key === 'Escape') onNo(); };
    window.addEventListener('keydown', key);
    return () => window.removeEventListener('keydown', key);
  }, [onNo]);
  return (
    <div className="scrim" role="presentation">
      <div className="confirm" role="alertdialog" aria-modal="true" aria-labelledby="confirm-title" ref={box}>
        <Pip pose={pose} className="confirm-pip" />
        <h2 id="confirm-title">{title}</h2>
        {children}
        <div className="confirm-actions">
          <Btn variant="sky" icon="arrow-left" onClick={onNo} data-autofocus>{noLabel}</Btn>
          <HoldButton variant="leaf" icon="check-circle" onHold={onYes}>{yesLabel}</HoldButton>
        </div>
      </div>
    </div>
  );
}
