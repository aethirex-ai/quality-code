"""Public artifact provenance and portable host configuration; no native calls."""
import hashlib,json,os,re,unittest
from pathlib import Path
from unittest.mock import patch
import run
ROOT=Path(__file__).resolve().parent
class PublicInstruments(unittest.TestCase):
 def test_all_public_frozen_and_fixture_hashes_match(self):
  protocol=json.loads((ROOT/'protocol.json').read_text())
  for field,base in [('frozen_sources_sha256',ROOT),('initial_fixture_sha256',ROOT/'fixture')]:
   for name,expected in protocol[field].items():
    self.assertEqual(hashlib.sha256((base/name).read_bytes()).hexdigest(),expected,name)
  run.verify_freeze(protocol,ROOT/'fixture',initial=True)
 def test_native_vs_public_adaptations_explicit(self):
  p=json.loads((ROOT/'protocol.json').read_text())
  for name,item in p['portable_adaptations'].items():
   self.assertEqual(item['public_sha256'],p['frozen_sources_sha256'][name])
   self.assertEqual(item['native_sha256'],p['native_frozen_sources_sha256'].get(name,p['native_supplementary_sources_sha256'].get(name)))
   self.assertNotEqual(item['native_sha256'],item['public_sha256'])
  self.assertEqual(p['native_supplementary_sources_sha256']['continue.py'],'4634cd157fdaddbab984081307167dea6400d15b185d66eb2f8b27dc22245cfd')
 def test_runtime_configuration_resolves_explicit_environment(self):
  with patch.dict(os.environ,{'SERVICEFLOW_NATIVE_CLI':'/explicit/codex','SERVICEFLOW_SESSIONS_DIR':'/explicit/sessions'},clear=True),patch('run.shutil.which',return_value=None):
   p=run.runtime_protocol({'native_cli':'codex','sessions_dir':'<set SERVICEFLOW_SESSIONS_DIR>'})
  self.assertEqual(p['native_cli'],'/explicit/codex');self.assertEqual(p['sessions_dir'],'/explicit/sessions')
 def test_host_paths_and_private_artifacts_excluded(self):
  p=json.loads((ROOT/'protocol.json').read_text())
  files=set(p['frozen_sources_sha256'])|{'protocol.json'}|{'fixture/'+n for n in p['initial_fixture_sha256']}
  for name in files:
   path=ROOT/name
   self.assertFalse(path.is_symlink(),name)
   if path.suffix!='.png':
    text=path.read_text()
    for token in ['/'+'Users/','/'+'private/tmp/','/'+'Applications/']:
     self.assertNotIn(token,text,name)
   self.assertNotIn('.git',path.relative_to(ROOT).parts)
  self.assertFalse((ROOT/'runs').exists())
if __name__=='__main__':unittest.main()
