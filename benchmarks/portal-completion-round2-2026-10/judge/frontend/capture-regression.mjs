const {chromium}=await import(process.env.BENCHMARK_PLAYWRIGHT_IMPORT||'playwright');
import assert from 'node:assert/strict';import {mkdir,writeFile,readFile} from 'node:fs/promises';import path from 'node:path';import {settleCapture} from './evaluate.mjs';
const out=path.resolve(process.argv[2]||'capture-regression-proof');await mkdir(out,{recursive:true});const browser=await chromium.launch({headless:true});const results=[];
try{for(const width of [375,1440]){const ctx=await browser.newContext({viewport:{width,height:1000}}),p=await ctx.newPage();
 await p.setContent(`<style>body{margin:0}header{position:fixed;inset:0 0 auto;height:100px;background:#eee;z-index:1}main{position:fixed;top:100px;bottom:0;left:0;right:0;overflow:auto}input:focus{outline:9px solid red}.space{height:1500px}</style><header><span data-testid="user-name">AethDesign Studio</span><button data-testid="tab-revisions" aria-selected="true">Revisions</button></header><main data-testid="project-detail" data-project-id="p1"><p data-testid="current-revision">1</p><div class="space"></div><label>Title<input data-testid="revision-title"></label></main>`);
 const values={'revision-title':'Matched review draft'};await p.getByTestId('revision-title').fill(values['revision-title']);assert.equal(await p.locator('main').evaluate(e=>e.scrollTop>0),true);
 const metadata=await settleCapture(p,{identity:'AethDesign Studio',project:'p1',section:'revisions',values});assert.equal(metadata.focus,'BODY');assert.deepEqual(metadata.scroll,{x:0,y:0,containers:[]});
 const target=path.join(out,`${width}-fixed-layout-top.png`);await p.screenshot({path:target,fullPage:false});const png=await readFile(target);assert.equal(png.readUInt32BE(16),width);assert.equal(png.readUInt32BE(20),1000);
 await assert.rejects(()=>settleCapture(p,{values:{'revision-title':'wrong draft'}}),/form population mismatch/);
 await p.getByTestId('tab-revisions').evaluate(e=>e.setAttribute('aria-selected','false'));await assert.rejects(()=>settleCapture(p,{section:'revisions'}),/selected tab mismatch/);
 results.push({width,viewportPixelDimensions:[width,1000],focusedScrolledFixtureNormalized:true,mismatchedFormRejected:true,wrongSelectedTabRejected:true,metadata});await ctx.close();
}}finally{await browser.close();}
await writeFile(path.join(out,'capture-regression.json'),JSON.stringify({status:'pass',results},null,2));console.log(JSON.stringify({status:'pass',cases:results.length}));
