from pathlib import Path
import json, subprocess, shutil
root=Path(__file__).parent
fixture=root.parent/'error-fixture'
seeds=json.loads((root/'seeds.json').read_text())
results=[]
for seed in seeds:
    target=root/'isolation-case'
    if target.exists(): shutil.rmtree(target)
    shutil.copytree(fixture,target)
    p=target/seed['file']
    p.write_text(p.read_text().replace(seed['faultyExpression'],seed['oracleReplacement']))
    proc=subprocess.run(['node',str(root/'evaluate.mjs'),str(target)],capture_output=True,text=True)
    report=json.loads(proc.stdout)
    passes=[group['id'] for group in report['seeds'] if group['pass']]
    assert passes == [seed['id']], (seed['id'],passes)
    assert report['regressionCount']==0,seed['id']
    results.append({'singleFix':seed['id'],'passingSeedGroups':passes,'regressionCount':0})
shutil.rmtree(target)
(root/'isolation-results.json').write_text(json.dumps(results,indent=2)+'\n')
print('PASS: each isolated fix resolves exactly its own seed group; healthy controls remain passing')
