// Mix voice-over, music and sound effects into out/video-silent.mp4 (frames already rendered).
import puppeteer from 'puppeteer-core';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const ROOT = 'D:/storybound/video/launch';
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const FFMPEG = 'C:/ffmpeg/ffmpeg.exe';
const CFG = JSON.parse(fs.readFileSync(path.join(ROOT, 'out', 'timeline.json'), 'utf8'));
const { scenes, total } = CFG;

// get the sfx cue list the page registers
const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--allow-file-access-from-files', '--disable-gpu'] });
const page = await browser.newPage();
await page.evaluateOnNewDocument((cfg) => { window.CFG = cfg; }, CFG);
await page.goto('file:///' + ROOT + '/video.html', { waitUntil: 'load' });
await page.waitForFunction('window.READY === true');
const sfx = await page.evaluate(() => window.SFX);
await browser.close();

const A = path.join(ROOT, 'audio'), SFXDIR = 'D:/storybound/assets/audio/sfx';
const silent = path.join(ROOT, 'out', 'video-silent.mp4');
const inputs = ['-i', silent];
const filt = [];
const labels = [];
let k = 1; // input 0 is the video
for (const s of scenes) {
  inputs.push('-i', path.join(A, s.id + '.mp3'));
  const ms = Math.round(s.voStart * 1000);
  filt.push(`[${k}:a]adelay=${ms}|${ms},volume=1.0[a${k}]`); labels.push(`[a${k}]`); k++;
}
inputs.push('-stream_loop', '1', '-i', 'D:/storybound/assets/audio/music/home.mp3');
filt.push(`[${k}:a]atrim=0:${total.toFixed(2)},asetpts=PTS-STARTPTS,volume=0.13,afade=t=in:d=1.5,afade=t=out:st=${(total - 3).toFixed(2)}:d=3[a${k}]`); labels.push(`[a${k}]`); k++;
for (const e of sfx) {
  const f = path.join(SFXDIR, e.file);
  inputs.push('-i', f);
  const ms = Math.round(e.t * 1000);
  filt.push(`[${k}:a]adelay=${ms}|${ms},volume=${(0.5 * e.vol).toFixed(2)}[a${k}]`); labels.push(`[a${k}]`); k++;
}
filt.push(`${labels.join('')}amix=inputs=${labels.length}:normalize=0:dropout_transition=0,alimiter=limit=0.95[mix]`);
fs.writeFileSync(path.join(ROOT, 'out', 'filter.txt'), filt.join(';\n'));
const out = path.join(ROOT, 'out', 'storybound-launch-draft.mp4');
execFileSync(FFMPEG, ['-y', ...inputs, '-filter_complex_script', path.join(ROOT, 'out', 'filter.txt'), '-map', '0:v', '-map', '[mix]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', total.toFixed(2), out], { stdio: 'inherit' });
console.log('DONE', out);
