// Opens every page at 320 px wide and fails when one scrolls sideways.
// Usage: node tools/check_layout.mjs   (needs `npm ci` and `npx playwright install chromium`)
import { createServer } from 'node:http';
import { existsSync, globSync, readFileSync, statSync } from 'node:fs';
import { extname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const root = resolve(fileURLToPath(import.meta.url), '../..');
// Pages the stores and Google link to; each must exist. Every other page is found and checked too.
const required = ['/', '/404.html', '/fut27/', '/fut27/privacy/', '/fut27/terms/', '/contact/'];
const found = globSync('**/*.html', { cwd: root, exclude: (f) => f.startsWith('node_modules') || f.startsWith('.') })
  .map((f) => '/' + f.replace(/(^|\/)index\.html$/, '$1'));
const pages = [...new Set([...required, ...found])].sort();
const width = 320;
const types = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css',
  '.svg': 'image/svg+xml',
  '.woff2': 'font/woff2',
  '.png': 'image/png',
};

function fileFor(path) {
  const file = join(root, decodeURIComponent(path));
  if (!file.startsWith(root)) return null;
  if (existsSync(file) && statSync(file).isDirectory()) return join(file, 'index.html');
  return file;
}

const server = createServer((req, res) => {
  const file = fileFor(new URL(req.url, 'http://localhost').pathname);
  if (!file || !existsSync(file)) {
    res.writeHead(404).end();
    return;
  }
  res.writeHead(200, { 'content-type': types[extname(file)] ?? 'application/octet-stream' });
  res.end(readFileSync(file));
});
await new Promise((done) => server.listen(0, '127.0.0.1', done));
const base = `http://127.0.0.1:${server.address().port}`;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width, height: 640 } });
const problems = [];
for (const path of pages) {
  if (!existsSync(fileFor(path))) {
    problems.push(`${path}: missing`);
    continue;
  }
  const response = await page.goto(base + path);
  if (!response.ok()) {
    problems.push(`${path}: HTTP ${response.status()}`);
    continue;
  }
  // Open every FAQ answer so their text is measured too.
  await page.evaluate(() => document.querySelectorAll('details').forEach((d) => (d.open = true)));
  const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
  if (scrollWidth > width) problems.push(`${path}: ${scrollWidth}px wide at ${width}px, scrolls sideways`);
}
await browser.close();
server.close();

for (const problem of problems) console.log(problem);
console.log(problems.length ? `${problems.length} problem(s)` : `${pages.length} pages fit ${width}px`);
process.exit(problems.length ? 1 : 0);
