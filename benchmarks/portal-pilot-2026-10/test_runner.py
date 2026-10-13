import unittest,json,sys,tempfile,subprocess,os,signal,time
from pathlib import Path
from unittest.mock import patch
import run
class Runner(unittest.TestCase):
 def test_only_delegation_capability_differs(self):
  p={'root_model':'native-observed-test','root_reasoning_effort':'high','native_helper_cap':3};site=Path('/tmp/identical-site')
  a=run.command('single',site,p);b=run.command('adaptive',site,p)
  self.assertEqual(a[:-6],b[:-6]);self.assertEqual(a[-6:],['--disable','multi_agent_v2','--disable','multi_agent','-c','agents.enabled=false']);self.assertEqual(b[-6:],['--enable','multi_agent_v2','--enable','multi_agent','-c','agents.enabled=true'])
  self.assertIn('agents.enabled=false',a);self.assertIn('agents.enabled=true',b);self.assertNotIn('--sandbox',a);self.assertNotIn('danger-full-access',' '.join(a));self.assertIn('features.network_proxy=true',a)
 def test_owned_group_cleanup_kills_surviving_descendant(self):
  with tempfile.TemporaryDirectory()as d:
   marker=Path(d)/'child';script='import subprocess,sys; p=subprocess.Popen([sys.executable,"-c","import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(30)"]);open(sys.argv[1],"w").write(str(p.pid))'
   process=subprocess.Popen([sys.executable,'-c',script,str(marker)],start_new_session=True);process.wait(timeout=5)
   while not marker.exists():time.sleep(.01)
   child=int(marker.read_text());time.sleep(.1);run.terminate_group(process,.1)
   deadline=time.monotonic()+2
   while time.monotonic()<deadline:
    status=subprocess.run(['ps','-p',str(child),'-o','stat='],capture_output=True,text=True).stdout.strip()
    if not status or status.startswith('Z'):break
    time.sleep(.05)
   self.assertTrue(not status or status.startswith('Z'))
 def test_port_listener_without_proven_workspace_ownership_not_signaled(self):
  responses=[subprocess.CompletedProcess([],0,'12345\n',''),subprocess.CompletedProcess([],0,'p12345\nn/unrelated\n',''),subprocess.CompletedProcess([],0,'python server.py --port 1234','')]
  with patch.object(run.subprocess,'run',side_effect=responses),patch.object(run.os,'kill')as kill:
   result=run.cleanup_bound_backend(Path('/tmp/specific-site'),1234);kill.assert_not_called();self.assertEqual(result[0]['action'],'not_signaled')
 def test_freeze_rejects_changed_source_or_fixture_and_missing_telemetry(self):
  import hashlib
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);site=root/'site';site.mkdir();(root/'fixture').mkdir()
   names=['run.py','telemetry.py','prices.json','judge/backend/evaluate.py','judge/frontend/evaluate.mjs','preview/broker.py','preview/render.mjs']
   hashes={}
   for name in names:
    path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('frozen');hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
   for base in (site,root/'fixture'):(base/'AGENTS.md').write_text('policy')
   p={'frozen_sources_sha256':hashes,'fixture_sha256':{'AGENTS.md':hashlib.sha256(b'policy').hexdigest()}}
   with patch.object(run,'ROOT',root):
    run.verify_freeze(p,site)
    (root/'telemetry.py').write_text('changed')
    with self.assertRaisesRegex(RuntimeError,'telemetry'):run.verify_freeze(p,site)
    (root/'telemetry.py').write_text('frozen');(site/'AGENTS.md').write_text('changed')
    with self.assertRaisesRegex(RuntimeError,'Fixture changed'):run.verify_freeze(p,site)
    del hashes['telemetry.py']
    with self.assertRaisesRegex(RuntimeError,'Incomplete'):run.verify_freeze(p,site)
 def test_input_failure_still_cleans_broker_before_final_measurement(self):
  from unittest.mock import MagicMock
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);d=root/'runs'/'single';site=d/'site';site.mkdir(parents=True)
   prompt=b'common';(root/'APP_PROMPT.txt').write_bytes(prompt);(site/'APP_PROMPT.txt').write_bytes(prompt)
   import hashlib
   (root/'protocol.json').write_text(json.dumps({'ports':{'single':12345},'prompt_sha256':hashlib.sha256(prompt).hexdigest(),'shared_budget_seconds':3000,'cleanup_reserve_seconds':30}))
   broker=MagicMock();broker.stdout.readline.return_value='{"ready":true}\n';broker.poll.return_value=None
   native=MagicMock();native.stdin.write.side_effect=BrokenPipeError('injected');native.returncode=9
   elapsed=[0.0];cleaned=[]
   def cleanup(p):cleaned.append(p);elapsed[0]+=2
   with patch.object(run,'ROOT',root),patch.object(run,'verify_freeze'),patch.object(run,'command',return_value=['native']),patch.object(run.subprocess,'Popen',side_effect=[broker,native]),patch.object(run.select,'select',return_value=([broker.stdout],[],[])),patch.object(run.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'{"ready":true}','')),patch.object(run,'cleanup_bound_backend',return_value=[]),patch.object(run,'terminate_group',side_effect=cleanup),patch.object(run.socket,'socket'),patch.object(run.time,'monotonic',side_effect=lambda:elapsed[0]):
    with self.assertRaises(BrokenPipeError):run.run('single')
   meta=json.loads((d/'metadata.json').read_text());self.assertEqual(cleaned,[native,broker]);self.assertEqual(meta['elapsed_seconds'],4);self.assertIn('BrokenPipeError',meta['runner_error']);self.assertEqual(meta['exit_code'],9)
