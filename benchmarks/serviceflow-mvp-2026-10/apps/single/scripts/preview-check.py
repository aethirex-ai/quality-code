"""Assert the supplied browser bridge outcomes; retain raw metadata and screenshot references."""
import argparse,json,subprocess,sys,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--id',required=True);p.add_argument('--page',default='/');p.add_argument('--viewport',choices=['375','1440'],default='1440');p.add_argument('--actions-file');p.add_argument('--expect',action='append',default=[]);a=p.parse_args()
if not re.fullmatch('[A-Za-z0-9_-]+',a.id):raise ValueError('Invalid check ID')
cmd=['python3','preview_client.py','--page',a.page,'--viewport',a.viewport]
if a.actions_file:cmd+=['--actions-file',a.actions_file]
r=subprocess.run(cmd,capture_output=True,text=True)
try:result=json.loads(r.stdout)
except Exception:print(json.dumps({'ok':False,'stderr':r.stderr[:300],'stdout':r.stdout[:300]}));sys.exit(1)
Path('evidence/browser').mkdir(exist_ok=True)
Path('evidence/browser/'+a.id+'.json').write_text(json.dumps(result,indent=2)+'\n')
failures=[]
if not result.get('ok'):failures.append(result.get('error','Bridge failure'))
for item in result.get('actionResults',[]):
 if not item.get('ok'):failures.append(item)
if result.get('horizontalOverflow'):failures.append('Document has horizontal overflow')
if result.get('errors'):failures.append(result['errors'])
if result.get('blockedRequests'):failures.append(result['blockedRequests'])
for text in a.expect:
 if text not in result.get('excerpt',''):failures.append('Expected visible text missing: '+text)
summary={'ok':not failures,'id':a.id,'viewport':a.viewport,'actions':len(result.get('actionResults',[])),'failures':failures,'screenshot':result.get('screenshot'),'excerpt':result.get('excerpt','')[:1200]}
print(json.dumps(summary));sys.exit(1 if failures else 0)
