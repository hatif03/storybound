import { useState } from 'react';
import { Btn } from '../components/Btn';
import { Icon } from '../components/Icon';
import { PipSays } from '../components/Pip';
import { SoundToggle } from '../components/SoundToggle';
import { say } from '../lib/sound';
import { useFocusHeading, type Source } from '../state/session';

const MAX = 24; // the backend cleans and caps hero names at 24 characters

// 6.3 Name your hero (optional). Pip shows the drawing and asks who it is. Skipping is fine: Pip picks a name from the drawing.
export function NameHero({ source, name, onNext, onRedraw }: { source: Source; name: string; onNext(name: string): void; onRedraw(): void }) {
  const h = useFocusHeading<HTMLHeadingElement>();
  const [value, setValue] = useState(name);
  const clean = value.replace(/\s+/g, ' ').trimStart().slice(0, MAX);
  const go = () => { say('lesson'); onNext(clean.trim()); };
  return (
    <main className="screen name">
      <header className="screen-head">
        <button type="button" className="corner-btn" onClick={onRedraw} aria-label="Use a different picture"><Icon name="arrow-left" /></button>
        <span />
        <SoundToggle />
      </header>
      <div className="name-body">
        <figure className="frame hero-frame">
          <img src={source.url} alt="Your drawing" />
          <Icon name="sparkle" className="sparkle s1" />
          <Icon name="sparkle" className="sparkle s2" />
        </figure>
        <form className="name-form" onSubmit={(e) => { e.preventDefault(); go(); }}>
          <PipSays pose="shocked"><h1 ref={h} tabIndex={-1}>Wow! Who is this?</h1></PipSays>
          <label className="field">
            <span className="field-label">Your hero&apos;s name <em>(you can skip this)</em></span>
            <input
              type="text" value={clean} maxLength={MAX} autoComplete="off" autoCapitalize="words" spellCheck={false} enterKeyHint="next"
              placeholder="Type a name" onChange={(e) => setValue(e.target.value)}
            />
          </label>
          <Btn big iconAfter="arrow-right" type="submit">{clean.trim() ? 'Next' : 'Pip picks a name'}</Btn>
        </form>
      </div>
    </main>
  );
}
