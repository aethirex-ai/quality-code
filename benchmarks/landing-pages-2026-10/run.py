from pathlib import Path
import subprocess,json,time,sys,os,signal
root=Path(__file__).resolve().parent
protocol=json.loads((root/'protocol.json').read_text())
condition=sys.argv[1];directory=root/'runs'/condition;site=directory/'site'
base=['codex','--no-daemon','-a','never','exec','--json','--ignore-user-config','--strict-config','--enable','multi_agent_v2','--enable','model_catalog_in_context','-m',protocol['root_model'],'-c','model_reasoning_effort="high"','-c','features.apps=false','-c','agents.max_concurrent_threads_per_session=3','-s','workspace-write','-C',str(site),'-o',str(directory/'final.md')]
if condition=='single':base+=['--disable','multi_agent','-c','agents.enabled=false']
else:base+=['--enable','multi_agent','-c','agents.enabled=true']
prompt='Read BRIEF.md and complete its three-business landing-page portfolio task. Follow the managed Quality Code risk and validation workflow. '
if condition=='single':prompt+='CONTROL CONDITION: perform all implementation, image generation, thinking and builder validation yourself. No subagents, delegation, recursive LLM CLI processes or additional model sessions. This single-agent restriction is explicit and overrides optional delegation guidance.'
else:prompt+='SWARM CONDITION: apply the installed Quality Code bounded swarm and scoped-context rules. This workload has independent page workstreams. Use justified native subagents and a workstream lead that delegates a bounded part to its own helper where useful; preserve useful primary work, shared total cap of primary plus 3 active descendants, shared 20-minute budget, reserved validation capacity, independent file ownership and small sufficient briefs. Choose child model/effort only through native supported controls and the current catalog. Do not open more CLI/model sessions outside native collaboration tools. Do not force an unnecessary management hierarchy if native controls do not permit it; record actual delegation and limitations.'
start=time.time();meta={'condition':condition,'start_unix':start,'command':base,'prompt':prompt,'wall_time_limit_seconds':1200};(directory/'metadata.json').write_text(json.dumps(meta,indent=2))
with (directory/'events.jsonl').open('w') as out,(directory/'stderr.log').open('w') as err:
 process=subprocess.Popen(base+[prompt],stdout=out,stderr=err,start_new_session=True)
 try:code=process.wait(timeout=1200);timed_out=False
 except subprocess.TimeoutExpired:
  os.killpg(process.pid,signal.SIGTERM)
  try:process.wait(timeout=10)
  except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
  code=process.returncode;timed_out=True
meta.update({'end_unix':time.time(),'elapsed_seconds':time.time()-start,'exit_code':code,'timed_out':timed_out});(directory/'metadata.json').write_text(json.dumps(meta,indent=2))
print(json.dumps({k:meta[k] for k in ['condition','elapsed_seconds','exit_code','timed_out']}))
