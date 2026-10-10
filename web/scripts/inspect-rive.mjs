// Quick inspection of the Pip Rive files: artboards, state machines, inputs, whether they load. Prints JSON.
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path'; import puppeteer from 'puppeteer-core';
const root = path.resolve(import.meta.dirname, '..');
const types = { '.js': 'text/javascript', '.wasm': 'application/wasm', '.riv': 'application/octet-stream', '.html': 'text/html' };
const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  const file = url.startsWith('/rive/') ? path.join(root, 'node_modules/@rive-app/canvas', url.slice(6)) : path.join(root, 'public', url);
  if (url === '/') { res.setHeader('content-type', 'text/html'); return res.end('<canvas id=c width=200 height=200></canvas>'); }
  if (!fs.existsSync(file)) { res.statusCode = 404; return res.end(); }
  res.setHeader('content-type', types[path.extname(file)] || 'application/octet-stream'); fs.createReadStream(file).pipe(res);
}).listen(0);
const port = server.address().port;
const browser = await puppeteer.launch({ executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: true });
const page = await browser.newPage();
await page.goto(`http://127.0.0.1:${port}/`);
await page.addScriptTag({ url: `http://127.0.0.1:${port}/rive/rive.js` });
const files = fs.readdirSync(path.join(root, 'public/assets/pip')).filter((f) => f.endsWith('.riv'));
const out = await page.evaluate(async (port, files) => {
  rive.RuntimeLoader.setWasmUrl(`http://127.0.0.1:${port}/rive/rive.wasm`);
  const results = [];
  for (const f of files) {
    const r = await new Promise((resolve) => {
      const canvas = document.createElement('canvas'); canvas.width = canvas.height = 200; document.body.append(canvas);
      const t = setTimeout(() => resolve({ file: f, error: 'timeout' }), 8000);
      const inst = new rive.Rive({
        src: `http://127.0.0.1:${port}/assets/pip/${f}`, canvas, stateMachines: 'State Machine 1', autoplay: true,
        onLoad: () => { clearTimeout(t); resolve({ file: f, artboards: inst.contents?.artboards?.map((a) => ({ name: a.name, sms: a.stateMachines.map((s) => s.name) })), inputs: inst.stateMachineInputs('State Machine 1')?.map((i) => i.name) ?? null, playing: inst.isPlaying, bounds: inst.bounds }); inst.cleanup(); },
        onLoadError: (e) => { clearTimeout(t); resolve({ file: f, error: String(e?.data ?? e) }); },
      });
    });
    results.push(r);
  }
  return results;
}, port, files);
if (process.argv.includes('--bounds')) {
  const crops = await page.evaluate(async (port, files) => {
    const res = {};
    for (const f of files) {
      const canvas = document.createElement('canvas'); canvas.width = canvas.height = 500; document.body.append(canvas);
      const inst = await new Promise((resolve) => { const r = new rive.Rive({ src: `http://127.0.0.1:${port}/assets/pip/${f}`, canvas, stateMachines: 'State Machine 1', autoplay: true, onLoad: () => resolve(r) }); });
      let x0 = 500, y0 = 500, x1 = 0, y1 = 0;
      for (let k = 0; k < 4; k++) {
        await new Promise((r) => setTimeout(r, 350));
        const d = canvas.getContext('2d').getImageData(0, 0, 500, 500).data;
        for (let y = 0; y < 500; y += 2) for (let x = 0; x < 500; x += 2) {
          const i = (y * 500 + x) * 4;
          if (d[i + 3] > 20 && (d[i] < 245 || d[i + 1] < 245 || d[i + 2] < 245)) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
        }
      }
      res[f.replace('.riv', '')] = { x: +(x0 / 500).toFixed(3), y: +(y0 / 500).toFixed(3), w: +((x1 - x0) / 500).toFixed(3), h: +((y1 - y0) / 500).toFixed(3) };
      inst.cleanup();
    }
    return res;
  }, port, files);
  console.log(JSON.stringify(crops, null, 1));
} else console.log(JSON.stringify(out, null, 1));
await browser.close(); server.close();
