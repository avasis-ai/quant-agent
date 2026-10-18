/** Review-fix acceptance checks. All requests and the MCP note stay on loopback. */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.SNIFF_QA_URL || 'http://127.0.0.1:8080';
assert.match(base, /^http:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/, 'QA writes must stay local.');
const directory = path.dirname(fileURLToPath(import.meta.url));
const shots = path.join(directory, 'shots-fixes');
await fs.mkdir(shots, { recursive: true });
const mint = '3LaVxn1Pp5gDjJZgGrpbQ8gRKj7GxgPE8cjF62Svpump';
const checks = [], errors = [], accessibility = [];
let AxeBuilder;
if (process.env.AXE_MODULE) ({ default: AxeBuilder } = await import(process.env.AXE_MODULE));

async function request(url, body) {
  const response = await fetch(base + url, body ? { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) } : {});
  assert.ok(response.ok, `${url}: ${response.status}`);
  return response.json();
}
async function rpc(method, params) {
  const response = await fetch(base + '/mcp', { method: 'POST', headers: { accept: 'application/json, text/event-stream', 'content-type': 'application/json' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method, params }) });
  assert.ok(response.ok);
  const result = await response.json();
  assert.ok(!result.error && !result.result.isError, JSON.stringify(result));
  return result.result;
}
async function check(name, run) { await run(); checks.push(name); console.log('PASS', name); }
async function ready(page) {
  await page.waitForFunction(() => document.getElementById('answer-status').textContent === 'Evidence ready' && !document.getElementById('go').disabled);
  await page.waitForFunction(() => !document.getElementById('graph')._cyreg.cy.animated());
}
async function trackReady(page) {
  await page.waitForFunction(() => /recalled|retrieved/.test(document.getElementById('status').textContent) && !document.getElementById('submit').disabled);
}
async function verifyPage(page, name) {
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), name + ' overflows');
  if (AxeBuilder) {
    const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
    accessibility.push({ name, violations: result.violations.map(v => ({ id: v.id, impact: v.impact, targets: v.nodes.map(n => n.target) })) });
    assert.equal(result.violations.length, 0, JSON.stringify(accessibility.at(-1)));
  }
}
async function capture(page, name) {
  await page.evaluate(async () => { await document.fonts.ready; document.activeElement?.blur(); scrollTo({ top: 0, left: 0, behavior: 'instant' }); });
  await page.waitForFunction(() => scrollY === 0);
  await page.screenshot({ path: path.join(shots, name + '.png'), fullPage: true });
}

await check('Local second agent recalls real evidence and attaches an explicitly unverified MCP note', async () => {
  await rpc('initialize', { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 'review-fix-qa', version: '1' } });
  await rpc('tools/call', { name: 'coin_dossier', arguments: { mint } });
  const recalled = await rpc('tools/call', { name: 'memory_recall', arguments: { entity: 'coin:' + mint } });
  const data = recalled.structuredContent || JSON.parse(recalled.content[0].text);
  assert.ok(data.result.rows.length);
  if (!data.result.notes.some(n => n.by === 'review-fix-qa-agent')) {
    await rpc('tools/call', { name: 'memory_note', arguments: { entity: 'coin:' + mint, by: 'review-fix-qa-agent', text: 'Local QA observation: inspected the public METHU launch history; this note is not a verified lineage finding.', evidence_ids: [data.result.rows[0].evidence_ids[0]] } });
  }
});

const browser = await chromium.launch({ headless: true });
try {
  for (const width of [1440, 390]) {
    const context = await browser.newContext({ viewport: { width, height: width === 1440 ? 1000 : 844 } });
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (['error', 'warning'].includes(message.type())) errors.push(message.text()); });
    await check(`/app brain citations, complete returned graph and mode-specific key banner at ${width}`, async () => {
      const question = 'How does QuantBase handle paper vs live?';
      const result = await request('/api/brain/ask', { question });
      await page.goto(base + '/app?q=' + encodeURIComponent(question), { waitUntil: 'networkidle' });
      await ready(page);
      assert.equal(await page.locator('#mode').textContent(), 'Public source excerpts');
      assert.equal(await page.locator('#map-title').textContent(), 'Public source graph');
      assert.doesNotMatch(await page.locator('.legend').textContent(), /Wallet|Hub/);
      assert.doesNotMatch(await page.locator('#note').textContent(), /key|dossier/i);
      assert.equal(await page.locator('#cardPanel').isVisible(), false);
      assert.equal(await page.locator('#verdict [data-e^="B"]').count(), result.cited.length);
      const graph = await page.locator('#graph').evaluate(node => ({ ids: node._cyreg.cy.nodes().map(n => n.id()), edgeTypes: node._cyreg.cy.edges().map(e => e.data('type')) }));
      assert.deepEqual(graph.ids.sort(), result.graph.nodes.map(n => n.key).sort());
      assert.ok(graph.edgeTypes.includes('MENTIONS') && graph.edgeTypes.includes('PART_OF'));
      assert.equal(await page.locator('#node-list button').filter({ hasText: /Wallet ·/ }).count(), 0);
      await page.locator('#verdict [data-e="B1"]').click();
      assert.equal(await page.locator('#source-details').getAttribute('open'), '');
      assert.equal(await page.locator('#source-B1 details').getAttribute('open'), '');
      assert.equal(await page.locator('#source-B1 pre').textContent(), result.sources[0].text);
      assert.equal(await page.locator('#source-B1 h3 a').getAttribute('href'), result.sources[0].url);
      assert.equal(await page.locator('.brain-source').count(), result.sources.length);
      assert.ok((await page.locator('.brain-source h3 a').evaluateAll(links => links.map(a => a.href))).every(url => !url.includes('/final/tracks/')));
      await verifyPage(page, 'app-brain-' + width);
      await capture(page, 'app-brain-' + width);
      // Change modes on the same page, checking that source panels do not leak.
      await page.locator(`#chips [data-mint="${mint}"]`).click();
      await ready(page);
      assert.match(await page.locator('#mode').textContent(), /Fixed dossier/);
      assert.match(await page.locator('#note').textContent(), /Claude key/);
      assert.equal(await page.locator('.brain-source').count(), 0);
    });
    await check(`/memory one-click METHU, second-agent attribution and fit/zoom at ${width}`, async () => {
      await page.goto(base + '/memory', { waitUntil: 'networkidle' });
      assert.match(await page.locator('#notes-title').textContent(), /Second-agent/);
      await page.locator('#see-methu').click();
      await trackReady(page);
      assert.match(page.url(), /entity=coin/);
      assert.ok(await page.locator('#findings .finding').count());
      const note = page.locator('#agent-notes .finding').filter({ hasText: 'review-fix-qa-agent' });
      assert.equal(await note.count(), 1);
      assert.equal(await note.locator('.note-label').textContent(), 'agent note · not verified');
      assert.match(await note.textContent(), /Source evidence:/);
      const fit = await page.locator('#graph').evaluate(node => ({ pane: node.clientWidth, svg: node.querySelector('svg').getBoundingClientRect().width }));
      assert.ok(fit.svg <= fit.pane, JSON.stringify(fit));
      await page.locator('#graph-zoom-in').click();
      assert.ok(await page.locator('#graph').evaluate(node => node.querySelector('svg').getBoundingClientRect().width > node.clientWidth));
      await page.locator('#graph-fit').click();
      assert.ok(await page.locator('#graph').evaluate(node => node.querySelector('svg').getBoundingClientRect().width <= node.clientWidth));
      const graphNote = page.locator('#graph .graph-node').filter({ hasText: 'Note' }).first();
      await graphNote.focus(); await graphNote.press('Enter');
      assert.match(await page.locator('#detail').textContent(), /agent note · not verified/);
      await verifyPage(page, 'memory-' + width);
      if (width === 390) await capture(page, 'memory-' + width);
    });
    await check(`/brain examples have clean complete excerpts and preserve original sections at ${width}`, async () => {
      await page.goto(base + '/brain', { waitUntil: 'networkidle' });
      for (const button of await page.locator('[data-question]').all()) {
        await button.click(); await trackReady(page);
        const answer = await page.locator('#answer').textContent();
        assert.doesNotMatch(answer, /\*\*|(?:^|\n)\s*- |…/);
        assert.ok(await page.locator('#sources .source').count());
        await page.locator('#answer a').first().click();
        const source = page.locator(new URL(page.url()).hash);
        await source.locator('summary').click();
        assert.equal(await source.locator('pre').isVisible(), true);
        await verifyPage(page, 'brain-example-' + width);
      }
      assert.match(await page.locator('#answer p').first().textContent(), /private key|privacy policy/i);
      if (width === 390) await capture(page, 'brain-' + width);
    });
    await check(`/blog matches the corrected evidence and source-only descriptions at ${width}`, async () => {
      await page.goto(base + '/blog', { waitUntil: 'networkidle' });
      const story = await page.locator('#story').textContent();
      assert.match(story, /every sentence must cite evidence of the matching kind; the server rejects answers that don't/);
      assert.match(story, /does not verify that every claim is true/);
      assert.match(story, /source-only corpus of 12 public documents/);
      assert.match(story, /eight model\/tool rounds/);
      assert.doesNotMatch(story, /every sentence has to prove itself|falls back to a FalkorDB/);
      assert.equal(await page.locator('img[src^="/blog-assets/"]').count(), 10);
      await page.locator('img[src^="/blog-assets/"]').evaluateAll(images => Promise.all(images.map(i => { i.loading = 'eager'; return i.decode(); })));
      await verifyPage(page, 'blog-' + width);
    });
    await context.close();
  }
  assert.deepEqual(errors, []);
} finally {
  await browser.close();
  await fs.writeFile(path.join(directory, 'fix-browser-results.json'), JSON.stringify({ generated: new Date().toISOString(), checks, errors, accessibility, note_scope: 'Local loopback database only; no production note was posted.' }, null, 2) + '\n');
}
console.log(`PASS ${checks.length} review-fix checks; no console errors or accessibility violations.`);
