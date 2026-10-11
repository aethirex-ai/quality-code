"""Prepare a NEW replay workspace; never modify an existing directory."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--work-dir',required=True)
parser.add_argument('--node',required=True)
parser.add_argument('--playwright-import',required=True)
args=parser.parse_args()
source=Path(__file__).resolve().parent;work=Path(args.work_dir).resolve()
if work.exists():raise SystemExit('Refusing existing replay directory')
work.mkdir(parents=True)
shutil.copytree(source/'fixture',work/'fixture')
brief=work/'fixture/BRIEF.md';brief.write_text(brief.read_text().replace('BENCHMARK_PLAYWRIGHT_IMPORT',args.playwright_import).replace('BENCHMARK_NODE',args.node))
protocol=json.loads((source/'protocol.json').read_text())
protocol['recorded_fixture_sha256']=protocol['fixture_sha256']
protocol['fixture_sha256']={str(p.relative_to(work/'fixture')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (work/'fixture').rglob('*') if p.is_file()}
protocol['replay_of']='2026-10-11 paired landing-page pilot'
(work/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
for name in ['run.py','evaluate.mjs','telemetry.py','test_telemetry.py','collect.py','prices.json']:
 shutil.copy2(source/name,work/name)
protocol['recorded_evaluator_sha256']=protocol['evaluator_sha256']
protocol['evaluator_sha256']=hashlib.sha256((work/'evaluate.mjs').read_bytes()).hexdigest()
(work/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
for condition in ['single','swarm']:
 site=work/'runs'/condition/'site';shutil.copytree(work/'fixture',site)
 for command in [['git','init','--quiet'],['git','add','.'],['git','-c','user.name=Benchmark fixture','-c','user.email=benchmark@example.invalid','commit','--quiet','-m','Frozen benchmark fixture']]:
  subprocess.run(command,cwd=site,check=True)
print(work)
