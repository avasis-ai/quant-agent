import fs from 'node:fs/promises';
const {chromium} = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const browser=await chromium.launch({headless:true});
const results=[];
try {for(const width of [1440,390]) {
 const page=await browser.newPage({viewport:{width,height:1000}});
 await page.goto('http://127.0.0.1:8098',{waitUntil:'networkidle'});
 await page.locator('#hero-visual').scrollIntoViewIfNeeded();
 const result=await page.evaluate(()=>new Promise(resolve=>{
  const times=[], shifts=[];let prev=null, start=null;
  const observer=new PerformanceObserver(list=>list.getEntries().forEach(e=>{if(!e.hadRecentInput)shifts.push(e.value);}));
  observer.observe({type:'layout-shift',buffered:false});
  function sample(now){if(start===null)start=now;if(prev!==null)times.push(now-prev);prev=now;
   if(now-start<9400)requestAnimationFrame(sample);else{observer.disconnect();times.sort((a,b)=>a-b);resolve({frames:times.length,medianMs:times[Math.floor(times.length*.5)],p95Ms:times[Math.floor(times.length*.95)],framesOver34ms:times.filter(t=>t>34).length,layoutShift:shifts.reduce((a,b)=>a+b,0)});}}
  requestAnimationFrame(sample);
 }));
 results.push({width,...result});await page.close();
}}finally{await browser.close();}
await fs.writeFile(new URL('./polish-performance.json', import.meta.url),JSON.stringify({checkedAt:new Date().toISOString(),environment:'Local headless Chromium; frame cadence is not a physical-device guarantee',results},null,2)+'\n');console.log(JSON.stringify(results));
