"""Equal local fixtures; hidden evaluation never enters builder workspaces."""
from pathlib import Path
import json,subprocess,shutil,hashlib,socket,sys
ROOT=Path(__file__).resolve().parent
PROTECTED=['APP_PROMPT.txt','BRIEF.md','BUDGET.md','qa_check.py','verify_app.py','MODEL_COSTS.json','NATIVE_MODELS.json']
def free_port():
 with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def prepare():
 fixture=ROOT/'fixture'
 if fixture.exists():raise RuntimeError('Refusing overwrite of prepared fixture')
 fixture.mkdir();subprocess.run([str(Path.home()/'.local/bin/quality-code'),'init',str(fixture)],check=True,capture_output=True,text=True)
 for name in PROTECTED[:5]:shutil.copy2(ROOT/name,fixture/name)
 shutil.copy2(ROOT/'prices.json',fixture/'MODEL_COSTS.json');shutil.copy2(ROOT/'native-model-catalog.json',fixture/'NATIVE_MODELS.json');shutil.copy2(ROOT/'preview/client.py',fixture/'preview_client.py')
 (fixture/'tests').mkdir();(fixture/'evidence').mkdir()
 (fixture/'MAP.md').write_text('''# AethDesign Atelier map\n## Product boundary\nFictional local portal with realSQLite auth/state and dependency-free frontend. No liveclients/services. API/UI contracts BRIEF; exactsharedAPP_PROMPT/BUDGET immutable.\n## Ownership\nServer/backend owns auth, permissions, SQLite transactions andstate; public/ owns visualinteraction. Onecontinuous visualowner andintegrator; delegate onlyreadyworthwhilecoherent outcomes.\n## Contracts\nPublicJSON, seed IDs/cookie/projectstate andstableUIhooks BRIEF. Mutations/reload/restart andclientisolation mustbe observable; no emptytests falsepasses.\n## Verification\nBuilderfulltests/renderedchecks/auditpacket required; parentfreshindependentauth/stategates pending afterbothoutputsfreeze. No self-certification or externalrelease inbuilder.\n## Safety and privacy\nLoopbackonly syntheticapp; explicitnativeprofile+networkallowlist, no sandboxbypass/externalmodelCLI/oracleinspection/realcredentials. Preserve protected workload/instrument files.\n''')
 (fixture/'TESTING.md').write_text('''# Builder testing\nUse verify_app.py to run real unittest regressions; add tests/test*.py. Empty suite fails. Tailor actualchecks/profiles while preserving highauth/state lanes. Native browserblockedMachpermissions; usefixed-originpreview_client.py/RUNTIME. QArecord launchfailures/exits/phases andglobal evidence/issues history; actualobservableAPI/frontproduct rechecks. Fieldtestauthrole/isolation, revisions/decisions/conflicts/DBrestart andnavigation/reload/visualstates. Independentparentgates remainpending insidebuilder; create scoped auditpacket and reportpending. No externalhidden feedback or postfreeze repairs.\n''')
 toml=(fixture/'.quality/quality.toml').read_text().replace('["Contracts and state", "Security, privacy, and safety", "Change invariants"]','["Contracts", "Safety and privacy", "Verification"]');start=toml.index('[verify]');end=toml.index('[[areas]]',start);toml=toml[:start]+'''[verify]\nfast = [["python3", "verify_app.py"]]\nchanged = [["python3", "verify_app.py"]]\nfull = [["python3", "verify_app.py"], ["git", "diff", "--check"]]\nrelease = [["python3", "verify_app.py"], ["git", "diff", "--check"]]\n\n'''+toml[end:];toml+='''\n[[areas]]\nname = "auth-and-state"\npaths = ["server.py", "backend/**", "database.py", "auth.py"]\nrisk = "high"\nmap_sections = ["Contracts", "Safety and privacy", "Verification"]\ntests = ["tests/**"]\nrequired_profiles = ["full"]\n''';(fixture/'.quality/quality.toml').write_text(toml)
 runtime='''# Local runtime and generic preview

Python 3.14.7 with stdlib SQLite; Node: node. No dependency installation. The native profile retains workspace filesystem protection and permits only 127.0.0.1/localhost command network traffic through the active proxy. Do not bypass proxies or sandbox controls. Native Chromium is blocked by Mach IPC permissions; use the parent preview bridge.

The parent starts the browser/broker before your timer. You create and start the actual backend when ready. `PORTAL_PORT` supplies the assigned port; this server serves the preview:

```sh
python3 server.py --host 127.0.0.1 --port "$PORTAL_PORT" --db demo.sqlite3
```

Your own isolated tests may use port 0 and fresh databases. The preview uses the assigned port. It never starts or executes your backend/source.

```sh
python3 preview_client.py --workspace . --ready
python3 preview_client.py --workspace . --page / --viewport 375 --actions-file actions.json
```

The other supported width is 1440. Readiness confirms the browser/broker, not the backend. Inspect returned PNGs with native image/file tools, not just metadata. Action files are valid JSON, at most 8KiB/24 actions: click/fill/select/check/press/scroll/reload. CSS selector length <=200, value <=2000, keys Tab/Escape/Enter only. No arbitrary JavaScript, URL, port, root or output setting. Each request starts with a fresh cookie context; login and later actions in the same request share cookies. Backend state persists between requests. Page paths are safe absolute same-origin paths without query/fragment; navigate query URLs through actual controls. Login sequence: fill login-email, fill login-password, click login-submit.

Backend-unavailable results are readiness evidence, malformed requests are protocol errors, and rendered/interaction failures need product diagnosis. Do not automatically count them as website bugs. The bridge blocks other origins, downloads and WebSockets. Visible text excerpts are capped at 1500 characters; media stays in files. A preview has a 75-second client timeout. Use purposeful flows rather than duplicate inspections.

```sh
python3 qa_check.py --owner backend --check-id auth-regression --phase verification -- python3 -m unittest tests.test_auth
```

Owners are backend/frontend/integration; phases initial/verification/recheck. Optional --issue-id links a correction. Records live in OWNER/check-runs.jsonl. Append stable owner/id issue updates to evidence/issues.jsonl as BRIEF specifies. Missing command launch errors are exit 127; expected scaffold/negative cases are distinct from product defects.

Preserve protected APP_PROMPT, BRIEF, BUDGET, RUNTIME, MODEL_COSTS, NATIVE_MODELS, qa_check.py, preview_client.py and verify_app.py. Implement source/tests and tailor actual profiles without lowering auth/state risk or gates. Parent independent audit remains pending after frozen outputs; no external release inside this builder session.
''';(fixture/'RUNTIME.md').write_text(runtime)
 finish(fixture)

def finish(fixture):
 if any((ROOT/'runs'/c/'metadata.json').exists() for c in ['adaptive','single']):raise RuntimeError('Cannot prepare a started condition')
 for name in PROTECTED[:5]:
  if (fixture/name).read_bytes()!=(ROOT/name).read_bytes():raise RuntimeError('Partial fixture differs: '+name)
 ports={c:free_port() for c in ['adaptive','single']}
 while len(set(ports.values()))!=2:ports['single']=free_port()
 for c in ['adaptive','single']:
  target=ROOT/'runs'/c/'site';target.parent.mkdir(parents=True);shutil.copytree(fixture,target,ignore=shutil.ignore_patterns('.git','__pycache__'));subprocess.run(['git','init','-q',str(target)],check=True);subprocess.run(['git','-C',str(target),'add','.'],check=True);subprocess.run(['git','-C',str(target),'-c','user.name=AethDesign','-c','user.email=aethdesign@gmail.com','commit','-q','-m','Frozen matched portal fixture'],check=True)
 hashes={str(p.relative_to(fixture)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(fixture.rglob('*')) if p.is_file() and '.git'not in p.parts}
 proto={'date':'2026-10-13','standard_commit':'a28198460f0f0898f7faeb0558785de3389079af','kind':'one paired fullstack portal; sameprompt/corpus/native permissions/model/effort/budget, delegationcapabilitydifferenceonly','root_model':'gpt-6.1-sol','root_reasoning_effort':'high','root_selection':'native model/list confirms support/high effort; matched supportedrootusedinpreviouspairs, notuniversalstandard default','shared_budget_seconds':3000,'cleanup_reserve_seconds':30,'native_helper_cap':3,'order':['adaptive','single'],'ports':ports,'prompt_sha256':hashlib.sha256((ROOT/'APP_PROMPT.txt').read_bytes()).hexdigest(),'fixture_sha256':hashes,'scoring':{'backend_contract_groups':12,'frontend_behavior_groups':11,'screenshots_per_subject':12,'visual':'freshanonymousmulti-screen0–5halfstepreview','bugs_iterations':'freshreviewdistinctcauses/fixandtargetrecheck/duplicates/tooling/expectednegative/missing/finalreproductions'},'measurement_boundary':'nativeroot+explicitall-descendants, modelusage/elapsedincludingcoordination/tools/previewwait/builderchecks/fixes/packet; parentsetup/negativepreflight/evaluation/independentaudits/publication excluded; imagegenerationnone; no subscription conversion','limitations':['onepair, adaptivefirst','model/topology/implementationdiffer; no causal/generalqualityorperfectmatch claim','12API/11frontendgroups samplecontracts; visualreviewqualitativeonejudge','approve-success/conflictfrontendnotseparatefrozenbrowserprobes; additionaltargetedfinaldiagnosisoutsidecounts','nativeChromiumblocked; equalparentfixedoriginpreviewbrowser withnativebackendhosting','nativecapabilitiesalpha; sharedhost/provider/cache loaduncontrolled']}
 (ROOT/'protocol.json').write_text(json.dumps(proto,indent=2)+'\n');print(json.dumps({'fixture_files':len(hashes),'ports':ports,'prompt_sha256':proto['prompt_sha256']}))
if __name__=='__main__':
 if '--finish' in sys.argv:finish(ROOT/'fixture')
 else:prepare()
