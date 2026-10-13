// Focused preflight audit regressions. No measured application is executed.
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,readFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {launch,stop,displayedEuroCents,evaluate,GROUPS} from './evaluate.mjs';
const root=path.dirname(fileURLToPath(import.meta.url)),out=path.resolve(process.argv[2]||path.join(root,'audit-regression-proof'));
await mkdir(out,{recursive:true});const results={cleanup:[],moneyParser:[],moneyBrowser:[]};
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const alive=pid=>{try{process.kill(pid,0);return true;}catch(e){if(e.code==='ESRCH')return false;throw e;}};
async function waitFor(fn,ms=2000){let end=Date.now()+ms;while(Date.now()<end){if(await fn())return;await delay(25);}throw Error('regression deadline exceeded');}
for(const leader of ['exited','running']){
 const work=await mkdtemp(path.join(tmpdir(),'front-cleanup-regression-'));let server,descendant;
 try{
 const childCode="import os,signal,time; from pathlib import Path; signal.signal(signal.SIGTERM,signal.SIG_IGN); Path(os.environ['PIDFILE']).write_text(str(os.getpid())); time.sleep(60)";
 const source=`import argparse,os,subprocess,sys,time,json\nfrom pathlib import Path\np=argparse.ArgumentParser();p.add_argument('--host');p.add_argument('--port');p.add_argument('--db');a=p.parse_args()\nos.environ['PIDFILE']=a.db+'.child'\nc=subprocess.Popen([sys.executable,'-c',${JSON.stringify(childCode)}],stdout=sys.stdout,stderr=sys.stderr)\nwhile not Path(os.environ['PIDFILE']).exists():time.sleep(.01)\nprint(json.dumps({'ready':True,'port':43210}),flush=True)\n${leader==='exited'?'os._exit(0)':'time.sleep(60)'}\n`;
 await writeFile(path.join(work,'server.py'),source);server=await launch(work,work);await server.ready();descendant=Number(await readFile(path.join(work,'data.sqlite.child'),'utf8'));assert(alive(descendant),'actual TERM-ignoring descendant must be alive before stop');
 if(leader==='exited')await waitFor(()=>server.child.exitCode!==null);
 const start=Date.now();await stop(server);const durationMs=Date.now()-start;assert(durationMs<2300,'cleanup bounded to 2.3 seconds');await waitFor(()=>!alive(descendant));assert(!alive(descendant),'actual descendant must terminate despite exited leader/inherited pipes');await stop(server);results.cleanup.push({leader,descendantTerminated:true,durationMs});
 }finally{if(server){await stop(server);try{process.kill(-server.child.pid,'SIGKILL');}catch(e){if(e.code!=='ESRCH')throw e;}}await rm(work,{recursive:true,force:true});}
}
// An actual live group's permission failure must never be interpreted as gone.
{
 const work=await mkdtemp(path.join(tmpdir(),'front-denied-group-'));let server;const originalKill=process.kill;
 try{server=await launch(path.join(root,'fixture'),work);await server.ready();const pid=server.child.pid;
  process.kill=function(target,signal){if(target===-pid&&signal==='SIGTERM'){let e=Error('seeded live-group permission denial');e.code='EPERM';throw e;}return originalKill.call(process,target,signal);};
  await assert.rejects(()=>stop(server),e=>e.code==='EPERM');assert(alive(pid),'refused live-group signal remains observable');results.liveGroupPermissionErrorNotWaived=true;
 }finally{process.kill=originalKill;if(server){server.stopped=false;await stop(server);}await rm(work,{recursive:true,force:true});}
}
for(const display of ['EUR 4200.00','€4,200.00','4.200,00 €','EUR4200','4\u202f200,00 EUR','€4,200','€4.200',"CHF is not used: €4'200.00"]){assert.equal(displayedEuroCents(display),420000,display);results.moneyParser.push({display,cents:420000});}
for(const display of ['EUR420000','EUR 420000.00','€420.00','€42,000.00','EUR -4200.00','EUR NaN','EUR 4,20,000','EUR 4200 and 7800']){assert.notEqual(displayedEuroCents(display),420000,display);results.moneyParser.push({display,rejected:true});}
for(const mode of ['healthy','money_us','money_de','money_space','money_plain','money_scale']){
 let report=await evaluate({site:path.join(root,'fixture'),out:path.join(out,mode),env:{FRONTEND_FIXTURE_MODE:mode},screenshots:mode==='healthy'});assert.equal(report.denominator,11);assert.equal(report.fatal,null);assert.equal(report.groups.find(g=>g.name==='authorized_cards').status,'pass');
 assert.equal(report.groups.find(g=>g.name==='detail_budget').status,mode==='money_scale'?'fail':'pass');
 if(mode!=='money_scale')assert.equal(report.passed,GROUPS.length);
 if(mode==='healthy')assert.equal(report.screenshots.filter(s=>s.status==='captured').length,12);
 results.moneyBrowser.push({mode,budgetGroup:report.groups.find(g=>g.name==='detail_budget').status,healthyControl:'authorized_cards',passed:report.passed});console.log(JSON.stringify(results.moneyBrowser.at(-1)));
}
await writeFile(path.join(out,'regression.json'),JSON.stringify(results,null,2));console.log(JSON.stringify({status:'pass',cleanupCases:results.cleanup.length,moneyParserCases:results.moneyParser.length,moneyBrowserCases:results.moneyBrowser.length,out}));
