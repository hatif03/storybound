import { useMemo, useState } from 'react';
import { Btn } from '../components/Btn';
import { Pip } from '../components/Pip';
import { SoundToggle } from '../components/SoundToggle';
import { sfx } from '../lib/sound';
import { useFocusHeading } from '../state/session';
import type { StoryState } from '../state/storyReducer';

/** Three pictures from the story, shuffled. The answer is the order of the pages, so it is right by construction. */
export function orderPages(story: StoryState): number[] {
  const withPic = story.pages.filter((p) => story.media[p.index]?.image).map((p) => p.index);
  if (withPic.length < 3) return [];
  return [withPic[0], withPic[Math.floor(withPic.length / 2)], withPic[withPic.length - 1]];
}

// "Which came first?" Tap the pictures in story order. Wrong taps wiggle back with a hint; there is no way to lose.
export function OrderGame({ story, onDone, onBack }: { story: StoryState; onDone(): void; onBack(): void }) {
  const h = useFocusHeading<HTMLHeadingElement>();
  const answer = useMemo(() => orderPages(story), [story]);
  const tray = useMemo(() => [...answer].sort((a, b) => ((a * 7) % 5) - ((b * 7) % 5) || b - a), [answer]); // a fixed, scrambled order
  const [placed, setPlaced] = useState<number[]>([]);
  const [wiggle, setWiggle] = useState<number | null>(null);
  const done = placed.length === answer.length;
  const need = ['first', 'next', 'last'][placed.length] ?? '';

  const tap = (idx: number) => {
    if (done || placed.includes(idx)) return;
    if (idx === answer[placed.length]) { sfx('star-pop'); setPlaced((p) => [...p, idx]); if (placed.length + 1 === answer.length) sfx('happy-chime'); }
    else { sfx('soft-boop'); setWiggle(idx); window.setTimeout(() => setWiggle(null), 500); }
  };

  return (
    <main className="screen order">
      <header className="screen-head">
        <button type="button" className="corner-btn" onClick={onBack} aria-label="Skip the game">Skip</button>
        <span />
        <SoundToggle />
      </header>
      <h1 ref={h} tabIndex={-1} className="quiz-q center">{done ? 'You put the story in order!' : `Which picture came ${need}?`}</h1>
      <div className="order-slots" aria-label="Story order">
        {answer.map((_, k) => (
          <div key={k} className="slot" data-filled={k < placed.length}>
            {k < placed.length ? <img src={story.media[placed[k]].image} alt={`Picture ${k + 1}`} /> : <span>{k + 1}</span>}
          </div>
        ))}
      </div>
      <ul className="order-tray" aria-label="Pictures to put in order">
        {tray.map((idx) => (
          <li key={idx}>
            <button type="button" className="order-card" data-wiggle={wiggle === idx} data-used={placed.includes(idx)} disabled={placed.includes(idx)} onClick={() => tap(idx)}
              aria-label={`Picture from the story`}>
              <img src={story.media[idx].image} alt="" />
            </button>
          </li>
        ))}
      </ul>
      <div className="confirm-bar">
        <Pip pose={done ? 'party' : 'wink'} className="notice-pip" />
        {done && <Btn big iconAfter="arrow-right" onClick={onDone}>Next</Btn>}
      </div>
    </main>
  );
}
