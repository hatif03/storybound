// Small-hands checks through a real browser with touch emulation, in demo (mock) mode: free, no model calls.
//   node scripts/e2e-touch.mjs [--url http://127.0.0.1:8000]
// A finger draws; a palm does not; a reload keeps the drawing; "start over" can be undone; a quick tap cannot leave a story but a hold can;
// the browser's back button stays inside the app.
import fs from 'node:fs';
import path from 'node:path';
import puppeteer from 'puppeteer-core';

const BASE = (process.argv.includes('--url') ? process.argv[process.argv.indexOf('--url') + 1] : 'http://127.0.0.1:8000') + '/?mock=1&speed=12';
const OUT = path.resolve(import.meta.dirname, '../shots/touch');
fs.mkdirSync(OUT, { recursive: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const b = await puppeteer.launch({ executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: 'new' });
const p = await b.newPage();
await p.setViewport({ width: 1180, height: 820, hasTouch: true, isMobile: false });
const cdp = await p.createCDPSession();
const results = [];
const check = (name, ok, detail = '') => { results.push({ name, ok: !!ok, detail }); console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? ' (' + detail + ')' : ''}`); };
const problems = [];
p.on('pageerror', (e) => problems.push(String(e).slice(0, 160)));

const touch = async (type, pts) => cdp.send('Input.dispatchTouchEvent', { type, touchPoints: pts });
const finger = (id, x, y, r = 6) => ({ id, x, y, radiusX: r, radiusY: r, force: 0.5 });
async function stroke(from, to, r = 6, id = 1) {
  await touch('touchStart', [finger(id, from.x, from.y, r)]);
  for (let i = 1; i <= 8; i++) await touch('touchMove', [finger(id, from.x + ((to.x - from.x) * i) / 8, from.y + ((to.y - from.y) * i) / 8, r)]);
  await touch('touchEnd', []);
  await sleep(120);
}
const draft = () => p.evaluate(() => { try { return JSON.parse(sessionStorage.getItem('storybound.draft') || '[]').length; } catch { return -1; } });
const canvasBox = async () => (await (await p.$('canvas.draw-canvas')).boundingBox());
const textBtn = (t) => p.evaluate((t) => [...document.querySelectorAll('button')].some((e) => e.textContent.trim().includes(t) && !e.disabled), t);
async function tapText(t) {
  const pt = await p.evaluate((t) => { const e = [...document.querySelectorAll('button')].find((e) => e.textContent.trim().includes(t) && !e.disabled); if (!e) return null; const r = e.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 }; }, t);
  if (!pt) throw new Error('no button ' + t);
  await touch('touchStart', [finger(1, pt.x, pt.y)]); await sleep(60); await touch('touchEnd', []); await sleep(250);
}
async function holdText(t, ms) {
  const pt = await p.evaluate((t) => { const e = [...document.querySelectorAll('button')].find((e) => e.textContent.trim().includes(t) && !e.disabled); const r = e.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 }; }, t);
  await touch('touchStart', [finger(1, pt.x, pt.y)]); await sleep(ms); await touch('touchEnd', []); await sleep(300);
}

await p.goto(BASE, { waitUntil: 'networkidle0' });
await p.evaluate(() => sessionStorage.clear());
await sleep(300);
await tapText("Let's go");
await p.waitForSelector('canvas.draw-canvas');
await sleep(400);
const box = await canvasBox();
const at = (fx, fy) => ({ x: box.x + box.width * fx, y: box.y + box.height * fy });

// 1. a finger draws
await stroke(at(0.2, 0.3), at(0.6, 0.5));
await stroke(at(0.3, 0.7), at(0.7, 0.6));
check('a finger draws strokes (draft kept in this tab)', (await draft()) === 2, `strokes: ${await draft()}`);

// 2. a palm does not (contact 100 px wide)
await stroke(at(0.5, 0.2), at(0.8, 0.9), 50);
check('a palm-sized touch draws nothing', (await draft()) === 2, `strokes: ${await draft()}`);

// 3. a second finger while one is down does not start a second stroke
await touch('touchStart', [finger(1, at(0.1, 0.1).x, at(0.1, 0.1).y)]);
await touch('touchStart', [finger(1, at(0.1, 0.1).x, at(0.1, 0.1).y), finger(2, at(0.9, 0.9).x, at(0.9, 0.9).y)]);
await touch('touchMove', [finger(1, at(0.15, 0.15).x, at(0.15, 0.15).y), finger(2, at(0.95, 0.9).x, at(0.95, 0.9).y)]);
await touch('touchEnd', []); await sleep(150);
check('two fingers make one stroke, not two', (await draft()) === 3, `strokes: ${await draft()}`);

// 4. a reload keeps the drawing
await p.reload({ waitUntil: 'networkidle0' });
await tapText("Let's go");
await p.waitForSelector('canvas.draw-canvas');
await sleep(400);
check('after a reload the drawing is still there', (await draft()) === 3, `strokes: ${await draft()}`);
await p.screenshot({ path: path.join(OUT, '01-drawing-after-reload.png') });

// 5. start over can be undone
await tapText('Start over').catch(async () => { // the trash button has only an aria-label
  const pt = await p.evaluate(() => { const e = document.querySelector('button[aria-label="Start over"]'); const r = e.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 }; });
  await touch('touchStart', [finger(1, pt.x, pt.y)]); await sleep(60); await touch('touchEnd', []); await sleep(250);
});
check('start over clears the page at once', (await draft()) === 0, `strokes: ${await draft()}`);
check('and offers "Bring my drawing back"', await textBtn('Bring my drawing back'));
await p.screenshot({ path: path.join(OUT, '02-start-over-can-be-undone.png') });
await tapText('Bring my drawing back');
check('bringing it back restores every stroke', (await draft()) === 3, `strokes: ${await draft()}`);

// 6. the browser's back button stays inside the app
const url0 = await p.url();
await p.goBack().catch(() => {});
await sleep(500);
check('the browser back button does not leave the app', (await p.url()) === url0 && !!(await p.$('canvas.draw-canvas')), await p.url());

// 7. a quick tap cannot leave a story, a hold can
await tapText('Done!');
await p.waitForSelector('button.sample', { timeout: 5000 }).catch(() => {});
await sleep(500);
await tapText('Pip picks a name');
await p.waitForSelector('.card', { timeout: 20000 });
await tapText('Sharing').catch(async () => { await p.evaluate(() => [...document.querySelectorAll('.card')].find((e) => e.textContent.includes('Sharing')).click()); });
await sleep(300);
await tapText('Yes!');
await p.waitForFunction(() => [...document.querySelectorAll('button')].some((e) => e.textContent.includes('Read page 1!')), { timeout: 120000 });
await p.evaluate(() => document.querySelector('button[aria-label="Stop and go back to the start"]').click());
await sleep(400);
check('the stop question has a hold button', await p.evaluate(() => !!document.querySelector('.confirm .btn-hold')));
await tapText('Yes, stop'); // a quick tap
check('a quick tap on "Yes, stop" does not stop the story', await p.evaluate(() => !!document.querySelector('.confirm') && document.body.innerText.includes('Read page 1!')));
await p.screenshot({ path: path.join(OUT, '03-hold-to-confirm.png') });
await holdText('Yes, stop', 1300);
check('holding it does', await p.evaluate(() => !document.querySelector('.confirm') && !!document.querySelector('canvas.draw-canvas, .sheet')));

await b.close();
const failed = results.filter((r) => !r.ok);
console.log(`\n${results.length - failed.length}/${results.length} passed; page errors: ${problems.length}`);
if (problems.length) console.log(problems.join('\n'));
fs.writeFileSync(path.join(OUT, 'results.json'), JSON.stringify({ results, problems }, null, 1));
process.exit(failed.length || problems.length ? 1 : 0);
