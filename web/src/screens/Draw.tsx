import { useCallback, useEffect, useRef, useState } from 'react';
import { getFixtures } from '../api/client';
import type { Fixture } from '../api/types';
import { Btn } from '../components/Btn';
import { ConfirmPictures } from '../components/ConfirmPictures';
import { DrawCanvas, type DrawHandle } from '../components/DrawCanvas';
import { Icon } from '../components/Icon';
import { Pip } from '../components/Pip';
import { BRUSHES, CRAYONS, ERASER } from '../components/palette';
import { SoundToggle } from '../components/SoundToggle';
import { say, sfx } from '../lib/sound';
import { useFocusHeading, type Source } from '../state/session';

const MAX_SIDE = 1024;

/** A photo of a paper drawing, scaled down to 1024 px and re-encoded (which also drops any metadata). */
async function preparephoto(file: File): Promise<Blob> {
  const bmp = await createImageBitmap(file); // honours the photo's rotation
  const scale = Math.min(1, MAX_SIDE / Math.max(bmp.width, bmp.height));
  const c = document.createElement('canvas');
  c.width = Math.round(bmp.width * scale);
  c.height = Math.round(bmp.height * scale);
  const ctx = c.getContext('2d')!;
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, c.width, c.height);
  ctx.drawImage(bmp, 0, 0, c.width, c.height);
  return new Promise((res, rej) => c.toBlob((b) => (b ? res(b) : rej(new Error('encode'))), 'image/jpeg', 0.9));
}

// 6.2 Draw. Crayons, three brush sizes, undo, start over (asks with pictures), a photo of a paper drawing, and sample drawings.
export function Draw({ initial, onDone, onBack }: { initial: Source | null; onDone(s: Source): void; onBack(): void }) {
  const h = useFocusHeading<HTMLHeadingElement>();
  const pad = useRef<DrawHandle>(null);
  const [color, setColor] = useState<string>(CRAYONS[0].id);
  const [brush, setBrush] = useState<number>(1);
  const [ink, setInk] = useState(0);
  const [confirmClear, setConfirmClear] = useState(false);
  const [preview, setPreview] = useState<Source | null>(initial && initial.kind !== 'canvas' ? initial : null);
  const [samples, setSamples] = useState<Fixture[]>([]);
  const [hint, setHint] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let live = true;
    getFixtures().then((f) => { if (live) setSamples(f.filter((x) => x.kind === 'benign')); }).catch(() => { /* samples are a bonus: stay quiet */ });
    return () => { live = false; };
  }, []);

  const hex = color === ERASER.id ? ERASER.hex : CRAYONS.find((c) => c.id === color)!.hex;
  const onChange = useCallback((n: number) => { setInk(n); if (n) setHint(''); }, []);

  const finish = async () => {
    if (preview) { onDone(preview); return; }
    if (!pad.current?.hasInk()) { setHint('Draw your hero first!'); say('keep-drawing'); return; }
    setBusy(true);
    try {
      const blob = await pad.current.toBlob();
      onDone({ kind: 'canvas', blob, url: URL.createObjectURL(blob) });
    } catch {
      setHint('Hmm, Pip could not save that. Try once more!');
    } finally {
      setBusy(false);
    }
  };

  const pickPhoto = async (file: File | undefined) => {
    if (!file) return;
    if (!file.type.startsWith('image/') || file.size > 30 * 1024 * 1024) { setHint('Pip can only open a picture. Try another one!'); return; }
    try {
      const blob = await preparephoto(file);
      setPreview({ kind: 'photo', blob, url: URL.createObjectURL(blob) });
      setHint('');
    } catch {
      setHint('Hmm, Pip could not open that picture. Try another one!');
    }
  };

  const brushPx = BRUSHES[brush].px;

  return (
    <main className="screen draw">
      <header className="screen-head">
        <button type="button" className="corner-btn" onClick={onBack} aria-label="Back to the start"><Icon name="arrow-left" /></button>
        <div className="head-pip"><Pip pose="happy" /></div>
        <h1 ref={h} tabIndex={-1} className="say">Draw your hero!</h1>
        <SoundToggle />
      </header>

      <div className="draw-body">
        <div className="stage-col">
          <div className="sheet" data-preview={!!preview}>
            {preview ? <img className="sheet-img" src={preview.url} alt={preview.kind === 'sample' ? `Sample drawing: ${preview.label}` : 'Your picture'} /> : (
              <DrawCanvas ref={pad} color={hex} size={brushPx} onChange={onChange} label="Drawing page. Draw with a finger, a pen or a mouse." />
            )}
          </div>
          {!preview && (
            <div className="tray" role="group" aria-label="Crayons">
              {CRAYONS.map((c) => (
                <button key={c.id} type="button" className="crayon" aria-pressed={color === c.id} aria-label={c.name} data-color={c.id}
                  onClick={() => { setColor(c.id); sfx('select'); }}>
                  <img src={`/assets/crayons/${c.id}.webp`} alt="" draggable={false} />
                </button>
              ))}
              <button type="button" className="crayon crayon-eraser" aria-pressed={color === ERASER.id} aria-label="Eraser" onClick={() => { setColor(ERASER.id); sfx('select'); }}>
                <img src="/assets/ui/eraser.webp" alt="" draggable={false} />
              </button>
            </div>
          )}
        </div>

        <aside className="tools" aria-label="Drawing tools">
          {!preview ? (
            <>
              <div className="brushes" role="group" aria-label="Brush size">
                {BRUSHES.map((b, i) => (
                  <button key={b.id} type="button" className="brush" aria-pressed={brush === i} aria-label={b.name} onClick={() => { setBrush(i); sfx('select'); }}>
                    <i style={{ width: b.dot, height: b.dot }} />
                  </button>
                ))}
              </div>
              <div className="tool-row">
                <Btn variant="paper" round icon="arrow-counter-clockwise" aria-label="Undo" disabled={!ink} onClick={() => pad.current?.undo()} />
                <Btn variant="paper" round icon="trash" aria-label="Start over" disabled={!ink} onClick={() => setConfirmClear(true)} />
                <label className="btn btn-paper btn-round file-btn" aria-label="Use a photo of a paper drawing">
                  <Icon name="camera" />
                  <input type="file" accept="image/*" onChange={(e) => { pickPhoto(e.target.files?.[0]); e.target.value = ''; }} />
                </label>
              </div>
            </>
          ) : (
            <Btn variant="paper" icon="paint-brush" onClick={() => setPreview(null)}>Draw my own</Btn>
          )}
          <Btn big icon="star" onClick={finish} disabled={busy} aria-disabled={!preview && !ink} className={!preview && !ink ? 'is-soft' : ''}>Done!</Btn>
          <p className="hint" role="status" aria-live="polite">{hint}</p>
        </aside>

        {samples.length > 0 && (
          <section className="samples" aria-label="Sample drawings">
            <h2>Or try a sample drawing</h2>
            <ul>
              {samples.map((f) => (
                <li key={f.id}>
                  <button type="button" className="sample" aria-label={`Use the sample drawing: ${f.label}`}
                    data-selected={preview?.kind === 'sample' && preview.id === f.id}
                    onClick={() => { setPreview({ kind: 'sample', id: f.id, url: f.url, label: f.label, fkind: f.kind }); sfx('select'); }}>
                    <img src={f.url} alt="" loading="lazy" width={96} height={72} />
                  </button>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>

      {confirmClear && (
        <ConfirmPictures title="Start over?" yesLabel="Yes, start over" noLabel="Keep drawing" onNo={() => setConfirmClear(false)} onYes={() => { pad.current?.clear(); setConfirmClear(false); }} />
      )}
    </main>
  );
}
