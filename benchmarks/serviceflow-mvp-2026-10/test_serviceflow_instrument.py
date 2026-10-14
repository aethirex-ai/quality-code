import json,tempfile,unittest
from pathlib import Path
import structural_gate,collect,run
class ServiceFlowInstrument(unittest.TestCase):
 def test_missing_or_malformed_manifest_cannot_pass(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);self.assertFalse(structural_gate.inspect(p)['accepted'])
   (p/'package.json').write_text('{broken');self.assertFalse(structural_gate.inspect(p)['accepted'])
 def test_structural_gate_does_not_claim_functional_acceptance(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)
   for name in ['README.md','.env.example']:(p/name).write_text('demo')
   (p/'package.json').write_text(json.dumps({'scripts':{'build':'npm build','benchmark:start':'npm start'}}))
   r=structural_gate.inspect(p);self.assertTrue(r['accepted']);self.assertIn('not functional acceptance',r['kind'])
 def test_dependency_and_build_trees_pruned_but_env_example_retained(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)
   for name in ['node_modules','dist','.next','.npm-cache']:
    (p/name).mkdir();(p/name/'secret.js').write_text('build/cache data')
   (p/'data').mkdir();(p/'data/.auth-secret').write_text('private generated auth key');(p/'cookies.json').write_text('private cookie');(p/'cookie.txt').write_text('private cookie');(p/'runtime').mkdir();(p/'runtime/tokens.json').write_text('private token');(p/'.env').write_text('SECRET=private');(p/'.env.example').write_text('SECRET=placeholder');(p/'app.ts').write_text('source');(p/'src/runtime').mkdir(parents=True);(p/'src/cookies.ts').write_text('auth source');(p/'src/runtime/state.ts').write_text('runtime source')
   self.assertEqual(set(collect.source_hashes(p)),{'.env.example','app.ts','src/cookies.ts','src/runtime/state.ts'})
 def test_uncapped_native_phase_and_rounds(self):
  p={'completion_mode':'uncapped'};self.assertIsNone(run.phase_limit(p,'auditor',False,None))
  rounds=run.audit_rounds(p);self.assertEqual([next(rounds)for _ in range(7)],list(range(1,8)))
 def test_typescript_complete_scope_passes_and_omitted_source_fails(self):
  from test_completion_runner import verdict
  snapshot={'package.json':'hash','src/main.ts':'hash','app/page.tsx':'hash','.env.example':'hash'}
  value=verdict();value['scope']['changed_files']=list(snapshot)
  self.assertEqual(run.validate_verdict(value,Path('.'),snapshot,{'audit_product_scope':'all-source'}),'PASS')
  value['scope']['changed_files'].remove('src/main.ts')
  with self.assertRaisesRegex(ValueError,'omitted product'):run.validate_verdict(value,Path('.'),snapshot,{'audit_product_scope':'all-source'})
 def test_host_provider_and_database_secrets_are_not_inherited(self):
  original={'OPENAI_API_KEY':'test-secret','DATABASE_URL':'test-database','AUTH_SECRET':'test-auth','PATH':'test-path','CODEX_PROXY_TOKEN':'native-test'}
  actual=run.isolated_environment(original)
  self.assertNotIn('OPENAI_API_KEY',actual);self.assertNotIn('DATABASE_URL',actual);self.assertNotIn('AUTH_SECRET',actual)
  self.assertEqual(actual['PATH'],'test-path');self.assertEqual(actual['CODEX_PROXY_TOKEN'],'native-test');self.assertIn('OPENAI_API_KEY',original)
 def test_real_node_environment_port_cleanup_and_foreign_control(self):
  import os,shutil,socket,subprocess,time
  node=shutil.which(run.NODE);self.assertIsNotNone(node)
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);owned=root/'owned';foreign=root/'foreign';(owned/'nested').mkdir(parents=True);foreign.mkdir()
   for folder in [owned/'nested',foreign]:
    script=folder/'server.cjs';script.write_text("require('node:http').createServer((q,r)=>r.end('ok')).listen(Number(process.env.PORTAL_PORT),'127.0.0.1');")
    with socket.socket()as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    proc=subprocess.Popen([node,str(script)],cwd=folder,env=dict(os.environ,PORTAL_PORT=str(port)),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
    try:
     end=time.monotonic()+5
     while True:
      try:
       with socket.create_connection(('127.0.0.1',port),timeout=.1):break
      except OSError:
       if time.monotonic()>end:raise
       time.sleep(.02)
     if folder.is_relative_to(owned):
      notes=run.cleanup_bound_backend(owned,port,('node',));proc.wait(timeout=3)
      self.assertEqual(notes[0]['action'],'owned backend terminated')
     else:
      with self.assertRaisesRegex(RuntimeError,'listener remains'):run.cleanup_bound_backend(owned,port,('node',))
      self.assertIsNone(proc.poll())
    finally:run.terminate_group(proc)
class CredentialFilenamePrivacy(unittest.TestCase):
 def test_generated_credentials_never_read_and_real_sources_retained(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   secret=['data/serviceflow.sqlite.secret','data/another.SECRET','data/.auth-secret']
   healthy=['src/secrets.ts','src/secret.ts','data/catalogue.json','data/secret-seed.sql','data/serviceflow.sqlite.secret.ts']
   for name in secret+healthy:
    target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text('owned synthetic fixture')
   original=Path.read_bytes;reads=[]
   def guarded(path):
    relative=path.relative_to(root).as_posix();reads.append(relative)
    if relative in secret:raise AssertionError('credential bytes accessed')
    return original(path)
   with patch.object(Path,'read_bytes',guarded):
    self.assertEqual(set(collect.source_hashes(root)),set(healthy))
    from phase_collect import source_hashes
    self.assertEqual(set(source_hashes(root)),set(healthy))
   self.assertFalse(set(secret)&set(reads))
 def test_filename_match_is_precise(self):
  for name in ['data/serviceflow.sqlite.secret','data/.auth-secret','nested/TOKEN.SECRET']:
   self.assertTrue(collect.private_credential_path(name),name)
  for name in ['src/secrets.ts','src/secret.ts','data/secrets.json','data/x.secret.sql','data/.auth-secret.ts']:
   self.assertFalse(collect.private_credential_path(name),name)
if __name__=='__main__':unittest.main()
