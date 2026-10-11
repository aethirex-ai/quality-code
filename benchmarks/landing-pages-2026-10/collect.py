"""Collect private native-run measurements, emitting only sanitized artifacts."""
import json
from pathlib import Path
import telemetry

ROOT=Path(__file__).resolve().parent

def collect(condition,sessions_dir):
    directory=ROOT/'runs'/condition
    events=[json.loads(line) for line in (directory/'events.jsonl').read_text().splitlines()]
    roots=[e['thread_id'] for e in events if e.get('type')=='thread.started']
    if len(roots)!=1:raise ValueError('Expected exactly one root thread')
    completions=[e['usage'] for e in events if e.get('type')=='turn.completed']
    usage=completions[0] if len(completions)==1 else None
    account=telemetry.extract(sessions_dir,roots[0],usage)
    discovered=telemetry.discover(sessions_dir,roots[0])
    parents={sid:telemetry.parent_ids(rows[0][1]) for sid,rows in discovered.items() if len(rows)==1}
    depths={roots[0]:0}
    while True:
        additions={sid:min(depths[p]+1 for p in values if p in depths)
                   for sid,values in parents.items() if sid not in depths and values & depths.keys()}
        if not additions:break
        depths.update(additions)
    ordered=sorted(depths,key=lambda sid:(depths[sid],sid))
    labels={sid:'primary' if sid==roots[0] else f'helper-{i}' for i,sid in enumerate(ordered)}
    account['tree']=[{'agent':labels[sid],'depth':depths[sid],
                     'parents':[labels[p] for p in sorted(parents.get(sid,set())) if p in labels]}
                    for sid in ordered]
    account['observed_max_depth']=max(depths.values())
    if len(completions)!=1:account['flags'].append('cli_completion_missing_or_duplicated')
    (directory/'telemetry.json').write_text(json.dumps(account,indent=2)+'\n')
    manifest=json.loads((directory/'site'/'image-manifest.json').read_text())
    if not isinstance(manifest,list):raise ValueError('Image manifest must be attempt array')
    images={page:{'attempts':0,'successful_outputs':0,'failures':0,'missing_outputs':0} for page in ['shop','craftsman','restaurant']}
    for attempt in manifest:
        row=images[attempt['page']];row['attempts']+=1
        if attempt['success']:
            row['successful_outputs']+=1
            paths=attempt.get('output_paths',[])
            if not paths or any(not (directory/'site'/p).is_file() for p in paths):row['missing_outputs']+=1
        else:row['failures']+=1
    measured=sum(row['attempts'] for row in images.values())
    result={'pages':images,'self_reported_attempts':measured,'native_image_calls':account['image_calls'],'transcript_count_reconciled':measured==account['image_calls'],'backend_model':None,'generation_tokens':None,'image_price':None,'probe_excluded':True}
    (directory/'images.json').write_text(json.dumps(result,indent=2)+'\n')
    return account,result

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('condition',choices=['single','swarm']);parser.add_argument('--sessions-dir',required=True);args=parser.parse_args()
    account,images=collect(args.condition,args.sessions_dir)
    print(json.dumps({'tokens':account['tokens'],'images':images,'flags':account['flags']}))
