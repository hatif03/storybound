import { useEffect, useState } from 'react';
import { getLessons } from '../api/client';
import type { Lesson } from '../api/types';
import { Btn } from '../components/Btn';
import { Icon } from '../components/Icon';
import { Pip } from '../components/Pip';
import { SoundToggle } from '../components/SoundToggle';
import { play, say, sfx } from '../lib/sound';
import { useSettings } from '../state/settings';
import { useFocusHeading } from '../state/session';

const KNOWN_CARDS = new Set(['sharing', 'kindness', 'honesty', 'inclusion', 'patience', 'helping', 'gratitude', 'listening', 'apologizing', 'courage', 'responsibility', 'emotions']);
const HAS_VOICE = new Set(['sharing', 'honesty', 'kindness', 'patience']);

// The backend's icon names (gift, star, heart, clock) are Phosphor names: they are the card picture when a lesson has no card art.
export function PickLesson({ chosen, starting, error, promises, onPromises, onBack, onPick, onGo }: {
  chosen: string | null; starting: boolean; error: string; promises: string[]; onPromises(p: string[]): void;
  onBack(): void; onPick(l: Lesson): void; onGo(): void;
}) {
  const h = useFocusHeading<HTMLHeadingElement>();
  const { sound } = useSettings();
  const [lessons, setLessons] = useState<Lesson[] | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let live = true;
    setLoadError(false);
    getLessons().then((l) => { if (live) setLessons(l); }).catch(() => { if (live) setLoadError(true); });
    return () => { live = false; };
  }, [attempt]);

  const pick = (l: Lesson) => {
    sfx('select');
    if (sound && HAS_VOICE.has(l.id)) play(`/assets/audio/voice/lesson-${l.id}.mp3`); // the card is read aloud on tap
    onPick(l);
  };

  return (
    <main className="screen lesson">
      <header className="screen-head">
        <button type="button" className="corner-btn" onClick={onBack} aria-label="Back"><Icon name="arrow-left" /></button>
        <div className="head-pip"><Pip pose="wink" /></div>
        <h1 ref={h} tabIndex={-1} className="say">What should we learn today?</h1>
        <SoundToggle />
      </header>

      {loadError && (
        <div className="notice" role="status">
          <Pip pose="shy" className="notice-pip" />
          <p>No internet. Let&apos;s try again!</p>
          <Btn variant="sky" icon="arrows-clockwise" onClick={() => setAttempt((n) => n + 1)}>Try again</Btn>
        </div>
      )}
      {!lessons && !loadError && <p className="muted center" role="status">Pip is getting the lesson cards…</p>}

      {lessons && (
        <ul className="cards" role="radiogroup" aria-label="Lessons">
          {lessons.map((l) => (
            <li key={l.id}>
              <button type="button" role="radio" aria-checked={chosen === l.id} className="card" data-chosen={chosen === l.id} onClick={() => pick(l)}>
                <span className="card-art">
                  {KNOWN_CARDS.has(l.id) ? <img src={`/assets/lessons/${l.id}.webp`} alt="" loading="lazy" /> : <Icon name={l.icon || 'book-open-text'} className="card-icon" />}
                </span>
                <span className="card-title">{l.title}</span>
                {chosen === l.id && <span className="card-blurb">{l.blurb}</span>}
                {chosen === l.id && <Icon name="check-circle" className="card-check" />}
              </button>
            </li>
          ))}
        </ul>
      )}

      <details className="grownup-promises">
        <summary>A grown-up can add a promise (optional)</summary>
        <p className="muted">Pip will keep it on every page and check it, like all the other promises. Up to three, for example: “Nobody in the story is left out.”</p>
        {[0, 1, 2].map((i) => (
          <input
            key={i} type="text" maxLength={140} aria-label={`Grown-up promise ${i + 1}`} placeholder={i === 0 ? 'Nobody in the story is left out' : ''}
            value={promises[i] ?? ''}
            onChange={(e) => { const next = [...promises]; next[i] = e.target.value; onPromises(next.slice(0, 3)); }}
          />
        ))}
      </details>

      <div className="confirm-bar" aria-live="polite">
        {error && <p className="problem" role="alert">{error}</p>}
        {chosen ? (
          <Btn big variant="leaf" icon="check-circle" disabled={starting} onClick={() => { say('yes'); onGo(); }}>{starting ? 'Starting…' : 'Yes!'}</Btn>
        ) : (
          <p className="muted">Tap a picture to pick a lesson.</p>
        )}
      </div>
    </main>
  );
}
