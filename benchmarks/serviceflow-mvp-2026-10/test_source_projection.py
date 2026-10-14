import importlib.util,json,hashlib,tempfile,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('project',str(Path(__file__).with_name('project_sources.py')));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Projection(unittest.TestCase):
 def fixture(self,root,entries):
  snap=root/'snapshot';(snap/'sources').mkdir(parents=True);h={}
  for name,body in entries.items():
   p=snap/'sources'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body);h[name]=hashlib.sha256(body).hexdigest()
  (snap/'manifest.json').write_text(json.dumps({'sources_sha256':h}));return snap
 def test_secret_excluded_without_reading(self):
  with tempfile.TemporaryDirectory()as t:
   r=Path(t);s=self.fixture(r,{'data/.auth-secret':b'synthetic-secret','data/serviceflow.sqlite.secret':b'never-read-secret','src/auth.ts':b'export const value=1;','.env.example':b'AI_KEY=\n'});(s/'sources/data/.auth-secret').unlink();(s/'sources/data/serviceflow.sqlite.secret').unlink()
   p=m.project(s,r/'out');self.assertEqual(p['source_file_count'],2);self.assertFalse((r/'out/data/.auth-secret').exists())
 def test_private_benchmark_report_omitted_before_reading(self):
  with tempfile.TemporaryDirectory()as t:
   r=Path(t);s=self.fixture(r,{'ROUTING.json':b'private-report','AUDIT_READY.md':b'private-handoff','src/routing.ts':b'export const route=1;'})
   (s/'sources/ROUTING.json').unlink();(s/'sources/AUDIT_READY.md').unlink();p=m.project(s,r/'out');self.assertEqual(p['source_file_count'],1);self.assertEqual({x['path'] for x in p['excluded_artifacts']},{'ROUTING.json','AUDIT_READY.md'})
 def test_hash_mismatch_has_no_partial_publication(self):
  with tempfile.TemporaryDirectory()as t:
   r=Path(t);s=self.fixture(r,{'src/index.ts':b'valid'});(s/'sources/src/index.ts').write_bytes(b'changed')
   with self.assertRaises(ValueError):m.project(s,r/'out')
   self.assertFalse((r/'out').exists())
 def test_private_path_rejected(self):
  with tempfile.TemporaryDirectory()as t:
   r=Path(t);s=self.fixture(r,{'README.md':('/'+'Users/synthetic/private').encode()})
   with self.assertRaises(ValueError):m.project(s,r/'out')
 def test_symlink_rejected(self):
  with tempfile.TemporaryDirectory()as t:
   r=Path(t);s=self.fixture(r,{'src/index.ts':b'valid'});p=s/'sources/src/index.ts';p.unlink();(r/'outside').write_bytes(b'valid');p.symlink_to(r/'outside')
   with self.assertRaises(ValueError):m.project(s,r/'out')
 def test_traversal_rejected(self):
  with tempfile.TemporaryDirectory()as t:
   r=Path(t);s=self.fixture(r,{});(s/'manifest.json').write_text(json.dumps({'sources_sha256':{'../bad':'ignored'}}))
   with self.assertRaises(ValueError):m.project(s,r/'out')
if __name__=='__main__':unittest.main()
