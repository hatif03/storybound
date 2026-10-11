// Open a cfo.ai share link in a fresh browser profile (no cookies, not signed in) and report what an anonymous visitor sees.
//   node scripts/check-share-link.mjs <url> [out.png]
import puppeteer from 'puppeteer-core';
const url = process.argv[2];
const out = process.argv[3] || 'shots/share-link.png';
const b = await puppeteer.launch({ executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: 'new' });
const ctx = await b.createBrowserContext();
const p = await ctx.newPage();
await p.setViewport({ width: 1400, height: 1000 });
await p.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });
await new Promise((r) => setTimeout(r, 8000));
const text = await p.evaluate(() => document.body.innerText);
await p.screenshot({ path: out, fullPage: false });
console.log('title:', await p.title());
console.log('asks to sign in:', /sign in|log in|log-in/i.test(text));
console.log('chars of visible text:', text.length);
console.log(text.slice(0, 900).replace(/\n+/g, ' | '));
await b.close();
