/** Normal-motion viewport regression checks for the merged Sniff site. */
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const base = process.env.SNIFF_QA_URL || 'http://127.0.0.1:8080';
assert.match(base, /^http:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/);
const b=await chromium.launch({headless:true});const results=[];
for (const width of [1440,390]) {
 const context=await b.newContext({viewport:{width,height:1000}}),page=await context.newPage();
 for(const mint of ['3LaVxn1Pp5gDjJZgGrpbQ8gRKj7GxgPE8cjF62Svpump','95JVHQQhHAPTJDVjw37ViiEwehstLEeX61Gbf13Upump']) {
  await page.goto(base+'/app?mint='+mint,{waitUntil:'networkidle'});
  await page.waitForFunction(()=>document.getElementById('answer-status').textContent==='Evidence ready');
  // Sample final rendered bounds after the configured 500 ms layout transition.
  await page.waitForTimeout(700);
  const viewport=await page.evaluate(()=>{const c=document.getElementById('graph')._cyreg.cy;return{zoom:c.zoom(),bounds:c.elements().renderedBoundingBox(),w:c.width(),h:c.height()}});
  assert.ok(viewport.zoom<=1.2);assert.ok(viewport.bounds.x1>=29&&viewport.bounds.y1>=29&&viewport.bounds.x2<=viewport.w-29&&viewport.bounds.y2<=viewport.h-29,JSON.stringify(viewport));
  await page.locator('#verdict [data-e]').first().click();
  await page.waitForFunction(()=>!document.getElementById('graph')._cyreg.cy.animated());
  assert.ok(await page.evaluate(()=>document.getElementById('graph')._cyreg.cy.zoom()<=1.2));
  results.push({width,mint,viewport});
 }
 await context.close();
}
await b.close();await fs.writeFile(new URL('./viewport-results-merged.json', import.meta.url),JSON.stringify({generated:new Date().toISOString(),checks:results},null,2)+'\n');console.log('PASS four animated graph viewports and evidence transitions');
