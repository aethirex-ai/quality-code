import assert from 'node:assert/strict';
import {mkdtemp,mkdir,readFile,writeFile,cp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';import path from 'node:path';import {fileURLToPath} from 'node:url';
const {chromium}=await import(process.env.BENCHMARK_PLAYWRIGHT_IMPORT || 'playwright');
import {evaluate as original} from './evaluate-original.mjs';
import {evaluate,ensureProjectDetail,GROUPS} from './evaluate.mjs';
const root=path.dirname(fileURLToPath(import.meta.url)),out=path.resolve(process.argv[2]||path.join(root,'navigation-regression-proof'));
await mkdir(out,{recursive:true});const work=await mkdtemp(path.join(tmpdir(),'front-nav-proof-')),results={};
try{
 // Transform a disposable copy only: delayed asynchronous boot, retained detail,
 // and hidden mounted overview controls reproduce the measured startup shape.
 await cp(path.join(root,'fixture'),work,{recursive:true});
 let html=await readFile(path.join(work,'index.html'),'utf8');
 html=html.replace("(async()=>{try{user=", "(async()=>{await new Promise(r=>setTimeout(r,350));try{user=");
 html=html.replace("app.innerHTML=header()+button('back-projects','Overview')", "app.innerHTML=header()+`<section data-testid=\"project-list\" hidden><button data-testid=\"open-project\" data-project-id=\"p1\">Open project</button></section>`+button('back-projects','Overview')");
 await writeFile(path.join(work,'index.html'),html);
 const before=await original({site:work,out:path.join(out,'original-delayed-detail'),screenshots:false});
 const targets=['literal_comment_persistence','decision_validation_persistence','staff_publish_reopens_history_activity'];
 assert.equal(before.fatal,null);assert.equal(before.passed,8);
 for(const target of targets)assert.equal(before.groups.find(g=>g.name===target).status,'fail',target);
 assert.equal(before.groups.find(g=>g.name==='authorized_cards').status,'pass');
 results.original={passed:before.passed,failedTargets:targets};
 const after=await evaluate({site:work,out:path.join(out,'corrected-delayed-detail'),screenshots:false});
 assert.equal(after.fatal,null);assert.equal(after.passed,GROUPS.length);results.corrected={passed:after.passed};
 results.negativeControls=[];
 for(const [mode,target] of Object.entries({literal:targets[0],validation:targets[1],publish:targets[2]})){
  const report=await evaluate({site:work,out:path.join(out,'negative-'+mode),env:{FRONTEND_FIXTURE_MODE:mode},screenshots:false});
  assert.equal(report.fatal,null);assert.equal(report.groups.find(g=>g.name===target).status,'fail',mode);
  assert.equal(report.groups.find(g=>g.name==='authorized_cards').status,'pass');
  results.negativeControls.push({mode,target,status:'fail',healthyControl:'authorized_cards:pass'});
 }
 // Exercise both semantic navigation branches independent of URL shape.
 const browser=await chromium.launch({headless:true});try{
  const page=await browser.newPage();page.setDefaultTimeout(1000);
  for(const initial of ['overview','p2']){
   await page.setContent(`<button data-testid="logout">Logout</button><section data-testid="project-list" ${initial==='p2'?'hidden':''}><button data-testid="open-project" data-project-id="p1">Open</button></section><button data-testid="back-projects" ${initial==='overview'?'hidden':''}>Back</button><section data-testid="project-detail" data-project-id="p2" ${initial==='overview'?'hidden':''}><h1 data-testid="project-title">Second</h1></section><script>(()=>{const q=id=>document.querySelector('[data-testid="'+id+'"]');q('back-projects').onclick=()=>{window.backUsed=true;q('project-detail').hidden=true;q('project-list').hidden=false;};q('open-project').onclick=()=>{q('project-list').hidden=true;q('project-detail').hidden=false;q('project-detail').dataset.projectId='p1';q('project-title').textContent='First';};})();</script>`);
   await ensureProjectDetail(page,'p1');assert.equal(await page.getByTestId('project-detail').getAttribute('data-project-id'),'p1');
   if(initial==='p2')assert.equal(await page.evaluate(()=>window.backUsed),true);
  }
  results.navigationBranches={overview:true,wrongDetailUsesActualBack:true};
  await page.setContent('<button data-testid="logout">Logout</button>');
  const start=Date.now();await assert.rejects(()=>ensureProjectDetail(page,'p1'),/authenticated overview or detail settles/);assert(Date.now()-start<6500);results.unsettledContractRejected=true;
 }finally{await browser.close();}
 await writeFile(path.join(out,'navigation-regression.json'),JSON.stringify(results,null,2));console.log(JSON.stringify({status:'pass',...results,out}));
}finally{await rm(work,{recursive:true,force:true});}
