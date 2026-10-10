import { useEffect, useRef, useState } from 'react';
import { getFixtures } from '../api/client';
import type { Fixture } from '../api/types';
import { Icon } from '../components/Icon';
import { Pip } from '../components/Pip';
import { MOCK } from '../mock/mockApi';
import { say, setMusic, unlock } from '../lib/sound';
import { setSettings, useSettings } from '../state/settings';
import { useFocusHeading } from '../state/session';
import type { StoryState } from '../state/storyReducer';
import { Receipt } from './Receipt';

const HOLD_MS = 3000;

// The gate: press and hold for three seconds (works with a held Space or Enter key too), or answer a small sum. A gate, not
// consent: the app collects nothing that needs consent.
function Gate({ onOpen, onBack }: { onOpen(): void; onBack(): void }) {
  const h = useFocusHeading<HTMLHeadingElement>();
  const [progress, setProgress] = useState(0);
  const timer = useRef<ReturnType<typeof setInterval>>();
  const t0 = useRef(0);
  const [sum] = useState(() => ({ a: 6 + Math.floor(Math.random() * 4), b: 6 + Math.floor(Math.random() * 4) }));
  const [asking, setAsking] = useState(false);
  const [answer, setAnswer] = useState('');
  const [wrong, setWrong] = useState(false);

  useEffect(() => { unlock(); say('gate'); return () => clearInterval(timer.current); }, []);

  const start = () => {
    if (timer.current) return;
    t0.current = performance.now();
    timer.current = setInterval(() => {
      const p = Math.min(1, (performance.now() - t0.current) / HOLD_MS);
      setProgress(p);
      if (p >= 1) { clearInterval(timer.current); timer.current = undefined; onOpen(); }
    }, 40);
  };
  const cancel = () => { clearInterval(timer.current); timer.current = undefined; setProgress(0); };

  return (
    <main className="screen gate grownup">
      <button type="button" className="g-btn back" onClick={onBack}><Icon name="arrow-left" /> Back to the story</button>
      <div className="gate-card">
        <Pip pose="wink" className="gate-pip" />
        <h1 ref={h} tabIndex={-1}>Grown-ups, hold the button.</h1>
        <p className="muted">This part is for parents and teachers.</p>
        <button
          type="button" className="hold" aria-describedby="hold-help" data-holding={progress > 0}
          onPointerDown={(e) => { e.currentTarget.setPointerCapture(e.pointerId); start(); }}
          onPointerUp={cancel} onPointerCancel={cancel} onContextMenu={(e) => e.preventDefault()}
          onKeyDown={(e) => { if ((e.key === ' ' || e.key === 'Enter') && !e.repeat) { e.preventDefault(); start(); } }}
          onKeyUp={(e) => { if (e.key === ' ' || e.key === 'Enter') cancel(); }}
          onBlur={cancel}
        >
          <svg viewBox="0 0 100 100" aria-hidden="true">
            <circle cx="50" cy="50" r="44" className="ring-bg" />
            <circle cx="50" cy="50" r="44" className="ring" style={{ strokeDashoffset: 276.5 * (1 - progress) }} />
          </svg>
          <Icon name="lock" />
          <span className="hold-label">{progress > 0 ? 'Keep holding…' : 'Hold to open'}</span>
        </button>
        <p id="hold-help" className="muted">Press and hold for three seconds. Using a keyboard? Hold Space.</p>

        {!asking ? (
          <button type="button" className="link" onClick={() => setAsking(true)}>Or answer a question instead</button>
        ) : (
          <form className="sum" onSubmit={(e) => { e.preventDefault(); if (Number(answer) === sum.a * sum.b) onOpen(); else { setWrong(true); setAnswer(''); } }}>
            <label>
              What is {sum.a} × {sum.b}?
              <input inputMode="numeric" autoComplete="off" value={answer} onChange={(e) => { setAnswer(e.target.value.replace(/\D/g, '').slice(0, 3)); setWrong(false); }} />
            </label>
            <button type="submit" className="g-btn primary">Open</button>
            {wrong && <p role="alert" className="muted">Not quite. Try again.</p>}
          </form>
        )}
      </div>
    </main>
  );
}

type Tab = 'receipt' | 'settings' | 'demo' | 'about';

const KIND: Record<string, { name: string; note: string }> = {
  'demo-unsafe': { name: 'Unsafe drawing', note: 'Should be refused calmly: no story is made.' },
  'demo-text': { name: 'Words in the drawing', note: 'Words are ignored; the story still happens.' },
  edge: { name: 'Tricky picture', note: 'Tests the edges of the safety checks.' },
  synthetic: { name: 'Test image', note: 'Blank, tiny or odd files that should ask for a redraw.' },
};

function DemoDrawer({ onUse }: { onUse(f: Fixture): void }) {
  const [list, setList] = useState<Fixture[] | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => { getFixtures().then((f) => setList(f.filter((x) => x.kind !== 'benign'))).catch(() => setFailed(true)); }, []);
  return (
    <section aria-labelledby="demo-title">
      <h2 id="demo-title">Demo drawer</h2>
      <p className="lead">For presenters. These samples test Pip&apos;s checks. They are kept out of the child&apos;s path on purpose, and unsafe ones are listed by name only.</p>
      {failed && <p className="muted">The samples could not be loaded. Is the server running?</p>}
      {!list && !failed && <p className="muted" role="status">Loading…</p>}
      {list && (['demo-unsafe', 'demo-text', 'edge', 'synthetic'] as const).map((k) => {
        const items = list.filter((f) => f.kind === k);
        if (!items.length) return null;
        return (
          <div key={k} className="drawer-group">
            <h3>{KIND[k].name}</h3>
            <p className="muted">{KIND[k].note}</p>
            <ul className="drawer">
              {items.map((f) => (
                <li key={f.id}>
                  <span>{f.label}</span>
                  <button type="button" className="g-btn" onClick={() => onUse(f)}>Use this sample</button>
                </li>
              ))}
            </ul>
          </div>
        );
      })}
    </section>
  );
}

function Switch({ on, label, hint, onToggle }: { on: boolean; label: string; hint: string; onToggle(): void }) {
  return (
    <div className="setting">
      <div><strong>{label}</strong><p className="muted">{hint}</p></div>
      <button type="button" role="switch" aria-checked={on} aria-label={label} className="switch" onClick={onToggle}><i /></button>
    </div>
  );
}

function Settings({ onForget }: { onForget(): void }) {
  const s = useSettings();
  return (
    <section aria-labelledby="set-title">
      <h2 id="set-title">Settings</h2>
      <Switch on={s.sound} label="Sound" hint="Tap sounds, Pip's voice, and pages read aloud as they open. Off by default." onToggle={() => { unlock(); setSettings({ sound: !s.sound, ...(s.sound ? { music: false } : {}) }); if (s.sound) setMusic(false); }} />
      <Switch on={s.music} label="Quiet music" hint="A soft background tune. Needs sound on." onToggle={() => { const next = !s.music; unlock(); setSettings({ music: next, ...(next ? { sound: true } : {}) }); setMusic(next); }} />
      <Switch on={s.calm} label="Calm motion" hint="Less movement. Also follows the device's own setting." onToggle={() => setSettings({ calm: !s.calm })} />
      <div className="setting">
        <div><strong>Text size</strong><p className="muted">For the words in the story.</p></div>
        <div className="seg" role="radiogroup" aria-label="Text size">
          {(['s', 'm', 'l'] as const).map((t) => (
            <button key={t} type="button" role="radio" aria-checked={s.textSize === t} onClick={() => setSettings({ textSize: t })}>{t === 's' ? 'Small' : t === 'm' ? 'Medium' : 'Large'}</button>
          ))}
        </div>
      </div>
      <div className="setting">
        <div><strong>Reader&apos;s age</strong><p className="muted">Sets how simple the words are in the next story.</p></div>
        <select aria-label="Reader's age" value={s.age} onChange={(e) => setSettings({ age: Number(e.target.value) })}>
          {[4, 5, 6, 7, 8].map((a) => <option key={a} value={a}>{a} years</option>)}
        </select>
      </div>
      <div className="setting">
        <div>
          <strong>Forget this story</strong>
          <p className="muted">Deletes the drawing, pictures, narration and movie from this browser tab and from the server. (The neatlogs trace of the run has names and places redacted and expires by itself.)</p>
        </div>
        <button type="button" className="g-btn" onClick={onForget}><Icon name="trash" /> Forget</button>
      </div>
    </section>
  );
}

function About() {
  return (
    <section aria-labelledby="about-title" className="about">
      <h2 id="about-title">About and credits</h2>
      <p>
        Storybound turns a child&apos;s drawing and a lesson into an eight-page story. Before a page is shown, Pip checks it against a list of
        promises (the oath), rewrites it if one is broken, and keeps a receipt of everything.
      </p>
      <h3>Privacy</h3>
      <ul className="plain-list">
        <li>The drawing is kept in this browser tab only, and sent to this server to make the story.</li>
        <li>No accounts, no ads, no tracking, no cookies. Fonts, pictures and sounds are all served from this app.</li>
        <li>The receipt never contains the drawing.</li>
      </ul>
      <h3>Credits</h3>
      <ul className="plain-list">
        <li>Illustrations: Vecteezy.com, Freepik (free licences). Pip the owl: Rive file.</li>
        <li>Fonts: Andika, Fredoka and Atkinson Hyperlegible (SIL Open Font Licence). Icons: Phosphor (MIT).</li>
        <li>Quiet music: a CC0 track. Sample drawings: public domain or CC0 (see the project&apos;s test-drawings notes).</li>
      </ul>
      {MOCK && <p className="muted">Demo mode is on: this is a recording of a real run, replayed.</p>}
    </section>
  );
}

export function Grownups({ story, practice, onBack, onUseSample, onForget }: {
  story: StoryState; practice?: { quiz: { index: number; kind: string; firstTry: boolean }[]; ordered: boolean };
  onBack(): void; onUseSample(f: Fixture): void; onForget(): void;
}) {
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState<Tab>('receipt');
  const h = useRef<HTMLHeadingElement>(null);
  useEffect(() => { if (open) h.current?.focus({ preventScroll: true }); }, [open]);
  if (!open) return <Gate onOpen={() => setOpen(true)} onBack={onBack} />;
  const tabs: [Tab, string][] = [['receipt', 'Receipt'], ['settings', 'Settings'], ['demo', 'Demo drawer'], ['about', 'About']];
  return (
    <main className="screen grownup area">
      <header className="area-head">
        <button type="button" className="g-btn" onClick={onBack}><Icon name="arrow-left" /> Back</button>
        <h1 ref={h} tabIndex={-1}>Grown-ups</h1>
      </header>
      <div className="tabs" role="tablist" aria-label="Grown-ups sections">
        {tabs.map(([id, label]) => (
          <button key={id} type="button" role="tab" id={`tab-${id}`} aria-selected={tab === id} aria-controls={`panel-${id}`} onClick={() => setTab(id)}>{label}</button>
        ))}
      </div>
      <div role="tabpanel" id={`panel-${tab}`} aria-labelledby={`tab-${tab}`} className="panel">
        {tab === 'receipt' && (
          <>
            {practice && (practice.quiz.length > 0 || practice.ordered) && (
              <section className="practice" aria-label="Today's practice">
                <h2>Today&apos;s practice</h2>
                <p>
                  {practice.quiz.length > 0 && <>Quiz: {practice.quiz.filter((r) => r.firstTry).length} of {practice.quiz.length} right on the first try. </>}
                  {practice.ordered && <>Put three pictures of the story in order. </>}
                  <span className="muted">This stays in this browser tab and is never sent anywhere.</span>
                </p>
              </section>
            )}
            <Receipt story={story} />
          </>
        )}
        {tab === 'settings' && <Settings onForget={onForget} />}
        {tab === 'demo' && <DemoDrawer onUse={onUseSample} />}
        {tab === 'about' && <About />}
      </div>
    </main>
  );
}
