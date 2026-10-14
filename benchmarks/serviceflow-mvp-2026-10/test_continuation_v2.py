"""Owned fake recovery scenarios. No real broker/native session/model is called."""
import copy,hashlib,importlib.util,io,json,os,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
R=Path(__file__).resolve().parent
os.environ['SERVICEFLOW_BENCHMARK_ROOT']=str(R)
spec=importlib.util.spec_from_file_location('continuation_v2',str(R/'continue-v2.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
from test_completion_runner import verdict,counter,snapshot,phase,BUILDER,AUDITOR
from phase_collect import source_hashes
P=json.loads((R/'protocol.json').read_text())
class FakeBroker:
 def __init__(self,*a,**k):self.stdout=io.StringIO('{"ready":true}\n')
class Clock:
 def __init__(self):self.w=200.;self.m=20.
 def time(self):self.w+=1;return self.w
 def monotonic(self):self.m+=1;return self.m
class Recovery(unittest.TestCase):
 condition="adaptive"
 def fixture(self,root,followed=False):
  directory=root/'runs'/self.condition;site=directory/'site';site.mkdir(parents=True)
  for name in ['app.ts','src/secrets.ts','data/catalogue.json','data/serviceflow.sqlite.secret','data/.auth-secret']:
   f=site/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('private sentinel' if name.endswith(('.secret','.auth-secret')) else 'product')
  (root/'protocol.json').write_text(json.dumps(P));(root/'AUDIT_PROMPT.txt').write_bytes((R/'AUDIT_PROMPT.txt').read_bytes())
  phases=[phase(1,'builder',BUILDER,snapshot(BUILDER,counter())),phase(2,'auditor',AUDITOR,snapshot(AUDITOR,counter()))]
  phases[0].update(end_unix=120,elapsed_seconds=15)
  if followed:phases.append(phase(3,'builder',BUILDER,snapshot(BUILDER,counter()),snapshot(BUILDER,counter())))
  final=source_hashes(site);final.update({'data/serviceflow.sqlite.secret':'private hash only','data/.auth-secret':'old hash only'})
  meta=dict(state='INCOMPLETE',start_unix=100,end_unix=150,elapsed_seconds=50,active_controller_elapsed_seconds=40,
            protocol_sha256='original-protocol',updated_protocol_sha256='amendment1-protocol',
            builder_root=BUILDER,phases=phases,final_source_sha256=final,source_snapshots=[],auditor_roots=[AUDITOR],
            controller_continuation={'version':1,'orchestration_gap_seconds':8,'prior_metadata_sha256':'prior'})
  (directory/'metadata-before-controller-continuation.json').write_text('v1 archive preserved')
  (directory/'metadata.json').write_text(json.dumps(meta))
  old=directory/'phases/02-auditor';old.mkdir(parents=True)
  v=verdict();v['scope']['acceptance_criteria']='truncated';v['verdict']='FAIL'
  v['findings']=[dict(id='AUD-001',severity='high',title='privacy finding',file='app.ts',line=1,evidence='owned fake reproduction',required_action='fix')]
  raw=json.dumps(v).encode();(old/'final.txt').write_bytes(raw)
  return directory,site,meta,raw
 def execute(self,root,statuses=('PASS',),gate_ok=True,malformed=False):
  calls=[];iterator=iter(statuses);clock=Clock();gate_calls=[]
  original_read=Path.read_bytes
  def no_credential_read(path):
   if path.name=='.auth-secret' or path.name.lower().endswith('.secret'):
    raise AssertionError('Controller attempted credential byte read')
   return original_read(path)
  def gates(*args,**kwargs):
   gate_calls.append(1);ok=gate_ok if isinstance(gate_ok,bool) else gate_ok[min(len(gate_calls)-1,len(gate_ok)-1)]
   return dict(accepted=ok,reports=[],tool_incomplete=False)
  def execute(condition,site,directory,protocol,meta,deadline,prompt,*,role,number,resume=None,env=None):
   self.assertIsNone(deadline);calls.append((role,resume,prompt.decode()))
   if role=='builder':self.assertEqual(resume,BUILDER);root_id=BUILDER
   else:self.assertIsNone(resume);root_id=f'{number:08d}-4444-4444-4444-444444444444'
   p=phase(number,role,root_id,snapshot(root_id,counter()),snapshot(root_id,counter()) if resume else None);meta['phases'].append(p)
   if role=='auditor':
    self.assertIn('fresh complete ServiceFlow audit',prompt.decode());self.assertIn('Read complete unchanged ACCEPTANCE.md',prompt.decode())
    self.assertIn(P['audit_acceptance_criteria'],prompt.decode())
    target=directory/'phases'/('%02d-auditor'%number);target.mkdir(parents=True)
    value=verdict();value['scope'].update(base=P['audit_scope_base'],acceptance_criteria='truncated' if malformed else P['audit_acceptance_criteria'],changed_files=list(source_hashes(site)))
    value['checks']=[dict(command=cmd,status='pass',exit_code=0,evidence='owned fake') for cmd in P['audit_required_commands']]
    value['verdict']=next(iterator)
    if value['verdict']=='FAIL':value['findings']=[dict(id='AUD-001',severity='high',title='failed case',file='app.ts',line=1,evidence='fake failure',required_action='repair')]
    (target/'final.txt').write_text(json.dumps(value))
   return p,None
  with patch.object(Path,'read_bytes',no_credential_read),patch.object(c,'ROOT',root),patch.object(c,'time',clock),patch.object(c.run,'verify_freeze',lambda *a,**k:None),patch.object(c.run,'execute_phase',execute),patch.object(c.run,'cleanup_bound_backend',lambda *a:[]),patch.object(c.run,'fixed_gates',gates),patch.object(c.run,'terminate_group',lambda *a:None),patch.object(c.subprocess,'Popen',FakeBroker),patch.object(c.select,'select',lambda *a:([1],[],[])),patch.object(c.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=0,stdout=json.dumps({'changed_files':['app.ts','src/secrets.ts','data/catalogue.json']}))):
   if malformed:
    with self.assertRaisesRegex(RuntimeError,'canonical report invalid'):c.continuation(self.condition)
    return json.loads((root/'runs'/self.condition/'metadata.json').read_text()),calls
   return c.continuation(self.condition),calls
 def test_single_previous_repair_skips_original_supplemental(self):
  self.condition="single"
  with tempfile.TemporaryDirectory() as d:
   root=Path(d).resolve();directory,site,old,raw=self.fixture(root,followed=True);out,calls=self.execute(root)
   self.assertEqual([x[0] for x in calls],['auditor']);self.assertEqual(out['phases'][1]['supplemental_delivery']['state'],'already_followed_by_builder')
   self.assertEqual((directory/'phases/02-auditor/final.txt').read_bytes(),raw)
 def test_adaptive_first_findings_exact_resume_eight_fails_then_pass(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d).resolve();directory,site,old,raw=self.fixture(root);out,calls=self.execute(root,('FAIL',)*8+('PASS',))
   self.assertEqual(out['state'],'PASS');self.assertEqual(calls[0][:2],('builder',BUILDER));self.assertEqual(sum(x[0]=='auditor' for x in calls),9)
   self.assertEqual(sum(x[0]=='builder' for x in calls),9);self.assertEqual(out['phases'][1]['supplemental_delivery']['state'],'delivered')
   self.assertEqual(out['phases'][0],old['phases'][0]);self.assertEqual(out['builder_root'],BUILDER)
   self.assertEqual((directory/'phases/02-auditor/final.txt').read_bytes(),raw)
   self.assertEqual(out['accepted_source_sha256'],source_hashes(site));self.assertNotIn('private sentinel',json.dumps(out))
 def test_repeat_recovery_archives_unique_and_active_time_no_gap_double_count(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d).resolve();directory,site,old,raw=self.fixture(root)
   first,calls=self.execute(root,('BLOCKED',));first_bytes=(directory/'metadata.json').read_bytes();first_snapshot=first['final_source_snapshot_path']
   second,calls2=self.execute(root,('PASS',))
   self.assertEqual(second['state'],'PASS');self.assertEqual(calls2[0][0],'auditor')
   self.assertEqual((directory/'metadata-before-controller-continuation-v2-001.json').read_text(),json.dumps(old))
   self.assertEqual((directory/'metadata-before-controller-continuation-v2-002.json').read_bytes(),first_bytes)
   self.assertEqual((directory/'metadata-before-controller-continuation.json').read_text(),'v1 archive preserved')
   self.assertNotEqual(first_snapshot,second['final_source_snapshot_path']);self.assertTrue((directory/first_snapshot).exists())
   history=second['controller_continuations'];self.assertEqual(len(history),3)
   self.assertEqual(history[1]['orchestration_gap_seconds'],51)
   self.assertEqual(second['active_controller_elapsed_seconds'],40+sum(s['monotonic_seconds'] for s in history if s.get('version')==2))
   self.assertEqual(second['elapsed_seconds'],second['end_unix']-100)
   self.assertEqual(history[1]['prior_protocol_sha256'],'amendment1-protocol')
   self.assertEqual(history[2]['prior_protocol_sha256'],history[1]['protocol_sha256'])
 def test_invalid_new_report_retained_and_next_recovery_repairs_once(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d).resolve();directory,site,old,raw=self.fixture(root,followed=True)
   invalid,calls=self.execute(root,malformed=True);last=invalid['phases'][-1]
   self.assertEqual(invalid['state'],'INCOMPLETE');self.assertEqual(last['canonical_state'],'invalid_scope_metadata');self.assertNotIn('verdict',last)
   q=directory/'phases'/('%02d-auditor'%last['number'])/'final.txt';saved=q.read_bytes()
   result,calls=self.execute(root);self.assertEqual(result['state'],'PASS');self.assertEqual(q.read_bytes(),saved)
 def test_inactive_guards_and_real_source_mismatch_before_archives(self):
  for mode in ['active','incomplete','source']:
   with self.subTest(mode=mode),tempfile.TemporaryDirectory() as d:
    root=Path(d).resolve();directory,site,old,raw=self.fixture(root)
    if mode=='active':old['end_unix']=None
    if mode=='incomplete':old['phases'][-1]['state']='running'
    if mode=='source':old['final_source_sha256']['src/secrets.ts']='wrong'
    (directory/'metadata.json').write_text(json.dumps(old))
    with patch.object(c,'ROOT',root),patch.object(c.run,'verify_freeze',lambda *a,**k:None):
     with self.assertRaises(RuntimeError):c.continuation(self.condition)
    self.assertFalse(list(directory.glob('*v2-*.json')))
 def test_structural_gate_rejects_pass_and_fresh_audit_follows_repair(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d).resolve();self.fixture(root,followed=True);out,calls=self.execute(root,('PASS','PASS'),gate_ok=[False,True])
   self.assertEqual(out['state'],'PASS');self.assertEqual([x[0] for x in calls],['auditor','builder','auditor'])
 def test_entry_requires_independent_exact_controller_sha(self):
  with tempfile.TemporaryDirectory() as d:
   proof=Path(d)/'proof.json'
   for value in [{'verdict':'PASS'},{'verdict':'FAIL','controller_sha256':'anything'},{'verdict':'PASS','controller_sha256':'wrong'}]:
    proof.write_text(json.dumps(value))
    with patch.dict(os.environ,{'SERVICEFLOW_AMENDMENT2_AUDIT':str(proof)}):
     with self.assertRaises(RuntimeError):c.independent_gate()
   proof.write_text(json.dumps({'verdict':'PASS','controller_sha256':hashlib.sha256(Path(c.__file__).read_bytes()).hexdigest()}))
   with patch.dict(os.environ,{'SERVICEFLOW_AMENDMENT2_AUDIT':str(proof)}):c.independent_gate()
if __name__=='__main__':unittest.main()
