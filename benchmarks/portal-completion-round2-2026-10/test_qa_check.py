import unittest,tempfile,json,io,sys
from pathlib import Path
from unittest.mock import patch
from contextlib import redirect_stdout
import qa_check
class Recorder(unittest.TestCase):
 def test_launch_error_and_followup_success_both_retained(self):
  with tempfile.TemporaryDirectory() as d,patch.object(qa_check,'ROOT',Path(d)),redirect_stdout(io.StringIO()):
   self.assertEqual(qa_check.run('backend','launch','verification','tool-launch',['/definitely/missing/command']),127)
   self.assertEqual(qa_check.run('backend','launch','recheck','tool-launch',[sys.executable,'-c','print("ok")']),0)
   rows=[json.loads(x) for x in (Path(d)/'backend/check-runs.jsonl').read_text().splitlines()];self.assertEqual([r['exit_code'] for r in rows],[127,0]);self.assertIn('FileNotFoundError',rows[0]['stderr'])
 def test_scaffold_and_negative_exits_preserve_phase_and_owner(self):
  with tempfile.TemporaryDirectory() as d,patch.object(qa_check,'ROOT',Path(d)),redirect_stdout(io.StringIO()):
   qa_check.run('frontend','scaffold','initial',None,[sys.executable,'-c','raise SystemExit(1)']);row=json.loads((Path(d)/'frontend/check-runs.jsonl').read_text());self.assertEqual(row['phase'],'initial');self.assertEqual(row['exit_code'],1)
 def test_no_symlink_log_or_invalid_owner(self):
  with tempfile.TemporaryDirectory() as d,patch.object(qa_check,'ROOT',Path(d)):
   root=Path(d);(root/'integration').mkdir();(root/'integration/check-runs.jsonl').symlink_to(root/'other')
   with self.assertRaises(ValueError):qa_check.run('integration','test','verification',None,[sys.executable,'-c','pass'])
   with self.assertRaises(ValueError):qa_check.run('../escape','test','verification',None,['true'])
