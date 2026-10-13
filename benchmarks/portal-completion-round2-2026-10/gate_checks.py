"""Fixed contract gates inside completion elapsed; no model/other-condition access."""
from pathlib import Path
import json,os,subprocess,sys,time,signal
from run import owned_run
ROOT=Path(__file__).resolve().parent

def gates(site,out):
 site=Path(site).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True);env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';node=env.get('PREVIEW_NODE','node');env.setdefault('BENCHMARK_PLAYWRIGHT_IMPORT',env.get('PREVIEW_PLAYWRIGHT_MODULE','playwright'))
 specs=[('backend',[sys.executable,'-B',str(ROOT/'judge/backend/evaluate.py'),str(site),str(out/'backend.json')],out/'backend.json',120),('frontend',[node,'--input-type=module','-e',"import {evaluate} from './judge/frontend/evaluate.mjs'; const [site,out]=process.argv.slice(1);const r=await evaluate({site,out,screenshots:false});console.log(JSON.stringify(r));process.exitCode=r.fatal||r.failed||r.notRun?1:0;",str(site),str(out/'frontend')],out/'frontend/report.json',80),('recovery',[node,str(ROOT/'judge/frontend/defect-probes.mjs'),str(site),str(out/'recovery')],out/'recovery/defect-probes.json',70)]
 rows=[];started=time.monotonic()
 for name,args,report,timeout in specs:
  row={'name':name,'command':args,'report':str(report)};rows.append(row)
  try:
   proc=owned_run(args,cwd=ROOT,env=env,timeout=timeout);row['exit_code']=proc.returncode;(out/(name+'-stdout.txt')).write_text(proc.stdout[-30000:]);(out/(name+'-stderr.log')).write_text(proc.stderr[-10000:]);value=json.loads(report.read_text());row['raw']=value
   if name=='backend':row['passed']=value.get('passed')==12 and value.get('denominator')==12 and not value.get('error');row['unknown']=bool(value.get('error'))
   elif name=='frontend':row['passed']=value.get('passed')==11 and value.get('denominator')==11 and not(value.get('fatal')or value.get('notRun'));row['unknown']=bool(value.get('fatal'))
   else:row['passed']=value.get('passed')==3 and value.get('supplementalCheckCount')==3 and len(value.get('checks',[]))==3 and not value.get('fatal');row['unknown']=bool(value.get('fatal'))
   row['passed']=row['passed'] and proc.returncode==0
  except Exception as exc:row.update(passed=False,unknown=True,error=type(exc).__name__+': '+str(exc))
 result={'schema':1,'accepted':all(row['passed'] for row in rows),'tool_incomplete':any(row['unknown'] for row in rows),'elapsed_seconds':time.monotonic()-started,'checks':rows,'boundary':'Per-condition gate checks are inside completion clock. Group/assertion failures are not distinct bugs.'};(out/'gate-checks.json').write_text(json.dumps(result,indent=2)+'\n');return result
def interrupted(signum, frame):
 raise KeyboardInterrupt('Owned gate interrupted; nested finally cleanup required')

if __name__=='__main__':
 signal.signal(signal.SIGTERM, interrupted)
 result=gates(*sys.argv[1:]);print(json.dumps(result));raise SystemExit(0 if result['accepted'] else 1)
