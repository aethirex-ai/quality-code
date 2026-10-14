"""Frozen task preservation and short canonical acceptance identity controls."""
import hashlib,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class AmendmentContracts(unittest.TestCase):
 def test_protected_task_and_fixture_bytes_are_unchanged(self):
  before=json.loads((ROOT/'protocol-before-amendment2.json').read_text())
  after=json.loads((ROOT/'protocol.json').read_text())
  self.assertEqual(before['fixture_sha256'],after['fixture_sha256'])
  self.assertEqual(before['initial_fixture_sha256'],after['initial_fixture_sha256'])
  for name in ['APP_PROMPT.txt','ACCEPTANCE.md','AUDIT_PROMPT.txt','BRAND.md']:
   self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),before['frozen_sources_sha256'][name])
  for name,expected in before['initial_fixture_sha256'].items():
   self.assertEqual(hashlib.sha256((ROOT/'fixture'/name).read_bytes()).hexdigest(),expected,name)
 def test_only_declared_protocol_amendment_values_change(self):
  before=json.loads((ROOT/'protocol-before-amendment2.json').read_text())
  after=json.loads((ROOT/'native-protocol-amendment2.json').read_text())
  public=json.loads((ROOT/'protocol.json').read_text())
  for name,value in after.items():
   if name not in ('native_cli','sessions_dir','frozen_sources_sha256','supplementary_instruments_sha256'):
    self.assertEqual(public[name],value,name)
  keys=set(before)|set(after)
  allowed={'audit_acceptance_criteria','acceptance_document_sha256','instrument_amendments','frozen_sources_sha256','supplementary_instruments_sha256'}
  self.assertEqual({k for k in keys if before.get(k)!=after.get(k)},allowed)
  self.assertEqual(after['instrument_amendments'][:-1],before['instrument_amendments'])
  for k in ['shared_budget_seconds','max_audit_rounds','initial_builder_cap_seconds','audit_phase_cap_seconds','repair_phase_cap_seconds']:
   self.assertIsNone(after[k])
 def test_frozen_staging_instruments_and_controller_match(self):
  after=json.loads((ROOT/'protocol.json').read_text())
  for name,expected in after['frozen_sources_sha256'].items():
   self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected,name)
  self.assertEqual(hashlib.sha256((ROOT/'continue-v2.py').read_bytes()).hexdigest(),after['supplementary_instruments_sha256']['continue-v2.py'])
if __name__=='__main__':unittest.main()
