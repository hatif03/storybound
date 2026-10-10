import { useEffect, useReducer, useRef, useState } from 'react';
import { ApiError, forgetStory, startStory } from './api/client';
import { connectEvents, type Connection } from './api/events';
import type { Fixture } from './api/types';
import { DemoBadge } from './components/DemoBadge';
import { stop } from './lib/sound';
import { End } from './screens/End';
import { Grownups } from './screens/Grownups';
import { Draw } from './screens/Draw';
import { Making } from './screens/Making';
import { NameHero } from './screens/NameHero';
import { PickLesson } from './screens/PickLesson';
import { Reader } from './screens/Reader';
import { Refusal } from './screens/Refusal';
import { Welcome } from './screens/Welcome';
import { getSettings } from './state/settings';
import { releaseSource, type Screen, type Source } from './state/session';
import { initialStory, storyReducer } from './state/storyReducer';
import { Icon } from './components/Icon';

// The screen machine: welcome -> draw -> name -> lesson -> making -> reader -> end, plus refusal and the grown-ups area.
// Everything the child chose lives in memory only. The story itself is folded from the event stream by storyReducer.
export default function App() {
  const [screen, setScreen] = useState<Screen>('welcome');
  const [back, setBack] = useState<Screen>('welcome'); // where the grown-ups area returns to
  const [source, setSource] = useState<Source | null>(null);
  const [heroName, setHeroName] = useState('');
  const [lessonId, setLessonId] = useState<string | null>(null);
  const [lessonTitle, setLessonTitle] = useState<string | undefined>();
  const [promises, setPromises] = useState<string[]>([]);
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState('');
  const [readFrom, setReadFrom] = useState(1);
  const [story, dispatch] = useReducer(storyReducer, initialStory);
  const conn = useRef<Connection | null>(null);
  const [online, setOnline] = useState(typeof navigator === 'undefined' ? true : navigator.onLine);

  useEffect(() => {
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    window.addEventListener('online', on);
    window.addEventListener('offline', off);
    return () => { window.removeEventListener('online', on); window.removeEventListener('offline', off); };
  }, []);

  const closeStream = () => { conn.current?.close(); conn.current = null; };
  useEffect(() => closeStream, []);

  const go = (s: Screen) => { stop(); setScreen(s); window.scrollTo?.(0, 0); };
  const openGrownups = (from: Screen) => { setBack(from); go('grownups'); };

  const newStory = () => {
    closeStream();
    dispatch({ type: 'reset' });
    releaseSource(source);
    setSource(null);
    setHeroName('');
    setLessonId(null);
    setPromises([]);
    setStartError('');
    go('draw');
  };

  const begin = async () => {
    if (!source || !lessonId || starting) return;
    setStarting(true);
    setStartError('');
    try {
      const { storyId } = await startStory({
        lessonId, age: getSettings().age, heroName: heroName || undefined, promises: promises.map((p) => p.trim()).filter(Boolean),
        drawing: source.kind === 'sample' ? { kind: 'fixture', id: source.id } : { kind: 'file', blob: source.blob, name: source.kind === 'photo' ? 'drawing.jpg' : 'drawing.png' },
      });
      closeStream();
      dispatch({ type: 'reset' });
      conn.current = connectEvents(storyId, { onEvent: (ev) => dispatch({ type: 'event', ev }), onNet: (net) => dispatch({ type: 'net', net }) });
      setReadFrom(1);
      go('making');
    } catch (e) {
      const busy = e instanceof ApiError && e.code === 'busy';
      setStartError(busy ? 'Pip is busy with other stories. Please try again in a minute.' : e instanceof ApiError && e.status === 0 ? 'No internet. Let’s try again!' : 'Oops, Pip dropped a page. Let’s try again!');
    } finally {
      setStarting(false);
    }
  };

  // A refusal arrives as a normal event: move to the calm screen. Never keep the child on the progress screen.
  useEffect(() => { if (story.phase === 'refused' && screen === 'making') go('refusal'); }, [story.phase, screen]);

  const useSample = (f: Fixture) => {
    closeStream();
    dispatch({ type: 'reset' });
    releaseSource(source);
    setSource({ kind: 'sample', id: f.id, url: f.url, label: f.label, fkind: f.kind });
    setLessonId(null);
    go('name');
  };

  const forget = async () => {
    if (story.storyId) await forgetStory(story.storyId).catch(() => { /* the server may already have lost it */ });
    newStory();
    go('welcome');
  };

  let view;
  switch (screen) {
    case 'welcome':
      view = <Welcome onStart={() => go('draw')} onGrownups={() => openGrownups('welcome')} />;
      break;
    case 'draw':
      view = <Draw initial={source} onBack={() => go('welcome')} onDone={(s) => { if (source !== s) releaseSource(source); setSource(s); go('name'); }} />;
      break;
    case 'name':
      view = source ? <NameHero source={source} name={heroName} onRedraw={() => { releaseSource(source); setSource(null); go('draw'); }} onNext={(n) => { setHeroName(n); go('lesson'); }} /> : null;
      break;
    case 'lesson':
      view = <PickLesson chosen={lessonId} starting={starting} error={startError} promises={promises} onPromises={setPromises} onBack={() => go('name')} onPick={(l) => { setLessonId(l.id); setLessonTitle(l.title); }} onGo={begin} />;
      break;
    case 'making':
      view = <Making story={story} source={source} lessonTitle={lessonTitle} onCancel={newStory} onRetry={() => conn.current?.retry()} onRead={() => { setReadFrom(1); go('reader'); }} />;
      break;
    case 'reader':
      view = <Reader story={story} source={source} startAt={readFrom} onEnd={() => go('end')} onLeave={() => go('welcome')} />;
      break;
    case 'end':
      view = <End story={story} lessonTitle={lessonTitle} onAgain={() => { setReadFrom(1); go('reader'); }} onNew={newStory} onGrownups={() => openGrownups('end')} />;
      break;
    case 'refusal':
      view = <Refusal story={story} onAgain={newStory} onGrownups={() => openGrownups('refusal')} />;
      break;
    case 'grownups':
      view = <Grownups story={story} onBack={() => go(back)} onUseSample={useSample} onForget={forget} />;
      break;
  }

  return (
    <div className="app" data-screen={screen}>
      {!online && (
        <div className="offline" role="status"><Icon name="cloud" /> No internet. Pip will keep trying.</div>
      )}
      {view}
      <DemoBadge />
    </div>
  );
}
