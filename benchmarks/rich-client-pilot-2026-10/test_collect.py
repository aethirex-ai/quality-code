import tempfile,unittest,json
from pathlib import Path
from collect import iteration_summary,freeze_output
class Iterations(unittest.TestCase):
 def test_initial_failures_and_repeated_failures_do_not_inflate_cycles(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'lighting').mkdir()
   rows=[{'check_id':'routes','phase':'initial','exit_code':1},{'check_id':'math','phase':'verification','exit_code':1},{'check_id':'math','phase':'recheck','exit_code':1},{'check_id':'math','phase':'recheck','exit_code':0},{'check_id':'math','phase':'recheck','exit_code':0}]
   (root/'lighting/check-runs.jsonl').write_text('\n'.join(map(json.dumps,rows)))
   (root/'lighting/issues.jsonl').write_text('\n'.join(map(json.dumps,[{'id':'qty','status':'open'},{'id':'qty','status':'fixed'}])))
   r=iteration_summary(root)['owners'];self.assertEqual(r['lighting']['initial_scaffold_nonzero_exits'],1);self.assertEqual(r['lighting']['verification_nonzero_exits'],2);self.assertEqual(len(r['lighting']['observed_check_recovery_sequences']),1);self.assertEqual(r['lighting']['distinct_reported_issue_ids'],1);self.assertIsNone(r['expedition']['recorded_check_runs']);self.assertFalse(r['expedition']['issue_history_present'])
 def test_malformed_history_is_not_silently_counted(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'lighting').mkdir();(root/'lighting/check-runs.jsonl').write_text('not JSON')
   with self.assertRaises(json.JSONDecodeError):iteration_summary(root)

class FrozenOutput(unittest.TestCase):
 def test_recollection_preserves_original_and_rejects_changed_output(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'site').mkdir();asset=root/'site/index.html';asset.write_text('original')
   freeze_output(root);before=(root/'frozen-output-hashes.json').read_bytes();freeze_output(root)
   self.assertEqual((root/'frozen-output-hashes.json').read_bytes(),before)
   asset.write_text('changed after grading')
   with self.assertRaisesRegex(ValueError,'Frozen output changed'):freeze_output(root)
   self.assertEqual((root/'frozen-output-hashes.json').read_bytes(),before)
