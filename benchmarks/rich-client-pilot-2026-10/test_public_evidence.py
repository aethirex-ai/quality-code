"""Public evidence must reconcile independently and retain measured asset bytes."""
import unittest,json,hashlib
from pathlib import Path
from decimal import Decimal
ROOT=Path(__file__).resolve().parent
class PublicEvidence(unittest.TestCase):
 def test_served_outputs_retain_frozen_bytes(self):
  served=ROOT.parents[1]/'docs/benchmarks/rich-client-pilot-2026-10'
  for condition in ['single','swarm']:
   hashes=json.loads((ROOT/f'{condition}-frozen-output-hashes.json').read_text())
   files=[p for p in (served/condition).rglob('*') if p.is_file()]
   self.assertEqual(sum(p.suffix=='.html' for p in files),7)
   for p in files:
    rel=str(p.relative_to(served/condition));self.assertIn(rel,hashes);self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),hashes[rel],rel)
 def test_price_components_and_image_originals(self):
  result=json.loads((ROOT/'results.json').read_text());rates=json.loads((ROOT/'prices.json').read_text())['models']
  for condition,value in result['conditions'].items():
   total=Decimal(0)
   for model,t in value['models'].items():
    a,b,_,c=map(lambda x:Decimal(str(x)),rates[model]['short']);total+=((t['input_tokens']-t['cached_input_tokens'])*a+t['cached_input_tokens']*b+t['output_tokens']*c)/1000000
   self.assertEqual(total,Decimal(str(value['standard_short_estimated_usd'])))
   self.assertEqual(total,sum(Decimal(v) for v in value['cost_components_usd']['total'].values()))
   evidence=json.loads((ROOT/f'{condition}-image-transcript-supplement.json').read_text());self.assertEqual(evidence['verified_successes'],4)
   for j in evidence['jobs']:
    asset=ROOT.parents[1]/'docs/benchmarks/rich-client-pilot-2026-10'/condition/j['delivered_original'];self.assertEqual(hashlib.sha256(asset.read_bytes()).hexdigest(),j['sha256']);self.assertEqual(j['matching_successful_return_count'],1)
 def test_mime_amendment_is_only_hosting_change_and_scores_retained(self):
  original=(ROOT/'evaluator.mjs').read_text();corrected=(ROOT/'evaluator-mime-corrected.mjs').read_text();self.assertEqual(corrected,original.replace("'.js':'text/javascript'","'.js':'text/javascript','.mjs':'text/javascript'"))
  amendment=json.loads((ROOT/'evaluation-amendment.json').read_text());self.assertEqual(hashlib.sha256(original.encode()).hexdigest(),amendment['original_sha256']);self.assertEqual(hashlib.sha256(corrected.encode()).hexdigest(),amendment['corrected_sha256'])
  for c in ['single','swarm']:
   for tag in ['original','mime-corrected']:
    d=json.loads((ROOT/f'{c}-objective-{tag}.json').read_text());self.assertEqual(d['total'],142);self.assertEqual(len(d['results']),142);self.assertEqual(sum(r['passed'] for r in d['results']),d['passed'])
