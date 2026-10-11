"""Run one frozen condition through the native logged-in CLI, never a direct API."""
from pathlib import Path
import subprocess,json,time,sys,os,signal
ROOT=Path(__file__).resolve().parent
kind,condition=sys.argv[1:3]
assert kind in ('design','errors') and condition in ('single','swarm')
directory=ROOT/('runs' if kind=='design' else 'error-runs')/condition
site=directory/'site';protocol=json.loads((ROOT/('protocol.json' if kind=='design' else 'error-protocol.json')).read_text())
limit=protocol['shared_budget_seconds'];capacity=protocol['swarm_active_helpers_cap']
command=['codex','--no-daemon','-a','never','exec','--json','--ignore-user-config','--strict-config','--enable','multi_agent_v2','--enable','model_catalog_in_context','-m',protocol['root_model'],'-c','model_reasoning_effort='+json.dumps(protocol['root_reasoning_effort']),'-c','features.apps=false','-c','agents.max_concurrent_threads_per_session='+str(capacity),'-s','workspace-write','-C',str(site),'-o',str(directory/'final.md')]
if condition=='single':command+=['--disable','multi_agent','-c','agents.enabled=false']
else:command+=['--enable','multi_agent','-c','agents.enabled=true']
prompt=('Complete BRIEF.md and its three-client portfolio task. ' if kind=='design' else 'Complete README.md: discover, reproduce, report and fix actual contract defects in the three helper modules, add focused regressions, and write FINDINGS.json. Do not read outside this solver workspace or inspect any oracle/evaluator/other condition. No image generation. ')
prompt+='Apply the revised project AGENTS.md policy, preserving risk and verification. Use already supplied instructions; retrieve only missing relevant contracts/source. '
if condition=='single':prompt+='CONTROL: do all implementation, image generation if required, diagnosis and validation yourself. No helpers, delegated model calls, other CLI/model sessions or child agents. This restriction overrides optional delegation.'
else:prompt+='ADAPTIVE SWARM: use justified native delegation for ready independent work, normally coherent direct owners and useful primary work. Do not force a hierarchy or a helper for a small coupled interaction. Choose helper model/effort from native catalog/support only; scope contexts/files and concise returns, avoid duplicate investigations and repeated passing tests. Primary owns final integration and product quality. Shared capacity primary plus '+str(capacity)+' active descendants; reserve verification. No external CLI/model sessions. Report actual topology and limitations.'
prompt+=' Entire tree shares '+str(limit)+' seconds including all tools/checks/retries; branch allowances do not reset it. No human follow-up, commits, deployment or account changes.'
if (directory/'metadata.json').exists():raise SystemExit('Refusing to rerun an already-started condition')
start=time.time();meta={'kind':kind,'condition':condition,'start_unix':start,'command':command,'prompt':prompt,'wall_time_limit_seconds':limit}
(directory/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
with (directory/'events.jsonl').open('w') as out,(directory/'stderr.log').open('w') as err:
 process=subprocess.Popen(command+[prompt],stdout=out,stderr=err,start_new_session=True)
 try:code=process.wait(timeout=limit);timed_out=False
 except subprocess.TimeoutExpired:
  os.killpg(process.pid,signal.SIGTERM)
  try:process.wait(timeout=10)
  except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
  code=process.returncode;timed_out=True
end=time.time();meta.update(end_unix=end,elapsed_seconds=end-start,exit_code=code,timed_out=timed_out)
(directory/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps({k:meta[k] for k in ('kind','condition','elapsed_seconds','exit_code','timed_out')}),flush=True)
