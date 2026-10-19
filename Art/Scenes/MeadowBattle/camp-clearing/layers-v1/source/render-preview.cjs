// Render the actual registered PNG stack; this does not repaint or modify plates.
// Requires Node.js, Playwright and Chromium (override CHROMIUM_PATH if needed).
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '..');
const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');

(async () => {
  const manifest = JSON.parse(fs.readFileSync(path.join(root, 'scene.json')));
  const server = http.createServer((request, response) => {
    const pathname = decodeURIComponent(new URL(request.url, 'http://127.0.0.1').pathname);
    const file = path.resolve(root, '.' + (pathname === '/' ? '/preview.html' : pathname));
    if (!file.startsWith(root + path.sep)) { response.writeHead(403).end(); return; }
    fs.readFile(file, (error, data) => {
      if (error) { response.writeHead(404).end(); return; }
      response.setHeader('Content-Type', file.endsWith('.png') ? 'image/png' :
        file.endsWith('.json') ? 'application/json' : 'text/html; charset=utf-8');
      response.end(data);
    });
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  try {
    browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium',
      headless: true, args: ['--no-sandbox'] });
    const page = await browser.newPage({ viewport: { width: 1309, height: 1201 }, deviceScaleFactor: 1 });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(`http://127.0.0.1:${server.address().port}/preview.html?review=1`);
    await page.evaluate(() => window.sceneReady);
    const images = await page.locator('.plate').evaluateAll(elements => elements.map(image => ({
      id: image.id, complete: image.complete, width: image.naturalWidth, height: image.naturalHeight,
    })));
    for (const image of images) {
      assert(image.complete);
      assert.deepEqual([image.width, image.height], manifest.canvasPx);
    }
    for (const layer of manifest.layers) {
      const zIndex = await page.locator(`[id="${layer.id}"]`).evaluate(image => Number(getComputedStyle(image).zIndex));
      assert.equal(zIndex, layer.zIndex);
    }
    const baseline = await page.locator('#scene').screenshot({ path: path.join(root, 'review.png') });
    const toggleResults = [];
    for (const layer of manifest.layers) {
      await page.locator(`[data-layer="${layer.id}"]`).evaluate(input => input.click());
      assert(await page.locator(`[id="${layer.id}"]`).evaluate(image => image.hidden));
      const without = await page.locator('#scene').screenshot();
      assert.notEqual(digest(without), digest(baseline));
      await page.locator(`[data-layer="${layer.id}"]`).evaluate(input => input.click());
      assert.equal(digest(await page.locator('#scene').screenshot()), digest(baseline));
      toggleResults.push({ id: layer.id, removalChangesRenderedPixels: true, restoringRecoversOriginal: true });
    }
    await page.evaluate(() => document.documentElement.classList.remove('review'));
    const frames = [];
    for (const width of [1194, 960]) {
      await page.setViewportSize({ width, height: 834 });
      const rectangles = await page.locator('.plate').evaluateAll(elements => elements.map(image => {
        const r = image.getBoundingClientRect();
        return [r.x, r.y, r.width, r.height];
      }));
      for (const r of rectangles) assert.deepEqual(r, rectangles[0]);
      assert(Math.abs(rectangles[0][2] / rectangles[0][3] - 1309 / 1201) < 0.001);
      frames.push({ viewportWidth: width, identicalLayerFrames: true, aspectPreserved: true });
    }
    assert.deepEqual(errors, []);
    const checks = { imageDecode: images, independentLayerToggles: toggleResults, resizedSharedCanvas: frames,
      scriptErrors: errors, renderer: 'Chromium via Playwright; fixed camera; no native iPad runtime claim' };
    const validationFile = path.join(root, 'validation.json');
    if (fs.existsSync(validationFile)) {
      const validation = JSON.parse(fs.readFileSync(validationFile));
      validation.status = 'asset-contract-and-browser-recomposition-checked-awaiting-art-review';
      validation.browser = checks;
      validation.outputs['review.png'] = { sha256: digest(baseline), bytes: baseline.length };
      fs.writeFileSync(validationFile, JSON.stringify(validation, null, 2) + '\n');
    }
    console.log(JSON.stringify(checks, null, 2));
  } finally {
    if (browser) await browser.close();
    server.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
