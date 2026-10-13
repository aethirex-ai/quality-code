"""No paid calls: native protocol behavior exercised with stdlib subprocess fakes."""
import copy
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import run
import phase_collect

BUILDER = '11111111-1111-1111-1111-111111111111'
AUDITOR = '22222222-2222-2222-2222-222222222222'
OTHER = '33333333-3333-3333-3333-333333333333'

def counter(i=10, c=2, o=3):
    return dict(input_tokens=i, cached_input_tokens=c, cache_write_input_tokens=0,
                output_tokens=o, reasoning_output_tokens=1, total_tokens=i+o)

def snapshot(root, usage, size=100, digest='hash'):
    return dict(id=root, cumulative_usage=usage, rollout_sha256=digest,
                rollout_bytes=size, actual_models=['synthetic-model'])

def phase(number, role, root, after, before=None, cli=None):
    return dict(number=number, role=role, root_id=root, state='completed', elapsed_seconds=1,
                native_before=before, native_after=after, cli_usage=cli or after['cumulative_usage'],
                resume_root=root if before else None)

def verdict():
    return dict(schema_version=1, verdict='PASS', risk='critical',
                scope=dict(base='HEAD', changed_files=['server.py', 'public/index.html'], acceptance_criteria='full portal'),
                checks=[dict(command=['./quality', 'verify', 'full'], status='pass', exit_code=0, evidence='fresh full checks passed')],
                findings=[], untested=[], residual_risk='No observed residual defects', worktree_unchanged=True)

class CompletionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.site = self.root / 'site'; self.site.mkdir()
        self.sessions = self.root / 'sessions'; self.sessions.mkdir()
        self.protocol = dict(native_cli='/discovered/native/codex', root_model='discovered-model',
                             root_reasoning_effort='high', native_helper_cap=4, cleanup_reserve_seconds=.02,
                             initial_builder_cap_seconds=2400, gate_reserve_seconds=3000,
                             sessions_dir=str(self.sessions))

    def test_single_disables_both_features_on_exact_resume(self):
        args = run.command('single', self.site, self.protocol, resume=BUILDER)
        self.assertIn(['exec', 'resume', BUILDER], [args[i:i+3] for i in range(len(args))])
        for feature in ('multi_agent', 'multi_agent_v2'):
            self.assertIn(['--disable', feature], [args[i:i+2] for i in range(len(args))])
        self.assertNotIn('--last', args); self.assertNotIn('-C', args)
        self.assertNotIn('--dangerously-bypass-approvals-and-sandbox', args)
        self.assertGreater(args.index('--strict-config'), args.index('exec'))
        self.assertGreater(args.index('--ignore-user-config'), args.index(BUILDER))

    def test_discovered_native_parser_fresh_and_exact_resume_no_model_call(self):
        import subprocess
        cli=Path('/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex')
        if not cli.is_file():
            self.skipTest('Native Codex CLI unavailable on this host')
        protocol=dict(self.protocol,native_cli=str(cli))
        for role,resume in (('builder',None),('auditor',None),('builder',BUILDER)):
            args=run.command('single',self.site,protocol,role=role,resume=resume)
            # --help parses the real CLI grammar and exits before any native model call.
            args[-1]='--help'
            result=subprocess.run(args,cwd=self.site,capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('--ignore-user-config',result.stdout)

    def test_auditor_disables_implementation_delegation_in_adaptive(self):
        args = run.command('adaptive', self.site, self.protocol, role='auditor')
        self.assertIn('--output-schema', args)
        self.assertIn('agents.enabled=false', args)
        self.assertNotIn('--enable multi_agent', ' '.join(args))
        with self.assertRaises(ValueError):
            run.command('adaptive', self.site, self.protocol, role='auditor', resume=BUILDER)

    def test_adaptive_builder_enables_both_features(self):
        args = run.command('adaptive', self.site, self.protocol)
        self.assertIn('agents.enabled=true', args)
        self.assertIn('--enable multi_agent_v2', ' '.join(args))
        self.assertIn('--enable multi_agent ', ' '.join(args)+' ')

    def test_local_network_profile_has_no_external_domain(self):
        args = run.command('single', self.site, self.protocol)
        domains = [v for v in args if v.startswith('permissions.portal-local.network.domains=')]
        self.assertEqual(domains, ['permissions.portal-local.network.domains={"127.0.0.1"="allow","localhost"="allow"}'])

    def test_budget_reserves_gate_and_cleanup(self):
        self.assertEqual(run.phase_limit(self.protocol, 'builder', True, 5400), 2400)
        self.assertEqual(run.phase_limit(self.protocol, 'builder', True, 3100), 100)
        self.assertEqual(run.phase_limit(self.protocol, 'builder', True, 2900), 0)
        self.assertEqual(run.phase_limit(self.protocol, 'auditor', False, 5400), 1200)
        self.assertEqual(run.phase_limit(self.protocol, 'builder', False, 5400), 900)
        self.assertAlmostEqual(run.phase_limit(self.protocol, 'auditor', False, .01), 0)

    def test_strict_pass_requires_complete_evidence(self):
        sources = {'server.py':'a','public/index.html':'b'}
        self.assertEqual(run.validate_verdict(verdict(), self.site, sources), 'PASS')
        for mutation in (lambda v:v['checks'][0].update(status='not_run',exit_code=None),
                         lambda v:v.update(worktree_unchanged=False),
                         lambda v:v.update(untested=['mobile layout']),
                         lambda v:v['checks'][0].update(evidence=''),
                         lambda v:v['scope'].update(changed_files=['server.py']),
                         lambda v:v.update(schema_version=2)):
            value = verdict(); mutation(value)
            with self.assertRaises(ValueError):
                run.validate_verdict(value, self.site, sources)

    def test_required_release_profile_and_complete_packet_scope(self):
        protocol = dict(audit_required_commands=[['./quality','verify','release']], audit_required_files=['test_portal.py'])
        with self.assertRaises(ValueError):
            run.validate_verdict(verdict(), self.site, {'server.py':'a','public/index.html':'b'}, protocol)

    def test_fail_needs_scoped_finding(self):
        value = verdict(); value['verdict'] = 'FAIL'
        with self.assertRaises(ValueError):
            run.validate_verdict(value, self.site, {'server.py':'a','public/index.html':'b'})
        value['findings'] = [dict(id='AUD-001',severity='high',title='Auth bug',file='server.py',line=5,evidence='Unauthorized read returned 200',required_action='Enforce authorization')]
        self.assertEqual(run.validate_verdict(value,self.site,{'server.py':'a','public/index.html':'b'}), 'FAIL')

    def test_resume_cumulative_and_increment_cli_reconcile_without_double_count(self):
        first = snapshot(BUILDER, counter())
        final = snapshot(BUILDER, counter(30,4,9),200,'newhash')
        audit = snapshot(AUDITOR,counter(7,1,3))
        phases = [phase(1,'builder',BUILDER,first),phase(2,'auditor',AUDITOR,audit),phase(3,'builder',BUILDER,final,first)]
        roots, rows, flags = phase_collect.reconcile_phases(phases)
        self.assertFalse(flags); self.assertEqual(len(roots),2)
        self.assertEqual(roots[BUILDER]['cumulative_usage']['input_tokens'],30)
        self.assertEqual(rows[-1]['observed_native_delta']['input_tokens'],20)
        self.assertEqual(rows[-1]['cli_counter_basis'],'root_cumulative')
        phases[-1]['cli_usage'] = {k:final['cumulative_usage'][k]-first['cumulative_usage'][k] for k in counter()}
        roots, rows, flags = phase_collect.reconcile_phases(phases)
        self.assertFalse(flags); self.assertEqual(rows[-1]['cli_counter_basis'],'phase_increment')

    def test_foreign_baseline_and_cli_mismatch_withhold(self):
        first = snapshot(BUILDER,counter())
        audit = snapshot(AUDITOR,counter())
        final = snapshot(BUILDER,counter(20,3,5),200,'after')
        phases=[phase(1,'builder',BUILDER,first),phase(2,'auditor',AUDITOR,audit),phase(3,'builder',BUILDER,final,dict(first,rollout_sha256='foreign'))]
        self.assertIn('phase_counter_reconciliation_failed',phase_collect.reconcile_phases(phases)[2])
        phases[-1]['native_before']=first; phases[-1]['cli_usage']=counter(999,2,3)
        self.assertIn('phase_counter_reconciliation_failed',phase_collect.reconcile_phases(phases)[2])

    def test_auditor_reuse_and_builder_restart_rejected(self):
        phases=[phase(1,'builder',BUILDER,snapshot(BUILDER,counter())),phase(2,'auditor',BUILDER,snapshot(BUILDER,counter()))]
        self.assertIn('audit_independence_violated',phase_collect.reconcile_phases(phases)[2])
        phases[1]=phase(2,'auditor',AUDITOR,snapshot(AUDITOR,counter()))
        phases.append(phase(3,'builder',OTHER,snapshot(OTHER,counter())))
        self.assertIn('builder_restart_or_role_collision',phase_collect.reconcile_phases(phases)[2])

    def native_log(self, root, cwd=None):
        path=self.sessions/(root+'.jsonl')
        path.write_text(json.dumps({'type':'session_meta','payload':{'id':root,'cwd':str(cwd or self.site)}})+'\n'+json.dumps({'type':'event_msg','payload':{'type':'token_count','info':{'total_token_usage':counter()}}})+'\n')
        return path

    def test_native_workspace_provenance_and_duplicate_detection(self):
        self.native_log(BUILDER,self.root)
        with self.assertRaises(RuntimeError):run.root_snapshot(self.sessions,BUILDER,self.site)
        self.native_log(BUILDER)
        self.assertEqual(run.root_snapshot(self.sessions,BUILDER,self.site)['id'],BUILDER)
        (self.sessions/'duplicate.jsonl').write_bytes((self.sessions/(BUILDER+'.jsonl')).read_bytes())
        with self.assertRaises(RuntimeError):run.root_snapshot(self.sessions,BUILDER,self.site)

    def test_cli_event_root_never_arbitrarily_selected(self):
        path=self.root/'events.jsonl'
        path.write_text(json.dumps({'type':'thread.started','thread_id':BUILDER})+'\n'+json.dumps({'type':'thread.started','thread_id':OTHER})+'\n')
        with self.assertRaises(RuntimeError):run.parse_events(path)

    def test_source_integrity_ignores_runtime_but_tracks_implementation(self):
        (self.site/'server.py').write_text('source')
        initial=phase_collect.source_hashes(self.site)
        (self.site/'portal.db').write_text('private')
        (self.site/'cookie.txt').write_text('secret')
        (self.site/'runtime').mkdir();(self.site/'runtime'/'tokens.json').write_text('secret')
        self.assertEqual(initial,phase_collect.source_hashes(self.site))
        (self.site/'server.py').write_text('mutation')
        self.assertNotEqual(initial,phase_collect.source_hashes(self.site))

    def test_immutable_initial_bytes_survive_repairs_and_refuse_collision(self):
        (self.site/'server.py').write_text('initial portal')
        inventory=phase_collect.source_hashes(self.site)
        target=self.root/'snapshots'/'initial'
        manifest=run.freeze_source_bytes(self.site,target,inventory)
        self.assertEqual(manifest['source_file_count'],1)
        (self.site/'server.py').write_text('repaired portal')
        self.assertEqual((target/'sources'/'server.py').read_text(),'initial portal')
        self.assertEqual(json.loads((target/'manifest.json').read_text())['sources_sha256'],inventory)
        self.assertNotIn(str(self.root),(target/'manifest.json').read_text())
        with self.assertRaisesRegex(RuntimeError,'collision'):
            run.freeze_source_bytes(self.site,target,phase_collect.source_hashes(self.site))

    def test_source_snapshot_refuses_symlinks_and_unsafe_new_paths(self):
        external=self.root/'foreign.py';external.write_text('foreign')
        (self.site/'linked.py').symlink_to(external)
        for inventory in ({'linked.py':'irrelevant'},{'../foreign.py':'irrelevant'},{str(external):'irrelevant'}):
            with self.assertRaises(RuntimeError):
                run.freeze_source_bytes(self.site,self.root/'snapshot',inventory)
        self.assertFalse((self.root/'snapshot').exists())
        (self.site/'linked.py').unlink()
        (self.site/'unlisted.py').write_text('new source')
        with self.assertRaisesRegex(RuntimeError,'inventory changed'):
            run.freeze_source_bytes(self.site,self.root/'unlisted-snapshot',{})
        (self.root/'linked-destination').symlink_to(self.site,target_is_directory=True)
        with self.assertRaises(RuntimeError):
            run.freeze_source_bytes(self.site,self.root/'linked-destination'/'snapshot',{})

    def test_fixed_gate_failure_stays_failure(self):
        proto=dict(self.protocol,gate_commands=[[sys.executable,'-c','print(\'{"accepted":false,"tool_incomplete":false}\')']])
        result=run.fixed_gates(proto,self.site,self.root,1,time.monotonic()+2,os.environ.copy())
        self.assertFalse(result['accepted']);self.assertFalse(result['tool_incomplete'])

    def detached_fixture(self):
        script=self.root/'detached-fixture.py'
        pidfile=self.root/'detached.pid'
        script.write_text("import subprocess,sys,time,pathlib\nchild=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\npathlib.Path(sys.argv[1]).write_text(str(child.pid))\ntime.sleep(60)\n")
        return script,pidfile

    def test_outer_gate_timeout_cleans_detached_descendant_and_preserves_foreign(self):
        import subprocess
        script,pidfile=self.detached_fixture()
        foreign=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])
        try:
            proto=dict(self.protocol,fixed_gate_cap_seconds=.7,gate_commands=[[sys.executable,str(script),str(pidfile)]])
            started=time.monotonic()
            with self.assertRaises(subprocess.TimeoutExpired):
                run.fixed_gates(proto,self.site,self.root,1,time.monotonic()+4,os.environ.copy())
            self.assertTrue(pidfile.is_file())
            self.assertIsNone(run.kernel_process_identity(int(pidfile.read_text())))
            self.assertIsNone(foreign.poll())
            self.assertLess(time.monotonic()-started,4)
        finally:
            foreign.terminate();foreign.wait(timeout=3)

    def test_fast_python_gate_exit_registers_detached_child_before_handoff(self):
        script=self.root/'fast-python.py';pidfile=self.root/'fast-python.pid'
        script.write_text("import pathlib,subprocess,sys\nchild=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\npathlib.Path(sys.argv[1]).write_text(str(child.pid))\n")
        result=run.owned_run([sys.executable,str(script),str(pidfile)],timeout=3,cwd=self.root,env=os.environ.copy(),cleanup_grace=.1)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIsNone(run.kernel_process_identity(int(pidfile.read_text())))

    def test_fast_node_spawn_exit_registers_detached_child_and_preserves_options(self):
        import shutil
        node=shutil.which(run.NODE)
        if not node:self.skipTest('Node unavailable')
        script=self.root/'fast-node.cjs';pidfile=self.root/'fast-node.pid'
        script.write_text("const cp=require('node:child_process'),fs=require('node:fs');const child=cp.spawn(process.env.CODEX_GATE_PYTHON,['-c','import time;time.sleep(60)'],{detached:true,stdio:'ignore'});fs.writeFileSync(process.argv[2],String(child.pid));process.exit(0);\n")
        env=os.environ.copy();env['NODE_OPTIONS']='--no-warnings';env['PYTHONPATH']=str(self.root/'existing-python-path')
        result=run.owned_run([node,str(script),str(pidfile)],timeout=4,cwd=self.root,env=env,cleanup_grace=.1)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIsNone(run.kernel_process_identity(int(pidfile.read_text())))
        self.assertEqual(env['NODE_OPTIONS'],'--no-warnings')
        self.assertEqual(env['PYTHONPATH'],str(self.root/'existing-python-path'))

    def test_nested_gate_interrupt_cleans_detached_evaluator_resources(self):
        import subprocess
        script,pidfile=self.detached_fixture()
        wrapper=self.root/'inner-wrapper.py'
        wrapper.write_text("import sys,signal\nsys.path.insert(0,"+repr(str(Path(run.__file__).parent))+ ")\nfrom run import owned_run\nfrom gate_checks import interrupted\nsignal.signal(signal.SIGTERM,interrupted)\nowned_run([sys.executable,"+repr(str(script))+","+repr(str(pidfile))+"],timeout=60,cwd="+repr(str(self.root))+",env=__import__('os').environ.copy())\n")
        with self.assertRaises(subprocess.TimeoutExpired):
            run.owned_run([sys.executable,str(wrapper)],timeout=.8,cwd=self.root,env=os.environ.copy())
        self.assertTrue(pidfile.is_file())
        self.assertIsNone(run.kernel_process_identity(int(pidfile.read_text())))

    def test_native_phase_global_timeout_is_observable(self):
        script=self.root/'synthetic.py'
        script.write_text('import json,time\nprint(json.dumps({"type":"thread.started","thread_id":"'+BUILDER+'"}),flush=True)\ntime.sleep(30)\n')
        self.native_log(BUILDER)
        meta={'phases':[]}
        # A resume of the exact owned root is permitted, but missing completion remains timed_out.
        with patch.object(run,'command',return_value=[sys.executable,str(script)]):
            started=time.monotonic()
            phase_result,_=run.execute_phase('single',self.site,self.root,self.protocol,meta,time.monotonic()+.2,b'brief',role='builder',number=2,resume=BUILDER,env=os.environ.copy())
        self.assertEqual(phase_result['state'],'timed_out')
        self.assertLess(time.monotonic()-started,3)
        self.assertIsNone(phase_result['cli_usage'])

    def orchestration(self, mutate_auditor=False):
        import io
        from types import SimpleNamespace
        directory=self.root/'runs'/'single';site=directory/'site';site.mkdir(parents=True)
        (site/'BRIEF.md').write_text('full portal')
        (self.root/'APP_PROMPT.txt').write_text('common builder prompt')
        (self.root/'AUDIT_PROMPT.txt').write_text('$audit-code-change full scope')
        protocol=dict(self.protocol,ports={'single':0},shared_budget_seconds=5400,
                      cleanup_reserve_seconds=30,max_audit_rounds=4,prompt_sha256='common')
        (self.root/'protocol.json').write_text(json.dumps(protocol))
        broker=SimpleNamespace(stdout=io.StringIO('{"ready":true}\n'),poll=lambda:None)
        called=[]
        def fake_subprocess(args,**kwargs):
            output={'ready':True} if '--ready' in args else {'changed_files':['server.py','public/index.html'],'base':'HEAD','acceptance_criteria':'full portal'}
            return SimpleNamespace(returncode=0,stdout=json.dumps(output),stderr='')
        def fake_phase(condition,workspace,d,proto,meta,deadline,prompt,*,role,number,resume=None,env=None):
            called.append({'role':role,'resume':resume,'prompt':prompt.decode()})
            folder=d/'phases'/('%02d-%s'%(number,role));folder.mkdir(parents=True)
            if role=='builder':
                (workspace/'server.py').write_text('repaired' if resume else 'initial')
                (workspace/'public').mkdir(exist_ok=True);(workspace/'public'/'index.html').write_text('portal')
                meta['builder_root']=BUILDER;root=BUILDER
            else:
                root=AUDITOR if number==2 else OTHER
                meta.setdefault('auditor_roots',[]).append(root)
                value=verdict()
                if number==2:
                    value['verdict']='FAIL'
                    value['findings']=[dict(id='AUD-001',severity='high',title='Boundary defect',file='server.py',line=1,evidence='Contract repro',required_action='Repair boundary')]
                (folder/'final.txt').write_text(json.dumps(value))
                if mutate_auditor:(workspace/'server.py').write_text('unauthorized audit mutation')
            result={'role':role,'root_id':root,'state':'completed','elapsed_seconds':.1}
            meta['phases'].append(result)
            return result,folder
        stack=[patch.object(run,'ROOT',self.root),patch.object(run,'verify_freeze'),
               patch.object(run.subprocess,'Popen',return_value=broker),patch.object(run.subprocess,'run',side_effect=fake_subprocess),
               patch.object(run.select,'select',return_value=([broker.stdout],[],[])),patch.object(run,'terminate_group'),
               patch.object(run,'cleanup_bound_backend',return_value=[]),patch.object(run,'fixed_gates',return_value={'accepted':True,'tool_incomplete':False,'reports':[]}),
               patch.object(run,'execute_phase',side_effect=fake_phase)]
        from contextlib import ExitStack
        with ExitStack() as context:
            for item in stack:context.enter_context(item)
            if mutate_auditor:
                with self.assertRaisesRegex(RuntimeError,'Auditor changed product sources'):run.run('single')
                meta=json.loads((directory/'metadata.json').read_text())
            else:meta=run.run('single')
        return meta,called

    def test_fail_repair_fresh_gate_accepts_only_after_exact_resume(self):
        meta,calls=self.orchestration()
        self.assertEqual(meta['state'],'PASS')
        self.assertEqual([c['role'] for c in calls],['builder','auditor','builder','auditor'])
        self.assertEqual(calls[2]['resume'],BUILDER)
        self.assertIn('repair-01-findings.json',calls[2]['prompt'])
        self.assertIn('audit-02-packet.json',calls[3]['prompt'])
        self.assertEqual(len(meta['auditor_roots']),2)
        self.assertGreaterEqual(meta['elapsed_seconds'],0)
        self.assertIn('final_source_sha256',meta)

    def test_auditor_source_mutation_never_reaches_pass_or_repair(self):
        meta,calls=self.orchestration(mutate_auditor=True)
        self.assertEqual(meta['state'],'INCOMPLETE')
        self.assertEqual(len(calls),2)
        self.assertIn('Auditor changed product sources',meta['runner_error'])

if __name__=='__main__':unittest.main()
