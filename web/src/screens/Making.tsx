import { useEffect, useRef, useState } from 'react';
import { Btn } from '../components/Btn';
import { ConfirmPictures } from '../components/ConfirmPictures';
import { Icon } from '../components/Icon';
import { Pip } from '../components/Pip';
import { PromiseSheet } from '../components/PromiseSheet';
import { SoundToggle } from '../components/SoundToggle';
import { Stones } from '../components/Stones';
import { say, sfx } from '../lib/sound';
import { stepLine, stepPose, stepVoice } from '../lib/steps';
import { useFocusHeading, type Source } from '../state/session';
import { pageReady, type StoryState } from '../state/storyReducer';

// 6.5 Making your story. Progress is told through Pip and follows the real events: no percentage, no countdown, no timer.
// A page opens only when everything for it exists: its final words, its picture and its voice. The child never sees a page half made.
export function Making({ story, source, lessonTitle, onRead, onCancel, onRetry }: {
  story: StoryState; source: Source | null; lessonTitle?: string; onRead(): void; onCancel(): void; onRetry(): void;
}) {
  const h = useFocusHeading<HTMLHeadingElement>();
  const [confirm, setConfirm] = useState(false);
  const line = stepLine(story);
  const firstReady = pageReady(story, 1);
  const allReady = Array.from({ length: story.totalPages }, (_, i) => pageReady(story, i + 1)).every(Boolean);
  const voice = stepVoice(story);
  const said = useRef('');

  useEffect(() => { // Pip's recorded voice, only when sound is on (say() checks), and each line at most once in a row
    if (voice && voice !== said.current) { said.current = voice; say(voice); }
  }, [voice]);
  useEffect(() => { if (firstReady) sfx('happy-chime'); }, [firstReady]);

  const lost = story.net === 'lost';
  const failed = story.phase === 'error';

  return (
    <main className="screen making" data-step={story.step.kind} data-page={story.step.index ?? ''}>
      <header className="screen-head">
        <button type="button" className="corner-btn" onClick={() => setConfirm(true)} aria-label="Stop and go back to the start"><Icon name="door" /></button>
        <span />
        <SoundToggle />
      </header>

      <h1 ref={h} tabIndex={-1} className="sr-only">Making your story</h1>
      <Stones story={story} />

      <div className="making-grid">
        <section className="making-pip" aria-label="Pip">
          <div className="bubble big" aria-live="polite" aria-atomic="true" data-testid="step-line">{failed ? 'Oops, Pip dropped a page. One moment!' : lost ? 'No internet. Let’s try again!' : line}</div>
          <Pip pose={failed || lost ? 'shy' : stepPose(story)} className="making-pip-art" />
          {story.net === 'reconnecting' && !lost && <p className="muted center" role="status">Pip is finding the way back…</p>}
          {lost && <Btn variant="sky" icon="arrows-clockwise" onClick={onRetry}>Try again</Btn>}
          {failed && <Btn variant="sky" icon="arrows-clockwise" onClick={onCancel}>Start again</Btn>}
          {firstReady && !failed && (
            <Btn big icon="book-open-text" className="read-now" onClick={onRead}>
              Read page 1!
            </Btn>
          )}
          {firstReady && story.phase === 'running' && !allReady && <p className="muted center">Pip is still getting the other pages ready.</p>}
        </section>

        <section className="making-stage" aria-label="Your hero">
          <figure className="frame hero-frame small">
            {source && <img src={source.url} alt="Your drawing" />}
          </figure>
          {story.card && (
            <p className="hero-line">
              Meet <strong>{story.card.name}</strong>{story.card.species ? <> the {story.card.species}</> : null}!
            </p>
          )}
        </section>

        <PromiseSheet story={story} lessonTitle={lessonTitle} />
      </div>

      {confirm && (
        <ConfirmPictures title="Stop making this story?" yesLabel="Yes, stop" noLabel="Keep going" pose="shy" onNo={() => setConfirm(false)} onYes={onCancel} />
      )}
    </main>
  );
}
