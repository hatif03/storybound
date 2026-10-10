import { useEffect } from 'react';
import { Btn } from '../components/Btn';
import { Icon } from '../components/Icon';
import { Pip } from '../components/Pip';
import { SoundToggle } from '../components/SoundToggle';
import { say } from '../lib/sound';
import { useFocusHeading } from '../state/session';
import { isRedraw, type StoryState } from '../state/storyReducer';

// 6.6 The calm refusal / redraw screen. Never blames, never says what was wrong, never alarming. The reason code lives only in the
// grown-ups area. The words under the heading are the backend's own calm message (run.refused.message).
export function Refusal({ story, onAgain, onGrownups }: { story: StoryState; onAgain(): void; onGrownups(): void }) {
  const h = useFocusHeading<HTMLHeadingElement>();
  const redraw = isRedraw(story.refusal?.reasonCode);
  useEffect(() => { say(redraw ? 'refusal-2' : 'refusal-1'); }, [redraw]);
  return (
    <main className="screen refusal" data-kind={redraw ? 'redraw' : 'calm'}>
      <header className="screen-head">
        <span />
        <span />
        <SoundToggle />
      </header>
      <div className="refusal-body">
        <Pip pose="comfort" className="refusal-pip" />
        <div className="refusal-text">
          <h1 ref={h} tabIndex={-1}>{redraw ? 'Let’s draw a bigger hero!' : 'Let’s try a different drawing!'}</h1>
          <p className="calm-message">{story.refusal?.message}</p>
          <Btn big icon="paint-brush" onClick={onAgain}>Draw again</Btn>
        </div>
      </div>
      <button type="button" className="quiet-link corner-link" onClick={onGrownups}><Icon name="lock" /> Grown-ups</button>
    </main>
  );
}
