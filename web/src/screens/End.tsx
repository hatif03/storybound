import { useEffect } from 'react';
import { Btn } from '../components/Btn';
import { Icon } from '../components/Icon';
import { Pip } from '../components/Pip';
import { SoundToggle } from '../components/SoundToggle';
import { familyViews } from '../lib/promises';
import { say, sfx } from '../lib/sound';
import { useFocusHeading } from '../state/session';
import { isDone, type StoryState } from '../state/storyReducer';

const PRAISE = ['you-did-it', 'amazing', 'great-job', 'awesome'];
const pick = (id: string | undefined) => PRAISE[(id ?? 'x').split('').reduce((a, c) => a + c.charCodeAt(0), 0) % PRAISE.length];

// 6.8 The end. Stickers are shown only for promises that were kept; the receipt (behind the grown-ups gate) shows everything.
export function End({ story, lessonTitle, onAgain, onNew, onGrownups }: {
  story: StoryState; lessonTitle?: string; onAgain(): void; onNew(): void; onGrownups(): void;
}) {
  const h = useFocusHeading<HTMLHeadingElement>();
  const fams = familyViews(story.promises, lessonTitle);
  const earned = fams.filter((f) => f.earned);
  const finishing = !isDone(story);
  useEffect(() => { sfx('happy-chime'); say('end-done'); }, []);
  return (
    <main className="screen end">
      <div className="confetti" aria-hidden="true">
        {Array.from({ length: 26 }, (_, i) => <i key={i} style={{ '--i': i } as React.CSSProperties} />)}
      </div>
      <header className="screen-head">
        <span />
        <span />
        <SoundToggle />
      </header>
      <div className="end-body">
        <Pip pose="party" className="end-pip" />
        <div className="end-main">
          <h1 ref={h} tabIndex={-1} className="end-title">The end!<br />You made a story!</h1>
          {finishing && <p className="muted" role="status">Pip is still finishing the last checks.</p>}
          {earned.length > 0 && (
            <section className="sticker-sheet" aria-label="Promises Pip kept">
              <h2>Pip kept these promises</h2>
              <ul>
                {earned.map((f) => (
                  <li key={f.id} className="sticker">
                    <img src={`/assets/stickers/${f.sticker}.svg`} alt="" width={96} height={96} />
                    <span>{f.kid}</span>
                  </li>
                ))}
                <li className="sticker praise"><img src={`/assets/stickers/praise-${pick(story.storyId)}.webp`} alt="You did it!" width={112} height={112} /></li>
              </ul>
            </section>
          )}
          <div className="end-actions">
            <Btn big icon="book-open-text" onClick={onAgain}>Read again</Btn>
            <Btn big variant="leaf" icon="plus" onClick={onNew}>Make another</Btn>
          </div>
          <button type="button" className="quiet-link" onClick={onGrownups}><Icon name="lock" /> Grown-ups</button>
        </div>
      </div>
    </main>
  );
}
