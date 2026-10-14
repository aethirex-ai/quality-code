"""Independent arithmetic and frozen-source checks for the published result."""
import hashlib,json,unittest
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parent
FIELDS=('input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens','total_tokens')
class PublishedResults(unittest.TestCase):
 def test_final_acceptance_and_request_level_costs(self):
  usage=json.loads((ROOT/'usage.json').read_text());prices=json.loads((ROOT/'prices.json').read_text())
  self.assertIs(usage['final'],True)
  aliases=set()
  for name,c in usage['conditions'].items():
   self.assertEqual(c['state'],'PASS');self.assertEqual(c['completed_phase_count'],c['phase_count']);self.assertEqual(set(c['coverage_flags'])-{'short_price_ineligible'},set())
   models=defaultdict(lambda:dict.fromkeys(FIELDS,0));tiers=defaultdict(lambda:{'requests':0,'cost':Decimal(0)})
   for session in c['sessions']:
    self.assertNotIn(session['session_alias'],aliases);aliases.add(session['session_alias']);sums=dict.fromkeys(FIELDS,0)
    for request in session['requests']:
     u=request['usage'];self.assertTrue(all(type(u[k])is int and u[k]>=0 for k in FIELDS));self.assertLessEqual(u['cached_input_tokens'],u['input_tokens']);self.assertLessEqual(u['reasoning_output_tokens'],u['output_tokens']);self.assertEqual(u['total_tokens'],u['input_tokens']+u['output_tokens']);self.assertEqual(u['cache_write_input_tokens'],0)
     tier='long'if u['input_tokens']>prices['long_context_threshold_input_tokens']else'short';self.assertEqual(request['tier'],tier)
     rates=list(map(lambda x:Decimal(str(x)),prices['models'][request['model']][tier]));cost=((u['input_tokens']-u['cached_input_tokens'])*rates[0]+u['cached_input_tokens']*rates[1]+u['output_tokens']*rates[3])/1000000
     tiers[tier]['requests']+=1;tiers[tier]['cost']+=cost
     for k in FIELDS:sums[k]+=u[k];models[request['model']][k]+=u[k]
    self.assertEqual(sums,session['usage'])
   self.assertEqual(dict(models),c['models']);self.assertEqual({k:sum(m[k]for m in models.values())for k in FIELDS},c['tokens'])
   estimate=c['mixed_tier_api_equivalent'];self.assertEqual(sum(t['cost']for t in tiers.values()),Decimal(estimate['total']))
   for tier,t in tiers.items():
    self.assertEqual(t['requests'],estimate['by_tier'][tier]['requests']);self.assertEqual(t['cost'],Decimal(estimate['by_tier'][tier]['total']))
 def test_time_intervals_and_gaps_reconcile(self):
  usage=json.loads((ROOT/'usage.json').read_text())
  for c in usage['conditions'].values():
   t=c['timing'];self.assertIsNotNone(t['end_unix']);self.assertAlmostEqual(t['end_unix']-t['start_unix'],t['elapsed_seconds'],places=3)
   self.assertAlmostEqual(t['elapsed_seconds'],t['active_controller_elapsed_seconds']+t['recorded_interruption_gap_sum_seconds'],delta=.5)
   self.assertGreaterEqual(t['active_controller_elapsed_seconds']+.1,t['phase_elapsed_sum_seconds'])
 def test_frozen_source_projections_match_every_retained_byte(self):
  for condition in ('single','adaptive'):
   for stage,directory in [('initial','initial'),('final','apps')]:
    manifest=json.loads((ROOT/'source-manifests'/f'{condition}-{stage}.json').read_text());sources=ROOT/directory/condition
    self.assertEqual(manifest['source_file_count'],len(manifest['sources_sha256']))
    for name,expected in manifest['sources_sha256'].items():
     p=sources/name;self.assertFalse(p.is_symlink());self.assertNotEqual(p.name,'.auth-secret');self.assertNotEqual(p.suffix.lower(),'.secret');self.assertFalse(p.name.startswith('.env')and p.name!='.env.example')
     self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),expected,name)
    for name,expected in manifest.get('publication_notes_sha256',{}).items():
     self.assertNotIn(name,manifest['sources_sha256']);self.assertEqual(hashlib.sha256((sources/name).read_bytes()).hexdigest(),expected)
 def test_public_request_records_have_aliases_and_no_private_identifiers(self):
  text=(ROOT/'usage.json').read_text()
  for marker in ('Users/','private/tmp/','Applications/'):
   self.assertNotIn('/'+marker,text)
  import re
  self.assertIsNone(re.search(r'\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b',text))
 def test_matched_capture_and_blind_review_provenance(self):
  manifest=json.loads((ROOT/'capture-manifest.json').read_text());review=json.loads((ROOT/'visual-review.json').read_text());gallery=ROOT.parents[1]/'docs/benchmarks'/ROOT.name
  self.assertEqual(len(manifest['screenshots']),32);self.assertEqual(set(review['reviewed_paths']),{s['path']for s in manifest['screenshots']})
  self.assertTrue(manifest['source_reverified_after_render']);self.assertTrue(manifest['capture_processes_and_databases_cleaned'])
  combinations=set()
  for s in manifest['screenshots']:
   combinations.add((s['condition'],s['state'],s['viewport']['width']));self.assertEqual(hashlib.sha256((gallery/s['path']).read_bytes()).hexdigest(),s['sha256']);self.assertFalse(s['unfinished_loading']);self.assertEqual(s['broken_image_count'],0)
  self.assertEqual(len(combinations),32)
  for subject in review['subjects'].values():
   self.assertEqual(len(subject['scores']),5);self.assertEqual(sum(subject['scores'].values()),subject['total'])
   for score in subject['scores'].values():self.assertTrue(0<=score<=5);self.assertEqual(score*2,int(score*2))
 def test_summary_matches_independent_evidence(self):
  result=json.loads((ROOT/'results.json').read_text());usage=json.loads((ROOT/'usage.json').read_text());audits=json.loads((ROOT/'app-audits.json').read_text());iterations=json.loads((ROOT/'iteration-review.json').read_text());review=json.loads((ROOT/'visual-review.json').read_text())
  for name,c in result['conditions'].items():
   self.assertEqual(c['state'],'PASS');self.assertEqual(audits['conditions'][name]['state'],'PASS');self.assertTrue(audits['conditions'][name]['accepted_source_equals_final'])
   for k in ('input_tokens','cached_input_tokens','output_tokens'):self.assertEqual(int(c[k].replace(',','')),usage['conditions'][name]['tokens'][k])
   self.assertEqual(c['product_fix_cycles'],iterations['conditions'][name]['category_counts']['confirmed_product_correction_recheck_cycles'])
   label=review['mapping_revealed_after_review'][name];self.assertEqual(float(c['visual_score'].split('/')[0]),review['subjects'][label]['total'])
if __name__=='__main__':unittest.main()
