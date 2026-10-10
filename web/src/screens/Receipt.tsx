import { useState } from 'react';
import { Icon } from '../components/Icon';
import { copyText, cost, degradeLine, duration, fieldName } from '../lib/format';
import { FAMILIES, STATE_LABEL, familyOf } from '../lib/promises';
import { isRedraw, keptCounts, type PromiseState, type StoryState } from '../state/storyReducer';

// The parent's receipt. It shows what the backend's receipt says plus the oath and verdicts that arrived as events. It never shows
// the child's drawing, and it never describes unsafe content: a refusal shows a reason code and a trace id only.

const STATE_ICON: Record<PromiseState['state'], string> = {
  kept: 'check-circle', kept_after_fix: 'sparkle', not_kept: 'warning', unchecked: 'info', waiting: 'clock', checking: 'magnifying-glass', fixing: 'sparkle',
};

function Status({ state }: { state: PromiseState['state'] }) {
  return <span className={`status status-${state}`}><Icon name={STATE_ICON[state]} /> {STATE_LABEL[state]}</span>;
}

function CopyButton({ text, label, done }: { text: string; label: string; done: string }) {
  const [state, setState] = useState<'idle' | 'ok' | 'fail'>('idle');
  return (
    <button type="button" className="g-btn" onClick={async () => { setState((await copyText(text)) ? 'ok' : 'fail'); setTimeout(() => setState('idle'), 2500); }}>
      <Icon name="copy" /> {state === 'ok' ? done : state === 'fail' ? 'Could not copy: select the text instead' : label}
      <span className="sr-only" role="status">{state === 'ok' ? done : ''}</span>
    </button>
  );
}

export function Receipt({ story }: { story: StoryState }) {
  const r = story.receipt;

  if (story.phase === 'refused') {
    const redraw = isRedraw(story.refusal?.reasonCode);
    return (
      <section className="receipt" aria-labelledby="rc-title">
        <h2 id="rc-title">{redraw ? 'No story: the drawing needs a redo' : 'No story was made'}</h2>
        <p className="lead">Nothing from this drawing was used to write a story.</p>
        <dl className="facts">
          <div><dt>Reason code</dt><dd><code>{story.refusal?.reasonCode}</code></dd></div>
          <div><dt>Message shown to the child</dt><dd>{story.refusal?.message}</dd></div>
          <div><dt>Trace id</dt><dd><code>{story.refusal?.traceId || 'none'}</code></dd></div>
        </dl>
        <p className="muted">For safety, the child is never told what was found, and this page does not describe it either.</p>
      </section>
    );
  }
  if (!r) {
    return (
      <section className="receipt" aria-labelledby="rc-title">
        <h2 id="rc-title">Receipt</h2>
        <p className="lead">{story.phase === 'running' ? 'Pip is still working. The receipt appears when the story is finished.' : story.phase === 'error' ? 'This story did not finish, so there is no receipt.' : 'There is no story yet. Make one and its receipt will be here.'}</p>
      </section>
    );
  }

  const counts = keptCounts(story);
  const titles = Object.fromEntries(story.promises.map((p) => [p.id, p.title]));
  const json = JSON.stringify(r, null, 2);
  const kind = story.outcome === 'shipped_with_notes' || r.counts.shipped_violations > 0 || (r.broken?.length ?? 0) > 0 ? 'notes' : 'clean';
  const groups = FAMILIES.map((f) => ({ f, ps: story.promises.filter((p) => familyOf(p.id) === f.id) })).filter((g) => g.ps.length);
  const rewritten = r.pages.filter((p) => p.attempts > 1).length;
  const repairsByPage = story.repairs.reduce<Record<number, typeof story.repairs>>((acc, x) => { (acc[x.index] ??= []).push(x); return acc; }, {});
  const safety = story.safety;

  return (
    <section className="receipt" aria-labelledby="rc-title">
      <h2 id="rc-title" className="sr-only">Receipt</h2>
      <p className="lead" data-testid="receipt-plain">{r.plain}</p>
      <p className={`outcome outcome-${kind}`}>
        <Icon name={kind === 'clean' ? 'seal-check' : 'info'} />
        {kind === 'clean' ? 'Every promise that was checked was kept.' : 'Shipped with notes: see below for what was not fully kept.'}
      </p>

      <dl className="stats">
        <div><dt>Promises in the oath</dt><dd>{r.counts.commitments}</dd></div>
        <div><dt>Checked this time</dt><dd>{r.counts.checked ?? counts.kept + counts.keptAfterFix + counts.notKept}</dd></div>
        <div><dt>Pages rewritten</dt><dd>{rewritten}</dd></div>
        <div><dt>Checks run</dt><dd>{r.counts.checks}</dd></div>
        <div><dt>Coverage</dt><dd>{r.coverage.pct}%</dd></div>
        <div><dt>Time</dt><dd>{duration(r.budget.seconds)}</dd></div>
        <div><dt>Cost</dt><dd>{cost(r.budget)}</dd></div>
        <div><dt>Tokens in / out</dt><dd>{r.budget.tokens_in.toLocaleString()} / {r.budget.tokens_out.toLocaleString()}</dd></div>
      </dl>

      <h3>The oath, promise by promise</h3>
      <p className="muted">{counts.kept + counts.keptAfterFix} kept · {counts.notKept} not kept · {counts.unchecked} not checked this time (a check is sometimes skipped to save time).</p>
      {groups.map(({ f, ps }) => (
        <div className="oath-group" key={f.id}>
          <h4>{f.grown}</h4>
          <ul className="oath">
            {ps.map((p) => (
              <li key={p.id} data-state={p.state}>
                <div className="oath-top"><strong>{p.title}</strong><Status state={p.state} /></div>
                <p>{p.plain}</p>
              </li>
            ))}
          </ul>
        </div>
      ))}

      <h3>What Pip rewrote</h3>
      {story.repairs.length === 0 ? <p>Nothing needed rewriting.</p> : (
        <ul className="plain-list">
          {Object.entries(repairsByPage).map(([idx, list]) => (
            <li key={idx}>
              <strong>{Number(idx) === 0 ? 'The hero or the whole story' : `Page ${idx}`}</strong>
              {list.map((x, i) => (
                <p key={i}>
                  Try {x.attempt}: {x.failed.map((id) => titles[id] ?? id).join('; ')}. Why: {x.because}.
                </p>
              ))}
            </li>
          ))}
        </ul>
      )}

      <h3>Safety</h3>
      <p>
        {safety?.action === 'sanitise' || (safety?.ignoredText.length ?? 0) > 0
          ? 'The drawing was checked first. Writing found on it was ignored and never repeated in the story.'
          : 'The drawing was checked first and nothing needed to be removed.'}
      </p>
      {r.ignored_drawing_text.length > 0 && (
        <>
          <h4>Words in the drawing that were ignored</h4>
          <ul className="plain-list">{r.ignored_drawing_text.map((t, i) => <li key={i}>“{t}”</li>)}</ul>
        </>
      )}

      <h3>Pictures and voice</h3>
      {r.degradations.length === 0 ? <p>Every page got its picture and its voice, or the story says plainly that it did not.</p> : (
        <ul className="plain-list">{r.degradations.map((d, i) => <li key={i}>{degradeLine(d)}</li>)}</ul>
      )}

      <h3>Coverage</h3>
      <p>
        {r.coverage.pct}% of what the story produces is covered by at least one promise.
        {r.coverage.uncovered.length > 0 ? ` Not covered: ${r.coverage.uncovered.map(fieldName).join(', ')}.` : ' Nothing is left uncovered.'}
      </p>

      <details className="builders">
        <summary>For builders</summary>
        <dl className="facts">
          <div><dt>Story id</dt><dd><code>{r.story_id}</code></dd></div>
          <div><dt>Arm</dt><dd>{r.arm === 'B1' ? 'B1 (checked and repaired)' : r.arm === 'B0' ? 'B0 (observe only)' : r.arm}</dd></div>
          <div><dt>Oath hash</dt><dd><code>{r.oath_hash}</code></dd></div>
          <div><dt>Trace id</dt><dd><code>{r.trace_id}</code> <CopyButton text={r.trace_id} label="Copy" done="Copied" /></dd></div>
          {r.prompt_version && <div><dt>Prompt version</dt><dd>{r.prompt_version}</dd></div>}
          {r.models && <div><dt>Models</dt><dd>{Object.entries(r.models).map(([k, v]) => `${k}: ${v}`).join(' · ')}</dd></div>}
          <div><dt>Made</dt><dd>{r.generated_at}</dd></div>
        </dl>
      </details>

      <details className="builders">
        <summary>Receipt as JSON</summary>
        <div className="json-actions">
          <CopyButton text={json} label="Copy receipt JSON" done="Copied" />
          <button type="button" className="g-btn" onClick={() => window.print()}><Icon name="printer" /> Print or save as PDF</button>
        </div>
        <pre className="json" tabIndex={0} aria-label="Receipt JSON">{json}</pre>
      </details>
    </section>
  );
}
