import unittest,tempfile,importlib.util,json,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('qa_check',Path(__file__).parent/'fixture/qa_check.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Checks(unittest.TestCase):
 def test_failed_check_preserved_before_recheck(self):
  with tempfile.TemporaryDirectory() as d:
   original=m.ROOT;m.ROOT=Path(d)
   try:
    self.assertEqual(m.run('lighting','math','verification','sum',[sys.executable,'-c','import sys;print("bad sum");sys.exit(1)']),1)
    self.assertEqual(m.run('lighting','math','recheck','sum',[sys.executable,'-c','print("fixed")']),0)
    rows=[json.loads(s) for s in (m.ROOT/'lighting/check-runs.jsonl').read_text().splitlines()];self.assertEqual([r['exit_code'] for r in rows],[1,0]);self.assertEqual([r['issue_id'] for r in rows],['sum','sum']);self.assertEqual(rows[0]['stdout'],'bad sum\n')
   finally:m.ROOT=original
 def test_invalid_ownership_does_not_execute(self):
  with self.assertRaises(ValueError):m.run('../other','math','verification',None,[sys.executable,'-c','raise Exception()'])
  with self.assertRaises(ValueError):m.run('lighting','../escape','verification',None,[sys.executable,'-c','raise Exception()'])
