// Records the demo walkthrough of the real app with sound and a voice-over: a real story, real models, no mock.
//   node scripts/record-demo.mjs [--url http://127.0.0.1:8000] [--out ../evidence/app-capture/work]
// Needs: the backend on :8000 serving web/dist, real model keys (about $0.45), ffmpeg at C:/ffmpeg, and the voice-over clips
// (python scripts/make_demo_voiceover.py). Writes cues.json (when each sound played, when each voice-over line
// starts, which stretches are waiting), frames/ with frames.json (the screen, each frame with its real time) and the audio files the app played. Then: python scripts/compose_demo.py
// The headless browser has no sound card, so the sound is rebuilt from the cues: every sound the app played is logged with its time
// (a hook on HTMLMediaElement.play), the files are fetched from the server, and compose_demo.py places each one at its time.
import fs from 'node:fs';
import path from 'node:path';
import puppeteer, { ElementHandle } from 'puppeteer-core';

// The app drops taps that land within 350 ms of a screen change (ghost taps from small hands): wait like a child would.
const nativeClick = ElementHandle.prototype.click;
ElementHandle.prototype.click = async function (...a) { await new Promise((r) => setTimeout(r, 450)); return nativeClick.apply(this, a); };

const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const root = path.resolve(import.meta.dirname, '..');
const arg = (name, dflt) => { const i = process.argv.indexOf(`--${name}`); return i > 0 ? process.argv[i + 1] : dflt; };
const BASE = arg('url', 'http://127.0.0.1:8000');
const OUT = path.resolve(root, arg('out', '../evidence/app-capture/work'));
const VO = JSON.parse(fs.readFileSync(path.resolve(root, '../evidence/app-capture/voiceover/manifest.json'), 'utf8')).clips;
fs.mkdirSync(path.join(OUT, 'audio'), { recursive: true });

const t0 = Date.now();
const log = (m) => console.log(`[${((Date.now() - t0) / 1000).toFixed(0).padStart(4)}s] ${m}`);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const cues = [];
const problems = [];

const browser = await puppeteer.launch({
  executablePath: EDGE, headless: 'new',
  args: ['--hide-scrollbars', '--autoplay-policy=no-user-gesture-required', '--window-size=1440,900'],
});
const page = await browser.newPage();
await page.setViewport({ width: 1440, height: 810 });
// sound on, background music on, a picture on every page (the app's default lets the agent choose the pages; the demo paints all of them)
await page.evaluateOnNewDocument(() => {
  sessionStorage.setItem('storybound.settings', JSON.stringify({ sound: true, music: true, pictures: 'full' }));
  window.__au = [];
  const ids = new WeakMap();
  let n = 0;
  const orig = HTMLMediaElement.prototype.play;
  HTMLMediaElement.prototype.play = function (...a) {
    if (!ids.has(this)) {
      const id = ++n;
      ids.set(this, id);
      this.addEventListener('pause', () => window.__au.push({ e: 'pause', id, t: Date.now() }));
      this.addEventListener('ended', () => window.__au.push({ e: 'ended', id, t: Date.now() }));
    }
    window.__au.push({ e: 'play', id: ids.get(this), t: Date.now(), src: this.src, vol: this.volume, loop: this.loop });
    const p = orig.apply(this, a);
    if (p && p.catch) p.catch(() => window.__au.push({ e: 'rejected', id: ids.get(this), t: Date.now() }));
    return p;
  };
});
page.on('console', (m) => { if (m.type() === 'error') problems.push(`console: ${m.text().slice(0, 200)}`); });
page.on('pageerror', (e) => problems.push(`pageerror: ${String(e).slice(0, 200)}`));
page.on('request', (r) => {
  const u = r.url();
  if (!u.startsWith(BASE) && !u.startsWith('data:') && !u.startsWith('blob:')) problems.push(`off-origin: ${u.slice(0, 120)}`);
});

// The screen is captured as timestamped frames (Chrome's screencast), not through a recorder that compresses time while the screen is still:
// every frame keeps the real clock time it was shown, so compose_demo.py can line the sound up with it exactly.
const framesDir = path.join(OUT, 'frames');
fs.rmSync(framesDir, { recursive: true, force: true });
fs.mkdirSync(framesDir, { recursive: true });
const frames = [];
const writes = [];
const cdp = await page.createCDPSession();
cdp.on('Page.screencastFrame', ({ data, metadata, sessionId }) => {
  const t = Math.round((metadata?.timestamp ?? Date.now() / 1000) * 1000);
  const name = `${String(frames.length).padStart(6, '0')}.jpg`;
  frames.push([t, name]);
  writes.push(fs.promises.writeFile(path.join(framesDir, name), Buffer.from(data, 'base64')));
  cdp.send('Page.screencastFrameAck', { sessionId }).catch(() => {});
});
await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 75, everyNthFrame: 3 });
// A screencast only sends a frame when the compositor draws one and skips some of them, so a screen that changes once and then stays still can be
// missed (found when the receipt never appeared in the video). A frame is also taken every second so no picture is ever more than a second stale.
let beating = false;
const beat = setInterval(async () => {
  if (beating) return;
  beating = true;
  try {
    const t = Date.now();
    const buf = await page.screenshot({ type: 'jpeg', quality: 70 });
    const name = `${String(frames.length).padStart(6, '0')}.jpg`;
    frames.push([t, name]);
    writes.push(fs.promises.writeFile(path.join(framesDir, name), buf));
  } catch { /* the page is changing: the next beat will do */ }
  beating = false;
}, 1000);
const recStart = Date.now();
log('recording started');

// ---- helpers ------------------------------------------------------------------------------------------------------------------
/** Say a voice-over line: it plays (in the finished video) from now, and the screen stays put until it is done. */
async function say(key, gapS = 0.8) {
  const c = VO[key];
  if (!c) throw new Error(`no voice-over clip ${key}`);
  cues.push({ type: 'vo', key, t: Date.now(), seconds: c.seconds });
  log(`voice-over: ${key} (${c.seconds}s)`);
  await sleep((c.seconds + gapS) * 1000);
}
const sayBackground = (key) => { const p = say(key); return p; };

const clickText = async (text, sel = 'button, a', timeout = 30000) => {
  const until = Date.now() + timeout;
  for (;;) {
    const found = await page.waitForFunction((t, s) => [...document.querySelectorAll(s)].some((e) => e.textContent.trim().includes(t) && !e.disabled), { timeout: Math.min(20000, Math.max(1000, until - Date.now())) }, text, sel).then(() => true).catch(() => false);
    if (found) break;
    if (Date.now() >= until) throw new Error(`timed out waiting for a button with "${text}"`);
  }
  await page.evaluate((t, s) => [...document.querySelectorAll(s)].find((e) => e.textContent.trim().includes(t) && !e.disabled).click(), text, sel);
};

const scrollTo = (sel, block) => page.evaluate((s, b) => document.querySelector(s)?.scrollIntoView({ behavior: 'smooth', block: b }), sel, block);

/** Has the page narration (a /pages/N/audio file) finished playing since `since`? */
const narrationDone = (since) => page.evaluate((s) => {
  const ev = window.__au.filter((e) => e.t >= s);
  const play = ev.filter((e) => e.e === 'play' && /\/pages\/\d+\/audio/.test(e.src)).pop();
  if (!play) return 'none';
  return ev.some((e) => e.id === play.id && (e.e === 'ended' || e.e === 'pause') && e.t > play.t) ? 'done' : 'playing';
}, since);

async function waitNarration(since, maxMs = 90000) {
  const began = Date.now();
  const until = began + maxMs;
  let state = 'none';
  while (Date.now() < until) {
    state = await narrationDone(since);
    if (state === 'done') return state;
    if (state === 'none' && Date.now() - began > 6000) return state; // the page had no voice (it starts reading about 1.8 s after it opens)
    await sleep(500);
  }
  return state;
}

// ---- the story ----------------------------------------------------------------------------------------------------------------
await page.goto(BASE, { waitUntil: 'networkidle0' });
await sleep(2500);
await say('intro');
await clickText("Let's go");

await page.waitForSelector('canvas.draw-canvas');
await sleep(2500);
const box = await (await page.$('canvas.draw-canvas')).boundingBox();
const at = (fx, fy) => [box.x + box.width * fx, box.y + box.height * fy];
async function stroke(points) {
  const [x0, y0] = at(...points[0]);
  await page.mouse.move(x0, y0);
  await page.mouse.down();
  for (const p of points.slice(1)) { const [x, y] = at(...p); await page.mouse.move(x, y, { steps: 16 }); }
  await page.mouse.up();
  await sleep(250);
}
const circle = (cx, cy, rx, ry, n = 24) => Array.from({ length: n + 1 }, (_, i) => [cx + rx * Math.cos((2 * Math.PI * i) / n), cy + ry * Math.sin((2 * Math.PI * i) / n)]);
const drawing = (async () => {
  await stroke(circle(0.5, 0.36, 0.14, 0.14));
  await stroke([[0.42, 0.24], [0.4, 0.06], [0.47, 0.22]]);
  await stroke([[0.53, 0.22], [0.6, 0.06], [0.58, 0.24]]);
  await stroke(circle(0.5, 0.72, 0.17, 0.2));
  await stroke([[0.46, 0.34], [0.46, 0.34]]);
  await stroke([[0.55, 0.34], [0.55, 0.34]]);
  await stroke([[0.44, 0.22], [0.5, 0.18], [0.56, 0.22], [0.5, 0.26], [0.44, 0.22]]);
  await stroke([[0.68, 0.62], [0.74, 0.78], [0.78, 0.62], [0.68, 0.62]]);
})();
await Promise.all([say('draw'), drawing]);
await sleep(1500);
await clickText('Done!');

await page.waitForSelector('input, button[type="submit"]', { timeout: 30000 });
await sleep(800);
await say('name');
await clickText('Pip picks a name');

await page.waitForSelector('.card', { timeout: 30000 });
await sleep(1000);
const lessonLine = say('lesson');
await sleep(4000);
await clickText('Sharing', '.card');
await page.evaluate(() => { document.querySelector('details.grownup-promises').open = true; });
await sleep(800);
await page.type('input[aria-label="Grown-up promise 1"]', 'Nobody in the story is left out', { delay: 70 });
await lessonLine;
await sleep(1500);
await clickText('Yes!');
log('story started');

// the Making screen: the agent works; nothing is shown to the child until page 1 has its words, picture and voice
await sleep(1500);
await say('making');
await say('waiting');
const waitFrom = Date.now();
for (;;) { // poll in short waits: one long wait exceeds the browser protocol timeout
  const there = await page.waitForFunction(() => [...document.querySelectorAll('button')].some((e) => e.textContent.includes('Read page 1!') && !e.disabled), { timeout: 20000 }).then(() => true).catch(() => false);
  if (there) break;
  if (Date.now() - waitFrom > 900000) throw new Error('page 1 was never released');
}
cues.push({ type: 'wait', from: waitFrom, to: Date.now() });
log(`first page released after ${((Date.now() - waitFrom) / 1000).toFixed(0)}s of waiting`);
await sleep(2500);
await say('ready');

const TOTAL = 8;
await clickText('Read page 1!');
let waited = 0;
let navAt = Date.now() - 1000; // when the page was asked for: the app starts reading it aloud the moment it shows
for (let n = 1; n <= TOTAL; n++) {
  const w0 = Date.now();
  // the reader holds a page back until its picture and voice exist; poll in short waits (one long wait exceeds the browser protocol timeout)
  for (;;) {
    const shown = await page.waitForSelector('.choice', { timeout: 20000 }).then(() => true).catch(() => false);
    if (shown) break;
    if (Date.now() - w0 > 1200000) throw new Error(`page ${n} was never released`);
  }
  if (Date.now() - w0 > 3000) { cues.push({ type: 'wait', from: w0, to: Date.now(), page: n }); waited++; log(`page ${n} was held back ${((Date.now() - w0) / 1000).toFixed(0)}s`); }
  const shownAt = Date.now() - w0 > 3000 ? Date.now() : Math.min(Date.now(), navAt + 1500); // a held-back page is shown when it is released
  const picture = await page.evaluate(() => document.querySelector('.picture')?.getAttribute('data-status'));
  cues.push({ type: 'page', page: n, t: shownAt, picture });
  const narr = await waitNarration((Date.now() - w0 > 3000 ? shownAt : navAt) - 300); // a held-back page starts reading when it is released
  log(`page ${n}: picture ${picture}, narration ${narr}`);
  await sleep(2500); // ample time to look at the page
  await scrollTo('.question', 'start'); // the page is taller than the screen: bring the question and the choices into view, like a child scrolling
  await sleep(2000);
  const choices = await page.$$('.choice');
  await choices[0].click();
  await sleep(1200);
  await scrollTo('.feedback-slot', 'center');
  const wrong = !!(await page.$('.try-other'));
  if (n === 1) {
    await say(wrong ? 'choice_wrong' : 'choice_right');
  } else if (n === 2) {
    await sleep(2500);
  } else {
    await sleep(2200);
  }
  if (wrong) { const again = await page.$$('.choice'); await again[1].click(); await sleep(1200); await scrollTo('.feedback-slot', 'center'); await sleep(2500); }
  await scrollTo('.next-inline', 'center');
  await sleep(800);
  if (n === 2) await say('pages');
  navAt = Date.now();
  await clickText(n < TOTAL ? 'Next' : 'The end', '.next-inline');
  await sleep(300);
}

// a quiz (only questions that passed every promise), then the picture-order game, then the end
const hasQuiz = await page.waitForFunction(() => !!document.querySelector('.quiz-body') || document.body.innerText.includes("Play Pip's quiz"), { timeout: 240000 }).then(() => true).catch(() => false);
if (hasQuiz) {
  if (!(await page.$('.quiz-body'))) await clickText("Play Pip's quiz");
  await page.waitForSelector('.quiz-body');
  await say('quiz');
  let q = 0;
  while (await page.$('.quiz-body')) {
    q++;
    const n = (await page.$$('.quiz-body .choice')).length;
    for (let k = 0; k < n; k++) {
      await sleep(2500);
      await (await page.$$('.quiz-body .choice'))[k].click();
      await sleep(2500);
      const head = await page.$eval('.look-head', (e) => e.textContent).catch(() => '');
      if (head.includes('Yes!')) break;
    }
    await clickText('Next', '.quiz-body button', 5000).catch(() => clickText('Done!', '.quiz-body button', 5000));
    await sleep(1200);
  }
  log(`quiz played: ${q} questions`);
}
await sleep(800);
if (await page.$('.order-tray') || (await page.evaluate(() => [...document.querySelectorAll('button')].some((e) => e.textContent.includes('Put the pictures in order'))))) {
  if (!(await page.$('.order-tray'))) await clickText('Put the pictures in order');
  await page.waitForSelector('.order-tray', { timeout: 20000 });
  const orderLine = say('order');
  await sleep(2500);
  for (let slot = 0; slot < 3; slot++) {
    for (const c of await page.$$('.order-card:not([disabled])')) {
      await c.click();
      await sleep(1200);
      if ((await page.$$('.slot[data-filled="true"]')).length > slot) break;
    }
  }
  await orderLine;
  await sleep(1500);
  await clickText('Next', 'button');
} else log('no picture-order game offered');
await page.waitForFunction(() => document.body.innerText.includes('The end!'), { timeout: 60000 });
await sleep(1500);
await say('end');

// the grown-ups area: wait until the receipt exists, then open it
for (let i = 0; i < 90; i++) {
  const ready = await page.evaluate(async () => {
    const id = (performance.getEntriesByType('resource').map((r) => r.name).find((n) => /\/api\/stories\/[0-9a-f]+\//.test(n)) || '').split('/')[5];
    return !!id && (await fetch(`/api/stories/${id}/receipt`)).status === 200;
  });
  if (ready) break;
  await sleep(10000);
}
await clickText('Grown-ups', 'button');
await page.waitForSelector('.sum, .link', { timeout: 10000 }).catch(() => {});
await sleep(1500);
await clickText('Or answer a question instead', 'button');
const q = await page.evaluate(() => document.querySelector('.sum label').textContent);
const m = q.match(/(\d+)\s*×\s*(\d+)/);
await page.type('.sum input', String(Number(m[1]) * Number(m[2])), { delay: 120 });
await sleep(800);
await clickText('Open', 'button');
await page.waitForSelector('[role="tablist"]');
await sleep(1500);
const receiptText = await page.evaluate(() => document.querySelector('[role="tabpanel"]').innerText);
fs.writeFileSync(path.join(OUT, 'receipt.txt'), receiptText);
log(`receipt mentions the grown-up promise: ${receiptText.includes('Nobody in the story is left out')}`);
await say('receipt');
await sleep(1500);

// fetch every sound the app played while the story still exists on the server
const au = await page.evaluate(() => window.__au);
const urls = [...new Set(au.filter((e) => e.e === 'play' && e.src).map((e) => e.src))];
const files = {};
for (const u of urls) {
  const b64 = await page.evaluate(async (url) => {
    const r = await fetch(url);
    if (!r.ok) return null;
    const buf = new Uint8Array(await r.arrayBuffer());
    let s = '';
    for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode(...buf.subarray(i, i + 0x8000));
    return btoa(s);
  }, u);
  if (!b64) continue;
  const name = `${Object.keys(files).length}-${path.basename(new URL(u).pathname)}`;
  fs.writeFileSync(path.join(OUT, 'audio', name), Buffer.from(b64, 'base64'));
  files[u] = name;
}
log(`${au.filter((e) => e.e === 'play').length} sounds played, ${Object.keys(files).length} files saved, ${au.filter((e) => e.e === 'rejected').length} rejected`);

await clickText('Settings', '[role="tab"]');
await sleep(1500);
const storyId = await page.evaluate(() => (performance.getEntriesByType('resource').map((r) => r.name).find((n) => /\/api\/stories\/[0-9a-f]+\//.test(n)) || '').split('/')[5]);
const forgetLine = say('forget');
await sleep(2500);
await clickText('Forget', 'button');
await forgetLine;
const after = await page.evaluate(async (id) => (await fetch(`/api/stories/${id}`)).status, storyId);
log(`after Forget, GET /api/stories/${storyId} -> ${after}`);
await sleep(2000);

clearInterval(beat);
await cdp.send('Page.stopScreencast');
await Promise.all(writes);
frames.sort((a, b) => a[0] - b[0]);
const endAt = Date.now();
await browser.close();
fs.writeFileSync(path.join(OUT, 'frames.json'), JSON.stringify(frames));
fs.writeFileSync(path.join(OUT, 'cues.json'), JSON.stringify({ recStart, end: endAt, cues, audio: au, files, storyId, forgottenStatus: after, problems: [...new Set(problems)] }, null, 1));
console.log('\nPROBLEMS:', problems.length ? '\n  ' + [...new Set(problems)].join('\n  ') : 'none');
console.log(JSON.stringify({ storyId, forgottenStatus: after, heldBackPages: waited }));
