/** Hero motion, reduced-motion switching, video fallback, image failure and keyboard checks. */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const browser=await chromium.launch({headless:true});const checks=[];
const base=process.env.SNIFF_QA_URL || 'http://127.0.0.1:8080';
assert.match(base,/^http:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/);
try {
 for(const width of [1440,390]){
  const context=await browser.newContext({viewport:{width,height:1000},reducedMotion:'no-preference'});
  const page=await context.newPage();
  await page.goto(base,{waitUntil:'networkidle'});
  assert.equal(await page.locator('#pause-flow').isDisabled(),false);
  await page.waitForFunction(()=>document.querySelector('.flow-trace').getAnimations()[0]?.currentTime>100);
  await page.locator('#pause-flow').click();
  assert.equal(await page.locator('#hero-flow').getAttribute('data-flow'),'paused');
  assert.equal(await page.locator('#pause-flow').getAttribute('aria-pressed'),'true');
  assert.ok(await page.locator('.flow-trace').evaluateAll(paths=>paths.every(path=>path.getAnimations().every(animation=>animation.playState==='paused'))));
  await page.locator('#pause-flow').click();
  assert.equal(await page.locator('#hero-flow').getAttribute('data-flow'),'playing');
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.waitForFunction(()=>document.getElementById('pause-flow').disabled && document.getElementById('pause-graph').disabled);
  assert.equal(await page.locator('#pause-flow').isDisabled(),true);
  assert.equal(await page.locator('#pause-graph').isDisabled(),true);
  assert.equal(await page.locator('.reveal-pending').count(),0);
  assert.equal(await page.locator('.flow-trace').first().evaluate(path=>getComputedStyle(path).strokeDashoffset),'0px');
  // A missing local story asset leaves the figure's designed gradient in place.
  await page.route('**/static/img/story/01-new-coin*.webp',route=>route.abort());
  await page.reload({waitUntil:'networkidle'});
  await page.locator('.story-new-coin').scrollIntoViewIfNeeded();
  const fallback=await page.locator('.story-new-coin .story-art').evaluate(art=>({background:getComputedStyle(art).backgroundImage,ready:art.querySelector('img').classList.contains('is-ready'),height:art.clientHeight}));
  assert.match(fallback.background,/gradient/);assert.equal(fallback.ready,false);assert.ok(fallback.height>100);
  await context.close();
  const nojs=await browser.newContext({viewport:{width,height:1000},javaScriptEnabled:false});
  const fallbackPage=await nojs.newPage();await fallbackPage.goto(base,{waitUntil:'networkidle'});
  assert.equal(await fallbackPage.locator('#watch-demo').getAttribute('href'),'https://youtu.be/fz89p-YZS6o');
  assert.equal(await fallbackPage.locator('.reveal-pending').count(),0);
  assert.ok(await fallbackPage.locator('#home-question').isVisible());
  await nojs.close();checks.push({width,pauseResume:true,reducedMotionSwitch:true,missingImageFallback:true,noJsVideoLink:true});
 }
}finally{await browser.close();}
await fs.writeFile(new URL('./qb-motion-results.json',import.meta.url),JSON.stringify({generated:new Date().toISOString(),checks},null,2)+'\n');
console.log('PASS hero pause/resume, dynamic reduced motion, missing-image fallback and no-JS links at both viewports.');
