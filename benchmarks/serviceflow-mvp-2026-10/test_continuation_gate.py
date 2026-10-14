"""Portable v1 approval boundary; no subprocess, metadata or native execution."""
import hashlib,importlib.util,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('portable_continuation_gate',ROOT/'continue.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
class PortableContinuationGate(unittest.TestCase):
 def reject_before_actions(self,path,pattern='proof'):
  with patch.dict(os.environ,{'SERVICEFLOW_AMENDMENT_AUDIT':str(path)}),patch.object(c.subprocess,'Popen',side_effect=AssertionError('subprocess forbidden')),patch.object(c,'continuation',side_effect=AssertionError('native continuation forbidden')),patch.object(c.time,'sleep',side_effect=AssertionError('metadata wait forbidden')):
   with self.assertRaisesRegex(RuntimeError,pattern):c.main()
 def test_historical_native_pass_rejected_before_actions(self):
  self.reject_before_actions(ROOT/'controller-amendment-audit.json','exact controller SHA256')
 def test_missing_portable_default_rejects_before_actions(self):
  with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{},clear=True),patch.object(c,'ROOT',Path(d)),patch.object(c.subprocess,'Popen',side_effect=AssertionError('subprocess forbidden')),patch.object(c,'continuation',side_effect=AssertionError('continuation forbidden')):
   self.assertFalse((Path(d)/'controller-amendment-portable-proof.json').exists())
   with self.assertRaisesRegex(RuntimeError,'proof unavailable'):c.main()
 def test_wrong_or_missing_hash_and_failed_verdict_rejected(self):
  exact=hashlib.sha256(Path(c.__file__).read_bytes()).hexdigest()
  for proof in [{'verdict':'PASS'},{'verdict':'PASS','controller_sha256':'wrong'},{'verdict':'FAIL','controller_sha256':exact}]:
   with self.subTest(proof=proof),tempfile.TemporaryDirectory() as d:
    path=Path(d)/'proof.json';path.write_text(json.dumps(proof));self.reject_before_actions(path,'exact controller SHA256')
 def test_missing_or_malformed_explicit_proof_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'proof.json';self.reject_before_actions(path,'proof unavailable')
   path.write_text('{malformed');self.reject_before_actions(path,'proof unavailable')
 def test_exact_portable_hash_passes_gate_without_actions(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'proof.json';path.write_text(json.dumps({'verdict':'PASS','controller_sha256':hashlib.sha256(Path(c.__file__).read_bytes()).hexdigest()}))
   with patch.dict(os.environ,{'SERVICEFLOW_AMENDMENT_AUDIT':str(path)}),patch.object(c.subprocess,'Popen',side_effect=AssertionError('subprocess forbidden')),patch.object(c,'continuation',side_effect=AssertionError('continuation forbidden')):
    c.independent_gate()
if __name__=='__main__':unittest.main()
