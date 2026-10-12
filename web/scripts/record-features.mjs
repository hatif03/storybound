// Records the feature tour of the app, including the grown-up side, with sound cues and a voice-over: the grown-ups gate, every setting, About,
// the demo drawer, a drawing the app refuses, writing inside a drawing that is ignored, start over and bring it back, a real story (skimmed),
// the read-along movie, the receipt, and Forget. A real story and movie on the real models (about $0.30 with half the pictures).
//   node scripts/record-features.mjs [--url http://127.0.0.1:8000] [--out ../evidence/features-capture/work]
// Needs the voice-over clips: python scripts/make_demo_voiceover.py --texts web/scripts/features-voiceover.json --out evidence/features-capture/voiceover
// Writes the same kind of files as record-demo.mjs (frames, cues.json, the sounds the app played) plus movie.mp4. Then: python scripts/compose_demo.py --work evidence/features-capture ...
import fs from 'node:fs';
import path from 'node:path';
import puppeteer, { ElementHandle } from 'puppeteer-core';

const nativeClick = ElementHandle.prototype.click;
ElementHandle.prototype.click = async function (...a) { await new Promise((r) => setTimeout(r, 450)); return nativeClick.apply(this, a); };

const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const root = path.resolve(import.meta.dirname, '..');
const arg = (name, dflt) => { const i = process.argv.indexOf(`--${name}`); return i > 0 ? process.argv[i + 1] : dflt; };
const BASE = arg('url', 'http://127.0.0.1:8000');
const OUT = path.resolve(root, arg('out', '../evidence/features-capture/work'));
const VO = JSON.parse(fs.readFileSync(path.resolve(root, '../evidence/features-capture/voiceover/manifest.json'), 'utf8')).clips;
fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(path.join(OUT, 'audio'), { recursive: true });

const t0 = Date.now();
const log = (m) => console.log(`[${((Date.now() - t0) / 1000).toFixed(0).padStart(4)}s] ${m}`);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const cues = [];
const problems = [];

const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--hide-scrollbars', '--autoplay-policy=no-user-gesture-required', '--window-size=1440,900'] });
const page = await browser.newPage();
await page.setViewport({ width: 1440, height: 810 });
await page.evaluateOnNewDocument(() => {
  if (!sessionStorage.getItem('storybound.settings')) sessionStorage.setItem('storybound.settings', JSON.stringify({ sound: true, music: false, pictures: 'half' }));
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
    if (!this.closest?.('section.movie')) window.__au.push({ e: 'play', id: ids.get(this), t: Date.now(), src: this.src, vol: this.volume, loop: this.loop });
    const p = orig.apply(this, a);
    if (p && p.catch) p.catch(() => window.__au.push({ e: 'rejected', id: ids.get(this), t: Date.now() }));
    return p;
  };
});
page.on('console', (m) => { if (m.type() === 'error') problems.push(`console: ${m.text().slice(0, 200)}`); });
page.on('pageerror', (e) => problems.push(`pageerror: ${String(e).slice(0, 200)}`));

const framesDir = path.join(OUT, 'frames');
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
async function say(key, gapS = 0.8) {
  const c = VO[key];
  if (!c) throw new Error(`no voice-over clip ${key}`);
  cues.push({ type: 'vo', key, t: Date.now(), seconds: c.seconds });
  log(`voice-over: ${key} (${c.seconds}s)`);
  await sleep((c.seconds + gapS) * 1000);
}
const clickText = async (text, sel = 'button, a', timeout = 30000) => {
  const until = Date.now() + timeout;
  for (;;) {
    const found = await page.waitForFunction((t, s) => [...document.querySelectorAll(s)].some((e) => e.textContent.trim().includes(t) && !e.disabled), { timeout: Math.min(20000, Math.max(1000, until - Date.now())) }, text, sel).then(() => true).catch(() => false);
    if (found) break;
    if (Date.now() >= until) throw new Error(`timed out waiting for a button with "${text}"`);
  }
  await page.evaluate((t, s) => [...document.querySelectorAll(s)].find((e) => e.textContent.trim().includes(t) && !e.disabled).click(), text, sel);
};
const clickSel = async (sel) => { await page.waitForSelector(sel, { timeout: 30000 }); await (await page.$(sel)).click(); };
const scrollBy = (px) => page.evaluate((p) => window.scrollBy({ top: p, behavior: 'smooth' }), px);
const scrollTop = () => page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));

/** The grown-ups gate: answer the multiplication question. */
async function openGate() {
  await page.waitForSelector('.sum, .link', { timeout: 15000 }).catch(() => {});
  await sleep(1500);
  await clickText('Or answer a question instead', 'button');
  const q = await page.evaluate(() => document.querySelector('.sum label').textContent);
  const m = q.match(/(\d+)\s*×\s*(\d+)/);
  await page.type('.sum input', String(Number(m[1]) * Number(m[2])), { delay: 120 });
  await sleep(600);
  await clickText('Open', 'button');
  await page.waitForSelector('[role="tablist"]');
  await sleep(1200);
}
const tab = async (name) => { await clickText(name, '[role="tab"]'); await sleep(1200); };

/** Pick the first sample of a demo-drawer group (0 = refused samples, 1 = writing in the drawing). */
async function useDrawerSample(groupIndex) {
  await page.evaluate((i) => [...document.querySelectorAll('.drawer-group')][i].querySelector('button').click(), groupIndex);
}

async function newStory(lessonText) {
  await page.waitForSelector('input, button[type="submit"]', { timeout: 30000 });
  await sleep(1200);
  await clickText('Pip picks a name');
  await page.waitForSelector('.card', { timeout: 30000 });
  await sleep(1200);
  await clickText(lessonText, '.card');
  await sleep(1500);
  await clickText('Yes!');
}

// ---- 1. the grown-ups area ------------------------------------------------------------------------------------------------------
await page.goto(BASE, { waitUntil: 'networkidle0' });
await sleep(2500);
await page.click('button[aria-label="Grown-ups area"]');
await say('gate', 0.2);
await openGate();

// settings: each one is shown being changed
await tab('Settings');
const settings = say('settings');
await sleep(4000);
await clickSel('button[role="switch"][aria-label="Quiet music"]');
await sleep(2500);
await clickSel('button[role="switch"][aria-label="Quiet music"]');
await sleep(1200);
await clickSel('button[role="switch"][aria-label="Calm motion"]');
await sleep(2000);
await clickSel('button[role="switch"][aria-label="Calm motion"]');
await sleep(1200);
await clickText('Large', 'button[role="radio"]');
await sleep(2500);
await clickText('Medium', 'button[role="radio"]');
await sleep(1200);
await page.select('select[aria-label="Reader\'s age"]', '8');
await sleep(2200);
await page.select('select[aria-label="Reader\'s age"]', '6');
await sleep(1000);
await scrollBy(300);
await sleep(1200);
await page.select('select[aria-label="Pictures"]', 'full');
await sleep(1800);
await page.select('select[aria-label="Pictures"]', 'half');
await settings;
await scrollTop();

await tab('About');
const about = say('about');
await sleep(5000);
await scrollBy(400);
await about;

await tab('Demo drawer');
const drawer = say('drawer');
await sleep(3000);
await scrollBy(450);
await drawer;
await scrollTop();

// ---- 2. a drawing the app refuses -------------------------------------------------------------------------------------------------
await useDrawerSample(0);
await newStory('Sharing');
await page.waitForSelector('.refusal-body', { timeout: 180000 });
log('the refusal screen is up');
await sleep(1000);
await say('unsafe');
await sleep(1500);

// ---- 3. writing inside a drawing is ignored; a real story, skimmed; the movie; the receipt --------------------------------------
await clickText('Grown-ups', 'button');
await openGate();
await tab('Demo drawer');
await sleep(1500);
await useDrawerSample(1);
await page.waitForSelector('input, button[type="submit"]', { timeout: 30000 });
await say('ignored', 0.3);
await newStory('Telling the truth');
log('story started (real models)');

const skimFrom = Date.now();
for (;;) {
  const there = await page.waitForFunction(() => [...document.querySelectorAll('button')].some((e) => e.textContent.includes('Read page 1!') && !e.disabled), { timeout: 20000 }).then(() => true).catch(() => false);
  if (there) break;
  if (Date.now() - skimFrom > 900000) throw new Error('page 1 was never released');
}
await clickText('Read page 1!');
for (let n = 1; n <= 8; n++) {
  for (;;) {
    const shown = await page.waitForSelector('.choice', { timeout: 20000 }).then(() => true).catch(() => false);
    if (shown) break;
    if (Date.now() - skimFrom > 1500000) throw new Error(`page ${n} was never released`);
  }
  await sleep(1200);
  await (await page.$$('.choice'))[0].click();
  await sleep(600);
  if (await page.$('.try-other')) await (await page.$$('.choice'))[1].click();
  await sleep(500);
  await clickText(n < 8 ? 'Next' : 'The end', '.next-inline');
}
// the quiz and the game, skimmed
const hasQuiz = await page.waitForFunction(() => !!document.querySelector('.quiz-body') || document.body.innerText.includes("Play Pip's quiz"), { timeout: 240000 }).then(() => true).catch(() => false);
if (hasQuiz) {
  if (!(await page.$('.quiz-body'))) await clickText("Play Pip's quiz");
  while (await page.$('.quiz-body')) {
    const n = (await page.$$('.quiz-body .choice')).length;
    for (let k = 0; k < n; k++) {
      await sleep(500);
      await (await page.$$('.quiz-body .choice'))[k].click();
      await sleep(700);
      const head = await page.$eval('.look-head', (e) => e.textContent).catch(() => '');
      if (head.includes('Yes!')) break;
    }
    await clickText('Next', '.quiz-body button', 5000).catch(() => clickText('Done!', '.quiz-body button', 5000));
    await sleep(500);
  }
}
await sleep(600);
if (await page.$('.order-tray') || (await page.evaluate(() => [...document.querySelectorAll('button')].some((e) => e.textContent.includes('Put the pictures in order'))))) {
  if (!(await page.$('.order-tray'))) await clickText('Put the pictures in order');
  await page.waitForSelector('.order-tray', { timeout: 20000 });
  for (let slot = 0; slot < 3; slot++) {
    for (const c of await page.$$('.order-card:not([disabled])')) {
      await c.click();
      await sleep(500);
      if ((await page.$$('.slot[data-filled="true"]')).length > slot) break;
    }
  }
  await sleep(600);
  await clickText('Next', 'button');
}
await page.waitForFunction(() => document.body.innerText.includes('The end!'), { timeout: 60000 });
cues.push({ type: 'wait', from: skimFrom, to: Date.now(), label: 'skim' });
log('skimmed the story to its end');
await sleep(800);
await say('skim', 0.2);
await say('end', 0.3);

// the movie
await clickText('Make my movie', 'button', 900000);
const movieFrom = Date.now();
await say('movie_wait', 0.2);
for (let i = 0; i < 120; i++) {
  if (await page.$('section.movie video')) break;
  await sleep(10000);
}
await page.waitForSelector('section.movie video', { timeout: 20000 });
cues.push({ type: 'wait', from: movieFrom + (VO.movie_wait.seconds + 1) * 1000, to: Date.now(), label: 'movie render' });
const src = await page.evaluate(() => document.querySelector('section.movie video').getAttribute('src'));
const movie = Buffer.from(await (await fetch(BASE + src)).arrayBuffer());
fs.writeFileSync(path.join(OUT, 'movie.mp4'), movie);
log(`movie ready in ${((Date.now() - movieFrom) / 1000).toFixed(0)}s (${(movie.length / 1e6).toFixed(1)} MB)`);
await sleep(1500);
await say('movie_play', 0.2);
const playFrom = Date.now();
await page.evaluate(async () => { const v = document.querySelector('section.movie video'); v.scrollIntoView({ block: 'center' }); v.muted = false; v.currentTime = 0; await v.play().catch(() => {}); });
await sleep(14000);
await page.evaluate(() => document.querySelector('section.movie video').pause());
cues.push({ type: 'movie', from: playFrom, to: Date.now(), file: 'movie.mp4' });

// the receipt, slowly
await clickText('Grown-ups', 'button');
await openGate();
await tab('Receipt');
const receiptLine = say('receipt', 0.2);
for (let i = 0; i < 4; i++) { await sleep(3000); await scrollBy(450); }
await receiptLine;
const receipt2 = say('receipt2', 0.2);
for (let i = 0; i < 4; i++) { await sleep(3000); await scrollBy(500); }
await receipt2;
const receiptText = await page.evaluate(() => document.querySelector('[role="tabpanel"]').innerText);
fs.writeFileSync(path.join(OUT, 'receipt.txt'), receiptText);
log(`the receipt mentions the ignored writing: ${/ignored/i.test(receiptText)}`);
await scrollTop();

// fetch the sounds the app played while the story still exists
const au = await page.evaluate(() => window.__au);
const urls = [...new Set(au.filter((e) => e.e === 'play' && e.src).map((e) => e.src))];
const files = {};
for (const u of urls) {
  const r = await fetch(u).catch(() => null);
  if (!r || !r.ok) continue;
  const name = `${Object.keys(files).length}-${path.basename(new URL(u).pathname)}`;
  fs.writeFileSync(path.join(OUT, 'audio', name), Buffer.from(await r.arrayBuffer()));
  files[u] = name;
}
log(`${au.filter((e) => e.e === 'play').length} sounds played, ${Object.keys(files).length} files saved`);

await tab('Settings');
const storyId = await page.evaluate(() => (performance.getEntriesByType('resource').map((r) => r.name).find((n) => /\/api\/stories\/[0-9a-f]+\//.test(n)) || '').split('/')[5]);
const forgetLine = say('forget', 0.3);
await sleep(3000);
await scrollBy(600);
await sleep(1500);
await clickText('Forget', 'button');
await forgetLine;
const after = await page.evaluate(async (id) => (await fetch(`/api/stories/${id}`)).status, storyId);
log(`after Forget, GET /api/stories/${storyId} -> ${after}`);
await sleep(1500);

// ---- 4. the drawing screen: start over, and bring it back ---------------------------------------------------------------------------
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
const drawLine = say('draw', 0.3);
await stroke(circle(0.5, 0.4, 0.15, 0.15));
await stroke(circle(0.5, 0.75, 0.18, 0.2));
await stroke([[0.42, 0.26], [0.4, 0.08], [0.47, 0.24]]);
await sleep(1500);
await page.click('button[aria-label="Start over"]');
await sleep(2500);
await clickText('Bring it back');
await sleep(2500);
await drawLine;
await sleep(1500);

clearInterval(beat);
await cdp.send('Page.stopScreencast');
await Promise.all(writes);
frames.sort((a, b) => a[0] - b[0]);
const endAt = Date.now();
await browser.close();
fs.writeFileSync(path.join(OUT, 'frames.json'), JSON.stringify(frames));
fs.writeFileSync(path.join(OUT, 'cues.json'), JSON.stringify({ recStart, end: endAt, cues, audio: au, files, storyId, forgottenStatus: after, problems: [...new Set(problems)] }, null, 1));
console.log('\nPROBLEMS:', problems.length ? '\n  ' + [...new Set(problems)].join('\n  ') : 'none');
console.log(JSON.stringify({ storyId, forgottenStatus: after }));
