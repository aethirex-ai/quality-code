"""Seal instrument and common corpus before either paid condition starts."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def freeze():
 p=ROOT/'protocol.json';v=json.loads(p.read_text())
 if (ROOT/'runs/single/metadata.json').exists():raise RuntimeError('Cannot reseal after fresh control starts')
 carried=(ROOT/'runs/adaptive/metadata.json').exists()
 if carried:
  original=ROOT/'protocol-original.json'
  amendment=v.get('condition_isolation_amendment',{})
  if not original.is_file()or amendment.get('original_protocol_sha256')!=hashlib.sha256(original.read_bytes()).hexdigest():raise RuntimeError('Carried adaptive requires pinned original protocol and explicit isolation amendment')
  metadata=json.loads((ROOT/'runs/adaptive/metadata.json').read_text())
  if metadata.get('protocol_sha256')!=amendment['original_protocol_sha256']or metadata.get('exit_code')!=0 or 'end_unix'not in metadata:raise RuntimeError('Adaptive original completion/protocol mismatch')
  if not (ROOT/'runs/adaptive/frozen-output-hashes.json').is_file():raise RuntimeError('Missing original adaptive freeze')
  from collect import freeze_evidence
  freeze_evidence(ROOT/'runs/adaptive',ROOT/'runs/adaptive/site')

 paths=[ROOT/n for n in ('run.py','prepare.py','freeze.py','collect.py','telemetry.py','prices.json','native-model-catalog.json','discover_models.py','APP_PROMPT.txt','BRIEF.md','BUDGET.md','qa_check.py','verify_app.py','.quality/quality.toml','MAP.md','TESTING.md','.gitignore','test_runner.py','test_collect.py','test_telemetry.py','test_qa_check.py')]
 for folder in ('preview','judge/backend','judge/frontend'):
  paths.extend(x for x in (ROOT/folder).rglob('*')if x.is_file()and x.suffix in ('.py','.mjs','.html')and '__pycache__'not in x.parts)
 v['frozen_sources_sha256']={str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest()for x in sorted(set(paths))}
 v['runner_sha256']=v['frozen_sources_sha256']['run.py']
 v['fixture_sha256']={str(x.relative_to(ROOT/'fixture')):hashlib.sha256(x.read_bytes()).hexdigest()for x in sorted((ROOT/'fixture').rglob('*'))if x.is_file()and '.git'not in x.parts and '__pycache__'not in x.parts}
 p.write_text(json.dumps(v,indent=2)+'\n')
 from run import verify_freeze
 for c in (('single',)if carried else ('single','adaptive')):verify_freeze(v,ROOT/'runs'/c/'site')
 print(json.dumps({'sources':len(v['frozen_sources_sha256']),'fixture_files':len(v['fixture_sha256']),'protocol_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))
if __name__=='__main__':freeze()
