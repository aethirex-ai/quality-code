"""Harness/framing tests and deliberately broken contract controls."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
import evaluate

HERE=Path(__file__).resolve().parent
CONTROL_RUNS=[]

class EvaluatorControls(unittest.TestCase):
    def run_evaluator(self, mutation='', script=None):
        with tempfile.TemporaryDirectory(prefix='backend-control-') as temp:
            root=Path(temp);site=root/'site';site.mkdir();output=root/'result.json'
            if script is None: shutil.copyfile(HERE/'test_fixture.py',site/'server.py')
            elif script: (site/'server.py').write_text(script)
            env={**os.environ,'QC_FIXTURE_MUTATION':mutation}
            result=subprocess.run([sys.executable,str(HERE/'evaluate.py'),str(site),str(output)],
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=120)
            self.assertTrue(output.is_file(),result.stderr.decode()[:1000])
            report=json.loads(output.read_text())
            self.assertEqual(report['denominator'],12)
            self.assertEqual(len(report['groups']),12)
            self.assertEqual(len({g['id'] for g in report['groups']}),12)
            evidence={g['id']:json.loads(Path(g['evidence']).read_text()) for g in report['groups']}
            for group in report['groups']:
                self.assertIn(group['status'],('pass','fail','blocked','error'))
                self.assertNotIn('defect_count',report)
            CONTROL_RUNS.append({'control':mutation or ('healthy' if script is None else 'launch_or_prerequisite'),
                'passed':report['passed'],'denominator':report['denominator'],'elapsed_seconds':report['elapsed_seconds'],
                'instrument_error':report['error'],'groups':[{k:v for k,v in g.items() if k!='evidence'} for g in report['groups']]})
            return result,report,{g['id']:g for g in report['groups']},evidence

    def test_healthy_reference(self):
        result,report,groups,evidence=self.run_evaluator()
        self.assertEqual(report['passed'],12,[(k,v['error']) for k,v in groups.items() if v['status']!='pass'])
        self.assertEqual(result.returncode,0)
        self.assertIsNone(report['error'])
        self.assertLess(report['elapsed_seconds'],120)
        self.assertTrue(evidence['concurrent_revision_writes']['requests'])

    def test_critical_mutations_with_healthy_controls(self):
        # Each targeted broken contract is detected, while an unrelated healthy
        # contract still passes. This guards against globally failing judges.
        pairs=[('isolation','client_isolation','session_lifecycle'),
               ('staff','staff_permissions','session_lifecycle'),
               ('stale','conflict_atomicity','comment_identity_and_activity'),
               ('duplicate','conflict_atomicity','revision_publication'),
               ('race','concurrent_revision_writes','authentication'),
               ('persistence','restart_persistence','revision_publication'),
               ('double_event','comment_identity_and_activity','authentication'),
               ('author','comment_identity_and_activity','revision_publication')]
        for mutation,target,control in pairs:
            with self.subTest(mutation=mutation):
                result,report,groups,evidence=self.run_evaluator(mutation)
                self.assertEqual(result.returncode,1)
                self.assertEqual(groups[target]['status'],'fail',groups[target])
                self.assertEqual(groups[target]['error']['kind'],'product')
                self.assertEqual(groups[control]['status'],'pass',groups[control])
                self.assertTrue(evidence[target]['requests'])
                self.assertIsNone(report['error'])

    def test_missing_server_retains_denominator(self):
        result,report,groups,_=self.run_evaluator(script='')
        self.assertEqual(report['passed'],0)
        self.assertTrue(all(g['status']=='fail' and g['error']['kind']=='product' for g in groups.values()))
        self.assertIsNone(report['error'])
        self.assertEqual(result.returncode,1)

    def test_launch_failure_reports_product_runtime(self):
        _,report,groups,_=self.run_evaluator(script='raise SystemExit(7)\n')
        self.assertEqual(report['passed'],0)
        self.assertTrue(all('before readiness' in g['error']['message'] for g in groups.values()))
        self.assertIsNone(report['error'])

    def test_prerequisite_failures_do_not_become_separate_defects(self):
        script=(HERE/'test_fixture.py').read_text().replace("if user is None: raise Reject(401,'Invalid credentials')", "if True: raise Reject(401,'Invalid credentials')")
        _,report,groups,_=self.run_evaluator(script=script)
        self.assertEqual(groups['authentication']['status'],'fail')
        self.assertEqual(groups['session_lifecycle']['status'],'blocked')
        self.assertEqual(groups['session_lifecycle']['error']['root_group'],'authentication')
        self.assertEqual(report['denominator'],12)

    def test_instrument_failure_is_not_product_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'server.py').write_text('pass\n')
            with mock.patch.object(evaluate.socket,'socket',side_effect=PermissionError('loopback disabled')):
                report=evaluate.evaluate(root,root/'output.json')
            self.assertEqual(report['denominator'],12)
            self.assertEqual(report['passed'],0)
            self.assertEqual(report['error']['kind'],'instrument')
            self.assertTrue(all(g['status']=='error' and g['error']['kind']=='instrument' for g in report['groups']))

    def test_owned_process_cleanup_and_bounded_readiness(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'server.py').write_text("import json,signal,time\nsignal.signal(signal.SIGTERM,signal.SIG_IGN)\nprint('x'*6000,flush=True)\nprint(json.dumps({'ready':True,'port':12345}),flush=True)\ntime.sleep(60)\n")
            server=evaluate.Server(root,root,time.monotonic()+4)
            try:
                server.start();process=server.process;pid=process.pid
                with mock.patch.object(evaluate.os,'killpg',wraps=evaluate.os.killpg) as kill:
                    server.stop()
                self.assertIsNotNone(process.poll())
                self.assertTrue(any(c.args[0]==pid and c.args[1]==evaluate.signal.SIGKILL for c in kill.call_args_list))
                self.assertTrue(process.stdout.closed and process.stderr.closed)
            finally: server.stop()

    def test_exited_leader_term_ignoring_descendant_with_inherited_pipes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);child_pid=None
            (root/'descendant.py').write_text("import os,signal,time\nfrom pathlib import Path\nsignal.signal(signal.SIGTERM,signal.SIG_IGN)\nPath('child.pid').write_text(str(os.getpid()))\nos.write(1,b'child stdout\\n');os.write(2,b'child stderr\\n')\ntime.sleep(8)\n")
            (root/'server.py').write_text("import json,subprocess,sys,time\nfrom pathlib import Path\nsubprocess.Popen([sys.executable,'descendant.py'])\nwhile not Path('child.pid').exists(): time.sleep(.01)\nprint(json.dumps({'ready':True,'port':12345}),flush=True)\n")
            server=evaluate.Server(root,root,time.monotonic()+5)
            try:
                server.start();process=server.process
                process.wait(timeout=2)
                self.assertIsNotNone(process.poll(),'Leader must exit before cleanup')
                child_pid=int((root/'child.pid').read_text())
                os.kill(child_pid,0)  # Live child was acknowledged after installing SIG_IGN.
                started=time.monotonic();server.stop();elapsed=time.monotonic()-started
                self.assertLess(elapsed,2,'Cleanup waited for descendant-held pipes')
                self.assertTrue(process.stdout.closed and process.stderr.closed)
                self.assertTrue(all(not thread.is_alive() for thread in server.threads))
                deadline=time.monotonic()+1
                while True:
                    check=subprocess.run(['ps','-p',str(child_pid),'-o','stat='],capture_output=True,text=True,timeout=1)
                    state=check.stdout.strip()
                    if not state or state.startswith('Z'): break
                    if time.monotonic()>=deadline: self.fail('Owned TERM-ignoring descendant remains running: '+state)
                    time.sleep(.02)
                CONTROL_RUNS.append({'control':'AUD-001 exited leader/inherited pipes','cleanup_seconds':round(elapsed,4),'descendant_running':False})
            finally:
                if child_pid:
                    try: os.kill(child_pid,evaluate.signal.SIGKILL)
                    except ProcessLookupError: pass
                server.stop()

    def test_incorrect_success_schema_is_product_failure(self):
        script=(HERE/'test_fixture.py').read_text().replace("return 200,{'projects':projects},[]", "return 200,{'projects':'incorrect type'},[]")
        _,report,groups,_=self.run_evaluator(script=script)
        self.assertEqual(groups['client_isolation']['status'],'fail')
        self.assertEqual(groups['client_isolation']['error']['kind'],'product')
        self.assertIsNone(report['error'])

if __name__=='__main__':
    program=unittest.main(verbosity=2,exit=False)
    Path(os.environ.get('PORTAL_CONTROL_OUTPUT',str(Path(tempfile.gettempdir())/'portal-backend-controls.json'))).write_text(json.dumps({'tests_run':program.result.testsRun,
        'failures':len(program.result.failures),'errors':len(program.result.errors),'runs':CONTROL_RUNS},indent=2)+'\n')
    raise SystemExit(0 if program.result.wasSuccessful() else 1)
