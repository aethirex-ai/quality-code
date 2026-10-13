import fs from 'node:fs/promises';
import readline from 'node:readline';
import {pathToFileURL} from 'node:url';
const module = process.argv[2];
const {chromium} = await import(module.startsWith('/') ? pathToFileURL(module).href : module);
const browser = await chromium.launch({headless:true,args:['--disable-background-networking','--disable-component-update']});
console.log(JSON.stringify({ready:true}));
async function render(req) {
  const secrets=(req.actions||[]).filter(a=>/password/i.test(a.selector||'') && a.value).map(a=>a.value);
  const scrub=s=>{for(const secret of secrets)s=s.split(secret).join('[REDACTED]');return s;};
  const context=await browser.newContext({viewport:{width:req.viewport,height:900},deviceScaleFactor:1,serviceWorkers:'block',acceptDownloads:false});
  const errors=[], blocked=[];
  let phase='readiness';
  try {
    await context.route('**/*',async route=>{
      const url=new URL(route.request().url());
      if(url.origin!==req.origin || url.protocol!=='http:' || url.username || url.password) {
        if(blocked.length<12) blocked.push('blocked outside fixed application origin');
        return route.abort('blockedbyclient');
      }
      return route.continue();
    });
    await context.routeWebSocket('**/*',ws=>{if(blocked.length<12)blocked.push('blocked websocket');ws.close();});
    const page=await context.newPage();
    page.on('pageerror',()=>{if(errors.length<12)errors.push('uncaught page error');});
    page.on('download',download=>download.cancel());
    page.setDefaultTimeout(1500);
    const response=await page.goto(req.origin+req.page,{waitUntil:'load',timeout:10000});
    if(!response) return {ok:false,classification:'readiness',error:'application server unavailable'};
    phase='product';
    if(!response.ok()) errors.push('initial page HTTP '+response.status());
    const actionResults=[];
    for(const action of req.actions||[]) {
      try {
        const options={timeout:1500};
        const locator=action.op==='reload' ? null : page.locator('css='+action.selector);
        if(action.op==='reload') await page.reload({waitUntil:'load',timeout:5000});
        else if(action.op==='click') await locator.click(options);
        else if(action.op==='fill') await locator.fill(action.value,options);
        else if(action.op==='select') await locator.selectOption(action.value,options);
        else if(action.op==='scroll') await locator.scrollIntoViewIfNeeded(options);
        else if(action.op==='check') await locator.check(options);
        else if(action.op==='press') await locator.press(action.value,options);
        await page.waitForTimeout(100);
        actionResults.push({op:action.op,ok:true});
      } catch {actionResults.push({op:action.op,ok:false,error:'action failed or timed out'});break;}
    }
    if(new URL(page.url()).origin!==req.origin) return {ok:false,classification:'product',error:'navigation outside fixed origin blocked',actionResults,blockedRequests:blocked};
    await page.evaluate(()=>Promise.race([document.fonts.ready,new Promise(resolve=>setTimeout(resolve,1500))]));
    const dom=await page.evaluate(()=>({title:document.title.slice(0,180),excerpt:(document.body?.innerText||'').slice(0,1500),width:innerWidth,documentWidth:document.documentElement.scrollWidth,horizontalOverflow:document.documentElement.scrollWidth>innerWidth,overflowingElements:Array.from(document.querySelectorAll('body *')).filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&(r.right>innerWidth+1||r.left< -1);}).slice(0,10).map(e=>({tag:e.tagName,id:e.id.slice(0,80)}))}));
    dom.excerpt=scrub(dom.excerpt);dom.title=scrub(dom.title);
    await page.screenshot({path:req.screenshot,animations:'disabled',fullPage:false,timeout:5000});
    if((await fs.stat(req.screenshot)).size>12*1024*1024)throw new Error('image limit');
    return {ok:true,classification:'product',page:req.page,viewport:req.viewport,...dom,errors,actionResults,blockedRequests:blocked};
  } catch {
    return {ok:false,classification:phase,error:phase==='readiness'?'application server unavailable or not ready':'render failed or timed out',errors,blockedRequests:blocked};
  } finally {await context.close();}
}
try {
  for await(const line of readline.createInterface({input:process.stdin,crlfDelay:Infinity})) {
    if(Buffer.byteLength(line)>16384){console.log(JSON.stringify({ok:false,error:'renderer request too large',classification:'protocol'}));continue;}
    let result;try {result=await render(JSON.parse(line));} catch {result={ok:false,error:'invalid renderer request',classification:'protocol'};}
    console.log(JSON.stringify(result));
  }
} finally {await browser.close();}
