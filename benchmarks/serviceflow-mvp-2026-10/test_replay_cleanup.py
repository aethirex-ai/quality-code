"""Post-trial portability guard: never waive denial for a live/unknown group."""
import unittest,signal
from types import SimpleNamespace
from unittest.mock import Mock,patch
import run
class ReplayCleanup(unittest.TestCase):
 def proc(self):return SimpleNamespace(pid=123456,poll=Mock(return_value=0),wait=Mock(return_value=-signal.SIGTERM))
 def denied(self,p,stdout,code=0):
  return patch.object(run.os,'killpg',side_effect=[None,PermissionError('denied')]),patch.object(run.subprocess,'run',return_value=SimpleNamespace(returncode=code,stdout=stdout))
 def test_zombie_only_group_during_zero_grace_is_reaped(self):
  p=self.proc();a,b=self.denied(p,'123456 Z+\n999999 S\n')
  with a,b:run.terminate_group(p,grace=0)
  p.wait.assert_called_once()
 def test_live_owned_group_permission_denial_remains_failure(self):
  p=self.proc();a,b=self.denied(p,'123456 S\n')
  with a,b,self.assertRaises(PermissionError):run.terminate_group(p,grace=0)
  p.wait.assert_not_called()
 def test_unknown_group_inspection_remains_failure(self):
  p=self.proc();a,b=self.denied(p,'',code=1)
  with a,b,self.assertRaises(PermissionError):run.terminate_group(p,grace=0)
 def test_empty_or_malformed_successful_inventory_remains_failure(self):
  for stdout in ['', '123456\n']:
   with self.subTest(stdout=stdout):
    p=self.proc();a,b=self.denied(p,stdout)
    with a,b,self.assertRaises(PermissionError):run.terminate_group(p,grace=0)
if __name__=='__main__':unittest.main()
