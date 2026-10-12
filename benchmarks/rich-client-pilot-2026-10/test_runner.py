import unittest,importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('runner',Path(__file__).parent/'run.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Runner(unittest.TestCase):
 def test_equal_controls_and_distinct_delegation(self):
  protocol={'root_model':'discovered-test-model','root_reasoning_effort':'high','swarm_active_helpers_cap':2,'shared_budget_seconds':2100}
  solo,sp=m.command_and_prompt('single',protocol,Path('/test/site'));team,tp=m.command_and_prompt('swarm',protocol,Path('/test/site'))
  for cmd in [solo,team]:
   self.assertIn('workspace-write',cmd);self.assertNotIn('danger-full-access',cmd);self.assertIn('agents.max_concurrent_threads_per_session=2',cmd)
  self.assertIn('agents.enabled=false',solo);self.assertIn('agents.enabled=true',team)
  self.assertIn('no subagents',sp);self.assertIn('lower-cost owners',tp);self.assertIn('retries',sp);self.assertIn('retries',tp);self.assertIn('qa_check.py',sp);self.assertIn('qa_check.py',tp)

class ProcessGroupLifecycle(unittest.TestCase):
 def test_exited_root_does_not_leave_sigterm_ignoring_child(self):
  import subprocess,sys,tempfile,time,os,signal
  with tempfile.TemporaryDirectory() as d:
   pidfile=Path(d)/'child.pid';ready=Path(d)/'ready'
   child='import signal,time;from pathlib import Path;signal.signal(signal.SIGTERM,signal.SIG_IGN);Path('+repr(str(ready))+').write_text("ready");time.sleep(60)'
   parent='import subprocess,sys,time;from pathlib import Path;p=subprocess.Popen([sys.executable,"-c",'+repr(child)+']);Path('+repr(str(pidfile))+').write_text(str(p.pid));\nwhile not Path('+repr(str(ready))+').exists():time.sleep(.01)'
   proc=subprocess.Popen([sys.executable,'-c',parent],start_new_session=True)
   childpid=None
   try:
    proc.wait(timeout=5);childpid=int(pidfile.read_text());os.kill(childpid,0)
    m.terminate_group(proc,grace=.15)
    deadline=time.monotonic()+3
    while time.monotonic()<deadline:
     try:os.kill(childpid,0)
     except ProcessLookupError:break
     # Linux may retain a killed orphan briefly as a zombie; no active work remains.
     state=Path('/proc')/str(childpid)/'stat'
     if state.exists() and state.read_text().split()[2]=='Z':break
     time.sleep(.05)
    else:self.fail('SIGTERM-ignoring descendant survived group cleanup')
   finally:
    try:os.killpg(proc.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    proc.wait(timeout=3)
 def test_gone_group_cleanup_is_idempotent(self):
  import subprocess,sys
  proc=subprocess.Popen([sys.executable,'-c','pass'],start_new_session=True);proc.wait(timeout=3)
  m.terminate_group(proc,grace=.01);m.terminate_group(proc,grace=.01)

class RuntimeDelivery(unittest.TestCase):
 def test_runtime_mapping_reaches_solver_and_completed_attempt_cannot_rerun(self):
  import tempfile,sys,os,json,contextlib,io
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'preview').mkdir();site=root/'runs/single/site';site.mkdir(parents=True)
   (root/'preview/broker.py').write_text('import json,time;print(json.dumps({"ready":True}),flush=True);time.sleep(60)')
   (site/'preview_client.py').write_text('import json;print(json.dumps({"ready":True}))')
   (root/'protocol.json').write_text(json.dumps({'shared_budget_seconds':10}))
   oldroot,oldcommand=m.ROOT,m.command_and_prompt;oldenv=os.environ.get('PREVIEW_NODE')
   m.ROOT=root;m.command_and_prompt=lambda *args:([sys.executable,'-c','import os;print(os.environ.get("BENCHMARK_NODE","MISSING"))'],'stub local command')
   os.environ['PREVIEW_NODE']=sys.executable
   try:
    with contextlib.redirect_stdout(io.StringIO()):m.run('single')
    self.assertEqual((site.parent/'events.jsonl').read_text().strip(),sys.executable)
    meta=json.loads((site.parent/'metadata.json').read_text());self.assertEqual(meta['exit_code'],0);self.assertTrue(meta['preview_ready_before_timer']);self.assertFalse(meta['timed_out'])
    with self.assertRaises(SystemExit):m.run('single')
   finally:
    m.ROOT=oldroot;m.command_and_prompt=oldcommand
    if oldenv is None:os.environ.pop('PREVIEW_NODE',None)
    else:os.environ['PREVIEW_NODE']=oldenv
