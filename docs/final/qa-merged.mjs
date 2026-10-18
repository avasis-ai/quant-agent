/** Merged-site browser acceptance and screenshots. See MERGE-RESULT.md for invocation. */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.SNIFF_QA_URL || 'http://127.0.0.1:8080';
assert.match(base, /^http:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/, 'QA mutations must remain on the local app.');
const directory = path.dirname(fileURLToPath(import.meta.url));
const shots = path.join(directory, 'shots-merged');
await fs.mkdir(shots, { recursive: true });
const browser = await chromium.launch({ headless: true, ...(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {}) });
const checks = [], errors = [], accessibility = [], expectedHttpErrors = [];
const mint = '3LaVxn1Pp5gDjJZgGrpbQ8gRKj7GxgPE8cjF62Svpump';
const coinPath = '/app?mint=' + mint;
const screenshot = async (page, name) => {
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.images].map(image => { image.loading = 'eager'; return image.decode().catch(() => {}); }));
  });
  await page.evaluate(() => { if (typeof document.activeElement?.blur === 'function') document.activeElement.blur(); scrollTo(0, 0); });
  await page.mouse.move(0, 0);
  await page.screenshot({ path: path.join(shots, name + '.png'), fullPage: true });
};
const ready = page => page.waitForFunction(() => document.getElementById('answer-status')?.textContent === 'Evidence ready' && !document.getElementById('go').disabled, null, { timeout: 20000 });
async function check(name, work) {
  await work(); checks.push(name); console.log('PASS', name);
}
function track(page) {
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => {
    if (!['error', 'warning'].includes(message.type())) return;
    if (/Failed to load resource.*status of (400|429)/.test(message.text())) expectedHttpErrors.push(message.text());
    else errors.push(message.text());
  });
  page.on('response', response => {
    if (response.url().startsWith(base + '/static/') && response.status() >= 400) errors.push('Static asset failed: ' + response.url());
  });
}
async function overflow(page) {
  const sizes = await page.evaluate(() => ({ document: document.documentElement.scrollWidth, viewport: innerWidth }));
  assert.ok(sizes.document <= sizes.viewport, JSON.stringify(sizes));
}
let AxeBuilder;
if (process.env.AXE_MODULE) ({ default: AxeBuilder } = await import(process.env.AXE_MODULE));
async function axe(page, label) {
  if (!AxeBuilder) return;
  const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
  accessibility.push({ page: label, violations: result.violations.map(violation => ({ id: violation.id, impact: violation.impact, nodes: violation.nodes.map(node => node.target) })) });
  assert.equal(result.violations.length, 0, JSON.stringify(accessibility.at(-1)));
}


async function graphViewport(page) {
  return page.locator('#graph').evaluate(container => {
    const cy = container._cyreg.cy;
    return { zoom: cy.zoom(), maximum: cy.maxZoom(), bounds: cy.elements().renderedBoundingBox(), width: cy.width(), height: cy.height() };
  });
}
async function assertGraphZoom(page) {
  const viewport = await graphViewport(page);
  assert.ok(viewport.zoom <= 1.2001 && viewport.maximum <= 1.2, JSON.stringify(viewport));
}
async function assertGraphFits(page) {
  const viewport = await graphViewport(page), { bounds, width, height } = viewport;
  await assertGraphZoom(page);
  assert.ok(bounds.x1 >= 29 && bounds.y1 >= 29 && bounds.x2 <= width - 29 && bounds.y2 <= height - 29, JSON.stringify(viewport));
}

try {
  for (const width of [1440, 390]) {
    const context = await browser.newContext({ viewport: { width, height: width === 1440 ? 1000 : 844 }, deviceScaleFactor: 1, reducedMotion: 'reduce', permissions: ['clipboard-read', 'clipboard-write'] });
    const page = await context.newPage(); track(page);
    await check(`Landing, snapshot and MCP at ${width}`, async () => {
      await page.goto(base, { waitUntil: 'networkidle' });
      assert.equal(await page.locator('[data-stat="coins"]').textContent(), '632,339');
      assert.equal(await page.locator('[data-stat="wallets"]').textContent(), '424,007');
      assert.equal(await page.locator('[data-stat="rings"]').textContent(), '6,556');
      assert.equal(await page.locator('[data-stat="links"]').textContent(), '1.5M');
      assert.equal(await page.locator('a[href="https://app.quantbase.live"]').count(), 1);
      assert.match(await page.locator('#tracks').textContent(), /Three tracks,[\s\S]*one product/);
      for (const route of ['/memory', '/brain', '/blog']) assert.ok(await page.locator(`.site-nav a[href="${route}"]`).count());
      assert.equal(await page.locator('.eval-table tbody tr').count(), 2);
      assert.equal(await page.locator('.eval-table tbody tr:last-child td:last-child').textContent(), '5');
      await screenshot(page, `home-${width}`);
      if (width === 1440) await page.screenshot({ path: path.join(shots, 'home-hero-1440.png') });
      await page.locator('[data-copy]').click();
      assert.equal(await page.evaluate(() => navigator.clipboard.readText()), 'claude mcp add --transport http sniff https://sniff.quantbase.live/mcp');
      await page.locator('[data-trace="2"]').click();
      assert.equal(await page.locator('#hero-visual').getAttribute('data-phase'), '2');
      assert.equal(await page.locator('#pause-graph').isDisabled(), true);
      await page.locator('body').click({ position: { x: 1, y: 1 } });
      await page.evaluate(() => scrollTo(0, 0));
      await overflow(page); await axe(page, `home-${width}`);
    });
    await check(`Home ask box hands mint to workspace at ${width}`, async () => {
      await page.locator('#home-question').fill(mint);
      await page.locator('.hero-ask button').click();
      await ready(page);
      assert.match(await page.locator('#card').textContent(), /METHU/);
      assert.equal(new URL(page.url()).pathname, '/app');
      assert.equal(new URL(page.url()).searchParams.get('mint'), mint);
    });
    await check(`Empty investigation at ${width}`, async () => {
      await page.goto(base + '/app', { waitUntil: 'networkidle' });
      assert.equal(await page.locator('#graph-empty').isVisible(), true);
      assert.equal(await page.locator('#zoom-in').isDisabled(), true);
      await screenshot(page, `app-empty-${width}`);
      await overflow(page); await axe(page, `app-empty-${width}`);
    });
    await check(`Search keyboard selection and real graph at ${width}`, async () => {
      await page.locator('#coin').fill('METHU');
      await page.waitForSelector('#sugg [role="option"]');
      await page.locator('#coin').press('ArrowDown');
      assert.equal(await page.locator('#coin').getAttribute('aria-activedescendant'), 'suggestion-0');
      await page.locator('#coin').press('Enter');
      assert.equal(await page.locator('#sugg').isVisible(), false);
      await page.locator('#form').evaluate(form => form.requestSubmit());
      await ready(page);
      await page.locator('#graph-details summary').click();
      const hubs = page.locator('#node-list button').filter({ hasText: 'Hub' });
      assert.ok(await hubs.count(), 'The other METHU ticker launch should show its recorded hub.');
      await hubs.first().click();
      assert.match(await page.locator('#evline').textContent(), /dead end/);
      // The ticker is shared by multiple launches. Capture the explicitly linked example.
      await page.goto(base + coinPath, { waitUntil: 'networkidle' });
      await ready(page);
      assert.match(await page.locator('#verdict').textContent(), /History, not a prediction/);
      assert.match(await page.locator('#graph-count').textContent(), /\d+ nodes · \d+ links/);
      assert.equal(await page.locator('#step-details').getAttribute('open'), null);
      await screenshot(page, `app-investigation-${width}`);
      await overflow(page); await axe(page, `app-investigation-${width}`);
      await assertGraphFits(page);
      const zoom = await page.locator('#zoom-value').textContent();
      await page.locator('#zoom-out').click();
      assert.notEqual(await page.locator('#zoom-value').textContent(), zoom);
      await page.locator('#zoom-in').click();
      await page.locator('#reset').click();
      await page.locator('#verdict [data-e="E2"]').click();
      assert.match(await page.locator('#evline').textContent(), /ATLi/);
      assert.equal(await page.locator('#verdict [data-e="E2"]').getAttribute('aria-pressed'), 'true');
      await assertGraphZoom(page);
      await screenshot(page, `app-evidence-${width}`);
      await page.locator('#reset').click();
      assert.equal(await page.locator('.ev.on').count(), 0);
      await page.locator('#graph-details summary').click();
      assert.ok(await page.locator('#node-list button').count() > 0);
      await page.locator('#node-list button').first().click();
      assert.notEqual(await page.locator('#evline').textContent(), 'Select a node or an evidence tag to follow a connection.');
      await page.locator('#copy-link').click();
      assert.equal(await page.evaluate(() => navigator.clipboard.readText()), page.url());
      await page.locator('#step-details summary').click();
      assert.match(await page.locator('#steps').textContent(), /Investigation complete/);
    });
    await check(`Settings and existing waitlist fallback at ${width}`, async () => {
      await page.goto(base + '/settings', { waitUntil: 'networkidle' });
      assert.equal(await page.locator('#youForm').isVisible(), true);
      assert.match(await page.locator('#youText').textContent(), /Fixed dossier|shared key/);
      await screenshot(page, `settings-${width}`);
      await overflow(page); await axe(page, `settings-${width}`);
      await page.goto(base + '/waitlist', { waitUntil: 'networkidle' });
      assert.equal(new URL(page.url()).pathname, '/');
      await screenshot(page, `waitlist-fallback-${width}`);
    });

    await check(`Real memory recall, provenance and keyboard graph selection at ${width}`, async () => {
      await page.goto(base + '/memory', { waitUntil: 'networkidle' });
      await screenshot(page, `memory-empty-${width}`);
      await page.locator('#my-session').click();
      await page.waitForFunction(() => /findings recalled/.test(document.getElementById('status').textContent));
      assert.ok(await page.locator('#findings .finding').count() > 0);
      assert.ok(await page.locator('#graph .graph-node').count() > 0);
      const first = page.locator('#graph .graph-node').first();
      await first.focus(); await first.press('Enter');
      assert.equal(await page.locator('#graph .graph-node.selected').count(), 1);
      assert.match(await page.locator('#detail').textContent(), /Session|Coin|Wallet|Question|Evidence/);
      await screenshot(page, `memory-session-${width}`);
      await page.locator('#query').fill(mint); await page.locator('#submit').click();
      await page.waitForFunction(() => /findings recalled/.test(document.getElementById('status').textContent) && !document.getElementById('submit').disabled);
      assert.match(await page.locator('#findings').textContent(), /coin_dossier|funding_trail/);
      await screenshot(page, `memory-${width}`); await overflow(page); await axe(page, `memory-${width}`);
      // Validation errors stay local and the form recovers to a real result.
      await page.locator('#query').fill('invalid'); await page.locator('#submit').click();
      await page.waitForFunction(() => document.getElementById('status').classList.contains('error'));
      assert.equal(await page.locator('#submit').isDisabled(), false);
      await page.locator('#query').fill(mint); await page.locator('#submit').click();
      await page.waitForFunction(() => !document.getElementById('submit').disabled && !document.getElementById('status').classList.contains('error'));
    });
    await check(`Company brain answers, sources and example questions at ${width}`, async () => {
      await page.goto(base + '/brain', { waitUntil: 'networkidle' });
      await screenshot(page, `brain-empty-${width}`);
      await page.locator('#submit').click();
      await page.waitForFunction(() => /retrieved/.test(document.getElementById('status').textContent));
      assert.ok(await page.locator('#sources .source').count() > 0);
      assert.ok(await page.locator('#answer a[href^="#source-B"]').count() > 0);
      assert.match(await page.locator('#answer').textContent(), /paper|Paper/);
      const section = page.locator('#graph .graph-node').filter({ has: page.locator('.node-kind', { hasText: /^Section$/ }) }).first();
      await section.focus(); await section.press('Enter');
      assert.match(await page.locator('#detail').textContent(), /Fetched|Read \[B/);
      await screenshot(page, `brain-${width}`); await overflow(page); await axe(page, `brain-${width}`);
      await page.locator('#answer a').first().click();
      assert.ok(new URL(page.url()).hash.startsWith('#source-B'));
      const source = page.locator(new URL(page.url()).hash);
      await source.locator('summary').click(); assert.equal(await source.locator('pre').isVisible(), true);
      await page.locator('[data-question]').nth(1).click();
      await page.waitForFunction(() => !document.getElementById('submit').disabled && /retrieved/.test(document.getElementById('status').textContent));
      assert.ok(await page.locator('#sources .source').count() > 0);
    });
    await check(`Local blog images and shared navigation at ${width}`, async () => {
      await page.goto(base + '/blog', { waitUntil: 'networkidle' });
      await screenshot(page, `blog-${width}`);
      assert.equal(await page.locator('img[src^="/blog-assets/"]').count(), 10);
      assert.ok(await page.locator('img').evaluateAll(images => images.every(image => image.complete && image.naturalWidth > 0)));
      await overflow(page); await axe(page, `blog-${width}`);
      if (width === 1440) await page.screenshot({ path: path.join(shots, 'blog-hero-1440.png') });
      if (width === 390) {
        await page.locator('.nav-menu summary').click();
        assert.equal(await page.locator('.nav-menu-links a[href="/memory"]').isVisible(), true);
        await axe(page, `mobile-navigation-${width}`);
        await page.screenshot({ path: path.join(shots, 'navigation-390.png') });
        await page.locator('.nav-menu-links a[href="/memory"]').click();
        assert.equal(new URL(page.url()).pathname, '/memory');
      }
    });
    await context.close();
  }

  await check('Responsive sweep from 320 to 1920, including laptop fold', async () => {
    const context = await browser.newContext({ reducedMotion: 'reduce' });
    const page = await context.newPage(); track(page);
    for (const width of [320, 375, 414, 640, 768, 1024, 1280, 1920]) {
      await page.setViewportSize({ width, height: 800 });
      for (const route of ['/', '/app', '/memory', '/brain', '/blog', '/settings']) {
        await page.goto(base + route, { waitUntil: 'networkidle' }); await overflow(page);
        if (width === 1280 && route === '/') {
          const bounds = await page.locator('.hero-ask').boundingBox();
          assert.ok(bounds.y + bounds.height < 800, 'Primary hero action must fit a 1280×800 laptop.');
        }
      }
    }
    await context.close();
  });

  await check('Recorded ring, shared-social and graduated examples', async () => {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
    const page = await context.newPage(); track(page);
    for (const [name, address] of [
      ['ring', '2f6jt6sR7CcuJ9sxWcqhXHBgE5r8kS3gXBJvaUWtpump'],
      ['socials', '95JVHQQhHAPTJDVjw37ViiEwehstLEeX61Gbf13Upump'],
      ['graduated', 'wV46Y351erjX7CiAyRRvzJgeWdtqpHXXBmv9LVzpump'],
    ]) {
      await page.goto(base + '/app?mint=' + address, { waitUntil: 'networkidle' }); await ready(page);
      assert.match(await page.locator('#graph-count').textContent(), /[1-9]\d* nodes/);
      if (name === 'socials') assert.match(await page.locator('#node-list').textContent(), /Handle/);
      if (name === 'graduated') assert.equal(await page.locator('#card .tag.grad').count(), 1);
      await assertGraphFits(page);
      await overflow(page); await axe(page, `app-${name}-1440`);
      await screenshot(page, `app-${name}-1440`);
    }
    await context.close();
  });

  await check('Unknown coin has an honest empty graph', async () => {
    const context = await browser.newContext({ reducedMotion: 'reduce' });
    const page = await context.newPage(); track(page);
    await page.goto(base + '/app?mint=11111111111111111111111111111111', { waitUntil: 'networkidle' }); await ready(page);
    assert.equal(await page.locator('#graph-empty').isVisible(), true);
    assert.match(await page.locator('#graph-empty h3').textContent(), /No recorded connections/);
    assert.match(await page.locator('#verdict').textContent(), /not in|isn’t in|isn't in/);
    assert.equal(await page.locator('#zoom-in').isDisabled(), true);
    await context.close();
  });

  await check('Partial SSE chunks, streaming steps and CRLF boundaries', async () => {
    const response = await fetch(base + '/api/ask', { method: 'POST', headers: { 'content-type': 'application/json', accept: 'text/event-stream' }, body: JSON.stringify({ mint, question: 'Who is behind this coin?' }) });
    assert.ok(response.ok);
    const sse = await response.text();
    for (const width of [1440, 390]) {
      const context = await browser.newContext({ viewport: { width, height: width === 1440 ? 1000 : 844 }, reducedMotion: 'reduce' });
      const page = await context.newPage(); track(page);
      await page.addInitScript(({ sse }) => {
        const original = window.fetch.bind(window);
        window.fetch = (url, options) => {
          if (String(url) !== '/api/ask') return original(url, options);
          const events = sse.trim().split('\n\n');
          const encoder = new TextEncoder();
          return Promise.resolve(new Response(new ReadableStream({ start(controller) {
            events.forEach((event, index) => setTimeout(() => {
              const bytes = encoder.encode(event.replace(/\n/g, '\r\n') + '\r\n\r\n');
              controller.enqueue(bytes.slice(0, -1));
              setTimeout(() => { controller.enqueue(bytes.slice(-1)); if (index === events.length - 1) controller.close(); }, 10);
            }, index * 650));
          } }), { headers: { 'content-type': 'text/event-stream' } }));
        };
      }, { sse });
      await page.goto(base + coinPath, { waitUntil: 'networkidle' });
      await page.waitForFunction(() => document.querySelectorAll('#steps .ok').length > 0);
      assert.equal(await page.locator('#go').isDisabled(), true);
      await screenshot(page, `app-streaming-${width}`);
      await ready(page);
      assert.equal(await page.locator('#go').isDisabled(), false);
      await context.close();
    }
  });

  await check('API error recovers and stale search suggestions cannot select a different coin', async () => {
    const context = await browser.newContext({ reducedMotion: 'reduce' });
    const page = await context.newPage(); track(page);
    await page.goto(base + '/app', { waitUntil: 'networkidle' });
    await page.locator('#coin').fill('METHU'); await page.waitForSelector('#sugg [role="option"]');
    await page.locator('#coin').fill('UNKNOWN-COIN-NAME');
    await page.route('**/api/ask', route => {
      assert.equal(JSON.parse(route.request().postData()).mint, null);
      return route.fulfill({ status: 429, contentType: 'application/json', body: JSON.stringify({ error: 'Fixture: hourly allowance reached. Try again later.' }) });
    });
    await page.locator('#go').click();
    await page.waitForFunction(() => document.getElementById('note').classList.contains('err'));
    assert.match(await page.locator('#note').textContent(), /hourly allowance/);
    assert.equal(await page.locator('#go').isDisabled(), false);
    await page.waitForTimeout(350); // A pending search must not reopen after submit.
    assert.equal(await page.locator('#sugg').isVisible(), false);
    await page.unroute('**/api/ask');
    await page.locator('#chips button').first().click(); await ready(page);
    await context.close();
  });

  await check('Visitor and owner settings lifecycle with local browser fixtures', async () => {
    const context = await browser.newContext({ reducedMotion: 'reduce' });
    const page = await context.newPage(); track(page);
    let admin = false, active = true, visitorChecks = 0;
    await page.route('**/api/settings/**', async route => {
      const request = route.request(), pathname = new URL(request.url()).pathname;
      assert.ok(!request.url().includes('browser-fixture-key'));
      let status = 200, result = { ok: true };
      const owner = () => ({ active, model: active ? 'fixture-claude' : null, ...(admin ? { last4: '…test' } : {}) });
      if (pathname.endsWith('/status')) result = { admin, owner: owner() };
      else if (pathname.endsWith('/visitor-check')) {
        assert.equal(request.headers()['x-anthropic-key'], 'browser-fixture-key');
        visitorChecks++; status = visitorChecks === 1 ? 400 : 200;
        result = status === 400 ? { error: 'Fixture: key rejected.' } : { ok: true, model: 'fixture-claude' };
      } else if (pathname.endsWith('/login')) { admin = true; result = { ok: true, owner: owner() }; }
      else if (pathname.endsWith('/logout')) admin = false;
      else if (pathname.endsWith('/owner-key')) { active = request.method() !== 'DELETE'; result = { ok: true, owner: owner() }; }
      else throw new Error('Unexpected settings request');
      await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(result) });
    });
    await page.route('**/api/ai/ping', route => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ ok: true, model: 'fixture-claude', reply: 'Sniff is ready.' }) }));
    await page.goto(base + '/settings', { waitUntil: 'networkidle' });
    await page.locator('#youKey').fill('browser-fixture-key'); await page.locator('#youSave').click();
    await page.waitForFunction(() => document.getElementById('youMsg').classList.contains('err'));
    assert.equal(await page.evaluate(() => sessionStorage.getItem('sniff.claudeKey')), null);
    await page.locator('#youSave').click(); await page.waitForSelector('#youActions:not(.hidden)');
    assert.equal(await page.evaluate(() => sessionStorage.getItem('sniff.claudeKey')), 'browser-fixture-key');
    await page.locator('#youTest').click();
    await page.waitForFunction(() => document.getElementById('youMsg').textContent.includes('Sniff is ready.'));
    await page.locator('#youForget').click();
    assert.equal(await page.evaluate(() => sessionStorage.getItem('sniff.claudeKey')), null);
    await page.locator('#ownerOpen').click();
    assert.equal(await page.locator('#pass').evaluate(input => input === document.activeElement), true);
    await page.locator('#pass').fill('fixture-passcode'); await page.locator('#unlock').click();
    await page.waitForSelector('#manage:not(.hidden)');
    await page.locator('#ownKey').fill('browser-fixture-key'); await page.locator('#ownSave').click();
    await page.waitForFunction(() => document.getElementById('ownMsg').textContent.includes('activated'));
    await page.locator('#ownRemove').click();
    await page.waitForFunction(() => document.getElementById('ownMsg').textContent.includes('removed'));
    await page.locator('#logout').click(); await page.waitForSelector('#lock:not(.hidden)');
    await context.close();
  });

  assert.equal(errors.length, 0, JSON.stringify(errors));
} finally {
  await fs.writeFile(path.join(directory, 'browser-results-merged.json'), JSON.stringify({ generated: new Date().toISOString(), base, checks, browserErrors: errors, expectedHttpErrors, accessibility }, null, 2) + '\n');
  await browser.close();
}
console.log(`${checks.length} browser acceptance groups passed; ${accessibility.length} accessibility scans; ${errors.length} browser errors.`);
