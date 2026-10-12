import fs from 'node:fs/promises';
import path from 'node:path';
import http from 'node:http';
import { pathToFileURL } from 'node:url';

export function exactCents(value, expected) {
  return typeof value === 'string' && /^(0|[1-9]\d*)$/.test(value) && Number.isSafeInteger(Number(value)) && Number(value) === expected;
}
const pages = ['lighting/index.html','lighting/collection.html','lighting/planner.html','expedition/index.html','expedition/journeys.html','expedition/builder.html'];
const mime = {'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp','.svg':'image/svg+xml'};
export async function evaluate(root, output, options = {}) {
  root = await fs.realpath(root); await fs.mkdir(output, {recursive:true});
  const results = [], errors = [], requests = [], runtime = [];
  let browser, server, origin, fatal = null;
  const check = async (name, fn) => {
    try { const outcome = await fn(); results.push({name,passed:outcome === true}); if(outcome !== true) errors.push({name,error:'Assertion failed'}); }
    catch(e) { results.push({name,passed:false}); errors.push({name,error:String(e.message || e).slice(0,600)}); }
  };
  const guarded = fn => async () => { if(fatal) throw Error(fatal); return fn(); };
  const context = async () => {
    const ctx = await browser.newContext({viewport:{width:1440,height:1000}});
    await ctx.route('**/*', async route => {
      const u = new URL(route.request().url());
      if(u.origin === origin || ['data:','blob:','about:'].includes(u.protocol)) return route.continue();
      requests.push(u.href.slice(0,250)); return route.abort();
    });
    ctx.on('page', p => { p.setDefaultTimeout(800); p.on('pageerror',e=>runtime.push(String(e.message).slice(0,400))); p.on('console',m=>{if(m.type()==='error') runtime.push(m.text().slice(0,400));}); });
    return ctx;
  };
  const go = async (p, rel) => p.goto(`${origin}/${rel}`,{waitUntil:'load',timeout:5000});
  const total = async (p,id,n) => exactCents(await p.locator(`[data-testid="${id}"]`).getAttribute('data-total-cents'),n);
  const cards = async (p,test,attribute, ids) => {
    const actual = await p.locator(`[data-testid="${test}"]:visible`).evaluateAll((els,a)=>els.map(e=>e.getAttribute(a)).sort(),attribute);
    return JSON.stringify(actual)===JSON.stringify([...ids].sort());
  };
  const form = async (p,id,status) => {
    const f=p.locator(`form[data-testid="${id}"]`);
    const fields=f.locator('input[required],select[required],textarea[required]');
    let names=0, emails=0, labeled=true;
    for(let i=0;i<await fields.count();i++) {
      const el=fields.nth(i), info=await el.evaluate(e=>({tag:e.tagName,type:e.type,name:e.name,id:e.id,label:!!(e.labels?.length||e.getAttribute('aria-label')||e.getAttribute('aria-labelledby')),labelText:[...(e.labels||[])].map(l=>l.textContent).join(' ')+(e.getAttribute('aria-label')||'')+' '+(e.getAttribute('aria-labelledby')||'').split(/\s+/).map(id=>document.getElementById(id)?.textContent||'').join(' ')}));
      labeled &&= info.label;
      if(info.type==='email'){emails++;await el.fill('demo@example.test');}
      else if(info.type==='checkbox'||info.type==='radio') await el.check();
      else if(info.tag==='SELECT'){await el.selectOption(await el.locator('option').evaluateAll(es=>es.find(e=>e.value&&!e.disabled)?.value));}
      else if(info.type==='number') await el.fill(await el.getAttribute('min')||'1');
      else if(info.type==='date') await el.fill('2027-01-10');
      else {if(/name/i.test(info.name+' '+info.id+' '+info.labelText))names++;await el.fill('Demo <img src=x onerror=alert(1)>');}
    }
    if(!names||!emails||!labeled)return false;
    await f.locator('button[type="submit"],input[type="submit"],button:not([type])').first().click();
    const s=p.locator(`[data-testid="${status}"]`);
    return await s.isVisible() && (await s.innerText()).trim().length>15 && /local|demo|prepared|specification|illustrative/i.test(await s.innerText()) && await f.locator('img[src="x"]').count()===0;
  };
  try {
    const pw = options.playwright || await import(process.env.BENCHMARK_PLAYWRIGHT_IMPORT || 'playwright');
    server=http.createServer(async(req,res)=>{
      try {
        const decoded=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
        const target=await fs.realpath(path.resolve(root,'.'+decoded+(decoded.endsWith('/')?'index.html':'')));
        if(!target.startsWith(root+path.sep))throw Error('Outside root');
        const data=await fs.readFile(target);res.writeHead(200,{'Content-Type':mime[path.extname(target)]||'application/octet-stream'});res.end(data);
      }catch{res.writeHead(404);res.end('Not found');}
    });
    await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});origin=`http://127.0.0.1:${server.address().port}`;
    browser=await pw.chromium.launch({headless:true});
  } catch(e) { fatal=`Evaluator setup: ${e.message}`; }
  for(const rel of pages) for(const width of [375,1440]) {
    const key=`${rel}@${width}`; let ctx,p, loaded=false;
    await check(`${key}: load and screenshot`,guarded(async()=>{ctx=await context();p=await ctx.newPage();await p.setViewportSize({width,height:1000});const response=await go(p,rel);loaded=response.ok();await p.screenshot({path:path.join(output,rel.replaceAll('/','-').replace('.html','')+`-${width}.png`),fullPage:true,timeout:10000});return loaded;}));
    const ready=fn=>guarded(async()=>{if(!loaded)throw Error('Page unavailable');return fn();});
    await check(`${key}: metadata`,ready(async()=>!!(await p.title()).trim() && !!(await p.locator('meta[name="description"]').getAttribute('content'))?.trim()));
    await check(`${key}: one h1 and semantic landmarks`,ready(async()=>await p.locator('h1').count()===1 && await p.locator('main').count()===1 && await p.locator('nav').count()>0 && await p.locator('footer').count()>0));
    await check(`${key}: loaded local images with descriptive alt`,ready(()=>p.locator('img').evaluateAll((els,o)=>els.length>0&&els.every(e=>e.complete&&e.naturalWidth>0&&(e.alt||'').trim().length>=5&&new URL(e.currentSrc||e.src).origin===o),origin)));
    await check(`${key}: no horizontal overflow`,ready(()=>p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1 && document.body.scrollWidth<=innerWidth+1)));
    await check(`${key}: visible attribution`,ready(async()=>await p.getByText('Fictional portfolio concept by AethDesign',{exact:true}).first().isVisible()));
    await check(`${key}: visible keyboard focus`,ready(async()=>{await p.keyboard.press('Tab');return p.evaluate(()=>{const e=document.activeElement;if(!e||e===document.body)return false;const s=getComputedStyle(e);return (s.outlineStyle!=='none'&&parseFloat(s.outlineWidth)>0)||s.boxShadow!=='none'||e.matches(':focus-visible')&&!!document.querySelector('style')&&s.textDecorationLine.includes('underline');});}));
    await check(`${key}: internal client navigation`,ready(async()=>{const links=await p.locator('nav a').evaluateAll(es=>es.map(e=>new URL(e.href).pathname));return pages.filter(x=>x.split('/')[0]===rel.split('/')[0]).every(x=>links.includes('/'+x)||x.endsWith('/index.html')&&links.includes('/'+x.replace('index.html','')));}));
    await ctx?.close();
  }
  let ctx,p;
  const setup=async()=>{await ctx?.close();ctx=await context();p=await ctx.newPage();};
  const functional=(name,fn)=>check(name,guarded(async()=>{if(!p)throw Error('Functional page unavailable');return fn();}));
  await check('lighting: functional context',guarded(async()=>{await setup();await go(p,'lighting/collection.html');return true;}));
  for(const [value,ids] of [['all',['arc','line','orbit']],['pendant',['arc']],['wall',['line']],['table',['orbit']],['all',['arc','line','orbit']]]) await functional(`lighting: filter ${value} ${ids.join(',')}`,async()=>{await p.locator('[data-testid="type-filter"]').selectOption(value);return cards(p,'product-card','data-product-id',ids);});
  for(const [id,name] of [['arc','ARC'],['line','LINE'],['orbit','ORBIT']]) await functional(`lighting: ${id} dialog Escape and focus`,async()=>{
    const trigger=p.locator(`button[data-testid="open-product"][data-product-id="${id}"]`);await trigger.click();const d=p.locator('[data-testid="product-dialog"]');
    const opened=await d.isVisible()&&(await d.innerText()).includes(name)&&await d.locator('[data-testid="close-product"]').isVisible();await p.keyboard.press('Escape');return opened && !await d.isVisible() && await trigger.evaluate(e=>e===document.activeElement);
  });
  for(const id of ['arc','line','orbit']) await functional(`lighting: ${id} close button and focus`,async()=>{const trigger=p.locator(`button[data-testid="open-product"][data-product-id="${id}"]`);await trigger.click();const d=p.locator('[data-testid="product-dialog"]');const opened=await d.isVisible();await d.locator('[data-testid="close-product"]').click();return opened&&!await d.isVisible()&&await trigger.evaluate(e=>e===document.activeElement);});
  const invalidEdit=async(fieldId, raw, maximum, totalId, unit, flat=0)=>{
    const field=p.locator(`[data-testid="${fieldId}"]`), before=Number(await field.inputValue());
    if(!Number.isInteger(before)||before<1||before>maximum||!await total(p,totalId,unit*before+flat))return false;
    await field.fill(raw);await field.dispatchEvent('change');
    const after=await field.inputValue(), n=Number(after), normalized=after!==''&&Number.isInteger(n)&&n>=1&&n<=maximum;
    const rejected=!normalized&&await field.evaluate(e=>!e.checkValidity()||e.getAttribute('aria-invalid')==='true');
    const retained=normalized?n:before;
    const immediate=(normalized||rejected)&&await total(p,totalId,unit*retained+flat);
    await p.reload();const restored=await p.locator(`[data-testid="${fieldId}"]`).inputValue();
    return immediate&&restored!==''&&Number(restored)===retained&&await total(p,totalId,unit*retained+flat);
  };
  await functional('lighting: add ARC twice count and total',async()=>{const b=p.locator('button[data-testid="add-product"][data-product-id="arc"]');await b.click();await b.click();const count=/^\D*2\D*$/.test(await p.locator('[data-testid="plan-count"]').first().innerText());await go(p,'lighting/planner.html');return count&&await total(p,'plan-total',49800)&&await p.locator('[data-testid="quantity-arc"]').inputValue()==='2';});
  await functional('lighting: quantity 3 integer total',async()=>{await p.locator('[data-testid="quantity-arc"]').fill('3');await p.locator('[data-testid="quantity-arc"]').dispatchEvent('change');return total(p,'plan-total',74700);});
  await functional('lighting: add LINE cross page total and count',async()=>{await go(p,'lighting/collection.html');await p.locator('button[data-testid="add-product"][data-product-id="line"]').click();await go(p,'lighting/planner.html');return await total(p,'plan-total',93600)&&/^\D*4\D*$/.test(await p.locator('[data-testid="plan-count"]').first().innerText());});
  await functional('lighting: remove LINE exact total',async()=>{await p.locator('button[data-testid="remove-product"][data-product-id="line"]').click();return total(p,'plan-total',74700);});
  await functional('lighting: persistence and named storage',async()=>{const stored=await p.evaluate(()=>localStorage.getItem('aurel.plan.v1'));await p.reload();return !!stored&&await total(p,'plan-total',74700)&&await p.locator('[data-testid="quantity-arc"]').inputValue()==='3';});
  for(const raw of ['0','11','1.5','']) await functional(`lighting: invalid ARC quantity ${raw||'empty'}`,()=>invalidEdit('quantity-arc',raw,10,'plan-total',24900));
  await functional('lighting: valid local form confirmation',()=>form(p,'project-form','project-status'));
  for(const value of ['{broken',JSON.stringify([{id:'arc',quantity:'NaN'},{id:'line',quantity:-3},{id:'orbit',quantity:99}])]) await functional(`lighting: corrupt state ${value.startsWith('{')?'syntax':'entries'}`,async()=>{await p.evaluate(v=>localStorage.setItem('aurel.plan.v1',v),value);await p.reload();const a=await p.locator('[data-testid="plan-total"]').getAttribute('data-total-cents');return /^(0|[1-9]\d*)$/.test(a||'')&&Number(a)<=767000&&await p.locator('[data-testid^="quantity-"]').evaluateAll(es=>es.every(e=>/^\d+$/.test(e.value)&&+e.value>=1&&+e.value<=10));});
  await check('expedition: functional context',guarded(async()=>{await setup();await go(p,'expedition/journeys.html');return true;}));
  for(const [value,ids] of [['all',['ridge','fjord','desert']],['alpine',['ridge']],['coastal',['fjord']],['desert',['desert']],['all',['ridge','fjord','desert']]]) await functional(`expedition: filter ${value} ${ids.join(',')}`,async()=>{await p.locator('[data-testid="terrain-filter"]').selectOption(value);return cards(p,'journey-card','data-journey-id',ids);});
  await functional('expedition: select RIDGE navigates builder',async()=>{await p.locator('button[data-testid="select-journey"][data-journey-id="ridge"]').click();await p.waitForURL('**/expedition/builder.html');return await p.locator('[data-testid="journey-select"]').inputValue()==='ridge';});
  let ridgeNarrative='';
  await functional('expedition: RIDGE 2 travelers integer estimate',async()=>{await p.locator('[data-testid="travelers"]').fill('2');await p.locator('[data-testid="travelers"]').dispatchEvent('change');return total(p,'trip-total',480000);});
  await functional('expedition: guide flat cost',async()=>{await p.locator('[data-testid="add-guide"]').check();return total(p,'trip-total',540000);});
  const itinerary=async()=>{
    const ds=p.locator('main details');const bs=p.locator('main button[aria-expanded]');
    if(await ds.count()>=3){let content=[];for(let i=0;i<3;i++){const d=ds.nth(i);if(!await d.getAttribute('open')){if(!await d.evaluate(e=>e.open))await d.locator('summary').click();}const t=(await d.innerText()).trim();content.push(t);}return content.every(t=>t.length>45)&&new Set(content).size===3;}
    if(await bs.count()<3)return false;let texts=[];for(let i=0;i<3;i++){const b=bs.nth(i);if(await b.getAttribute('aria-expanded')==='false')await b.click();const id=await b.getAttribute('aria-controls');if(!id||!(await b.innerText()).trim())return false;const region=p.locator(`[id="${id}"]`);if(!await region.isVisible())return false;texts.push((await region.innerText()).trim());}return texts.every(t=>t.length>30)&&new Set(texts).size===3;
  };
  await functional('expedition: three accessible RIDGE itinerary sections',async()=>{const ok=await itinerary();ridgeNarrative=await p.locator('main details,main [aria-controls]').evaluateAll(es=>es.map(e=>e.tagName==='DETAILS'?e.innerText:document.getElementById(e.getAttribute('aria-controls'))?.innerText||'').join('\n'));return ok;});
  await functional('expedition: FJORD switch exact estimate and narrative',async()=>{await p.locator('[data-testid="journey-select"]').selectOption('fjord');return await total(p,'trip-total',420000)&&await itinerary()&&!!ridgeNarrative&&ridgeNarrative!==await p.locator('main details,main [aria-controls]').evaluateAll(es=>es.map(e=>e.tagName==='DETAILS'?e.innerText:document.getElementById(e.getAttribute('aria-controls'))?.innerText||'').join('\n'));});
  await functional('expedition: visible FJORD summary',async()=>{const t=await p.locator('main').innerText();return /fjord/i.test(t)&&/5\s*days?/i.test(t)&&/(?:2\s*(?:travelers?|travellers?|guests?|people|persons?)|(?:travelers?|travellers?|guests?|people|persons?)\s*:?\s*2)/i.test(t)&&/guide/i.test(t);});
  await functional('expedition: persistence and named storage',async()=>{const stored=await p.evaluate(()=>localStorage.getItem('meridian.trip.v1'));await p.reload();return !!stored&&await total(p,'trip-total',420000)&&await p.locator('[data-testid="journey-select"]').inputValue()==='fjord'&&await p.locator('[data-testid="travelers"]').inputValue()==='2'&&await p.locator('[data-testid="add-guide"]').isChecked();});
  for(const raw of ['0','7','1.5','']) await functional(`expedition: invalid travelers ${raw||'empty'}`,()=>invalidEdit('travelers',raw,6,'trip-total',180000,60000));
  await functional('expedition: valid local form confirmation',()=>form(p,'trip-form','trip-status'));
  for(const value of ['{broken',JSON.stringify({journey:'invalid',travelers:'NaN',guide:'yes'})]) await functional(`expedition: corrupt state ${value==='{broken'?'syntax':'entries'}`,async()=>{await p.evaluate(v=>localStorage.setItem('meridian.trip.v1',v),value);await p.reload();const n=await p.locator('[data-testid="travelers"]').inputValue();const a=await p.locator('[data-testid="trip-total"]').getAttribute('data-total-cents');return ['ridge','fjord','desert'].includes(await p.locator('[data-testid="journey-select"]').inputValue())&&/^[1-6]$/.test(n)&&/^(0|[1-9]\d*)$/.test(a||'')&&Number(a)<=1500000;});
  await check('all pages: no external HTTP resources',async()=>!fatal&&requests.length===0);
  await check('all pages: no browser runtime or console errors',async()=>!fatal&&runtime.length===0);
  await ctx?.close(); await browser?.close(); if(server?.listening)await new Promise(resolve=>server.close(resolve));
  const report={version:1,passed:results.filter(r=>r.passed).length,total:results.length,results,errors,externalRequests:requests,runtimeErrors:runtime,fatal};
  await fs.writeFile(path.join(output,'objective.json'),JSON.stringify(report,null,2)+'\n');return report;
}
if(process.argv[1] && import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){
  if(process.argv.length!==4){console.error('Usage: node evaluator.mjs WORKSPACE OUTPUTDIR');process.exitCode=2;}
  else {const r=await evaluate(process.argv[2],process.argv[3]);console.log(JSON.stringify({passed:r.passed,total:r.total,fatal:r.fatal}));}
}
