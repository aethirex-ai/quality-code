"""Matched native builder sessions; shared time includes owned solver cleanup."""
import json,os,sys,time,signal,subprocess,select,socket,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
NODE=os.environ.get('PREVIEW_NODE','node')
PW=os.environ.get('PREVIEW_PLAYWRIGHT_MODULE','playwright')
def terminate_group(process,grace=2):
 pgid=process.pid
 try:os.killpg(pgid,signal.SIGTERM)
 except ProcessLookupError:return
 until=time.monotonic()+grace
 while time.monotonic()<until:process.poll();time.sleep(.05)
 try:os.killpg(pgid,signal.SIGKILL)
 except ProcessLookupError:pass
 try:process.wait(timeout=2)
 except subprocess.TimeoutExpired:raise RuntimeError('Owned process leader did not exit')
def command(condition,site,protocol):
 args=['codex','--no-daemon','-a','never','exec','--json','--ignore-user-config','--strict-config','--enable','model_catalog_in_context','-m',protocol['root_model'],'-c','model_reasoning_effort='+json.dumps(protocol['root_reasoning_effort']),'-c','features.apps=false','-c','agents.max_concurrent_threads_per_session='+str(protocol['native_helper_cap']),'-c','default_permissions="portal-local"','-c','permissions.portal-local.extends=":workspace"','-c','permissions.portal-local.network.enabled=true','-c','permissions.portal-local.network.allow_local_binding=true','-c','permissions.portal-local.network.domains={"127.0.0.1"="allow","localhost"="allow"}','-c','features.network_proxy=true','-C',str(site)]
 args+=['--enable' if condition=='adaptive' else '--disable','multi_agent_v2','--enable' if condition=='adaptive' else '--disable','multi_agent','-c','agents.enabled='+('true' if condition=='adaptive' else 'false')]
 return args

def cleanup_bound_backend(site,port):
 """Only a listener whose kernel cwd and command identify this unique app."""
 found=subprocess.run(['lsof','-nP','-iTCP:'+str(port),'-sTCP:LISTEN','-t'],capture_output=True,text=True,timeout=2)
 notes=[]
 for token in set(found.stdout.split()):
  if not token.isdigit():continue
  pid=int(token);cwd=subprocess.run(['lsof','-a','-p',str(pid),'-d','cwd','-Fn'],capture_output=True,text=True,timeout=2).stdout
  cmd=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True,timeout=2).stdout.strip()
  if 'n'+str(site.resolve()) not in cwd.splitlines() or 'server.py'not in cmd or str(port)not in cmd:
   notes.append({'listener_pid':pid,'action':'not_signaled','reason':'ownership not proven'});continue
  try:os.kill(pid,signal.SIGTERM)
  except ProcessLookupError:continue
  deadline=time.monotonic()+1
  while time.monotonic()<deadline:
   try:os.kill(pid,0)
   except ProcessLookupError:break
   time.sleep(.05)
  # Revalidate before escalation so a reused PID cannot be signaled blindly.
  current=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True,timeout=2).stdout.strip()
  if current==cmd:
   try:os.kill(pid,signal.SIGKILL)
   except ProcessLookupError:pass
  notes.append({'listener_pid':pid,'action':'owned backend terminated'})
 return notes

def verify_freeze(protocol,site):
 required={'run.py','telemetry.py','prices.json','judge/backend/evaluate.py','judge/frontend/evaluate.mjs','preview/broker.py','preview/render.mjs'}
 hashes=protocol.get('frozen_sources_sha256',{})
 if not required.issubset(hashes):raise RuntimeError('Incomplete measured-source freeze')
 for relative,expected in hashes.items():
  path=ROOT/relative
  if path.is_symlink()or not path.is_file()or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
   raise RuntimeError('Frozen source changed: '+relative)
 for relative,expected in protocol['fixture_sha256'].items():
  for base in (ROOT/'fixture',site):
   path=base/relative
   if path.is_symlink()or not path.is_file()or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
    raise RuntimeError('Fixture changed: '+str(base/relative))
 if (site/'server.py').exists()or (site/'public').exists():raise RuntimeError('App implementation already exists before timing')

def run(condition):
 if condition not in ['single','adaptive']:raise ValueError('Unknown condition')
 protocol=json.loads((ROOT/'protocol.json').read_text());d=ROOT/'runs'/condition;site=d/'site';port=protocol['ports'][condition]
 if(d/'metadata.json').exists():raise RuntimeError('Refusing already-started condition')
 verify_freeze(protocol,site)
 prompt=(ROOT/'APP_PROMPT.txt').read_bytes()
 if hashlib.sha256(prompt).hexdigest()!=protocol['prompt_sha256'] or (site/'APP_PROMPT.txt').read_bytes()!=prompt:raise RuntimeError('Common prompt changed')
 # Browser startup is preparation. All termination after the native start is measured.
 env=os.environ.copy();env.update(PREVIEW_NODE=NODE,PREVIEW_PLAYWRIGHT_MODULE=PW,BENCHMARK_NODE=NODE,PORTAL_PORT=str(port))
 log=(d/'preview-broker.log').open('w');broker=None;process=None;meta=None;start_clock=None;failure=None
 try:
  broker=subprocess.Popen([sys.executable,str(ROOT/'preview/broker.py'),'--workspace',str(site),'--port',str(port)],stdout=subprocess.PIPE,stderr=log,text=True,env=env,start_new_session=True)
  ready,_,_=select.select([broker.stdout],[],[],30)
  if not ready:raise RuntimeError('Browser readiness timeout before timer')
  line=broker.stdout.readline();log.write(line);log.flush();state=json.loads(line)
  if not state.get('ready')or broker.poll()is not None:raise RuntimeError('Browser not ready')
  h=subprocess.run([sys.executable,str(site/'preview_client.py'),'--workspace',str(site),'--ready'],capture_output=True,text=True,timeout=10)
  if h.returncode or not json.loads(h.stdout).get('ready'):raise RuntimeError('Mailbox handshake failed')
  with socket.socket()as sock:
   try:sock.bind(('127.0.0.1',port))
   except OSError:raise RuntimeError('Assigned app port already occupied')
  args=command(condition,site,protocol)+['-o',str(d/'final.md'),'-'];start_clock=time.monotonic()
  meta={'condition':condition,'start_unix':time.time(),'command':args,'common_prompt_sha256':protocol['prompt_sha256'],'protocol_sha256':hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest(),'shared_budget_seconds':protocol['shared_budget_seconds'],'preview_ready_before_timer':True,'parent_does_not_start_backend':True,'exit_code':None,'timed_out':False}
  (d/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
  with(d/'events.jsonl').open('wb')as out,(d/'stderr.log').open('wb')as err:
   process=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=out,stderr=err,cwd=site,env=env,start_new_session=True)
   process.stdin.write(prompt);process.stdin.close()
   remaining=protocol['shared_budget_seconds']-protocol['cleanup_reserve_seconds']-(time.monotonic()-start_clock)
   try:meta['exit_code']=process.wait(timeout=max(0,remaining))
   except subprocess.TimeoutExpired:meta['timed_out']=True
 except BaseException as exc:
  failure=exc
 finally:
  cleanup_errors=[]
  if process is not None:
   try:terminate_group(process)
   except Exception as exc:cleanup_errors.append('native cleanup: '+str(exc))
   if meta is not None:meta['exit_code']=process.returncode
  if meta is not None:
   try:meta['backend_cleanup']=cleanup_bound_backend(site,port)
   except Exception as exc:cleanup_errors.append('backend cleanup: '+str(exc))
  if broker is not None:
   try:terminate_group(broker)
   except Exception as exc:cleanup_errors.append('browser cleanup: '+str(exc))
   if broker.stdout:broker.stdout.close()
  log.close()
  if meta is not None:
   meta.update(end_unix=time.time(),elapsed_seconds=time.monotonic()-start_clock,cleanup_errors=cleanup_errors)
   meta['budget_exceeded']=meta['elapsed_seconds']>protocol['shared_budget_seconds']
   if failure is not None:meta['runner_error']=type(failure).__name__+': '+str(failure)
   (d/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
   print(json.dumps({k:meta[k]for k in ['condition','elapsed_seconds','exit_code','timed_out','budget_exceeded','cleanup_errors']}),flush=True)
  if cleanup_errors and failure is None:failure=RuntimeError('; '.join(cleanup_errors))
 if failure is not None:raise failure
if __name__=='__main__':run(sys.argv[1])
