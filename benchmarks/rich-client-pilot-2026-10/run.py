"""Run one frozen native condition with equal bounded preview access and no API key."""
from pathlib import Path
import json,subprocess,sys,time,signal,os,select
ROOT=Path(__file__).resolve().parent

def terminate_group(process,grace=2):
 """Terminate surviving descendants even when the group leader already exited."""
 pgid=process.pid
 try:os.killpg(pgid,signal.SIGTERM)
 except ProcessLookupError:return
 deadline=time.monotonic()+grace
 while time.monotonic()<deadline:
  process.poll()
  time.sleep(0.05)
 try:os.killpg(pgid,signal.SIGKILL)
 except ProcessLookupError:pass
 try:process.wait(timeout=2)
 except subprocess.TimeoutExpired:raise RuntimeError('Process leader did not terminate')

def command_and_prompt(condition,protocol,site):
 command=['codex','--no-daemon','-a','never','exec','--json','--ignore-user-config','--strict-config','--enable','multi_agent_v2','--enable','model_catalog_in_context','-m',protocol['root_model'],'-c','model_reasoning_effort='+json.dumps(protocol['root_reasoning_effort']),'-c','features.apps=false','-c','agents.max_concurrent_threads_per_session='+str(protocol['swarm_active_helpers_cap']),'-s','workspace-write','-C',str(site)]
 prompt='Complete BRIEF.md: two rich three-page client experiences plus portfolio index, four native images, exact local interaction contracts and iteration/error evidence. Apply supplied project policy; read relevant source/contracts only. Same native root and shared35minute budget as paired condition. Preview client in RUNTIME.md gives generic local screenshots/diagnostics, not grading. Inspect rendered desktop/mobile and relevant interaction states, fix observed issues and preserve failed checks/fix cycles via qa_check.py and owner issues.jsonl. No external model/CLI sessions, no other condition/evaluator inspection; outside-workspace retrieval only for explicitly listed runtime libraries, required applicable skill instructions and native-generated asset paths, no account/commit/deploy changes. '
 if condition=='single':
  command+=['--disable','multi_agent','-c','agents.enabled=false'];prompt+='CONTROL: perform all image generation, implementation and checks yourself, no subagents/delegated model calls. Optional delegation is overridden. '
 else:
  command+=['--enable','multi_agent','-c','agents.enabled=true']
  prompt+="""CHEAPER IMPLEMENTATION OWNERSHIP: discover currently supported models/effort/tools through the native catalog and MODEL_COSTS.json dated official rate evidence. Select the least costly supported model likely to meet each task contract. Delegate the two ready independent complete client experiences to qualified lower-cost owners in fresh scoped context; each owns all its pages/styles/interactions and focused checks. Explain intensity/uncertainty/tool fit and supported effort in concise MODEL_DECISIONS.json (role,chosen_model,effort,evidence,reason,escalations); prices/model identifiers here are experiment observations, never universal policy defaults. Do not use the root-priced model for initial routine implementation merely because it is familiar; if no cheaper qualified option is available report routing limitation. Escalate on concrete repeated failed checks/ambiguous requirements rather than silently choosing expensive workers. No forced recursion; ceiling two active implementation helpers, reserve independent gate capacity if needed. Primary owns concise design/architecture contract (DESIGN.md, roughly400words), native four-image generation/inspection while owners implement, root portfolio, manifest and integration/rendered validation. Pass image paths rather than full results; don't reimplement complete helper work or rewrite verbose helper reports. Review changed scope/evidence and perform necessary integration checks; correctness and product quality remain mandatory. Aim to keep most implementation output on cheaper owners and primary output concise; exact usage unavailable is a disclosed limitation, not invented budget numbers. Track genuine issues/fix cycles regardless of who introduced or discovered them. """
 prompt+='Entire tree shares '+str(protocol['shared_budget_seconds'])+' seconds including images,tools,retries,preview,checks,coordination. Branch budgets never reset. Reserve final5minutes for integration/visual verification. Return concise paths, checks, unresolved issues, routing/model/effort/topology and limitations. No human follow-up.'
 return command,prompt

def run(condition):
 if condition not in ('single','swarm'):raise ValueError('condition')
 protocol=json.loads((ROOT/'protocol.json').read_text());directory=ROOT/'runs'/condition;site=directory/'site'
 if (directory/'metadata.json').exists():raise SystemExit('Refusing to rerun already-started condition')
 env=os.environ.copy();env['BENCHMARK_NODE']=env.get('PREVIEW_NODE','node');brokerlog=(directory/'preview-broker.log').open('w')
 broker=subprocess.Popen([sys.executable,str(ROOT/'preview/broker.py'),'--workspace',str(site)],stdout=subprocess.PIPE,stderr=brokerlog,text=True,env=env,start_new_session=True)
 try:
  ready,_,_=select.select([broker.stdout],[],[],30)
  if not ready:raise RuntimeError('Preview broker readiness timeout before timed run')
  line=broker.stdout.readline();brokerlog.write(line);brokerlog.flush()
  if not line.strip() or broker.poll() is not None:raise RuntimeError('Preview unavailable before timed run')
  state=json.loads(line)
  if not state.get('ready'):raise RuntimeError('Preview readiness not confirmed')
  handshake=subprocess.run([sys.executable,str(site/'preview_client.py'),'--ready'],cwd=site,capture_output=True,text=True,timeout=10)
  if handshake.returncode or not json.loads(handshake.stdout).get('ready'):raise RuntimeError('Preview client handshake failed before timer')
  command,prompt=command_and_prompt(condition,protocol,site);command+=['-o',str(directory/'final.md')]
  start=time.time();meta={'condition':condition,'start_unix':start,'command':command,'prompt':prompt,'shared_budget_seconds':protocol['shared_budget_seconds'],'preview_ready_before_timer':True}
  (directory/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
  with (directory/'events.jsonl').open('w') as out,(directory/'stderr.log').open('w') as err:
   process=subprocess.Popen(command+[prompt],stdout=out,stderr=err,start_new_session=True,env=env)
   try:code=process.wait(timeout=max(0,protocol['shared_budget_seconds']-4));timed_out=False
   except subprocess.TimeoutExpired:
    terminate_group(process)
    code=process.returncode;timed_out=True
   finally:terminate_group(process)
  end=time.time();meta.update(end_unix=end,elapsed_seconds=end-start,exit_code=code,timed_out=timed_out)
  (directory/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps({k:meta[k] for k in ['condition','elapsed_seconds','exit_code','timed_out']}),flush=True)
 finally:
  try:terminate_group(broker)
  finally:
   if broker.stdout:broker.stdout.close()
   brokerlog.close()
if __name__=='__main__':run(sys.argv[1])
