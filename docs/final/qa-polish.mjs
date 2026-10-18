/** Local landing polish acceptance: both viewports, staged trail, controls and motion fallback. */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const {chromium} = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.SNIFF_QA_URL || 'http://127.0.0.1:8098';
assert.match(base, /^http:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/);
const shots = new URL('./shots-polish/', import.meta.url);
await fs.mkdir(shots, {recursive:true});
const browser = await chromium.launch({headless:true});
const results = [];
try {
  for (const width of [1440,390]) {
    const context = await browser.newContext({viewport:{width,height:1000}});
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(base, {waitUntil:'networkidle'});
    await page.evaluate(() => document.fonts.ready);
    assert.equal(await page.locator('#hero-visual').getAttribute('data-animation'), 'waiting');
    const layout = await page.evaluate(() => ({width:innerWidth, scrollWidth:document.documentElement.scrollWidth, body:getComputedStyle(document.querySelector('.hero-description')).fontSize}));
    assert.ok(layout.scrollWidth <= width, JSON.stringify(layout));
    assert.equal(layout.body, width === 390 ? '17px' : '18px');
    await page.screenshot({path:new URL(`hero-${width}.png`, shots).pathname});
    await page.locator('#hero-visual').scrollIntoViewIfNeeded();
    await page.waitForFunction(() => document.querySelector('#hero-visual').dataset.animation === 'playing');
    await page.waitForTimeout(1200);
    await page.locator('#hero-visual').screenshot({path:new URL(`graph-tracing-${width}.png`, shots).pathname});
    await page.locator('#pause-graph').click();
    const frozen = await page.locator('.edge-creator').evaluate(el=>el.style.strokeDashoffset);
    await page.waitForTimeout(250);
    assert.equal(await page.locator('.edge-creator').evaluate(el=>el.style.strokeDashoffset), frozen);
    await page.locator('#pause-graph').click();
    await page.waitForFunction(() => document.querySelector('#hero-visual').dataset.animation === 'complete', null, {timeout:12000});
    assert.equal(await page.locator('#pause-graph').textContent(), 'Replay');
    assert.ok(await page.locator('.staged-edge').evaluateAll(edges=>edges.every(edge=>Number(edge.style.strokeDashoffset) === 0)));
    assert.equal(await page.locator('.hub-node').evaluate(el=>el.style.getPropertyValue('--reached')), '1');
    await page.locator('#hero-visual').screenshot({path:new URL(`graph-complete-${width}.png`, shots).pathname});
    await page.locator('#pause-graph').click();
    await page.waitForFunction(() => document.querySelector('#hero-visual').dataset.animation === 'playing');
    await page.emulateMedia({reducedMotion:'reduce'});
    await page.waitForFunction(() => document.getElementById('pause-graph').disabled);
    assert.equal(await page.locator('#pause-graph').isDisabled(), true);
    assert.ok(await page.locator('.staged-edge').evaluateAll(edges=>edges.every(edge=>Number(edge.style.strokeDashoffset) === 0)));
    assert.equal(await page.locator('.graph-sparks').evaluate(el=>getComputedStyle(el).display), 'none');
    await page.evaluate(async () => {
      await Promise.all([...document.images].map(img=>{img.loading='eager'; return img.decode().catch(()=>{});}));
      scrollTo(0,0);
    });
    await page.screenshot({path:new URL(`home-${width}.png`, shots).pathname,fullPage:true});
    assert.deepEqual(errors, []);
    results.push({width,layout,scrollTriggered:true,pauseResume:true,finalHold:true,replay:true,reducedMotion:true,browserErrors:errors});
    await context.close();
    const staticContext = await browser.newContext({viewport:{width,height:1000},javaScriptEnabled:false});
    const staticPage = await staticContext.newPage();
    await staticPage.goto(base);
    assert.equal(await staticPage.locator('.hub-node .svg-title').evaluate(el=>getComputedStyle(el).opacity), '1');
    await staticContext.close();
  }
} finally { await browser.close(); }
await fs.writeFile(new URL('./polish-results.json',import.meta.url),JSON.stringify({checkedAt:new Date().toISOString(),results},null,2)+'\n');
console.log('PASS: 1440/390 layout, scroll trigger, pause/resume, final hold, replay, reduced motion, no-JS graph, no browser errors.');
