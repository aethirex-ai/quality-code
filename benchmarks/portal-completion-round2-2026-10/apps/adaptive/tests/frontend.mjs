import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFile} from 'node:fs/promises';
import {Workspace,ApiError} from '../public/state.mjs';
const origin = process.argv[2];
assert.match(origin,/^http:\/\/127\.0\.0\.1:\d+$/);
const credentials={c1:['alex@harbor.test','HarborDemo!42'],c2:['sam@northline.test','NorthDemo!42'],s1:['studio@aethdesign.test','StudioDemo!42']};
function transport(){let cookie='';return async (path,options={})=>{const response=await fetch(origin+path,{...options,headers:{'Content-Type':'application/json',Origin:origin,...(cookie?{Cookie:cookie}:{}),...options.headers}});const next=response.headers.get('set-cookie');if(next)cookie=next.split(';')[0];const data=await response.json();if(!response.ok)throw new ApiError(response.status,data.error.message);return data;};}
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
const tests=[];function test(name,fn){tests.push([name,fn]);}
const login=async(w,id)=>{await w.login(...credentials[id]);assert.equal(w.user.id,id);};
const external=async(id)=>{const api=transport();await api('/api/login',{method:'POST',body:JSON.stringify({email:credentials[id][0],password:credentials[id][1]})});return api;};
const post=(api,path,body)=>api(path,{method:'POST',body:JSON.stringify(body)});
const count=(api,path,field)=>api(path).then(d=>d[field].length);

test('authorized overview, normal save, literal text, selection/reload and drafts',async()=>{
 const api=transport(),w=new Workspace(api);await w.boot();assert.equal(w.user,null);await login(w,'c1');assert.deepEqual(w.projects.map(p=>p.id),['p1','p2']);
 await w.open('p1');w.draft('note','Keep the checkout clear.');w.setTab('discussion');assert.equal(w.draft('note'),'Keep the checkout clear.');
 await w.open('p2');await w.open('p1');assert.equal(w.draft('note'),'Keep the checkout clear.');
 const body='<img src=x onerror=alert(1)> Überprüfung 日本語 🚀';w.draft('comment',body);const before=await count(api,'/api/projects/p1/activity','events');
 await w.mutate('comment',{body},{comment:body});assert.equal(w.draft('comment'),'');assert.equal(w.detail.comments.at(-1).body,body);assert.equal(w.detail.comments.at(-1).author.id,'c1');assert.equal(await count(api,'/api/projects/p1/activity','events'),before+1);
 const reloaded=new Workspace(api);await reloaded.boot(()=>({project:'p1',tab:'discussion'}));assert.equal(reloaded.selectedId,'p1');assert.equal(reloaded.tab,'discussion');assert.equal(reloaded.detail.comments.at(-1).body,body);
 await reloaded.logout();await login(reloaded,'c2');assert.deepEqual(reloaded.projects.map(p=>p.id),['p3']);assert.equal(reloaded.detail,null);assert.equal(reloaded.drafts.size,0);
});
test('committed comment survives failed refresh; recovery never duplicates POST',async()=>{
 const raw=transport();let fail=false,writes=0;const api=async(path,options={})=>{if(options.method==='POST'&&path.endsWith('/comments'))writes++;if(fail&&!options.method&&path.startsWith('/api/projects/p1'))throw new ApiError(503,'Refresh temporarily unavailable.');const result=await raw(path,options);if(options.method==='POST'&&path.endsWith('/comments'))fail=true;return result;};
 const w=new Workspace(api);await login(w,'c1');await w.open('p1');const body='Committed once, recovered later ✨';w.draft('comment',body);const before=await count(raw,'/api/projects/p1/comments','comments');
 await w.mutate('comment',{body},{comment:body});assert.equal(w.draft('comment'),'');assert.equal(w.message('comment').state,'success');assert.equal(w.message('comment').recover,true);assert.equal(w.detail.comments.at(-1).body,body);assert.equal(w.detail.events.at(-1).type,'comment_added');assert.equal(w.detail.events.at(-1).commentId,w.detail.comments.at(-1).id);assert.equal(w.detail.events.length,before+1);
 fail=false;await w.refresh();assert.equal(await count(raw,'/api/projects/p1/comments','comments'),before+1);assert.equal(writes,1);assert.equal(w.detail.comments.filter(c=>c.body===body).length,1);assert.equal(w.message('comment').recover,false,'successful refresh clears the recovery prompt');
});
test('committed decision failed refresh disables finalized review and keeps money/revision',async()=>{
 const raw=transport();let fail=false;const api=async(path,options={})=>{if(fail&&!options.method&&path.startsWith('/api/projects/p3'))throw new ApiError(503,'Refresh unavailable.');const result=await raw(path,options);if(path.endsWith('/decision')&&options.method==='POST')fail=true;return result;};
 const w=new Workspace(api);await login(w,'c2');await w.open('p3');const before=await count(raw,'/api/projects/p3/activity','events');w.draft('note','Add onboarding context.');await w.mutate('decision',{revision:1,decision:'request_changes',note:w.draft('note')},{note:w.draft('note')});
 assert.equal(w.detail.project.status,'changes_requested');assert.equal(w.detail.project.budgetCents,360000);assert.equal(w.detail.project.currentRevision,1);assert.equal(w.message('decision').recover,true);assert.equal(w.draft('note'),'');assert.equal(w.detail.events.at(-1).type,'decision_submitted');assert.equal(w.detail.events.at(-1).decision,'request_changes');assert.equal(w.detail.events.length,before+1);
 fail=false;await w.refresh();assert.equal(await count(raw,'/api/projects/p3/activity','events'),before+1);
});
test('committed publication failed refresh updates revision and clears acknowledged draft',async()=>{
 const raw=transport();let fail=false;const api=async(path,options={})=>{if(fail&&!options.method&&path.startsWith('/api/projects/p2'))throw new ApiError(503,'Refresh unavailable.');const result=await raw(path,options);if(path.endsWith('/revisions')&&options.method==='POST')fail=true;return result;};
 const w=new Workspace(api);await login(w,'s1');await w.open('p2');w.draft('title','Handoff detail');w.draft('summary','Engineering notes and empty states.');const before=await count(raw,'/api/projects/p2/activity','events');
 await w.mutate('revision',{expectedRevision:2,title:w.draft('title'),summary:w.draft('summary')},{title:w.draft('title'),summary:w.draft('summary')});
 assert.equal(w.detail.project.currentRevision,3);assert.equal(w.detail.project.status,'awaiting_review');assert.equal(w.detail.revisions.at(-1).number,3);assert.equal(w.draft('title'),'');assert.equal(w.message('revision').recover,true);assert.equal(w.detail.events.at(-1).type,'revision_published');assert.equal(w.detail.events.at(-1).revision,3);assert.equal(w.detail.events.length,before+1);
 fail=false;await w.refresh();assert.equal(await count(raw,'/api/projects/p2/activity','events'),before+1);
});
test('delayed old-account conflict recovery cannot expose old project after logout/login',async()=>{
 const raw=transport(),staff=await external('s1'),started=deferred(),release=deferred();let conflict=false;
 const api=async(path,options={})=>{if(conflict&&!options.method&&path==='/api/projects/p1'){started.resolve();await release.promise;}try{return await raw(path,options);}catch(e){if(path.endsWith('/decision')&&e.status===409)conflict=true;throw e;}};
 const snapshots=[],w=new Workspace(api,s=>snapshots.push({user:s.user?.id,project:s.detail?.project.id,selected:s.selectedId}));await login(w,'c1');await w.open('p1');w.draft('note','Old-account draft');
 await post(staff,'/api/projects/p1/revisions',{expectedRevision:1,title:'Checkout refinement',summary:'Mobile checkout detail and cart recovery.'});
 const saving=w.mutate('decision',{revision:1,decision:'approve',note:w.draft('note')},{note:w.draft('note')});await started.promise;
 await w.logout();await login(w,'c2');await w.open('p3');const switchAt=snapshots.length;release.resolve();await saving;
 assert.equal(w.user.id,'c2');assert.equal(w.selectedId,'p3');assert.equal(w.detail.project.id,'p3');assert.equal(w.drafts.size,0);assert.equal(w.message('decision'),undefined);
 assert.ok(snapshots.slice(switchAt).every(s=>s.user==='c2'&&s.project!=='p1'&&s.selected!=='p1'));
 const events=await raw('/api/projects/p3/activity');assert.ok(events.events.every(e=>e.actor.id!=='c1'));
});
test('navigation race ignores delayed detail and retains unsent draft',async()=>{
 const raw=transport(),started=deferred(),release=deferred();let hold=false;
 const api=async(path,options={})=>{const result=await raw(path,options);if(hold&&path==='/api/projects/p1'){started.resolve();await release.promise;}return result;};
 const w=new Workspace(api);await login(w,'c1');await w.open('p1');w.draft('comment','Unsent draft while navigating');hold=true;const refresh=w.refresh();await started.promise;await w.open('p2');release.resolve();await refresh;assert.equal(w.detail.project.id,'p2');hold=false;await w.open('p1');assert.equal(w.draft('comment'),'Unsent draft while navigating');
});
test('in-flight save preserves a newer draft and acknowledged save across navigation',async()=>{
 const raw=transport(),started=deferred(),release=deferred();let held=false;
 const api=async(path,options={})=>{const result=await raw(path,options);if(path.endsWith('/comments')&&options.method==='POST'&&!held){held=true;started.resolve();await release.promise;}return result;};
 const w=new Workspace(api);await login(w,'c1');await w.open('p1');w.draft('comment','First submitted message');const saving=w.mutate('comment',{body:w.draft('comment')},{comment:w.draft('comment')});await started.promise;w.draft('comment','A newer unsent draft');await w.open('p2');release.resolve();await saving;await w.open('p1');assert.equal(w.draft('comment'),'A newer unsent draft');assert.equal(w.message('comment').state,'success');assert.ok(w.detail.comments.some(c=>c.body==='First submitted message'));
});
test('failed mutation preserves draft and creates no event; healthy control succeeds',async()=>{
 const raw=transport(),w=new Workspace(raw);await login(w,'c1');await w.open('p1');const before=await count(raw,'/api/projects/p1/activity','events');const bad='\ud800';w.draft('comment',bad);await w.mutate('comment',{body:bad},{comment:bad});assert.equal(w.draft('comment'),bad);assert.equal(w.message('comment').state,'error');assert.equal(await count(raw,'/api/projects/p1/activity','events'),before);
 const good='Healthy Unicode après error 🌱';w.draft('comment',good);await w.mutate('comment',{body:good},{comment:good});assert.equal(w.detail.comments.at(-1).body,good);assert.equal(await count(raw,'/api/projects/p1/activity','events'),before+1);
});
test('late successful save from previous account never changes the new account',async()=>{
 const raw=transport(),started=deferred(),release=deferred();let held=false;
 const api=async(path,options={})=>{const result=await raw(path,options);if(path.endsWith('/comments')&&options.method==='POST'&&!held){held=true;started.resolve();await release.promise;}return result;};
 const w=new Workspace(api);await login(w,'c1');await w.open('p1');w.draft('comment','Previous-account save');const saving=w.mutate('comment',{body:w.draft('comment')},{comment:w.draft('comment')});await started.promise;await w.logout();await login(w,'c2');await w.open('p3');release.resolve();await saving;assert.equal(w.detail.project.id,'p3');assert.equal(w.user.id,'c2');assert.equal(w.drafts.size,0);assert.equal(w.feedback.size,0);assert.equal(w.pending.size,0);
});
test('permissions remain server enforced through integrated controller calls',async()=>{
 const api=transport(),w=new Workspace(api);await login(w,'c1');await w.open('p1');const before=await count(api,'/api/projects/p1/activity','events');await w.mutate('revision',{expectedRevision:2,title:'Forged',summary:'Denied'});assert.equal(w.message('revision').state,'error');assert.equal(await count(api,'/api/projects/p1/activity','events'),before);await assert.rejects(()=>api('/api/projects/p3'),e=>e.status===404);
});
test('renderer escapes client text and uses CSP-compatible native progress',async()=>{
 const app=await readFile(new URL('../public/app.mjs',import.meta.url),'utf8');assert.ok(app.includes('esc(c.body)'));assert.ok(app.includes('esc(r.summary)'));assert.ok(app.includes('esc(m.text)'));assert.ok(app.includes('<progress class="progress-track"'));assert.ok(!app.includes('style="'));assert.ok(!app.includes('innerHTML=c.body'));assert.ok(!app.includes('localStorage.setItem(\'password'));
});
test('actual app render retains saved project/tab while session boot is loading',async()=>{
 const source=await readFile(new URL('../public/app.mjs',import.meta.url),'utf8');
 const storage=new Map([['aeth.selection.c1',JSON.stringify({project:'p1',tab:'discussion'})]]);
 const root={innerHTML:'',addEventListener(){},querySelector(){return null;}};
 const location={search:'?project=p1&tab=discussion'};
 const context={Workspace,Intl,URLSearchParams,console,location,document:{activeElement:null,querySelector:()=>root},window:{addEventListener(){}},localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)},history:{replaceState(_a,_b,url){location.search=url.includes('?')?url.slice(url.indexOf('?')):'';}}};
 const executable=source.replace("import {Workspace} from './state.mjs';",'').replace('workspace.boot(selection);','globalThis.appTest={workspace,selection};');
 vm.runInNewContext(executable,context);const {workspace:w,selection}=context.appTest;w.api=transport();
 await w.login(...credentials.c1,selection);assert.equal(w.selectedId,'p1','render must not erase selection before it is read');assert.equal(w.tab,'discussion');
 const saved=JSON.parse(storage.get('aeth.selection.c1'));assert.equal(saved.project,'p1');assert.equal(saved.tab,'discussion');
 assert.ok(root.innerHTML.includes('data-testid="project-list"'),'restored detail keeps visible project navigation');
 const cardIds=[...root.innerHTML.matchAll(/data-testid="project-card" data-project-id="([^"]+)"/g)].map(match=>match[1]);assert.deepEqual(cardIds,['p1','p2']);
 assert.ok(root.innerHTML.includes('data-testid="open-project" data-project-id="p1"'));

});
let failures=0;for(const [name,fn] of tests){try{await fn();console.log('PASS '+name);}catch(e){failures++;console.error('FAIL '+name+'\n'+e.stack);}}if(failures)process.exit(1);console.log(`${tests.length} frontend/integrated regressions passed.`);
