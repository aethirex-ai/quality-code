"""Verify preserved provenance and public corpus without paid/native calls."""
import hashlib,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
class PublicationIntegrity(unittest.TestCase):
 def test_all_recorded_instruments_match_published_hashes(self):
  proof=json.loads((ROOT/'replay-source-provenance.json').read_text());protocol=json.loads((ROOT/'protocol.json').read_text())
  self.assertEqual(len(proof['sources']),61)
  self.assertEqual(digest(ROOT/'protocol.json'),proof['published_protocol_sha256'])
  for row in proof['sources']:
   self.assertEqual(digest(ROOT/row['path']),row['published_sha256'],row['path'])
   self.assertEqual(protocol['native_frozen_sources_sha256'][row['path']],row['native_sha256'])
   self.assertEqual(protocol['frozen_sources_sha256'][row['path']],row['published_sha256'])
  adapted=[r['path']for r in proof['sources']if r['native_sha256']!=r['published_sha256']]
  self.assertEqual(adapted,['capture-brand.mjs','run.py'])
  row=next(x for x in proof['sources']if x['path']=='run.py');self.assertEqual(digest(ROOT/'runner-native.py'),row['native_sha256'])
 def test_brand_capture_decodes_space_and_unicode_paths(self):
  import subprocess,tempfile,shutil
  node=shutil.which('node')
  self.assertIsNotNone(node,'Node is required for the portable capture regression')
  with tempfile.TemporaryDirectory(prefix='capture space ü ')as tmp:
   target=Path(tmp)/'capture.mjs';source=(ROOT/'capture-brand.mjs').read_text()
   prefix=source.split('await mkdir(out,')[0]
   prefix=prefix.replace("const {chromium}=await import(process.env.BENCHMARK_PLAYWRIGHT_IMPORT||'playwright');",'')
   target.write_text(prefix+'console.log(out);')
   run=subprocess.run([node,str(target)],capture_output=True,text=True,check=True)
   self.assertEqual(Path(run.stdout.strip()).resolve(),(Path(tmp)/'brand').resolve())
 def test_blank_common_corpus_retains_native_bytes(self):
  proof=json.loads((ROOT/'replay-source-provenance.json').read_text());self.assertEqual(len(proof['fixture_source_sha256']),25)
  for name,expected in proof['fixture_source_sha256'].items():self.assertEqual(digest(ROOT/'fixture'/name),expected,name)
 def test_retained_single_source_and_diagnostic_bytes(self):
  m=json.loads((ROOT/'source-manifests/single-final.json').read_text());self.assertEqual(m['publication']['state'],'INCOMPLETE')
  for name,expected in m['sources_sha256'].items():self.assertEqual(digest(ROOT/'apps/single'/name),expected,name)
  proof=json.loads((ROOT/'single-diagnostic-provenance.json').read_text())
  for row in proof['reports']:self.assertEqual(digest(ROOT/row['path']),row['published_sha256'])
  gallery=ROOT.parents[1]/'docs/benchmarks'/ROOT.name
  for row in proof['screenshots']:self.assertEqual(digest(gallery/row['path']),row['sha256'])
  summary=json.loads((ROOT/'diagnostics/single/summary.json').read_text())
  raw=json.loads((ROOT/'diagnostics/single/recovery.json').read_text())
  uncertain=[c['name']for c in raw['checks']if c.get('evidence',{}).get('instrumentErrors')]
  self.assertTrue(uncertain)
  self.assertEqual(uncertain,summary['recovery']['uncertain_due_to_recorded_instrument_error'])
 def test_control_proofs_preserve_public_hashes(self):
  proof=json.loads((ROOT/'instrument-controls/provenance.json').read_text())
  self.assertEqual(len(proof['records']),7)
  for row in proof['records']:self.assertEqual(digest(ROOT/'instrument-controls'/row['path']),row['published_sha256'])
 def test_results_do_not_turn_partial_observations_into_acceptance(self):
  r=json.loads((ROOT/'results.json').read_text());u=json.loads((ROOT/'usage-diagnostic.json').read_text())
  self.assertFalse(r['validity']['accepted_quality_comparison']);self.assertFalse(r['validity']['cheap_model_routing_exercised'])
  for name,condition in r['conditions'].items():
   self.assertEqual(condition['state'],'INCOMPLETE');self.assertIsNone(condition['accepted_completion_seconds']);self.assertIsNone(condition['complete_cost_usd']);self.assertIsNone(condition['complete_tokens'])
   raw=json.loads((ROOT/'diagnostics'/name/'backend.json').read_text());self.assertEqual(condition['post_clock_samples']['backend']['passed'],raw['passed'])
   raw=json.loads((ROOT/'diagnostics'/name/'frontend.json').read_text());self.assertEqual(condition['post_clock_samples']['frontend']['passed'],raw['passed'])
  rows=u['adaptive']['unique_owned_session_rows'];expected=u['adaptive']['all_reported_unique_owned_subset']
  for key in expected:self.assertEqual(sum(row['reported_counters'][key]for row in rows),expected[key],key)
  from decimal import Decimal
  self.assertEqual(sum(Decimal(row['conditional_standard_short_proxy']['total_usd'])for row in rows),Decimal(u['adaptive']['all_reported_subset_conditional_standard_short_proxy']['total_usd']))
  self.assertEqual(r['conditions']['adaptive']['phases'][-1]['state'],'timed_out')
  self.assertEqual(len(r['conditions']['adaptive']['canonical_audit_reports']),1)
  canonical=json.loads((ROOT/r['conditions']['adaptive']['canonical_audit_reports'][0]).read_text());self.assertEqual(canonical['verdict'],'FAIL')
 def test_all_additional_frozen_sources_and_sanitized_reports_match(self):
  for name in ['adaptive-initial','adaptive-final']:
   m=json.loads((ROOT/'source-manifests'/(name+'.json')).read_text());prefix=m['publication']['path_prefix']
   for path,expected in m['sources_sha256'].items():self.assertEqual(digest(ROOT/prefix/path),expected,path)
  for label in ['adaptive']:
   proof=json.loads((ROOT/(label+'-diagnostic-provenance.json')).read_text())
   for row in proof['reports']:self.assertEqual(digest(ROOT/row['path']),row['published_sha256'])
   for row in proof['screenshots']:self.assertEqual(digest(ROOT.parents[1]/'docs/benchmarks'/ROOT.name/row['path']),row['sha256'])
  proof=json.loads((ROOT/'report-provenance.json').read_text())
  for row in proof['records']:self.assertEqual(digest(ROOT/row['path']),row['published_sha256'])
 def test_public_sources_exclude_local_session_locations(self):
  proof=json.loads((ROOT/'replay-source-provenance.json').read_text())
  for name in [r['path']for r in proof['sources']]+['protocol.json']:
   b=(ROOT/name).read_bytes()
   self.assertNotIn(b'/Users/',b,name);self.assertNotIn(b'/private/tmp/',b,name)
if __name__=='__main__':unittest.main()
