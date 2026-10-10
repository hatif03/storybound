import { useEffect, useState } from 'react';
import type { Page, QuizItem } from '../api/types';
import { Btn } from '../components/Btn';
import { Pip } from '../components/Pip';
import { SoundToggle } from '../components/SoundToggle';
import { sfx } from '../lib/sound';
import { useFocusHeading } from '../state/session';
import type { StoryState } from '../state/storyReducer';

export interface QuizResult { index: number; kind: string; firstTry: boolean }

// A quiz that points back at the story. No timer, no lives, no score for the child: a wrong answer shows the line of the
// story that answers it and lets the child try again. Every question was verified against the story before it got here.
export function Quiz({ story, onDone, onBack }: { story: StoryState; onDone(results: QuizResult[]): void; onBack(): void }) {
  const items = story.quiz?.items ?? [];
  const h = useFocusHeading<HTMLHeadingElement>();
  const [i, setI] = useState(0);
  const [tried, setTried] = useState<string[]>([]);
  const [results, setResults] = useState<QuizResult[]>([]);
  const q: QuizItem | undefined = items[i];
  useEffect(() => { setTried([]); }, [i]);
  if (!q) return null;
  const page: Page | undefined = story.pages.find((p) => p.index === q.evidence_page);
  const img = story.media[q.evidence_page]?.image;
  const right = q.options.find((o) => o.is_correct)!;
  const solved = tried.includes(right.id);
  const showLook = tried.length > 0; // any answer shows the line that answers it
  const last = i === items.length - 1;

  const pick = (id: string) => {
    if (solved || tried.includes(id)) return;
    const ok = id === right.id;
    sfx(ok ? 'star-pop' : 'soft-boop');
    if (ok) sfx('happy-chime');
    setTried((t) => [...t, id]);
  };
  const next = () => {
    const rec = { index: q.index, kind: q.kind, firstTry: tried[0] === right.id };
    const all = [...results, rec];
    if (last) onDone(all); else { setResults(all); setI(i + 1); }
  };

  return (
    <main className="screen quiz" data-q={i + 1}>
      <header className="screen-head">
        <button type="button" className="corner-btn" onClick={onBack} aria-label="Skip the quiz">Skip</button>
        <ol className="dots" aria-label={`Question ${i + 1} of ${items.length}`}>
          {items.map((it, k) => <li key={it.index} data-on={k <= i} />)}
        </ol>
        <SoundToggle />
      </header>
      <h1 ref={h} tabIndex={-1} className="sr-only">Quiz question {i + 1} of {items.length}</h1>
      <div className="quiz-body">
        <Pip pose={solved ? 'cool' : tried.length ? 'bubble' : 'wink'} className="quiz-pip" />
        <section>
          <p className="quiz-kicker">Pip asks</p>
          <h2 className="quiz-q">{q.question}</h2>
          <div className="choices" role="group" aria-label="Answers">
            {q.options.map((o) => {
              const was = tried.includes(o.id);
              const mood = was ? (o.is_correct ? 'kind' : 'think') : 'idle';
              return (
                <button key={o.id} type="button" className="choice" data-mood={mood} aria-pressed={was} disabled={solved && !was} onClick={() => pick(o.id)}>
                  <span className="choice-badge" aria-hidden="true"><span>{o.id.toUpperCase()}</span></span>
                  <span className="choice-text">{o.text}</span>
                </button>
              );
            })}
          </div>
          <div className="look" aria-live="polite">
            {showLook && (
              <blockquote className="look-card">
                {img && <img src={img} alt="" />}
                <div>
                  <p className="look-head">{solved ? 'Yes! Here is where the story says so.' : 'Good try! Let’s look at the story.'}</p>
                  <p className="look-quote">“{q.evidence_quote}”</p>
                  {!solved && page && <p className="muted">Page {page.index}</p>}
                </div>
              </blockquote>
            )}
          </div>
          {solved && <Btn big iconAfter={last ? 'star' : 'arrow-right'} onClick={next}>{last ? 'Done!' : 'Next'}</Btn>}
        </section>
      </div>
    </main>
  );
}
