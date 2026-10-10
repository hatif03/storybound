import { useEffect, useRef, useState } from 'react';
import { getVideoStatus, startVideo, videoUrl } from '../api/client';
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
  const [movie, setMovie] = useState<'idle' | 'making' | 'done' | 'failed'>('idle');
  const timer = useRef<number | undefined>(undefined);
  useEffect(() => () => window.clearInterval(timer.current), []);
  const makeMovie = async () => {
    if (!story.storyId || movie === 'making') return;
    setMovie('making');
    try {
      const first = await startVideo(story.storyId);
      if (first.status === 'failed') { setMovie('failed'); return; }
      timer.current = window.setInterval(async () => {
        try {
          const s = await getVideoStatus(story.storyId!);
          if (s.status === 'done' || s.status === 'failed') { window.clearInterval(timer.current); setMovie(s.status); }
        } catch { /* keep trying: the movie takes a few minutes */ }
      }, 5000);
    } catch { setMovie('failed'); }
  };
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
          {!finishing && movie !== 'done' && (
            <div className="end-actions">
              <Btn big variant="sun" icon="play" disabled={movie === 'making'} onClick={makeMovie}>
                {movie === 'making' ? 'Pip is making your movie…' : movie === 'failed' ? 'Try the movie again' : 'Make my movie'}
              </Btn>
            </div>
          )}
          {movie === 'making' && <p className="muted" role="status">This takes a few minutes. You can keep reading while Pip works.</p>}
          {movie === 'failed' && <p className="muted" role="status">The movie did not work this time. You can try again.</p>}
          {movie === 'done' && story.storyId && (
            <section className="movie" aria-label="Your movie">
              <video controls preload="metadata" src={videoUrl(story.storyId)} width={640} />
              <a className="g-btn" href={videoUrl(story.storyId)} download="my-story.mp4"><Icon name="play" /> Save the movie</a>
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
