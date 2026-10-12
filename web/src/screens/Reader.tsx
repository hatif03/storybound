import { useEffect, useRef, useState } from 'react';
import type { Choice, Page } from '../api/types';
import { Btn } from '../components/Btn';
import { ConfirmPictures } from '../components/ConfirmPictures';
import { Icon } from '../components/Icon';
import { Pip } from '../components/Pip';
import { SoundToggle } from '../components/SoundToggle';
import { Stones } from '../components/Stones';
import { nowPlaying, play, say, sfx, stop, subscribePlaying } from '../lib/sound';
import { stepLine } from '../lib/steps';
import { useSettings } from '../state/settings';
import { useFocusHeading, type Source } from '../state/session';
import { audioStatus, imageStatus, isDone, pageReady, type StoryState } from '../state/storyReducer';

// 6.7 The story reader. Works with whatever has arrived: a page can be read before its picture or voice exists, and a page
// whose picture or voice never comes is a calm text-only page (never an error).

/** How long the picture is looked at before the page starts reading itself. */
export const AUTOPLAY_DELAY_MS = 1800;

function usePlaying(url: string | undefined): boolean {
  const [now, setNow] = useState<string | null>(nowPlaying());
  useEffect(() => subscribePlaying(setNow), []);
  return !!url && now === url;
}

function Picture({ story, page, source }: { story: StoryState; page: Page; source: Source | null }) {
  const status = imageStatus(story, page.index);
  const url = story.media[page.index]?.image;
  const [broken, setBroken] = useState(false);
  useEffect(() => setBroken(false), [url]);
  return (
    <figure className="picture" data-status={broken ? 'missing' : status}>
      {status === 'ready' && !broken ? (
        <img src={url} alt={page.scenario} onError={() => setBroken(true)} />
      ) : status === 'pending' && !broken ? (
        <div className="paper-cut" role="status">
          <Pip pose="bubble" className="cut-pip" />
          <p>Pip is still painting this picture…</p>
        </div>
      ) : (
        <div className="paper-cut">
          <Pip pose="read" className="cut-pip" />
          <p>{story.degradations.some((d) => d.what === 'image' && d.index === page.index && /kept its picture budget|paints some pages only/.test(d.why))
            ? 'Pip saved the paint for the big moments. Listen to this page!'
            : 'No picture on this page. The words still tell the story!'}</p>
        </div>
      )}
      {source && <img className="hero-sticker" src={source.url} alt="" />}
    </figure>
  );
}

function Listen({ story, page }: { story: StoryState; page: Page }) {
  const status = audioStatus(story, page.index);
  const url = story.media[page.index]?.audio;
  const playing = usePlaying(url);
  const [heard, setHeard] = useState(false); // after the page has been read once, the button offers to read it again
  useEffect(() => { if (playing) setHeard(true); }, [playing]);
  if (status === 'missing') {
    return <p className="no-sound"><Icon name="speaker-slash" /> No voice on this page</p>;
  }
  if (status === 'pending') {
    return <p className="no-sound"><Icon name="speaker-high" /> Pip is finding a voice…</p>;
  }
  return (
    <Btn variant="sky" icon={playing ? 'speaker-slash' : heard ? 'arrows-clockwise' : 'speaker-high'} aria-pressed={playing} quiet
      onClick={() => (playing ? stop() : play(url!))} className="listen">
      {playing ? 'Stop' : heard ? 'Listen again' : 'Listen'}
    </Btn>
  );
}

function Waiting({ story, n }: { story: StoryState; n: number }) {
  return (
    <section className="waiting" aria-live="polite">
      <Pip pose="daydream" className="waiting-pip" />
      <h2>Page {n} is on its way!</h2>
      <p>{stepLine(story)}</p>
    </section>
  );
}

export function Reader({ story, source, startAt, onEnd, onLeave }: { story: StoryState; source: Source | null; startAt: number; onEnd(): void; onLeave(): void }) {
  const h = useFocusHeading<HTMLHeadingElement>();
  const { sound } = useSettings();
  const [n, setN] = useState(startAt);
  const [picked, setPicked] = useState<string | null>(null);
  const [leaving, setLeaving] = useState(false);
  const top = useRef<HTMLElement>(null);
  const ready = pageReady(story, n);
  const page = ready ? story.pages.find((p) => p.index === n) : undefined; // a page is shown only when its picture and voice exist too
  const total = story.totalPages;
  const mediaRef = useRef(story.media);
  mediaRef.current = story.media;

  const go = (to: number) => {
    stop();
    if (to > total) { onEnd(); return; }
    if (to < 1) return;
    sfx('page-turn');
    setN(to);
    setPicked(null);
  };

  // New page: scroll to the top, give the child a moment to see the picture, then read the page aloud by itself (a page is only shown once its
  // voice exists, and the first tap on Welcome unlocked audio). The Listen button stays to read it again as often as anyone likes.
  const autoplay = useRef<number>(0);
  useEffect(() => {
    top.current?.scrollIntoView?.({ block: 'start' });
    if (sound && ready) {
      autoplay.current = window.setTimeout(() => {
        const audio = mediaRef.current[n]?.audio;
        if (audio) play(audio);
      }, AUTOPLAY_DELAY_MS);
    }
    return () => { window.clearTimeout(autoplay.current); stop(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [n, ready]);

  // If the story ended without this page (it never arrived), go to the end rather than wait forever.
  useEffect(() => { if (!story.pages.some((p) => p.index === n) && isDone(story)) onEnd(); }, [n, story, onEnd]);

  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement)?.closest?.('input, textarea')) return;
      if (e.key === 'ArrowRight') go(n + 1);
      if (e.key === 'ArrowLeft') go(n - 1);
    };
    window.addEventListener('keydown', key);
    return () => window.removeEventListener('keydown', key);
  });

  const choose = (c: Choice) => {
    setPicked(c.id);
    window.clearTimeout(autoplay.current); // an answer before the story began reading: it does not start afterwards
    stop();
    if (c.is_correct) { sfx('star-pop'); sfx('happy-chime'); say('reader-kind'); } else { sfx('soft-boop'); say('reader-think'); }
  };

  const pickedChoice = page?.choices.find((c) => c.id === picked);
  const hasNext = n < total;

  return (
    <main className="screen reader" data-page={n}>
      <header className="screen-head">
        <button type="button" className="corner-btn" onClick={() => setLeaving(true)} aria-label="Leave the story"><Icon name="door" /></button>
        <Stones story={story} active={n} onPick={(i) => go(i)} />
        <SoundToggle />
      </header>

      <h1 ref={h} tabIndex={-1} className="sr-only">Page {n} of {total}</h1>
      <article className="spread" ref={top} key={n}>
        {page ? (
          <>
            <section className="page page-left" aria-label="Picture">
              <Picture story={story} page={page} source={source} />
            </section>
            <section className="page page-right" aria-label="The story">
              <div className="plate">
                <p className="scenario">{page.scenario}</p>
                <Listen story={story} page={page} />
              </div>
              <h2 className="question">{page.question}</h2>
              <div className="choices" role="group" aria-label="Choices">
                {page.choices.map((c) => {
                  const chosen = picked === c.id;
                  const mood = chosen ? (c.is_correct ? 'kind' : 'think') : 'idle';
                  return (
                    <button key={c.id} type="button" className="choice" data-mood={mood} aria-pressed={chosen} onClick={() => choose(c)}>
                      <span className="choice-badge" aria-hidden="true">
                        {mood === 'kind' ? <Icon name="star" /> : mood === 'think' ? <Icon name="lightbulb" /> : <span>{c.id.toUpperCase()}</span>}
                      </span>
                      <span className="choice-text">{c.text}</span>
                    </button>
                  );
                })}
              </div>
              <div className="feedback-slot" aria-live="polite">
                {pickedChoice && (
                  <div className="feedback" data-mood={pickedChoice.is_correct ? 'kind' : 'think'}>
                    <Pip pose={pickedChoice.is_correct ? 'cool' : 'dizzy'} className="feedback-pip" />
                    <div>
                      <p className="feedback-head">{pickedChoice.is_correct ? 'That was a kind thing to do!' : 'Hmm, let’s think about that.'}</p>
                      <p className="feedback-text">{pickedChoice.feedback}</p>
                    </div>
                  </div>
                )}
              </div>
              {pickedChoice && (
                <div className="after-pick">
                  {!pickedChoice.is_correct && <p className="try-other">Try the other one!</p>}
                  <Btn big iconAfter={hasNext ? 'arrow-right' : 'star'} className="next-inline" onClick={() => go(n + 1)}>{hasNext ? 'Next' : 'The end'}</Btn>
                </div>
              )}
            </section>
          </>
        ) : (
          <Waiting story={story} n={n} />
        )}
      </article>

      {n > 1 && <button type="button" className="side-arrow left" aria-label="Previous page" onClick={() => go(n - 1)}><Icon name="arrow-left" /></button>}
      {(page || hasNext) && <button type="button" className="side-arrow right" aria-label={hasNext ? 'Next page' : 'The end'} onClick={() => go(n + 1)}><Icon name={hasNext ? 'arrow-right' : 'star'} /></button>}

      {leaving && <ConfirmPictures title="Leave the story?" yesLabel="Yes, leave" noLabel="Keep reading" pose="wink" onNo={() => setLeaving(false)} onYes={onLeave} />}
    </main>
  );
}
