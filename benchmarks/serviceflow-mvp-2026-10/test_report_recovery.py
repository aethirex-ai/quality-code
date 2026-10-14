"""Owned synthetic report correction checks; no native/model or live data calls."""
import copy,hashlib,importlib.util,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
MODULES=Path(__file__).resolve().parent
os.environ['SERVICEFLOW_BENCHMARK_ROOT']=str(MODULES);sys.path.insert(0,str(MODULES))
spec=importlib.util.spec_from_file_location('recovery',str(MODULES/'report_recovery.py'));c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
from test_completion_runner import phase,snapshot,counter,verdict,BUILDER,AUDITOR,OTHER
class Clock:
 def __init__(self):self.w=200.;self.m=10.
 def time(self):self.w+=1;return self.w
 def monotonic(self):self.m+=1;return self.m
class Recovery(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve()
  self.directory=self.root/'runs/adaptive';self.site=self.directory/'site';self.site.mkdir(parents=True);(self.site/'app.ts').write_text('owned product')
  self.current=c.phase_collect.source_hashes(self.site)
  self.p=json.loads((MODULES/'protocol.json').read_text());self.p.update(native_cli='/owned/fake/codex',sessions_dir='owned-sessions')
  (self.root/'protocol.json').write_text(json.dumps(self.p))
  self.before=snapshot(AUDITOR,counter(),digest='before',size=100);self.before['actual_models']=[self.p['root_model']]
  self.after=snapshot(AUDITOR,counter(15,3,6),digest='after',size=120);self.after['actual_models']=[self.p['root_model']]
  first=phase(1,'builder',BUILDER,snapshot(BUILDER,counter()));audit=phase(8,'auditor',AUDITOR,self.before)
  audit.update(canonical_state='invalid_scope_metadata',canonical_error='historical exit130 cleanup status contradiction')
  self.meta=dict(state='INCOMPLETE',start_unix=100,end_unix=150,elapsed_seconds=50,active_controller_elapsed_seconds=40,builder_root=BUILDER,auditor_roots=[AUDITOR],phases=[first,audit],final_source_sha256=self.current,source_snapshots=[{'round':1,'sources_sha256':self.current}],fixed_gates=[{'accepted':True,'tool_incomplete':False}])
  snap=self.directory/'snapshots/final';self.meta['final_source_snapshot']=c.run.freeze_source_bytes(self.site,snap,self.current);self.meta['final_source_snapshot_path']='snapshots/final'
  (self.directory/'audit-01-source-hashes.json').write_text(json.dumps(self.current));(self.directory/'audit-01-packet.json').write_text(json.dumps({'changed_files':list(self.current)}))
  self.raw=verdict();self.raw['scope'].update(acceptance_criteria=self.p['audit_acceptance_criteria'],changed_files=list(self.current));self.raw['checks']=[dict(command=cmd,status='pass',exit_code=0,evidence='owned asserted checks')for cmd in self.p['audit_required_commands']]
  self.raw['checks'].append(dict(command=['npm','run','benchmark:start'],status='pass',exit_code=130,evidence='Deliberate Ctrl-C cleanup after browser assertions'))
  self.phase_dir=self.directory/'phases/08-auditor';self.phase_dir.mkdir(parents=True)
  for n,val in [('final.txt',self.raw),('metadata.json',audit),('events.jsonl',{'retained':'original events'})]:(self.phase_dir/n).write_text(json.dumps(val))
  self.original={n:(self.phase_dir/n).read_bytes() for n in ['final.txt','metadata.json','events.jsonl']}
  self.save();self.original_meta=(self.directory/'metadata.json').read_bytes()
 def save(self):(self.directory/'metadata.json').write_text(json.dumps(self.meta))
 def invoke(self,status='PASS',exit_code=0,root=AUDITOR,usage='delta',mutate=None,raises=False,missing_required=False,startup=False):
  owner=self;commands=[]
  class Fake:
   def __init__(self,args,**kw):self.args=args;self.kw=kw;self.returncode=exit_code;commands.append(args)
   def communicate(self,input):
    owner.assertIn(b'never invent exit0',input);owner.assertIn(b'SAME original independent auditor',input)
    if raises:raise OSError('owned process transport failure')
    if startup:
     self.kw['stderr'].write((c.STARTUP_ERROR+'\n').encode());self.kw['stderr'].flush();return
    cli={k:owner.after['cumulative_usage'][k]-owner.before['cumulative_usage'][k] for k in c.phase_collect.FIELDS}
    if usage=='cumulative':cli=owner.after['cumulative_usage']
    if usage=='mismatch':cli=dict(cli,input_tokens=999)
    if usage=='missing':cli=None
    self.kw['stdout'].write((json.dumps({'type':'thread.started','thread_id':root})+'\n'+json.dumps({'type':'turn.completed','usage':cli})+'\n').encode());self.kw['stdout'].flush()
    report=copy.deepcopy(owner.raw);report['checks']=report['checks'][:-1];report['verdict']=status
    if missing_required:report['checks']=report['checks'][:1]
    if status=='FAIL':report['findings']=[dict(id='AUD-001',severity='high',title='required evidence failed',file='app.ts',line=1,evidence='owned reproducible failure',required_action='repair')]
    if status=='BLOCKED':report['untested']=['required evidence uncertain']
    out=Path(self.args[self.args.index('-o')+1]);out.write_text(json.dumps(report))
    if mutate=='source':(owner.site/'app.ts').write_text('auditor source mutation')
    if mutate=='original':(owner.phase_dir/'final.txt').write_text('changed immutable original')
  snapshots=iter([self.before,self.after])
  with patch.object(c,'ROOT',self.root),patch.object(c,'time',Clock()),patch.object(c.run,'verify_freeze',lambda *a,**k:None),patch.object(c.run,'root_snapshot',lambda *a:next(snapshots)),patch.object(c.run,'terminate_group',lambda *a:None),patch.object(c.subprocess,'Popen',Fake):
   if exit_code or root!=AUDITOR or usage in ('mismatch','missing') or mutate or raises or missing_required:
    with self.assertRaises(Exception):c.recover()
    result=json.loads((self.directory/'metadata.json').read_text())
   else:result=c.recover()
  return result,commands
 def assert_immutable(self):
  for name,value in self.original.items():self.assertEqual((self.phase_dir/name).read_bytes(),value)
  self.assertEqual((self.phase_dir/'format-001/metadata-before.json').read_bytes(),self.original_meta)
 def test_01_success_exact_root_counter_conservation_immutable_accounting(self):
  result,args=self.invoke();self.assertEqual(result['state'],'PASS');self.assert_immutable();audit=result['phases'][-1]
  self.assertEqual(len(result['phases']),2);self.assertEqual(audit['cli_usage'],self.after['cumulative_usage']);self.assertIsNone(audit['native_before']);self.assertEqual(audit['canonical_state'],'validated_after_format_correction');self.assertNotIn('canonical_error',audit)
  roots,rows,flags=c.phase_collect.reconcile_phases(result['phases']);self.assertFalse(flags);self.assertEqual(roots[AUDITOR]['cumulative_usage'],self.after['cumulative_usage'])
  correction=audit['formatting_corrections'][0];self.assertEqual(correction['verified_native_delta']['input_tokens'],5)
  self.assertEqual(result['active_controller_elapsed_seconds'],41);self.assertEqual(correction['orchestration_gap_seconds'],51);self.assertEqual(result['elapsed_seconds'],result['end_unix']-100);self.assertEqual(audit['elapsed_seconds'],2)
  with patch.object(c,'ROOT',self.root):
   with self.assertRaisesRegex(RuntimeError,'already accepted'):c.preflight()
  cmd=args[0];self.assertEqual(cmd[cmd.index('exec')+1:cmd.index('exec')+3],['resume',AUDITOR]);self.assertIn('agents.enabled=false',cmd);self.assertIn('read-only',cmd);self.assertIn('--output-schema',cmd);self.assertIn(self.p['root_model'],cmd);self.assertFalse(any(a.startswith(('permissions.','default_permissions=')) for a in cmd))
 def test_02_corrected_fail_preserved(self):
  result,_=self.invoke(status='FAIL');self.assertEqual(result['state'],'FAIL');self.assertEqual(result['phases'][-1]['verdict'],'FAIL');self.assert_immutable()
 def test_03_corrected_blocked_preserved(self):
  result,_=self.invoke(status='BLOCKED');self.assertEqual(result['state'],'BLOCKED');self.assert_immutable()
 def reject(self,pattern):
  self.save()
  with patch.object(c,'ROOT',self.root),patch.object(c.run,'verify_freeze',lambda *a,**k:None),patch.object(c.run,'root_snapshot',return_value=self.before),patch.object(c.subprocess,'Popen',side_effect=AssertionError('native call forbidden')):
   with self.assertRaisesRegex(RuntimeError,pattern):c.recover()
  self.assertFalse(list(self.phase_dir.glob('format-*')))
 def test_04_changed_source_preflight_rejected(self):
  (self.site/'app.ts').write_text('different');self.reject('source mismatch')
 def test_05_auditor_source_change_fails_and_retains_usage(self):
  result,_=self.invoke(mutate='source');self.assertEqual(result['state'],'INCOMPLETE');self.assertEqual(result['phases'][-1]['native_after'],self.after)
 def test_06_wrong_root_retained_no_complete_totals(self):
  result,_=self.invoke(root=OTHER);p=result['phases'][-1];self.assertEqual(p['formatting_corrections'][0]['observed_root'],OTHER);self.assertIsNone(p['cli_usage']);self.assertFalse(result['report_recovery_accounting_complete'])
 def test_07_proof_wrong_hash_rejected(self):
  proof=self.root/'proof.json';proof.write_text(json.dumps({'verdict':'PASS','controller_sha256':'bad'}))
  with patch.dict(os.environ,{'SERVICEFLOW_REPORT_RECOVERY_AUDIT':str(proof)}):
   with self.assertRaises(RuntimeError):c.gate()
 def test_08_proof_exact_controller_pass(self):
  proof=self.root/'proof.json';proof.write_text(json.dumps({'verdict':'PASS','controller_sha256':hashlib.sha256(Path(c.__file__).read_bytes()).hexdigest()}))
  with patch.dict(os.environ,{'SERVICEFLOW_REPORT_RECOVERY_AUDIT':str(proof)}):c.gate()
 def test_09_active_condition_rejected(self):self.meta['end_unix']=None;self.reject('complete')
 def test_10_builder_auditor_collision_rejected(self):self.meta['builder_root']=AUDITOR;self.reject('independence')
 def test_11_original_resumed_auditor_rejected(self):self.meta['phases'][-1]['resume_root']=AUDITOR;self.reject('original fresh')
 def test_12_wrong_original_model_rejected(self):self.meta['phases'][-1]['native_after']['actual_models']=['other'];self.reject('Matched model')
 def test_13_cli_counter_mismatch_preserves_unknown(self):
  result,_=self.invoke(usage='mismatch');self.assertIsNone(result['phases'][-1]['cli_usage']);self.assertEqual(result['phases'][-1]['native_after'],self.after)
 def test_14_nonzero_process_preserves_verified_usage_but_not_acceptance(self):
  result,_=self.invoke(exit_code=1);self.assertEqual(result['state'],'INCOMPLETE');self.assertEqual(result['phases'][-1]['cli_usage'],self.after['cumulative_usage']);self.assertTrue(result['phases'][-1]['formatting_corrections'][0]['counters_verified'])
 def test_15_missing_cli_usage_withholds_complete_accounting(self):
  result,_=self.invoke(usage='missing');self.assertEqual(result['state'],'INCOMPLETE');self.assertIsNone(result['phases'][-1]['cli_usage'])
 def test_16_cumulative_cli_basis_accepted_without_double_count(self):
  result,_=self.invoke(usage='cumulative');self.assertEqual(result['state'],'PASS');self.assertEqual(result['phases'][-1]['formatting_corrections'][0]['cli_counter_basis'],'root_cumulative')
 def test_17_tampered_final_snapshot_rejected(self):
  (self.directory/'snapshots/final/sources/app.ts').write_text('tampered');self.reject('snapshot source mismatch')
 def test_18_missing_required_profile_not_accepted(self):
  result,_=self.invoke(missing_required=True);self.assertEqual(result['state'],'INCOMPLETE');self.assertNotIn('verdict',result['phases'][-1])
 def test_19_original_evidence_mutation_rejected(self):
  result,_=self.invoke(mutate='original');self.assertEqual(result['state'],'INCOMPLETE');self.assertIn('evidence changed',result['runner_error'])
 def test_20_transport_failure_preserves_native_after_and_invalidates(self):
  result,_=self.invoke(raises=True);self.assertEqual(result['state'],'INCOMPLETE');self.assertEqual(result['phases'][-1]['native_after'],self.after);self.assertIsNone(result['phases'][-1]['cli_usage']);self.assert_immutable()

 def startup_failure(self):
  grown=self.after;self.after=copy.deepcopy(self.before)
  result,_=self.invoke(exit_code=1,startup=True)
  self.after=grown
  self.assertEqual(result['phases'][-1]['state'],'invalid')
  return result
 def test_21_exact_startup_retry_retains_archive_timing_and_corrected_state(self):
  failed=self.startup_failure();archive=(self.phase_dir/'format-001/metadata.json').read_bytes();old_meta=(self.directory/'metadata.json').read_bytes()
  result,_=self.invoke();audit=result['phases'][-1]
  self.assertEqual(result['state'],'PASS');self.assertEqual(audit['canonical_state'],'validated_after_format_correction');self.assertNotIn('canonical_error',audit)
  self.assertEqual(len(audit['formatting_corrections']),2);self.assertEqual(len(result['report_recovery_segments']),2)
  self.assertEqual(result['active_controller_elapsed_seconds'],42);self.assertEqual(audit['elapsed_seconds'],3)
  self.assertEqual((self.phase_dir/'format-001/metadata.json').read_bytes(),archive)
  self.assertEqual((self.phase_dir/'format-002/metadata-before.json').read_bytes(),old_meta)
  self.assertTrue(result['report_retry_restore']['failed_elapsed_retained']);self.assertEqual(audit['cli_usage'],self.after['cumulative_usage'])
  self.assertIn('canonical_error',audit['formatting_corrections'][-1]['prior_canonical_metadata'])
  roots,_,flags=c.phase_collect.reconcile_phases(result['phases']);self.assertFalse(flags);self.assertEqual(roots[AUDITOR],self.after)
 def reject_retry(self,pattern):
  before=(self.directory/'metadata.json').read_bytes()
  with patch.object(c,'ROOT',self.root),patch.object(c.run,'verify_freeze',lambda *a,**k:None),patch.object(c.subprocess,'Popen',side_effect=AssertionError('native forbidden')):
   with self.assertRaisesRegex(RuntimeError,pattern):c.recover()
  self.assertEqual((self.directory/'metadata.json').read_bytes(),before);self.assertFalse((self.phase_dir/'format-002').exists())
 def test_22_retry_nonempty_events_rejected(self):
  self.startup_failure();(self.phase_dir/'format-001/events.jsonl').write_text('{}');self.reject_retry('empty events')
 def test_23_retry_other_startup_error_rejected(self):
  self.startup_failure();(self.phase_dir/'format-001/stderr.log').write_text('other failure');self.reject_retry('known startup')
 def test_24_retry_native_growth_rejected(self):
  result=self.startup_failure();result['phases'][-1]['native_after']=self.after
  (self.directory/'metadata.json').write_text(json.dumps(result));self.reject_retry('grew or changed')
 def test_25_retry_original_phase_archive_tamper_rejected(self):
  self.startup_failure();(self.phase_dir/'format-001/original-phase.json').write_text('{}');self.reject_retry('Archived original phase changed')
 def test_26_retry_failed_record_tamper_rejected(self):
  self.startup_failure();(self.phase_dir/'format-001/metadata.json').write_text('{}');self.reject_retry('metadata/exit mismatch')
 def test_27_retry_source_change_rejected(self):
  self.startup_failure();(self.site/'app.ts').write_text('changed');self.reject_retry('source mismatch')

if __name__=='__main__':unittest.main()
