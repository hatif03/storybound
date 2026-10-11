// The quiz and the picture-order game through the real UI in demo (mock) mode: free, no model calls.
//   node scripts/e2e-quiz-mock.mjs [--url http://127.0.0.1:8000]
import fs from 'node:fs';
import path from 'node:path';
import puppeteer, { ElementHandle } from 'puppeteer-core';
// The app drops taps that land within 350 ms of a screen change (ghost taps from small hands): a script that clicks the moment an
// element appears has to wait like a child would.
const nativeClick = ElementHandle.prototype.click;
ElementHandle.prototype.click = async function (...a) { await new Promise((r) => setTimeout(r, 450)); return nativeClick.apply(this, a); };

const BASE = (process.argv.includes('--url') ? process.argv[process.argv.indexOf('--url') + 1] : 'http://127.0.0.1:8000') + '/?mock=1&speed=12';
const OUT = path.resolve(import.meta.dirname, '../shots/quiz');
fs.mkdirSync(OUT, { recursive: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const b = await puppeteer.launch({ executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: 'new' });
const p = await b.newPage();
await p.setViewport({ width: 1280, height: 800 });
const problems = [];
p.on('pageerror', (e) => problems.push(String(e).slice(0, 160)));
p.on('console', (m) => { if (m.type() === 'error') problems.push('console: ' + m.text().slice(0, 160)); });
const click = async (text, sel = 'button', timeout = 60000) => {
  await p.waitForFunction((t, s) => [...document.querySelectorAll(s)].some((e) => e.textContent.trim().includes(t) && !e.disabled), { timeout }, text, sel);
  await p.evaluate((t, s) => [...document.querySelectorAll(s)].find((e) => e.textContent.trim().includes(t) && !e.disabled).click(), text, sel);
};
await p.goto(BASE, { waitUntil: 'networkidle0' });
await click("Let's go");
await p.waitForSelector('button.sample', { timeout: 30000 });
await p.click('button.sample');
await sleep(500);
await click('Done!');
await click('Pip picks a name');
await p.waitForSelector('.card');
await click('Sharing', '.card');
await click('Yes!');
await click('Read page 1!', 'button', 120000);
for (let n = 1; n <= 8; n++) {
  await p.waitForSelector('.choice', { timeout: 60000 });
  const cs = await p.$$('.choice'); await cs[0].click(); await sleep(300);
  if (await p.$('.try-other')) { const again = await p.$$('.choice'); await again[1].click(); await sleep(300); }
  await click(n < 8 ? 'Next' : 'The end', '.next-inline');
}
await p.waitForFunction(() => document.body.innerText.includes('The end!'), { timeout: 60000 });
await p.waitForFunction(() => [...document.querySelectorAll('button')].some((e) => e.textContent.includes("Play Pip's quiz")), { timeout: 60000 });
await p.screenshot({ path: path.join(OUT, '01-end-offers-games.png') });
console.log('end screen offers the quiz button: true');
await click("Play Pip's quiz");
let q = 0, wrongShowedLine = false;
while (await p.$('.quiz-body')) {
  q++;
  const n = (await p.$$('.quiz-body .choice')).length;
  for (let k = 0; k < n; k++) {
    await (await p.$$('.quiz-body .choice'))[k].click(); await sleep(250);
    const head = await p.$eval('.look-head', (e) => e.textContent).catch(() => '');
    if (head.includes('Good try')) { wrongShowedLine = true; if (q === 1) await p.screenshot({ path: path.join(OUT, '02-wrong-answer-shows-the-line.png') }); }
    if (head.includes('Yes!')) { if (q === 1) await p.screenshot({ path: path.join(OUT, '03-right-answer.png') }); break; }
  }
  await click('Next', '.quiz-body button', 3000).catch(() => click('Done!', '.quiz-body button', 3000));
  await sleep(400);
}
console.log(`quiz: ${q} questions, a wrong answer showed the story line: ${wrongShowedLine}`);
if (await p.$('.order-tray')) {
  await p.screenshot({ path: path.join(OUT, '04-order-game.png') });
  for (let slot = 0; slot < 3; slot++) {
    for (const c of await p.$$('.order-card:not([disabled])')) { await c.click(); await sleep(250); if ((await p.$$('.slot[data-filled="true"]')).length > slot) break; }
  }
  console.log('order game finished:', (await p.$$('.slot[data-filled="true"]')).length === 3);
  await p.screenshot({ path: path.join(OUT, '05-order-done.png') });
  await click('Next');
}
await p.waitForFunction(() => document.body.innerText.includes('The end!'), { timeout: 20000 });
console.log('back on the end screen; talk-about card:', await p.evaluate(() => !!document.querySelector('.talk')));
console.log('problems:', problems.length ? [...new Set(problems)] : 'none');
await b.close();
