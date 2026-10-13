"""Read native model metadata without creating a thread or running a model."""
import subprocess,json,time,select,signal
from pathlib import Path
p=subprocess.Popen(['codex','--no-daemon','app-server'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,start_new_session=True)
def send(v):p.stdin.write(json.dumps(v)+'\n');p.stdin.flush()
def response(id):
 end=time.monotonic()+20
 while time.monotonic()<end:
  ready,_,_=select.select([p.stdout],[],[],min(2,end-time.monotonic()))
  if not ready:continue
  line=p.stdout.readline()
  if not line:raise RuntimeError('Native metadata server ended')
  row=json.loads(line)
  if row.get('id')==id:return row
 raise RuntimeError('Native metadata timeout')
try:
 send({'id':1,'method':'initialize','params':{'clientInfo':{'name':'aethdesign-portal-preflight','version':'1.0'}}});r=response(1)
 if 'error'in r:raise RuntimeError('initialize rejected')
 send({'method':'initialized','params':{}});send({'id':2,'method':'model/list','params':{'includeHidden':False}});r=response(2)
 if 'error'in r:raise RuntimeError('model/list rejected '+str(r['error']))
 result=r.get('result',{});models=result.get('data',result.get('models',[]));allowed=['id','model','displayName','description','supportedReasoningEfforts','defaultReasoningEffort','isDefault','hidden']
 safe=[{k:v for k,v in m.items() if k in allowed} for m in models];Path('native-model-catalog.json').write_text(json.dumps({'method':'native app-server model/list; no thread/model execution','models':safe},indent=2)+'\n');print(json.dumps({'models':[{k:v for k,v in m.items() if k in ['id','model','supportedReasoningEfforts','defaultReasoningEffort']} for m in safe]}))
finally:
 try:__import__('os').killpg(p.pid,signal.SIGTERM)
 except ProcessLookupError:pass
 try:p.wait(timeout=2)
 except subprocess.TimeoutExpired:__import__('os').killpg(p.pid,signal.SIGKILL);p.wait(timeout=2)
