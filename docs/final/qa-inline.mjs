/** Inline demo acceptance. Loopback only, real snapshot and /api/ask; no deployed writes. */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.SNIFF_QA_URL || 'http://127.0.0.1:8080';
assert.match(base, /^http:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/);
const dir = path.dirname(fileURLToPath(import.meta.url));
const shots = path.join(dir, 'shots-inline');
await fs.mkdir(shots, { recursive: true });
let AxeBuilder;
if (process.env.AXE_MODULE) ({ default: AxeBuilder } = await import(process.env.AXE_MODULE));
const checks = [], errors = [], accessibility = [], dossiers = [];
const coins = [
  ['METHU', '3LaVxn1Pp5gDjJZgGrpbQ8gRKj7GxgPE8cjF62Svpump'],
  ['Subprime Cat', '2f6jt6sR7CcuJ9sxWcqhXHBgE5r8kS3gXBJvaUWtpump'],
  ['Women in Finance', '95JVHQQhHAPTJDVjw37ViiEwehstLEeX61Gbf13Upump'],
  ['Higher', 'wV46Y351erjX7CiAyRRvzJgeWdtqpHXXBmv9LVzpump'],
  ['Agent Alley', '251ndGnv5tN45Fr4jpBtSeuvfyEZCN6Jk7K9u9pgpump'],
  ['Chill House Vrax', 'b1U8BazMzFbrCpD2rLmVTbiJSdHUh7mUWy3dn5Spump'],
];
async function check(name, run) { await run(); checks.push(name); console.log('PASS', name); }
async function inlineReady(page) {
  await page.waitForFunction(() => document.getElementById('inline-status').textContent.startsWith('Evidence ready') && !document.querySelector('#inline-form button').disabled);
  await page.waitForFunction(() => !document.getElementById('inline-graph')._cyreg?.cy?.animated());
  await page.waitForTimeout(550);
}
async function appReady(page) { await page.waitForFunction(() => document.getElementById('answer-status').textContent === 'Evidence ready' && !document.getElementById('go').disabled); }
async function verify(page, name) {
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), name + ' overflow');
  if (AxeBuilder) {
    const result = await new AxeBuilder({ page }).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
    accessibility.push({ name, violations: result.violations.map(v => ({ id: v.id, impact: v.impact, targets: v.nodes.map(n => n.target) })) });
    assert.equal(result.violations.length, 0, JSON.stringify(accessibility.at(-1)));
  }
}
const browser = await chromium.launch({ headless: true });
try {
  for (const [name, mint] of coins) {
    const response = await fetch(base + '/api/dossier?mint=' + mint);
    assert.ok(response.ok);
    const body = await response.json();
    assert.equal(body.coin_dossier.found, true);
    assert.equal(body.coin_dossier.coin.name, name);
    dossiers.push({ name, mint, evidence: body.evidence.length, ring: body.coin_dossier.ring?.creators || null, graduated: body.coin_dossier.coin.graduated, funder: body.coin_dossier.funders[0]?.label });
  }
  checks.push('All six suggestion mints return real snapshot dossiers');
  for (const width of [1440, 390]) {
    const context = await browser.newContext({ viewport: { width, height: width === 1440 ? 1000 : 844 } });
    const page = await context.newPage();
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(base + '/', { waitUntil: 'networkidle' });
    await verify(page, 'home-' + width);
    await page.screenshot({ path: path.join(shots, `home-${width}.png`) });
    for (const [name, mint] of width === 1440 ? coins : [coins[1],coins[2],coins[3]]) {
      await check(`Inline ${name} at ${width}: dossier, citations, graph, full link, no navigation`, async () => {
        await page.locator(`.inline-examples [data-inline-mint="${mint}"]`).click();
        await inlineReady(page);
        assert.equal(new URL(page.url()).pathname, '/');
        assert.equal(await page.locator('#inline-title').textContent(), name);
        assert.equal(await page.locator('.inline-coin strong').textContent(), name);
        assert.ok(await page.locator('#inline-answer [data-inline-e^="E"]').count());
        const graph = await page.locator('#inline-graph').evaluate(n => ({ focus: n._cyreg.cy.nodes('.focus').map(n=>n.id()), nodes: n._cyreg.cy.nodes().map(n=>({id:n.id(),kind:n.data('kind')})) }));
        assert.deepEqual(graph.focus, ['coin:' + mint]);
        assert.ok(graph.nodes.length >= 3);
        if (name === 'Chill House Vrax') assert.ok(graph.nodes.some(n=>n.kind==='hub'));
        const link = new URL(await page.locator('#inline-full').getAttribute('href'), base);
        assert.equal(link.searchParams.get('mint'), mint);
        assert.equal(link.searchParams.get('q'), 'Who is behind this coin?');
        const cite = page.locator('#inline-answer [data-inline-e]').first();
        await cite.click();
        assert.equal(await cite.getAttribute('aria-pressed'), 'true');
        assert.match(await page.locator('#inline-selection').textContent(), /^\[E\d+\]/);
        await page.locator('#inline-fit').click();
        await verify(page, name + '-' + width);
        await page.locator('#inline-demo').screenshot({ style: '.site-header { visibility: hidden !important; }', path: path.join(shots, `inline-${name.toLowerCase().replaceAll(' ','-')}-${width}.png`) });
      });
    }
    await check(`Hero question resolves a coin and preserves the question at ${width}`, async () => {
      await page.locator('#home-question').fill('Who funded Subprime Cat?');
      await page.locator('#inline-form button').click();
      await inlineReady(page);
      assert.equal(await page.locator('#inline-title').textContent(), 'Subprime Cat');
      const link = new URL(await page.locator('#inline-full').getAttribute('href'), base);
      assert.equal(link.searchParams.get('q'), 'Who funded Subprime Cat?');
      await page.locator('#inline-full').click();
      await appReady(page);
      assert.equal(await page.locator('#coin').inputValue(), 'Subprime Cat');
      assert.equal(await page.locator('#q').inputValue(), 'Who funded Subprime Cat?');
    });
    await check(`/app?q= resolves a new coin after METHU in the same session at ${width}`, async () => {
      await page.goto(base + '/app?mint=' + coins[0][1]);
      await appReady(page);
      await page.goto(base + '/app?q=Subprime%20Cat');
      await appReady(page);
      assert.equal(await page.locator('#coin').inputValue(), 'Subprime Cat');
      assert.equal(await page.locator('#q').inputValue(), '');
      assert.match(await page.locator('#card').textContent(), /Subprime Cat/);
      assert.doesNotMatch(await page.locator('#card').textContent(), /METHU/);
      await verify(page, 'app-q-' + width);
      await page.screenshot({ path: path.join(shots, `app-q-subprime-${width}.png`), fullPage: true });
    });
    await check(`Unknown coin is explicit on both pages and sends no /api/ask at ${width}`, async () => {
      await page.goto(base + '/');
      let asks = 0;
      const count = req => { if (new URL(req.url()).pathname === '/api/ask') asks++; };
      page.on('request', count);
      await page.locator('#home-question').fill('ZzzzzNotASnapshotCoin999999');
      await page.locator('#inline-form button').click();
      await page.waitForFunction(() => !document.getElementById('inline-retry').hidden);
      assert.match(await page.locator('#inline-status').textContent(), /Not in our snapshot \(ends 14 Oct 2026\)/);
      assert.equal(await page.locator('#inline-full').isVisible(), false);
      await verify(page, 'unknown-' + width);
      await page.locator('#inline-demo').screenshot({ style: '.site-header { visibility: hidden !important; }', path: path.join(shots, `inline-unknown-${width}.png`) });
      await page.goto(base + '/app?q=ZzzzzNotASnapshotCoin999999');
      await page.waitForFunction(() => document.getElementById('answer-status').textContent === 'Coin not found');
      assert.match(await page.locator('#resolve-note').textContent(), /ends 14 Oct 2026/);
      assert.equal(asks, 0);
      page.off('request', count);
    });
    await context.close();
  }
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
  const page = await context.newPage();
  page.on('pageerror', e => errors.push(e.message));
  await check('Reduced motion, ticker and mint entry, rate-limit error and retry', async () => {
    await page.goto(base + '/');
    await page.locator('#home-question').fill('$METHU');
    await page.locator('#inline-form button').click();
    await inlineReady(page);
    assert.equal(await page.locator('#inline-title').textContent(), 'METHU');
    assert.equal(await page.locator('#inline-demo').evaluate(n=>getComputedStyle(n).animationName), 'none');
    await page.locator('#home-question').fill(coins[3][1]);
    await page.locator('#inline-form button').click();
    await inlineReady(page);
    assert.equal(await page.locator('#inline-title').textContent(), 'Higher');
    await page.route('**/api/ask', route => route.fulfill({ status: 429, contentType:'application/json', body:JSON.stringify({error:'Too many tries. Wait 1 min.'}) }), { times: 1 });
    await page.locator('.inline-examples [data-inline-mint="' + coins[1][1] + '"]').click();
    await page.waitForFunction(() => document.getElementById('inline-status').textContent.startsWith('Too many tries'));
    assert.equal(await page.locator('#inline-dossier').isVisible(), true);
    assert.equal(await page.locator('#inline-retry').isVisible(), true);
    await page.locator('#inline-again').click();
    await inlineReady(page);
    assert.equal(await page.locator('#inline-title').textContent(), 'Subprime Cat');
    await verify(page, 'reduced-motion');
    await page.locator('#inline-demo').screenshot({ style: '.site-header { visibility: hidden !important; }', path: path.join(shots, 'inline-reduced-motion-390.png') });
  });
  await check('Ambiguous ticker exposes a mint picker and changes the investigated coin', async () => {
    await page.locator('#home-question').fill('$SPCAT');
    await page.locator('#inline-form button').click();
    await inlineReady(page);
    assert.equal(await page.locator('#inline-matches').isVisible(), true);
    assert.ok(await page.locator('#inline-match-select option').count() > 1);
    await page.locator('#inline-match-select').selectOption(coins[1][1]);
    await inlineReady(page);
    assert.equal(await page.locator('#inline-title').textContent(), 'Subprime Cat');
    assert.equal(new URL(await page.locator('#inline-full').getAttribute('href'),base).searchParams.get('mint'),coins[1][1]);
  });
  await check('Rapid chip switching cancels the previous request', async () => {
    await page.locator('.inline-examples [data-inline-mint="' + coins[0][1] + '"]').click();
    await page.locator('.inline-examples [data-inline-mint="' + coins[3][1] + '"]').click();
    await inlineReady(page);
    assert.equal(await page.locator('#inline-title').textContent(), 'Higher');
    assert.match(await page.locator('#inline-full').getAttribute('href'), new RegExp(coins[3][1]));
  });
  await check('AI verdict mode renders clickable E citations without a key prompt', async () => {
    // Mock only the model-mode stream; the dossier and graph remain real snapshot reads.
    const response = await fetch(base + '/api/ask', { method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({mint:coins[1][1],question:'Who is behind this coin?'}) });
    assert.ok(response.ok);
    const actual = await response.json();
    const events = [{type:'start',mode:'agent',using:'owner'},...actual.steps,{type:'evidence',items:actual.evidence},{...actual.verdict,type:'verdict',mode:'agent'},{type:'done',ms:100}];
    await page.route('**/api/ask', route=>route.fulfill({status:200,contentType:'text/event-stream',body:events.map(e=>'data: '+JSON.stringify(e)+'\n\n').join('')}), {times:1});
    await page.locator('.inline-examples [data-inline-mint="' + coins[1][1] + '"]').click();
    await inlineReady(page);
    assert.equal(await page.locator('#inline-mode').textContent(), 'Written by Claude from graph evidence');
    assert.ok(await page.locator('#inline-answer [data-inline-e^="E"]').count());
    assert.doesNotMatch(await page.locator('#inline-demo').textContent(), /add.*key|enter.*key|settings/i);
  });
  await context.close();
  assert.deepEqual(errors, []);
} finally {
  await browser.close();
  await fs.writeFile(path.join(dir,'inline-browser-results.json'), JSON.stringify({generated:new Date().toISOString(),base,checks,errors,accessibility,dossiers,ai_note:'No local owner key configured. Real graph/dossier streaming tested. AI display uses a mocked agent-mode stream; shared-owner tool calls, citations and caps are separately covered by pytest.'},null,2)+'\n');
}
console.log(`PASS ${checks.length} checks, ${accessibility.length} accessibility scans, ${errors.length} page errors.`);
