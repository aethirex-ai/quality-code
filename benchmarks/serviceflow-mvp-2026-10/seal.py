"""Prepare identical isolated ServiceFlow corpora; no native model calls."""
from pathlib import Path
import hashlib,json,shutil,socket,subprocess
ROOT=Path(__file__).resolve().parent

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def port():
 with socket.socket()as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def seal():
 if any((ROOT/'runs'/c/'metadata.json').exists()for c in ['single','adaptive']):raise RuntimeError('Refuse resealing started trial')
 f=ROOT/'fixture'
 for name in ['APP_PROMPT.txt','AUDIT_PROMPT.txt','BRAND.md']:
  shutil.copy2(ROOT/name,f/name)
 shutil.copy2(ROOT/'ACCEPTANCE.md',f/'BRIEF.md')
 if not (f/'.git').exists():subprocess.run(['git','init'],cwd=f,check=True,capture_output=True)
 subprocess.run(['git','add','.'],cwd=f,check=True)
 subprocess.run(['git','-c','user.name=AethDesign','-c','user.email=aethdesign@gmail.com','commit','--allow-empty','-m','Freeze common ServiceFlow task corpus'],cwd=f,check=True,capture_output=True)
 initial={p.relative_to(f).as_posix():digest(p)for p in sorted(f.rglob('*'))if p.is_file()and '.git'not in p.relative_to(f).parts and '__pycache__'not in p.relative_to(f).parts}
 protected={n:h for n,h in initial.items()if n in ['APP_PROMPT.txt','AUDIT_PROMPT.txt','BRIEF.md','BRAND.md','BUDGET.md','RUNTIME.md','NATIVE_MODELS.json','MODEL_COSTS.json','AGENTS.md','CLAUDE.md','quality','qa_check.py','preview_client.py','.quality/quality.py','.quality/LICENSE','.quality/audit-result.schema.json']or n.startswith('brand/')}
 files=[p for p in ROOT.iterdir()if p.is_file()and p.suffix in ['.py','.md','.txt','.json']and p.name not in ['protocol.json']]
 files+=list((ROOT/'preview').glob('*.py'))+list((ROOT/'preview').glob('*.mjs'))+list((ROOT/'gate_support').glob('*.py'))+list((ROOT/'gate_support').glob('*.cjs'))
 frozen={p.relative_to(ROOT).as_posix():digest(p)for p in sorted(set(files))}
 p={'date':'2026-10-14','kind':'ServiceFlow full-stack MVP matched uncapped task-to-independent-acceptance pair','completion_mode':'uncapped','native_cli':'codex','sessions_dir':'<set SERVICEFLOW_SESSIONS_DIR>','root_model':'gpt-6.1-sol','root_reasoning_effort':'high','native_helper_cap':3,'root_selection':'Same matched root/auditor as preceding experiment; native refreshed catalog supports high; implementation helpers select supported fit. Generic policy has no model names.','shared_budget_seconds':None,'initial_builder_cap_seconds':None,'audit_phase_cap_seconds':None,'repair_phase_cap_seconds':None,'gate_reserve_seconds':None,'cleanup_reserve_seconds':30,'fixed_gate_cap_seconds':None,'max_audit_rounds':None,'order':['single','adaptive'],'ports':{'single':port(),'adaptive':port()},'prompt_sha256':digest(ROOT/'APP_PROMPT.txt'),'fixture_sha256':protected,'initial_fixture_sha256':initial,'frozen_sources_sha256':frozen,'required_frozen_sources':['run.py','phase_collect.py','collect.py','telemetry.py','qa_check.py','structural_gate.py','preview/broker.py','preview/render.mjs','APP_PROMPT.txt','AUDIT_PROMPT.txt','audit-output-schema.json','ACCEPTANCE.md'],'audit_product_scope':'all-source','audit_required_risk':'critical','audit_required_commands':[['./quality','verify','full'],['./quality','verify','release']],'required_critical_route':'auth-and-state','critical_implementation_paths':['src/auth/service.ts','app/api/requests/route.ts','package.json'],'initial_forbidden_paths':['package.json','src','app','public','server.ts'],'backend_command_markers':['node','next','tsx','vite','npm','bun'],'network_allow_domains':['127.0.0.1','localhost','registry.npmjs.org','binaries.prisma.sh','github.com','release-assets.githubusercontent.com','objects.githubusercontent.com'],'audit_scope_base':'HEAD','audit_acceptance_criteria':(ROOT/'ACCEPTANCE.md').read_text(),'gate_commands':[['python3','{root}/structural_gate.py','{site}','{out}']],'measurement_boundary':'Initial builder and descendants, parent structural checks, every fresh independent full-scope audit, exact-root repairs and cleanup included. Setup/preflight and final blind grading/publication separately reported, not free. No live AI calls. Native counters/subsets reconciled without double-counting; missing consumption unknown.','limitations':['Single exploratory pair, single first; no causal or subscription-saving inference.','Independent stack choices may affect comparison.','No elapsed or audit-round caps; native/account/transport/tool blockers remain observable.','Parent browser preview needed because native Chromium IPC is blocked.','Parent structural gate is not a functional score; complete fresh independent acceptance required.']}
 (ROOT/'protocol.json').write_text(json.dumps(p,indent=2)+'\n')
 for c in p['order']:
  site=ROOT/'runs'/c/'site'
  if site.exists():raise RuntimeError('Refuse existing condition directory')
  shutil.copytree(f,site)
 print(json.dumps({'prepared':p['order'],'corpus_files':len(initial),'protected_files':len(protected),'frozen_instruments':len(frozen),'ports':p['ports'],'completion_mode':p['completion_mode']}))
if __name__=='__main__':seal()
