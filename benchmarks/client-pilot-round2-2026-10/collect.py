"""Collect only known native root/descendant sessions; raw logs stay private."""
import json,argparse
from pathlib import Path
import telemetry
ROOT=Path(__file__).resolve().parent

def collect(kind,condition,sessions):
 directory=ROOT/('runs' if kind=='design' else 'error-runs')/condition
 events=[json.loads(x) for x in (directory/'events.jsonl').read_text().splitlines()]
 roots=[x['thread_id'] for x in events if x.get('type')=='thread.started']
 if len(roots)!=1:raise ValueError('Expected one native root')
 completions=[x['usage'] for x in events if x.get('type')=='turn.completed']
 account=telemetry.extract(sessions,roots[0],completions[0] if len(completions)==1 else None)
 if len(completions)!=1:
  account['flags'].append('cli_completion_missing_or_duplicated');account['standard_short_estimated_usd']=None
 discovered=telemetry.discover(sessions,roots[0])
 parents={sid:telemetry.parent_ids(rows[0][1]) for sid,rows in discovered.items() if len(rows)==1}
 depths={roots[0]:0}
 while True:
  new={sid:min(depths[p]+1 for p in ps if p in depths) for sid,ps in parents.items() if sid not in depths and ps & depths.keys()}
  if not new:break
  depths.update(new)
 ordered=sorted(depths,key=lambda sid:(depths[sid],sid));labels={sid:'primary' if sid==roots[0] else f'helper-{i}' for i,sid in enumerate(ordered)}
 account['tree']=[{'agent':labels[sid],'depth':depths[sid],'parents':[labels[p] for p in sorted(parents.get(sid,set())) if p in labels]} for sid in ordered]
 account['observed_max_depth']=max(depths.values());(directory/'telemetry.json').write_text(json.dumps(account,indent=2)+'\n')
 if kind=='design':
  manifest_path=directory/'site/image-manifest.json'
  manifest=json.loads(manifest_path.read_text()) if manifest_path.is_file() else []
  if not isinstance(manifest,list):raise ValueError('Manifest must be an attempt array')
  pages={p:{'attempts':0,'successful_outputs':0,'failures':0,'missing_outputs':0} for p in ('hotel','studio','landscape')}
  for attempt in manifest:
   row=pages[attempt['page']];row['attempts']+=1
   if attempt['success']:
    row['successful_outputs']+=1;paths=attempt.get('output_paths',[])
    if not paths or any(not (directory/'site'/p).is_file() for p in paths):row['missing_outputs']+=1
   else:row['failures']+=1
  count=sum(x['attempts'] for x in pages.values())
  images={'pages':pages,'self_reported_attempts':count,'native_image_calls':account['image_calls'],'transcript_count_reconciled':manifest_path.is_file() and count==account['image_calls'],'backend_model':None,'generation_tokens':None,'image_price':None,'probe_excluded':True}
  (directory/'images.json').write_text(json.dumps(images,indent=2)+'\n')
 return account
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('kind',choices=['design','errors']);p.add_argument('condition',choices=['single','swarm']);p.add_argument('--sessions-dir',required=True);a=p.parse_args();r=collect(a.kind,a.condition,a.sessions_dir);print(json.dumps({k:r[k] for k in ('session_counts','tokens','image_calls','standard_short_estimated_usd','flags')}))
