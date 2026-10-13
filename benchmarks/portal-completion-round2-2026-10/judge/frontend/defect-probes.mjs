// Supplemental defect probes: separate scope, never added to the 11-group score.
const {chromium}=await import(process.env.BENCHMARK_PLAYWRIGHT_IMPORT||'playwright');
import {mkdtemp,mkdir,writeFile,rm} from 'node:fs/promises';
import path from 'node:path';import {tmpdir} from 'node:os';import {fileURLToPath} from 'node:url';
import {launch,stop,login,tab,ensureProjectDetail} from './evaluate.mjs';
const wait=ms=>new Promise(r=>setTimeout(r,ms));const check=(x,m)=>{if(!x)throw Error(m);};
async function until(fn,m){const end=Date.now()+5000;while(Date.now()<end){if(await fn())return;await wait(50);}throw Error(m);}
const ACCOUNTS={client:['alex@harbor.test','HarborDemo!42','Alex Morgan'],other:['sam@northline.test','NorthDemo!42','Sam Ellis']};
export async function probes({site,out,env={}}){
 await mkdir(out,{recursive:true});const report={schema:1,scope:'supplemental_browser_contracts',scored:false,supplementalCheckCount:3,originalFrontendDenominator:11,checks:[]};let browser;
 const run=async(name,fn)=>{const work=await mkdtemp(path.join(tmpdir(),'portal-probe-'));let server,ctx;const row={name,status:'not_run'};report.checks.push(row);
  try{server=await launch(site,work,env);const url=await server.ready();ctx=await browser.newContext({viewport:{width:1440,height:1000}});const page=await ctx.newPage();page.setDefaultTimeout(5000);const errors=[];page.on('pageerror',e=>errors.push(e.message));
   const req=async(resource,body,cookie)=>{const r=await fetch(url+resource,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json',...(cookie?{Cookie:cookie}:{})},body:body===undefined?undefined:JSON.stringify(body)});return {status:r.status,body:await r.json(),cookie:r.headers.get('set-cookie')?.split(';')[0]};};
   await login(page,url,ACCOUNTS.client);await ensureProjectDetail(page,'p1');await fn({page,url,req,row,errors});row.status='pass';
  }catch(e){row.status='fail';row.error=String(e.message).slice(0,1200);}finally{await ctx?.close();await stop(server);await rm(work,{recursive:true,force:true});}
 };
 try{browser=await chromium.launch({headless:true});
  await run('healthy_comment_and_identity',async({page,url,row})=>{const h=id=>page.getByTestId(id);check((await h('project-title').innerText()).includes('Harbor Commerce Platform'),'healthy project title');await tab(page,'discussion');const draft='Healthy probe comment 🚀';await h('comment-body').fill(draft);await h('comment-submit').click();await until(async()=>(await h('comment-text').allTextContents()).includes(draft),'healthy comment missing');await page.reload({waitUntil:'domcontentloaded'});await ensureProjectDetail(page,'p1');await tab(page,'discussion');check((await h('comment-text').allTextContents()).includes(draft),'healthy comment persistence');row.evidence={identity:'Alex Morgan',literalUnicodePersisted:true};});
  await run('late_conflict_refresh_after_account_switch',async({page,url,req,row,errors})=>{
   const h=id=>page.getByTestId(id);await tab(page,'revisions');await h('decision-note').fill('Preserve race draft');
   const staff=await req('/api/login',{email:'studio@aethdesign.test',password:'StudioDemo!42'});check(staff.status===200,'staff setup login failed');
   const pub=await req('/api/projects/p1/revisions',{expectedRevision:1,title:'Intervening revision',summary:'Deterministic stale review'},staff.cookie);check(pub.status===201,'intervening revision failed');
   let release,started;const gate=new Promise(r=>release=r),start=new Promise(r=>started=r);let conflictConfirmed=false,switching=false;const held=[],heldRequests=[],completed=[],canceled=[],routeErrors=[];
   const routePattern='**/api/projects**';
   await page.route(routePattern,async route=>{
    const request=route.request(),u=new URL(request.url());
    if(u.origin!==url)return route.continue();
    if(request.method()==='POST'&&u.pathname==='/api/projects/p1/decision'){
     const response=await route.fetch();conflictConfirmed=response.status()===409;await route.fulfill({response});return;
    }
    if(request.method()!=='GET'||!conflictConfirmed||switching)return route.continue();
    // Snapshot any public project read strategy before the session changes.
    const response=await route.fetch();let resolve;const done=new Promise(r=>resolve=r);completed.push(done);held.push(u.pathname);heldRequests.push(request);started();
    try{await gate;const failure=request.failure()?.errorText;if(switching&&!page.isClosed()&&failure&&/abort|cancel/i.test(failure)){canceled.push({path:u.pathname,transportFailure:failure});return;}await route.fulfill({response});}catch(e){
     const failure=request.failure()?.errorText;
     if(switching&&!page.isClosed()&&failure&&/abort|cancel/i.test(failure))canceled.push({path:u.pathname,transportFailure:failure});
     else routeErrors.push({path:u.pathname,message:String(e.message).slice(0,500),transportFailure:failure||null});
    }finally{resolve();}
   });
   try{await h('approve-revision').click();await Promise.race([start,wait(5000).then(()=>{throw Error(conflictConfirmed?'409 did not trigger any public project dataset refresh required by BRIEF':'stale decision did not return 409');})]);
    switching=true;await h('logout').click();await h('login-form').waitFor();await h('login-email').fill(ACCOUNTS.other[0]);await h('login-password').fill(ACCOUNTS.other[1]);await h('login-submit').click();await h('project-list').waitFor();check((await h('user-name').innerText()).includes('Sam Ellis'),'other account not settled');release();await Promise.all(completed);await page.waitForLoadState('networkidle',{timeout:5000});await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
    for(const request of heldRequests){const failure=request.failure()?.errorText;if(failure&&/abort|cancel/i.test(failure)&&!canceled.some(v=>v.path===new URL(request.url()).pathname))canceled.push({path:new URL(request.url()).pathname,transportFailure:failure});}
    const body=await page.locator('body').innerText(),ids=await h('project-card').evaluateAll(es=>es.filter(e=>e.getClientRects().length).map(e=>e.dataset.projectId));row.evidence={actualDecisionStatus:409,heldProjectReadPaths:held,canceledProjectReads:canceled,instrumentErrors:routeErrors,identity:await h('user-name').innerText(),visibleProjectIds:ids,leakedTitle:body.includes('Harbor Commerce Platform'),errors};check(!body.includes('Harbor Commerce Platform'),'late conflict refresh leaked previous account project');check(await h('project-list').isVisible()&&JSON.stringify(ids)==='["p3"]','late refresh replaced authorized overview');check(!routeErrors.length,'live route instrumentation failure: '+JSON.stringify(routeErrors));check(!errors.length,'late refresh runtime error: '+errors.join('; '));
   }finally{release?.();await page.unroute(routePattern);}

  });
  await run('committed_comment_refresh_failure',async({page,url,row})=>{
   const h=id=>page.getByTestId(id);await tab(page,'discussion');const draft='Committed exactly once despite failed refresh';let committed=false,posts=0;const injectedPaths=[],routeErrors=[];const routePattern='**/api/projects**';
   await page.route(routePattern,async route=>{const request=route.request(),u=new URL(request.url());
    try{
     if(u.origin!==url)return await route.continue();
     if(request.method()==='POST'&&u.pathname==='/api/projects/p1/comments'){
      const response=await route.fetch();if(response.status()===201){committed=true;posts++;}return await route.fulfill({response});
     }
     if(request.method()==='GET'&&committed){injectedPaths.push(u.pathname);return await route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:{code:'probe_refresh_unavailable',message:'Project dataset refresh unavailable'}})});}
     return await route.continue();
    }catch(e){routeErrors.push({path:u.pathname,message:String(e.message).slice(0,500)});}
   });
   await h('comment-body').fill(draft);await h('comment-submit').click();await until(()=>committed,'comment POST did not succeed');await page.waitForLoadState('networkidle',{timeout:5000});await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
   const feedback=await h('comment-status').innerText(),retainedDraft=await h('comment-body').inputValue();row.evidence={postStatus:201,refreshStrategy:injectedPaths.length?'public_dataset_reread':'no_refresh_response_acknowledgment',injectedProjectReadPaths:injectedPaths,feedback,retainedDraft,postCount:posts,instrumentErrors:routeErrors};
   check(!routeErrors.length,'comment route instrumentation failure: '+JSON.stringify(routeErrors));check(/saved|added|posted|sent/i.test(feedback)&&!/(?:not|could not|couldn't|unable to|failed to)\s+(?:save|post|send|add|submit)/i.test(feedback),'refresh failure hid successful mutation');check(retainedDraft!==draft||!await h('comment-submit').isEnabled(),'committed draft remains resubmittable');
   if(await h('comment-submit').isEnabled())await h('comment-submit').click();await page.waitForLoadState('networkidle',{timeout:5000});check(posts===1,'same committed draft submitted twice');await page.unroute(routePattern);await page.reload({waitUntil:'domcontentloaded'});await ensureProjectDetail(page,'p1');await tab(page,'discussion');const count=(await h('comment-text').allTextContents()).filter(t=>t===draft).length;check(count===1,'committed comment persisted more/less than once');Object.assign(row.evidence,{postCount:posts,persistedCount:count});
  });

 }catch(e){report.fatal=String(e.message).slice(0,1200);}finally{await browser?.close();}
 report.passed=report.checks.filter(r=>r.status==='pass').length;report.failed=report.checks.filter(r=>r.status==='fail').length;await writeFile(path.join(out,'defect-probes.json'),JSON.stringify(report,null,2));return report;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){const [site,out]=process.argv.slice(2);if(!site||!out)throw Error('Usage: node defect-probes.mjs SITE OUTPUT');const r=await probes({site:path.resolve(site),out:path.resolve(out)});console.log(JSON.stringify(r));process.exitCode=r.fatal||r.failed?1:0;}
