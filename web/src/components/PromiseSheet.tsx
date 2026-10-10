// The child-sized oath: one sticker slot per family of promises. A slot fills only when every promise in it was kept.
import { useEffect, useRef } from 'react';
import { Icon } from './Icon';
import { familyViews, kidLine, type FamilyView } from '../lib/promises';
import type { StoryState } from '../state/storyReducer';
import { sfx } from '../lib/sound';

function Row({ f }: { f: FamilyView }) {
  const state = f.earned ? 'earned' : f.fixing ? 'fixing' : f.checking || f.kept ? 'checking' : 'waiting';
  const status = f.earned ? 'kept' : f.fixing ? 'Pip is fixing something' : f.checking || f.kept ? 'being checked' : 'waiting';
  return (
    <li className="slot" data-state={state}>
      <img className="slot-sticker" src={`/assets/stickers/${f.earned ? f.sticker : 'empty-slot'}.svg`} alt="" width={64} height={64} />
      <div className="slot-text">
        <strong>{f.kid}</strong>
        <span className="ticks" aria-hidden="true">
          {f.promises.map((p) => (
            <i key={p.id} className={`tick tick-${p.state}`} title={kidLine(p)}>
              {p.state === 'kept' || p.state === 'kept_after_fix' ? <Icon name="check" weight="bold" /> : p.state === 'fixing' ? <Icon name="sparkle" /> : null}
            </i>
          ))}
        </span>
        <span className="sr-only">{`${f.kid}: ${status}, ${f.kept} of ${f.promises.length} promises kept`}</span>
      </div>
      {f.earned && <Icon name="star" className="slot-star" />}
    </li>
  );
}

export function PromiseSheet({ story, lessonTitle }: { story: StoryState; lessonTitle?: string }) {
  const fams = familyViews(story.promises, lessonTitle);
  const earned = fams.filter((f) => f.earned).length;
  const prev = useRef(earned);
  useEffect(() => { if (earned > prev.current) sfx('star-pop'); prev.current = earned; }, [earned]);
  const last = [...story.promises].reverse().find((p) => p.state === 'kept' || p.state === 'kept_after_fix');
  if (!fams.length) {
    return (
      <section className="promise-sheet" aria-label="Pip's promises">
        <h2>Pip&apos;s promises</h2>
        <p className="muted">Pip is thinking up the promises. They will show up here.</p>
      </section>
    );
  }
  return (
    <section className="promise-sheet" aria-label="Pip's promises">
      <h2>Pip&apos;s promises</h2>
      <ul className="slots">{fams.map((f) => <Row key={f.id} f={f} />)}</ul>
      <p className="last-kept" role="status" aria-live="polite">{last ? `Pip checked: ${kidLine(last)}` : 'Pip checks every promise before you see a page.'}</p>
    </section>
  );
}
