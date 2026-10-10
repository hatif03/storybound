import { Btn } from '../components/Btn';
import { Icon } from '../components/Icon';
import { PipSays } from '../components/Pip';
import { SoundToggle } from '../components/SoundToggle';
import { say, unlock } from '../lib/sound';
import { useFocusHeading } from '../state/session';

// 6.1 Welcome. The big button is also the audio unlock: the first tap lets later pages read themselves aloud.
export function Welcome({ onStart, onGrownups }: { onStart(): void; onGrownups(): void }) {
  const h = useFocusHeading<HTMLHeadingElement>();
  return (
    <main className="screen welcome">
      <div className="corners">
        <button type="button" className="corner-btn corner-quiet" onClick={onGrownups} aria-label="Grown-ups area">
          <Icon name="lock" />
          <span className="corner-text">Grown-ups</span>
        </button>
        <SoundToggle />
      </div>
      <h1 ref={h} tabIndex={-1} className="sr-only">Storybound</h1>
      <img className="wordmark" src="/assets/brand/wordmark.svg" alt="" width={360} height={110} />
      <PipSays pose="happy" className="welcome-pip">Hi! Let&apos;s make a story!</PipSays>
      <Btn big icon="play" onClick={() => { unlock(); say('draw'); onStart(); }} className="welcome-go">Let&apos;s go!</Btn>
      <p className="tagline">Draw a hero. Pip writes the story.</p>
    </main>
  );
}
