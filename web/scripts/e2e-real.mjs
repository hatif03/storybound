// A real story through the real app: draw, lesson, a grown-up promise, read every page, make the movie, forget the story.
// Needs the backend on :8000 serving web/dist (npm run build), real model keys; costs about $0.40 plus about $0.04 for the movie.
//   node scripts/e2e-real.mjs [--url http://127.0.0.1:8000] [--out shots/e2e] [--no-video] [--record file.webm]
// --record saves a screen capture of the whole run (puppeteer's screencast; needs ffmpeg at C:/ffmpeg/ffmpeg.exe).
// Prints a step log and every console error, failed request or request that leaves the app's own origin.
import fs from 'node:fs';
import path from 'node:path';
import puppeteer, { ElementHandle } from 'puppeteer-core';
// The app drops taps that land within 350 ms of a screen change (ghost taps from small hands): a script that clicks the moment an
// element appears has to wait like a child would.
const nativeClick = ElementHandle.prototype.click;
ElementHandle.prototype.click = async function (...a) { await new Promise((r) => setTimeout(r, 450)); return nativeClick.apply(this, a); };

const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const root = path.resolve(import.meta.dirname, '..');
const arg = (name, dflt) => { const i = process.argv.indexOf(`--${name}`); return i > 0 ? process.argv[i + 1] : dflt; };
const BASE = arg('url', 'http://127.0.0.1:8000');
const OUT = path.resolve(root, arg('out', 'shots/e2e'));
const VIDEO = !process.argv.includes('--no-video');
const DWELL = Number(arg('dwell', '0')); // seconds spent on each page, like a child reading (0 = click straight through)
const PICTURES = arg('pictures', 'full'); // full | half | none: the illustration policy
fs.mkdirSync(OUT, { recursive: true });

const t0 = Date.now();
const log = (m) => console.log(`[${((Date.now() - t0) / 1000).toFixed(0).padStart(4)}s] ${m}`);
const problems = [];
const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--hide-scrollbars'] });
const page = await browser.newPage();
await page.setViewport({ width: 1280, height: 800 });
page.on('console', (m) => { if (m.type() === 'error') problems.push(`console: ${m.text().slice(0, 200)}`); });
page.on('pageerror', (e) => problems.push(`pageerror: ${String(e).slice(0, 200)}`));
page.on('requestfailed', (r) => problems.push(`failed: ${r.url().slice(0, 120)}`));
page.on('request', (r) => {
  const u = r.url();
  if (!u.startsWith(BASE) && !u.startsWith('data:') && !u.startsWith('blob:')) problems.push(`off-origin: ${u.slice(0, 120)}`);
});
const REC = arg('record', '');
const recorder = REC ? await page.screencast({ path: REC, ffmpegPath: 'C:/ffmpeg/ffmpeg.exe' }) : null;
const shot = (name) => page.screenshot({ path: path.join(OUT, `${name}.png`) });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const clickText = async (text, sel = 'button, a', timeout = 30000) => {
  // poll in short waits: one long wait exceeds the browser protocol timeout
  const until = Date.now() + timeout;
  for (;;) {
    const found = await page.waitForFunction((t, s) => [...document.querySelectorAll(s)].some((e) => e.textContent.trim().includes(t) && !e.disabled), { timeout: Math.min(20000, Math.max(1000, until - Date.now())) }, text, sel).then(() => true).catch(() => false);
    if (found) break;
    if (Date.now() >= until) throw new Error(`timed out waiting for a button with "${text}"`);
  }
  await page.evaluate((t, s) => [...document.querySelectorAll(s)].find((e) => e.textContent.trim().includes(t) && !e.disabled).click(), text, sel);
};

await page.goto(BASE, { waitUntil: 'networkidle0' });
if (PICTURES !== 'full') { // the grown-up setting lives in sessionStorage and is read at load
  await page.evaluate((v) => sessionStorage.setItem('storybound.settings', JSON.stringify({ pictures: v })), PICTURES);
  await page.reload({ waitUntil: 'networkidle0' });
}
await shot('01-welcome');
log('welcome');
await clickText("Let's go");

// draw a simple bunny with the mouse: head, ears, body, bow and carrot
await page.waitForSelector('canvas.draw-canvas');
await sleep(2500); // the screen animates in: measure after it settles
const box = await (await page.$('canvas.draw-canvas')).boundingBox();
const at = (fx, fy) => [box.x + box.width * fx, box.y + box.height * fy];
async function stroke(points) {
  const [x0, y0] = at(...points[0]);
  await page.mouse.move(x0, y0);
  await page.mouse.down();
  for (const p of points.slice(1)) { const [x, y] = at(...p); await page.mouse.move(x, y, { steps: 6 }); }
  await page.mouse.up();
}
const circle = (cx, cy, rx, ry, n = 24) => Array.from({ length: n + 1 }, (_, i) => [cx + rx * Math.cos((2 * Math.PI * i) / n), cy + ry * Math.sin((2 * Math.PI * i) / n)]);
await stroke(circle(0.5, 0.36, 0.14, 0.14)); // head
await stroke([[0.42, 0.24], [0.4, 0.06], [0.47, 0.22]]); // ears
await stroke([[0.53, 0.22], [0.6, 0.06], [0.58, 0.24]]);
await stroke(circle(0.5, 0.72, 0.17, 0.2)); // body
await stroke([[0.46, 0.34], [0.46, 0.34]]); // eyes
await stroke([[0.55, 0.34], [0.55, 0.34]]);
await stroke([[0.44, 0.22], [0.5, 0.18], [0.56, 0.22], [0.5, 0.26], [0.44, 0.22]]); // bow
await stroke([[0.68, 0.62], [0.74, 0.78], [0.78, 0.62], [0.68, 0.62]]); // carrot
await shot('02-drawing');
log('drew a bunny');
await clickText('Done!');

await page.waitForSelector('input, button[type="submit"]', { timeout: 30000 });
await shot('03-name');
await clickText('Pip picks a name');
log('name screen done');

await page.waitForSelector('.card', { timeout: 30000 });
await clickText('Sharing', '.card');
await page.evaluate(() => { document.querySelector('details.grownup-promises').open = true; });
await page.type('input[aria-label="Grown-up promise 1"]', 'Nobody in the story is left out');
await shot('04-lesson-with-promise');
await clickText('Yes!');
log('story started with a grown-up promise');

await clickText('Read page 1!', 'button', 600000);
log('first page ready');
await shot('05-making-first-page');

const TOTAL = 8;
let painted = 0;
for (let n = 1; n <= TOTAL; n++) {
  await page.waitForSelector('.choice', { timeout: 300000 });
  if (DWELL) await sleep(DWELL * 1000);
  const hasPic = await page.evaluate(() => !!document.querySelector('.picture[data-status="ready"]'));
  if (hasPic) painted++;
  if (n === 1) await shot('06-reader-page-1');
  const choices = await page.$$('.choice');
  await choices[0].click();
  await sleep(400);
  if (await page.$('.try-other')) { const again = await page.$$('.choice'); await again[1].click(); await sleep(400); }
  if (n === 4) await shot('07-reader-answer');
  log(`page ${n} read${hasPic ? '' : ' (no picture element)'}`);
  await clickText(n < TOTAL ? 'Next' : 'The end', '.next-inline');
}
log(`pages with a painted picture: ${painted} of ${TOTAL} (policy: ${PICTURES})`);
// the end screen offers the quiz and the picture game when they are ready (the quiz is verified after the story)
await page.waitForFunction(() => document.body.innerText.includes('The end!'), { timeout: 60000 });
await shot('08-end');
let quizQs = 0, wrongShowedLine = false, orderPlayed = false;
const hasQuizButton = await page.waitForFunction(() => [...document.querySelectorAll('button')].some((e) => e.textContent.includes("Play Pip's quiz")), { timeout: 240000 }).then(() => true).catch(() => false);
log(`quiz button offered on the end screen: ${hasQuizButton}`);
if (hasQuizButton) {
  await clickText("Play Pip's quiz");
  while (await page.$('.quiz-body')) {
    quizQs++;
    const n = (await page.$$('.quiz-body .choice')).length;
    for (let k = 0; k < n; k++) {
      await (await page.$$('.quiz-body .choice'))[k].click();
      await sleep(300);
      const head = await page.$eval('.look-head', (e) => e.textContent).catch(() => '');
      if (head.includes('Good try')) wrongShowedLine = true;
      if (head.includes('Yes!')) break;
    }
    if (quizQs === 1) await shot('08a-quiz');
    await clickText('Next', '.quiz-body button', 5000).catch(() => clickText('Done!', '.quiz-body button', 5000));
    await sleep(500);
  }
  log(`quiz played: ${quizQs} questions, a wrong answer showed the story line: ${wrongShowedLine}`);
}
await sleep(600);
const onOrder = !!(await page.$('.order-tray')); // after the quiz the app goes straight to the order game when three or more pictures are ready
if (onOrder || (await page.evaluate(() => [...document.querySelectorAll('button')].some((e) => e.textContent.includes('Put the pictures in order'))))) {
  if (!onOrder) await clickText('Put the pictures in order');
  await page.waitForSelector('.order-tray', { timeout: 20000 });
  await shot('08b-order-game');
  for (let slot = 0; slot < 3; slot++) {
    for (const c of await page.$$('.order-card:not([disabled])')) {
      await c.click();
      await sleep(250);
      if ((await page.$$('.slot[data-filled="true"]')).length > slot) break;
    }
  }
  orderPlayed = (await page.$$('.slot[data-filled="true"]')).length === 3;
  log(`picture-order game finished: ${orderPlayed}`);
  await clickText('Next', 'button');
}
else log('picture-order game not offered (fewer than three pictures: expected with the half-pictures policy only if fewer than 3 pages are painted)');
await page.waitForFunction(() => document.body.innerText.includes('The end!'), { timeout: 60000 });
log(`talk-about card shown: ${await page.evaluate(() => !!document.querySelector('.talk'))}`);
log('reached the end screen');

let storyId = null;
let videoOk = null;
if (VIDEO) {
  await clickText('Make my movie', 'button', 600000);
  log('movie requested');
  const t1 = Date.now();
  for (let i = 0; i < 45; i++) { // poll in short waits: one long wait exceeds the browser protocol timeout
    if (await page.$('section.movie video')) break;
    await sleep(20000);
  }
  await page.waitForSelector('section.movie video', { timeout: 20000 });
  const info = await page.evaluate(async () => {
    const v = document.querySelector('section.movie video');
    await new Promise((r) => (v.readyState >= 1 ? r() : v.addEventListener('loadedmetadata', r, { once: true })));
    return { src: v.getAttribute('src'), duration: v.duration, w: v.videoWidth, h: v.videoHeight };
  });
  storyId = info.src.split('/')[3];
  videoOk = info.duration > 60 && info.w === 1920;
  await shot('09-movie');
  log(`movie ready in ${((Date.now() - t1) / 1000).toFixed(0)}s: ${info.duration.toFixed(1)}s ${info.w}x${info.h}`);
}

// the receipt is written when the story's last checks finish; a parent opens it after that (poll in short waits)
for (let i = 0; i < 90; i++) {
  const ready = await page.evaluate(async () => {
    const id = (performance.getEntriesByType('resource').map((r) => r.name).find((n) => /\/api\/stories\/[0-9a-f]+\//.test(n)) || '').split('/')[5];
    return !!id && (await fetch(`/api/stories/${id}/receipt`)).status === 200;
  });
  if (ready) break;
  await sleep(10000);
}
log('receipt ready');
// the grown-ups area: receipt, then forget
await clickText('Grown-ups', 'button');
await page.waitForSelector('.sum, .link', { timeout: 10000 }).catch(() => {});
await clickText('Or answer a question instead', 'button');
const q = await page.evaluate(() => document.querySelector('.sum label').textContent);
const m = q.match(/(\d+)\s*×\s*(\d+)/);
await page.type('.sum input', String(Number(m[1]) * Number(m[2])));
await clickText('Open', 'button');
await page.waitForSelector('[role="tablist"]');
await shot('10-grownups-receipt');
const receiptText = await page.evaluate(() => document.querySelector('[role="tabpanel"]').innerText);
log(`receipt mentions the grown-up promise: ${receiptText.includes('Nobody in the story is left out')}`);
await clickText('Settings', '[role="tab"]');
if (!storyId) storyId = await page.evaluate(() => (performance.getEntriesByType('resource').map((r) => r.name).find((n) => /\/api\/stories\/[0-9a-f]+\//.test(n)) || '').split('/')[5]);
await clickText('Forget', 'button');
await sleep(1500);
const after = await page.evaluate(async (id) => (await fetch(`/api/stories/${id}`)).status, storyId);
log(`after Forget, GET /api/stories/${storyId} -> ${after}`);
await shot('11-after-forget');

await browser.close();
console.log('\nPROBLEMS:', problems.length ? '\n  ' + [...new Set(problems)].join('\n  ') : 'none');
console.log(JSON.stringify({ storyId, videoOk, forgottenStatus: after }));
