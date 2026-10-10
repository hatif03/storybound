// Screenshots of every screen in demo mode, at three sizes (phone 390x844, tablet portrait 820x1180, desktop 1280x800) plus the
// tablet-landscape reference (1180x820). Uses Microsoft Edge through puppeteer-core. Writes web/shots/<size>/NN-name.png.
// It also reports console errors and any request that leaves the app's own origin (there must be none).
//   node scripts/shots.mjs [--url http://127.0.0.1:5173] [--only phone,desktop] [--speed 8]
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import puppeteer from 'puppeteer-core';

const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const root = path.resolve(import.meta.dirname, '..');
const out = path.join(root, 'shots');
const arg = (name, dflt) => { const i = process.argv.indexOf(`--${name}`); return i > 0 ? process.argv[i + 1] : dflt; };
const SPEED = Number(arg('speed', '8'));
const only = (arg('only', '') || '').split(',').filter(Boolean);

const SIZES = [
  { name: 'phone', width: 390, height: 844 },
  { name: 'tablet-portrait', width: 820, height: 1180 },
  { name: 'tablet-landscape', width: 1180, height: 820 },
  { name: 'desktop', width: 1280, height: 800 },
].filter((s) => !only.length || only.includes(s.name));

let server;
let base = arg('url', '');
if (!base) {
  const port = 5199;
  server = spawn(process.execPath, [path.join(root, 'node_modules/vite/bin/vite.js'), '--port', String(port), '--strictPort', '--host', '127.0.0.1'], { cwd: root, stdio: 'pipe' });
  base = `http://127.0.0.1:${port}`;
  for (let i = 0; i < 60; i++) { try { if ((await fetch(base)).ok) break; } catch { /* not up yet */ } await new Promise((r) => setTimeout(r, 500)); }
}
const origin = new URL(base).origin;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const problems = [];
const browser = await puppeteer.launch({ executablePath: EDGE, headless: true, args: ['--autoplay-policy=no-user-gesture-required'] });

async function newPage(size, query) {
  const page = await browser.newPage();
  await page.setViewport({ width: size.width, height: size.height, deviceScaleFactor: 1 });
  page.on('pageerror', (e) => problems.push(`[${size.name}] pageerror: ${e.message}`));
  page.on('console', (m) => { if (m.type() === 'error') problems.push(`[${size.name}] console.error: ${m.text()}`); });
  page.on('request', (r) => { const u = r.url(); if (!u.startsWith(origin) && !u.startsWith('data:') && !u.startsWith('blob:')) problems.push(`[${size.name}] EXTERNAL REQUEST: ${u}`); });
  page.on('response', (r) => { if (r.status() >= 400 && r.url().startsWith(origin)) problems.push(`[${size.name}] HTTP ${r.status()}: ${r.url()}`); });
  await page.goto(`${base}/?mock=1&${query}`, { waitUntil: 'networkidle2' });
  return page;
}

let counter = 0;
async function shot(page, size, name, full = false) {
  const dir = path.join(out, size.name);
  fs.mkdirSync(dir, { recursive: true });
  await sleep(500); // let entrance animations settle
  await page.screenshot({ path: path.join(dir, `${String(++counter).padStart(2, '0')}-${name}.png`), fullPage: full });
}
const click = async (page, selector) => { await page.waitForSelector(selector, { visible: true, timeout: 20000 }); await page.click(selector); };
const clickText = async (page, text, sel = 'button, label, a') => {
  await page.waitForFunction((t, s) => [...document.querySelectorAll(s)].some((e) => e.textContent?.trim().includes(t) && e.getClientRects().length), { timeout: 20000 }, text, sel);
  const h = await page.evaluateHandle((t, s) => [...document.querySelectorAll(s)].find((e) => e.textContent?.trim().includes(t) && e.getClientRects().length), text, sel);
  await h.asElement().click();
};
const waitStep = (page, step, timeout = 120000) => page.waitForSelector(`.making[data-step="${step}"]`, { timeout });

async function drawSomething(page) {
  const box = await (await page.waitForSelector('.draw-canvas', { visible: true })).boundingBox();
  const at = (fx, fy) => [box.x + box.width * fx, box.y + box.height * fy];
  const stroke = async (pts) => { await page.mouse.move(...at(...pts[0])); await page.mouse.down(); for (const p of pts.slice(1)) await page.mouse.move(...at(...p), { steps: 6 }); await page.mouse.up(); };
  await click(page, '.crayon[data-color="brown"]');
  await stroke([[0.3, 0.45], [0.3, 0.75], [0.5, 0.78], [0.7, 0.75], [0.7, 0.45], [0.5, 0.35], [0.3, 0.45]]); // body
  await click(page, '.crayon[data-color="pink"]');
  await stroke([[0.36, 0.34], [0.3, 0.15], [0.4, 0.2], [0.42, 0.34]]); // ear
  await stroke([[0.58, 0.34], [0.6, 0.15], [0.68, 0.22], [0.64, 0.36]]); // ear
  await click(page, '.crayon[data-color="sky"]');
  await page.mouse.click(...at(0.43, 0.52)); await page.mouse.click(...at(0.57, 0.52)); // eyes
  await click(page, '.crayon[data-color="red"]');
  await stroke([[0.44, 0.64], [0.5, 0.68], [0.56, 0.64]]); // smile
}

/** welcome -> draw -> (sample) -> name -> lesson -> start. Returns when the making screen is up. */
async function toMaking(page, size, { shots = false, scenarioSample = false } = {}) {
  await page.waitForSelector('.welcome');
  if (shots) await shot(page, size, 'welcome');
  await clickText(page, "Let's go!");
  await page.waitForSelector('.draw');
  if (shots) await shot(page, size, 'draw-empty');
  if (scenarioSample) {
    await click(page, '.sample'); // first sample drawing
    if (shots) await shot(page, size, 'draw-sample-picked');
  } else {
    await drawSomething(page);
    if (shots) {
      await shot(page, size, 'draw-drawn');
      await click(page, 'button[aria-label="Start over"]');
      await shot(page, size, 'draw-start-over-confirm');
      await clickText(page, 'Keep drawing');
    }
  }
  await clickText(page, 'Done!');
  await page.waitForSelector('.name');
  if (shots) await shot(page, size, 'name');
  await page.type('.name input', 'Poppy');
  if (shots) await shot(page, size, 'name-typed');
  await clickText(page, 'Next');
  await page.waitForSelector('.lesson .card');
  if (shots) await shot(page, size, 'lesson');
  await click(page, '.lesson .card');
  if (shots) await shot(page, size, 'lesson-picked');
  await clickText(page, 'Yes!');
}

async function main(size) {
  counter = 0;
  console.log(`\n== ${size.name} ${size.width}x${size.height}`);

  // ---- the full story run ----
  let page = await newPage(size, `speed=${SPEED}`);
  await toMaking(page, size, { shots: true });
  await waitStep(page, 'meeting');
  await shot(page, size, 'making-meeting');
  await waitStep(page, 'writing');
  await shot(page, size, 'making-writing-promises');
  await waitStep(page, 'fixing');
  await shot(page, size, 'making-fixing');
  await page.waitForSelector('.read-now', { timeout: 60000 });
  await shot(page, size, 'making-page1-ready');
  await click(page, '.read-now');
  await page.waitForSelector('.reader .spread');
  await shot(page, size, 'reader-picture-pending');
  // wrong answer first (a gentle "let's think"), then the right one
  const choices = await page.$$('.choice');
  const wrongIdx = 0; // the first choice, whichever it is (the page shows kind or thinking feedback accordingly)
  await choices[wrongIdx].click();
  await shot(page, size, 'reader-feedback-1');
  await choices[1 - wrongIdx].click();
  await shot(page, size, 'reader-feedback-2');
  await page.waitForSelector('.picture > img:not(.hero-sticker)', { timeout: 120000 });
  await shot(page, size, 'reader-picture');
  // jump to page 5 using the stones
  await page.waitForFunction(() => document.querySelectorAll('.stones .stone-done').length >= 8, { timeout: 120000 });
  await page.keyboard.press('ArrowRight'); await page.keyboard.press('ArrowRight'); await page.keyboard.press('ArrowRight'); await page.keyboard.press('ArrowRight');
  await page.waitForFunction(() => document.querySelector('.reader')?.dataset.page === '5');
  await shot(page, size, 'reader-page5');
  await page.evaluate(() => { document.documentElement.dataset.text = 'l'; });
  await shot(page, size, 'reader-page5-large-text');
  await page.evaluate(() => { document.documentElement.dataset.text = 'm'; });
  for (let i = 0; i < 3; i++) await page.keyboard.press('ArrowRight');
  await page.waitForFunction(() => document.querySelector('.reader')?.dataset.page === '8');
  const last = await page.$$('.choice');
  await last[1].click();
  await clickText(page, 'The end');
  await page.waitForSelector('.end');
  await shot(page, size, 'end');
  // grown-ups: gate, then the receipt
  await clickText(page, 'Grown-ups');
  await page.waitForSelector('.gate');
  await shot(page, size, 'gate');
  const hold = await (await page.$('.hold')).boundingBox();
  await page.mouse.move(hold.x + hold.width / 2, hold.y + hold.height / 2);
  await page.mouse.down();
  await sleep(1400);
  await shot(page, size, 'gate-holding');
  await sleep(2000);
  await page.mouse.up();
  await page.waitForSelector('.area');
  await shot(page, size, 'receipt-top');
  await shot(page, size, 'receipt-full', true);
  await clickText(page, 'Receipt as JSON', 'summary');
  await shot(page, size, 'receipt-json');
  await clickText(page, 'Settings', '[role="tab"]');
  await shot(page, size, 'settings');
  await clickText(page, 'Demo drawer', '[role="tab"]');
  await shot(page, size, 'demo-drawer');
  await clickText(page, 'About', '[role="tab"]');
  await shot(page, size, 'about');
  await page.close();

  // ---- refusal and redraw ----
  for (const [scenario, label] of [['refuse', 'refusal'], ['redraw', 'redraw']]) {
    page = await newPage(size, `speed=60&scenario=${scenario}`);
    await toMaking(page, size, { scenarioSample: true });
    await page.waitForSelector('.refusal', { timeout: 30000 });
    await shot(page, size, label);
    await page.close();
  }

  // ---- degraded media: a page with no picture, a page with no voice ----
  page = await newPage(size, 'speed=60&scenario=degraded');
  await toMaking(page, size, { scenarioSample: true });
  await page.waitForSelector('.read-now', { timeout: 30000 });
  await page.waitForSelector('.making[data-step="done"]', { timeout: 60000 });
  await shot(page, size, 'making-done');
  await click(page, '.read-now');
  await page.waitForSelector('.reader .spread');
  for (let i = 0; i < 3; i++) await page.keyboard.press('ArrowRight');
  await page.waitForFunction(() => document.querySelector('.reader')?.dataset.page === '4');
  await shot(page, size, 'reader-no-picture');
  await page.keyboard.press('ArrowRight'); await page.keyboard.press('ArrowRight');
  await page.waitForFunction(() => document.querySelector('.reader')?.dataset.page === '6');
  await shot(page, size, 'reader-no-voice');
  await page.close();
}

try {
  for (const s of SIZES) {
    try { await main(s); } catch (e) { problems.push(`[${s.name}] FLOW FAILED: ${e.message}`); console.error(e); }
  }
} finally {
  await browser.close();
  server?.kill();
}
console.log('\nProblems found:', problems.length ? '\n' + [...new Set(problems)].join('\n') : 'none');
console.log(`Screenshots in ${out}`);
process.exit(problems.some((p) => p.includes('FLOW FAILED')) ? 1 : 0);
