/** Browser half of the local shared-key contract. Run the companion fixture server on port 8081. */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const {chromium} = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = 'http://127.0.0.1:8081';
const output = new URL('./shots-qb/pass-2/', import.meta.url);
await fs.mkdir(output, {recursive:true});
const browser = await chromium.launch({headless:true});
const checks=[];
try {
  for (const width of [1440,390]) {
    const context=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'});
    const page=await context.newPage();
    const errors=[],requests=[];
    page.on('pageerror', error=>errors.push(error.message));
    page.on('request', request=>{if(request.url().endsWith('/api/ask'))requests.push(request);});
    await page.goto(base+'/app?mint=3LaVxn1Pp5gDjJZgGrpbQ8gRKj7GxgPE8cjF62Svpump',{waitUntil:'networkidle'});
    await page.waitForFunction(()=>document.getElementById('answer-status').textContent==='Evidence ready');
    assert.equal(await page.evaluate(()=>sessionStorage.getItem('sniff.claudeKey')),null);
    assert.equal(requests.length,1);
    assert.equal(requests[0].headers()['x-anthropic-key'],undefined);
    assert.equal(await page.locator('#mode').textContent(),'Written by Claude from graph evidence');
    assert.doesNotMatch(await page.locator('#note').textContent(),/Add a Claude key/);
    assert.ok(await page.locator('#verdict [data-e="E1"]').count());
    await page.locator('#verdict [data-e="E1"]').click();
    assert.equal(await page.locator('#verdict [data-e="E1"]').getAttribute('aria-pressed'),'true');
    await page.locator('#results').scrollIntoViewIfNeeded();
    await page.screenshot({path:new URL(`app-shared-key-${width}.png`,output).pathname,fullPage:true});
    await page.goto(base+'/settings',{waitUntil:'networkidle'});
    assert.match(await page.locator('#youText').textContent(),/Using Sniff’s shared key/);
    assert.doesNotMatch(await page.locator('#youText').textContent(),/Add a key/);
    await page.screenshot({path:new URL(`settings-shared-key-${width}.png`,output).pathname,fullPage:true});
    assert.equal(errors.length,0,JSON.stringify(errors));
    checks.push({width,anonymous:true,visitorKeyHeader:false,claudeAnswer:true,interactiveCitation:true,sharedKeyStatus:true});
    await context.close();
  }
} finally {await browser.close();}
await fs.writeFile(new URL('./qb-shared-key-results.json',import.meta.url),JSON.stringify({generated:new Date().toISOString(),base,checks},null,2)+'\n');
console.log('PASS anonymous shared-key answer, evidence selection and active settings at both viewports.');
