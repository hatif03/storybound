// The event stream. Real mode: server-sent events (the browser resends Last-Event-ID itself when it reconnects; if the
// connection is closed for good we reopen it, and the reducer ignores events it has already seen). Demo mode: a timed replay.
import { EVENT_TYPES, type StoryEvent } from './types';
import { MOCK, MOCK_SPEED, mockEvents } from '../mock/mockApi';
import type { Net } from '../state/storyReducer';

export interface Connection { close(): void; retry(): void }
interface Handlers { onEvent(ev: StoryEvent): void; onNet(net: Net): void }

const TERMINAL = new Set(['run.finished', 'run.refused', 'error']);
const MAX_FAILURES = 5;

export function connectEvents(storyId: string, h: Handlers): Connection {
  return MOCK ? replay(h) : live(storyId, h);
}

function live(storyId: string, h: Handlers): Connection {
  const url = `/api/stories/${encodeURIComponent(storyId)}/events`;
  let es: EventSource | null = null;
  let closed = false;
  let failures = 0;
  let timer: ReturnType<typeof setTimeout> | undefined;

  const stop = () => { es?.close(); es = null; clearTimeout(timer); };

  const open = () => {
    if (closed) return;
    stop();
    const src = new EventSource(url);
    es = src;
    src.onopen = () => { failures = 0; h.onNet('ok'); };
    for (const type of EVENT_TYPES) {
      src.addEventListener(type, (m) => {
        failures = 0;
        let ev: StoryEvent;
        try {
          ev = JSON.parse((m as MessageEvent).data) as StoryEvent;
        } catch {
          return; // a garbled line must never break the story
        }
        if (ev.id === undefined && (m as MessageEvent).lastEventId) ev.id = Number((m as MessageEvent).lastEventId);
        h.onEvent(ev);
        if (TERMINAL.has(type)) { closed = true; stop(); } // otherwise the browser would reconnect after the server hangs up
      });
    }
    src.onerror = () => {
      if (closed) return;
      failures++;
      if (failures >= MAX_FAILURES) { stop(); h.onNet('lost'); return; }
      h.onNet('reconnecting');
      if (src.readyState === EventSource.CLOSED) timer = setTimeout(open, Math.min(1000 * failures, 5000)); // e.g. a 404 while the server restarts
    };
  };

  open();
  return {
    close: () => { closed = true; stop(); },
    retry: () => { failures = 0; closed = false; h.onNet('reconnecting'); open(); },
  };
}

/** Replays a recorded run at its own pace, divided by ?speed. A single quiet stretch is capped at 30 s of real time. */
function replay(h: Handlers): Connection {
  const list = mockEvents();
  let timer: ReturnType<typeof setTimeout> | undefined;
  let i = 0;
  let stopped = false;
  const next = () => {
    if (stopped || i >= list.length) return;
    const ev = list[i];
    const prev = i === 0 ? 0 : list[i - 1].t;
    const wait = i === 0 ? 400 : Math.min(30_000, ((ev.t - prev) * 1000) / MOCK_SPEED);
    timer = setTimeout(() => {
      if (stopped) return;
      h.onEvent(ev);
      i++;
      next();
    }, wait);
  };
  next();
  return { close: () => { stopped = true; clearTimeout(timer); }, retry: () => {} };
}
