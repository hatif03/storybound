// Renders video.html frame by frame (deterministic seek) and mixes audio.
// Usage: node render.mjs test 1.5,10,20     -> PNG frames of those seconds into out/test
//        node render.mjs full                 -> out/storybound-launch-draft.mp4
import puppeteer from 'puppeteer-core';
import fs from 'node:fs';
import path from 'node:path';
import { spawn, execFileSync } from 'node:child_process';

const ROOT = 'D:/storybound/video/launch';
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const FFMPEG = 'C:/ffmpeg/ffmpeg.exe', FFPROBE = 'C:/ffmpeg/ffprobe.exe';
const FPS = 30;
const mode = process.argv[2] || 'test';

const sc = JSON.parse(fs.readFileSync(path.join(ROOT, 'scenes.json'), 'utf8'));
let t = 0;
const scenes = sc.map((s) => {
  const vo = parseFloat(execFileSync(FFPROBE, ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path.join(ROOT, 'audio', s.id + '.mp3')]).toString());
  const dur = Math.max(s.min, vo + 1.0) + (s.hold || 0);
  const o = { id: s.id, start: t, dur, vo, voStart: t + 0.3 };
  t += dur; return o;
});
const total = t + 1.5;
const CFG = { scenes, total };
fs.mkdirSync(path.join(ROOT, 'out'), { recursive: true });
fs.writeFileSync(path.join(ROOT, 'out', 'timeline.json'), JSON.stringify(CFG, null, 1));
console.log('total seconds', total.toFixed(1), scenes.map((s) => s.dur.toFixed(1)).join(' '));

const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--allow-file-access-from-files', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1'] });
const page = await browser.newPage();
await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
await page.evaluateOnNewDocument((cfg) => { window.CFG = cfg; }, CFG);
await page.goto('file:///' + ROOT + '/video.html', { waitUntil: 'load' });
await page.waitForFunction('window.READY === true', { timeout: 60000 });
await page.evaluate('document.fonts.ready');
await new Promise((r) => setTimeout(r, 1500)); // let images decode

if (mode === 'test') {
  const dir = path.join(ROOT, 'out', 'test'); fs.mkdirSync(dir, { recursive: true });
  const times = (process.argv[3] || '1,10,20').split(',').map(Number);
  for (const tt of times) {
    await page.evaluate((x) => window.seek(x), tt);
    await new Promise((r) => setTimeout(r, 120));
    await page.screenshot({ path: path.join(dir, `t${String(tt).replace('.', '_')}.png`), type: 'png' });
    console.log('shot', tt);
  }
  await browser.close();
  process.exit(0);
}

// ---- full render: pipe JPEG frames to ffmpeg ----
const silent = path.join(ROOT, 'out', 'video-silent.mp4');
const ff = spawn(FFMPEG, ['-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', silent], { stdio: ['pipe', 'inherit', 'inherit'] });
const N = Math.ceil(total * FPS);
const t0 = Date.now();
for (let i = 0; i < N; i++) {
  await page.evaluate((x) => window.seek(x), i / FPS);
  const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
  if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
  if (i % 150 === 0) console.log(`frame ${i}/${N}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
}
ff.stdin.end();
await new Promise((r) => ff.on('close', r));
const sfx = await page.evaluate(() => window.SFX);
await browser.close();

// ---- audio mix: VO per scene + music bed + sfx ----
const A = path.join(ROOT, 'audio'), SFXDIR = 'D:/storybound/assets/audio/sfx';
const inputs = []; const filt = []; let k = 0; const labels = [];
for (const s of scenes) { inputs.push('-i', path.join(A, s.id + '.mp3')); filt.push(`[${k}:a]adelay=${Math.round(s.voStart * 1000)}|${Math.round(s.voStart * 1000)},volume=1.0[a${k}]`); labels.push(`[a${k}]`); k++; }
inputs.push('-stream_loop', '1', '-i', 'D:/storybound/assets/audio/music/home.mp3');
filt.push(`[${k}:a]atrim=0:${total.toFixed(2)},volume=0.13,afade=t=in:d=1.5,afade=t=out:st=${(total - 3).toFixed(2)}:d=3[a${k}]`); labels.push(`[a${k}]`); k++;
for (const e of sfx) { inputs.push('-i', path.join(SFXDIR, e.file)); filt.push(`[${k}:a]adelay=${Math.round(e.t * 1000)}|${Math.round(e.t * 1000)},volume=${(0.5 * e.vol).toFixed(2)}[a${k}]`); labels.push(`[a${k}]`); k++; }
filt.push(`${labels.join('')}amix=inputs=${labels.length}:normalize=0:dropout_transition=0,alimiter=limit=0.95[mix]`);
const finalOut = path.join(ROOT, 'out', 'storybound-launch-draft.mp4');
execFileSync(FFMPEG, ['-y', '-i', silent, ...inputs, '-filter_complex', filt.join(';'), '-map', '0:v', '-map', '[mix]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', finalOut], { stdio: 'inherit' });
console.log('DONE', finalOut, ((Date.now() - t0) / 1000).toFixed(0) + 's');
