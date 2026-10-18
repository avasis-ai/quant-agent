/** Delay each real SSE event on a loopback relay to inspect in-progress UI. */
import http from 'node:http';
import { once } from 'node:events';
import { setTimeout as delay } from 'node:timers/promises';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const dir = path.dirname(fileURLToPath(import.meta.url));
const base = process.env.SNIFF_QA_URL || 'http://127.0.0.1:8080';
assert.match(base, /^http:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/);
const upstream = new URL(base);
const results = [];
const server = http.createServer((req,res) => {
  const headers = { ...req.headers, host: upstream.host };
  if (headers.origin) headers.origin = base;
  const proxy = http.request({hostname:upstream.hostname,port:upstream.port,method:req.method,path:req.url,headers}, async source => {
    res.writeHead(source.statusCode,source.headers);
    if (req.url !== '/api/ask' || source.statusCode !== 200) { source.pipe(res); return; }
    let buffer='';
    for await (const chunk of source) {
      buffer += chunk.toString();
      let end;
      while ((end=buffer.indexOf('\n\n')) !== -1) {
        const event=buffer.slice(0,end+2);buffer=buffer.slice(end+2);
        await delay(300);
        res.write(event);
      }
    }
    if(buffer)res.write(buffer);
    res.end();
  });
  proxy.on('error',()=>{res.statusCode=502;res.end('Local preview unavailable');});
  req.pipe(proxy);
});
server.listen(0,'127.0.0.1');
await once(server,'listening');
const relay='http://127.0.0.1:'+server.address().port;
const browser=await chromium.launch({headless:true});
try {
  for (const width of [1440,390]) {
    const page=await browser.newPage({viewport:{width,height:width===1440?1000:844}});
    await page.goto(relay+'/');
    await page.locator('.inline-examples [data-inline-mint="2f6jt6sR7CcuJ9sxWcqhXHBgE5r8kS3gXBJvaUWtpump"]').click();
    await page.waitForFunction(()=>document.getElementById('inline-steps').children.length>=2 && document.querySelector('#inline-form button').disabled);
    assert.equal(await page.locator('#inline-mode').textContent(),'');
    const count=await page.locator('#inline-steps li').count();
    await page.locator('#inline-demo').screenshot({style:'.site-header { visibility:hidden !important; }',path:path.join(dir,'shots-inline',`inline-streaming-${width}.png`)});
    await page.waitForFunction(()=>document.getElementById('inline-status').textContent.startsWith('Evidence ready'));
    results.push({width,stepsBeforeVerdict:count,completed:true});
    await page.close();
  }
} finally {
  await browser.close();
  server.closeAllConnections();
  server.close();
  await fs.writeFile(path.join(dir,'inline-stream-results.json'),JSON.stringify({generated:new Date().toISOString(),upstream:base,note:'Actual /api/ask SSE events relayed locally with 300ms per event. No event or graph content mocked.',results},null,2)+'\n');
}
console.log('PASS real SSE steps are visible before the verdict at 1440 and 390 px.');
