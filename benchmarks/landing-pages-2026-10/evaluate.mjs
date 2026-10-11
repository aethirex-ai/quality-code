const {chromium} = await import(process.env.BENCHMARK_PLAYWRIGHT_IMPORT || 'playwright');
import {fileURLToPath} from 'node:url'; import fs from 'node:fs'; import path from 'node:path'; import {spawn} from 'node:child_process';
const condition=process.argv[2],root=path.dirname(fileURLToPath(import.meta.url)),site=path.join(root,'runs',condition,'site'),out=path.join(root,'runs',condition,'evaluation');fs.mkdirSync(out,{recursive:true});
const port=condition==='single'?48731:48732;
const server=spawn('python3',['-m','http.server',String(port),'--bind','127.0.0.1','--directory',site],{stdio:'ignore'});
let browser; const report={condition,pages:{},method:'frozen browser checks; objective assertions are separate from subjective visual quality'};
try {
 for(let n=0;n<40;n++){try{const r=await fetch(`http://127.0.0.1:${port}/`);if(r.ok)break;}catch{} await new Promise(r=>setTimeout(r,100));}
 browser=await chromium.launch({headless:true});
 for(const category of ['shop','craftsman','restaurant']){
  const entry={checks:[],screenshots:[],image_assets:[],errors:[],external_requests:[]};report.pages[category]=entry;
  const check=(name,passed,evidence)=>entry.checks.push({name,passed:Boolean(passed),evidence});
  for(const [mode,width,height] of [['desktop',1440,1000],['mobile',375,812]]){
   const context=await browser.newContext({viewport:{width,height},reducedMotion:'reduce'});const page=await context.newPage();
   const errors=[],external=[];
   page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
   page.on('response',r=>{if(r.status()>=400)errors.push(`HTTP ${r.status()} ${r.url()}`);});
   page.on('request',r=>{if(!r.url().startsWith(`http://127.0.0.1:${port}`)&&!r.url().startsWith('data:'))external.push(r.url());});
   await page.route('**/*',route=>route.request().url().startsWith(`http://127.0.0.1:${port}`)||route.request().url().startsWith('data:')?route.continue():route.abort());
   try{
    await page.goto(`http://127.0.0.1:${port}/${category}/`,{waitUntil:'networkidle',timeout:15000});await page.waitForTimeout(200);
    const info=await page.evaluate(()=>({title:document.title,description:document.querySelector('meta[name="description"]')?.content,h1s:[...document.querySelectorAll('h1')].map(x=>x.textContent),main:!!document.querySelector('main'),nav:!!document.querySelector('nav'),footer:!!document.querySelector('footer'),overflow:document.documentElement.scrollWidth>innerWidth+1,attribution:document.body.innerText.includes('Fictional portfolio concept by AethDesign'),images:[...document.images].map(i=>({src:i.getAttribute('src'),alt:i.alt,loaded:i.complete&&i.naturalWidth>0,width:i.naturalWidth,height:i.naturalHeight}))}));
    check(`${mode}: title and description`,info.title.length>2&&info.description?.length>10,info.title);
    check(`${mode}: one h1 and semantic landmarks`,info.h1s.length===1&&info.main&&info.nav&&info.footer,info.h1s);
    check(`${mode}: no horizontal overflow`,!info.overflow,{viewport:width});
    check(`${mode}: local loaded descriptive imagery`,info.images.length>=2&&info.images.every(i=>i.loaded&&i.alt.trim().length>3&&!/^https?:/.test(i.src)),info.images);
    check(`${mode}: fictional portfolio attribution`,info.attribution,'Visible attribution text');
    entry.image_assets=info.images;
    await page.screenshot({path:path.join(out,`${category}-${mode}.png`),fullPage:true});entry.screenshots.push(`${category}-${mode}.png`);
    if(category==='shop'){
     const add=page.locator('[data-testid="add-to-bag"]').first(),count=page.locator('[data-testid="bag-count"]').first();
     const before=await count.innerText();await add.click();const one=await count.innerText();await add.click();const two=await count.innerText();check(`${mode}: bag increments 0→1→2`,/\b0\b/.test(before)&&/\b1\b/.test(one)&&/\b2\b/.test(two),[before,one,two]);
    }else{
     const prefix=category==='craftsman'?'estimate':'reservation';const form=page.locator(`form[data-testid="${prefix}-form"]`);
     const labelInfo=await form.evaluate(f=>[...f.querySelectorAll('input,select,textarea')].filter(i=>i.type!=='hidden'&&i.type!=='submit').map(i=>({name:i.name,labeled:!!(i.labels?.length||i.getAttribute('aria-label')||i.getAttribute('aria-labelledby'))})));
     check(`${mode}: labeled form inputs`,labelInfo.length>=2&&labelInfo.every(i=>i.labeled),labelInfo);
     await form.locator('[name="name"]').fill('Alex Example');await form.locator('[name="email"]').fill('alex@example.invalid');
     if(category==='restaurant'){
      await form.locator('[name="date"]').fill('2027-06-15');const guests=form.locator('[name="guests"]');if(await guests.evaluate(e=>e.tagName==='SELECT'))await guests.selectOption('2');else await guests.fill('2');
     }
     // Fill any additional required controls so valid-submission grading does not silently
     // assume that the specified minimum field set is the entire form.
     const additional=await form.locator('input[required],select[required],textarea[required]').evaluateAll(els=>els.map((e,i)=>({name:e.name,type:e.type,tag:e.tagName,value:e.value,checked:e.checked})).filter(e=>!['name','email','date','guests'].includes(e.name)));
     for(const field of additional){if(!field.name)continue;const loc=form.locator(`[name="${field.name}"]`).first();if(field.tag==='SELECT'){const value=await loc.evaluate(e=>[...e.options].find(o=>o.value&&!o.disabled)?.value);if(value)await loc.selectOption(value);}else if(field.type==='checkbox'||field.type==='radio')await loc.check();else if(!field.value)await loc.fill(field.type==='tel'?'030 000000':field.type==='number'?'2':field.type==='date'?'2027-06-15':'Example project enquiry');}
     await form.locator('button[type="submit"],input[type="submit"],button:not([type])').first().click();
     const status=page.locator(`[data-testid="${prefix}-status"]`);await status.waitFor({state:'visible',timeout:3000});const statusText=await status.innerText();check(`${mode}: valid demo form confirmation`,statusText.trim().length>15,statusText);
    }
    await page.keyboard.press('Tab');const focus=await page.evaluate(()=>({tag:document.activeElement?.tagName,outline:getComputedStyle(document.activeElement).outlineStyle}));check(`${mode}: keyboard focus reaches control`,!['BODY','HTML'].includes(focus.tag),focus);
   }catch(e){check(`${mode}: page and interaction execution`,false,e.message);entry.errors.push(e.message);}
   check(`${mode}: no runtime or HTTP errors`,errors.length===0,errors);check(`${mode}: no external requests`,external.length===0,external);
   entry.errors.push(...errors);entry.external_requests.push(...external);await context.close();
  }
 }
 const indexContext=await browser.newContext();const indexPage=await indexContext.newPage();await indexPage.goto(`http://127.0.0.1:${port}/`);report.index_links=await indexPage.locator('a[href]').evaluateAll(a=>a.map(x=>x.getAttribute('href')));await indexContext.close();
 const checks=Object.values(report.pages).flatMap(p=>p.checks);report.summary={passed:checks.filter(c=>c.passed).length,total:checks.length,failed:checks.filter(c=>!c.passed)};
 fs.writeFileSync(path.join(out,'objective.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report.summary));
}finally{if(browser)await browser.close();server.kill();}
