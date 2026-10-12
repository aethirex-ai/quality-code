"""Post-run accounting. Native logs remain private; missing evidence is explicit."""
import argparse,json,hashlib
from pathlib import Path
from decimal import Decimal
import telemetry
ROOT=Path(__file__).resolve().parent

def records(path):
 if not path.is_file():return None
 rows=[]
 for line in path.read_text().splitlines():
  if line.strip():rows.append(json.loads(line))
 return rows

def iteration_summary(site):
 owners={}
 for owner in ['lighting','expedition','integration']:
  checks=records(site/owner/'check-runs.jsonl');issues=records(site/owner/'issues.jsonl');cycles=[]
  if checks is not None:
   waiting={}
   for r in checks:
    key=r['check_id']
    if r['phase']=='initial':continue
    if r['exit_code']!=0:waiting.setdefault(key,[]).append(r)
    elif key in waiting:
     fail=waiting.pop(key);cycles.append({'check_id':key,'failed_runs':len(fail),'recheck_phase':r['phase'],'issue_id':r.get('issue_id'),'classification':'observed failed-check-to-pass sequence; independent cause/fix review required'})
  grouped={}
  if issues is not None:
   for r in issues:
    if not isinstance(r.get('id'),str) or not r['id']:raise ValueError('Issue needs stable id')
    grouped.setdefault(r['id'],[]).append(r)
  owners[owner]={'check_history_present':checks is not None,'issue_history_present':issues is not None,'recorded_check_runs':len(checks) if checks is not None else None,'initial_scaffold_nonzero_exits':sum(r['exit_code']!=0 and r['phase']=='initial' for r in checks) if checks is not None else None,'verification_nonzero_exits':sum(r['exit_code']!=0 and r['phase']!='initial' for r in checks) if checks is not None else None,'passing_runs':sum(r['exit_code']==0 for r in checks) if checks is not None else None,'observed_check_recovery_sequences':cycles if checks is not None else None,'distinct_reported_issue_ids':len(grouped) if issues is not None else None,'latest_reported_statuses':{k:v[-1].get('status') for k,v in grouped.items()},'limits':'Reported ids are not independently confirmed distinct software defects; planned failures, tooling, visuals, duplicate causes and unresolved final findings are classified separately.'}
 previews=records(site/'.preview-events.jsonl')
 return {'owners':owners,'preview_history_present':previews is not None,'recorded_previews':len(previews) if previews is not None else None,'classification_pending_independent_review':True}

def freeze_output(directory):
 hashes={str(p.relative_to(directory/'site')):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((directory/'site').rglob('*')) if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts and '.preview-mailbox' not in p.parts}
 freeze_path=directory/'frozen-output-hashes.json'
 if freeze_path.exists():
  if json.loads(freeze_path.read_text())!=hashes:raise ValueError('Frozen output changed; refusing to replace original evidence')
 else:freeze_path.write_text(json.dumps(hashes,indent=2)+'\n')

def collect(condition,sessions):
 directory=ROOT/'runs'/condition;meta=json.loads((directory/'metadata.json').read_text())
 if 'end_unix' not in meta:raise ValueError('Refusing complete accounting for active condition')
 events=records(directory/'events.jsonl');roots=[x['thread_id'] for x in events if x.get('type')=='thread.started'];completions=[x['usage'] for x in events if x.get('type')=='turn.completed']
 if len(roots)!=1:raise ValueError('Expected exactly one native root')
 account=telemetry.extract(sessions,roots[0],completions[0] if len(completions)==1 else None)
 if len(completions)!=1:account['flags'].append('cli_completion_missing_or_duplicated');account['standard_short_estimated_usd']=None
 prices=json.loads((ROOT/'prices.json').read_text());components={};total={'uncached_input':Decimal(0),'cached_input':Decimal(0),'output_including_reasoning':Decimal(0)}
 if account['standard_short_estimated_usd'] is not None:
  for model,t in account['models'].items():
   rates=prices['models'][model]['short'];row={'uncached_input':Decimal(t['input_tokens']-t['cached_input_tokens'])*Decimal(str(rates[0]))/1000000,'cached_input':Decimal(t['cached_input_tokens'])*Decimal(str(rates[1]))/1000000,'output_including_reasoning':Decimal(t['output_tokens'])*Decimal(str(rates[3]))/1000000}
   components[model]={k:str(v) for k,v in row.items()};components[model]['total']=str(sum(row.values()))
   for k in total:total[k]+=row[k]
  if abs(float(sum(total.values()))-account['standard_short_estimated_usd'])>1e-12:raise ValueError('Independent Decimal mismatch')
 account['cost_components_usd']={'by_model':components,'total':{k:str(v) for k,v in total.items()}} if components else None
 account['iteration_evidence']=iteration_summary(directory/'site')
 path=directory/'site/image-manifest.json'
 if path.is_file():
  attempts=json.loads(path.read_text());counts={c:{'attempts':0,'successes':0,'failures':0,'missing_outputs':0} for c in ['lighting','expedition']}
  if not isinstance(attempts,list):raise ValueError('Manifest must be attempt array')
  for a in attempts:
   if type(a.get('success'))is not bool:raise ValueError('Attempt success must be boolean')
   row=counts[a['client']];row['attempts']+=1;row['successes' if a['success'] else 'failures']+=1
   if a['success']:
    paths=a.get('output_paths',[])
    if not paths:row['missing_outputs']+=1
    for rel in paths:
     p=(directory/'site'/rel).resolve()
     if not p.is_relative_to((directory/'site').resolve()):raise ValueError('Image path escapes measured workspace')
     if not p.is_file():row['missing_outputs']+=1
  images={'manifest_present':True,'by_client':counts,'native_calls':account['image_calls'],'automatic_count_reconciled':sum(r['attempts'] for r in counts.values())==account['image_calls'],'generator_model':None,'generator_tokens':None,'generator_charges':None}
 else:images={'manifest_present':False,'by_client':None,'native_calls':account['image_calls'],'automatic_count_reconciled':False}
 (directory/'telemetry.json').write_text(json.dumps(account,indent=2)+'\n');(directory/'images.json').write_text(json.dumps(images,indent=2)+'\n')
 freeze_output(directory)
 return account
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('condition',choices=['single','swarm']);p.add_argument('--sessions-dir',required=True);a=p.parse_args();r=collect(a.condition,a.sessions_dir);print(json.dumps({k:r[k] for k in ['tokens','models','standard_short_estimated_usd','cost_components_usd','flags']}))
