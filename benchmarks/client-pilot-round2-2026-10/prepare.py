"""Prepare new paired workspaces from published fixtures, refusing existing paths."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--work-dir',required=True);p.add_argument('--node',required=True);p.add_argument('--playwright-import',required=True)
a=p.parse_args();source=Path(__file__).resolve().parent;work=Path(a.work_dir).resolve()
if work.exists():raise SystemExit('Refusing existing replay directory')
work.mkdir(parents=True)
for name in ('run.py','collect.py','telemetry.py','test_telemetry.py','test_prepare.py','evaluate.mjs','prices.json'):
 shutil.copy2(source/name,work/name)
for fixture in ('fixture','error-fixture'):
 shutil.copytree(source/fixture,work/fixture)
brief=work/'fixture/BRIEF.md'
brief.write_text(brief.read_text().replace('BENCHMARK_NODE',a.node).replace('BENCHMARK_PLAYWRIGHT_IMPORT',a.playwright_import))
shutil.copytree(source/'error-judge',work/'error-judge')
for kind,fixture,run_dir,protocol_name in [('design','fixture','runs','protocol.json'),('errors','error-fixture','error-runs','error-protocol.json')]:
 protocol=json.loads((source/protocol_name).read_text())
 protocol['recorded_fixture_sha256']=protocol['fixture_sha256'];protocol['recorded_evaluator_sha256']=protocol['evaluator_sha256'];protocol['recorded_runner_sha256']=protocol['runner_sha256']
 protocol['fixture_sha256']={str(f.relative_to(work/fixture)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((work/fixture).rglob('*')) if f.is_file()}
 evaluator=work/('evaluate.mjs' if kind=='design' else 'error-judge/evaluate.mjs')
 protocol['evaluator_sha256']=hashlib.sha256(evaluator.read_bytes()).hexdigest();protocol['runner_sha256']=hashlib.sha256((work/'run.py').read_bytes()).hexdigest();protocol['replay_of']='2026-10-11 exploratory round-two client pilot'
 (work/protocol_name).write_text(json.dumps(protocol,indent=2)+'\n')
 for condition in ('single','swarm'):
  site=work/run_dir/condition/'site';shutil.copytree(work/fixture,site)
  for command in [['git','init','--quiet'],['git','add','.'],['git','-c','user.name=Benchmark fixture','-c','user.email=benchmark@example.invalid','commit','--quiet','-m','Frozen replay fixture']]:subprocess.run(command,cwd=site,check=True)
print(work)
