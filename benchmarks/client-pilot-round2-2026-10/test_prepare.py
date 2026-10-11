"""Offline replay checks; never starts a native model or image provider."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parent

class ReplayPreparation(unittest.TestCase):
    def test_fresh_isolated_workspaces_and_recorded_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory) / 'replay'
            command = [sys.executable, str(SOURCE / 'prepare.py'), '--work-dir', str(work),
                       '--node', '/test/runtime/node', '--playwright-import', '/test/runtime/playwright.mjs']
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            for protocol_name, fixture in [('protocol.json', 'fixture'), ('error-protocol.json', 'error-fixture')]:
                original = json.loads((SOURCE / protocol_name).read_text())
                replay = json.loads((work / protocol_name).read_text())
                for key in ('fixture_sha256', 'evaluator_sha256', 'runner_sha256'):
                    self.assertEqual(replay['recorded_' + key], original[key])
                self.assertEqual(replay['fixture_sha256'], {
                    str(p.relative_to(work / fixture)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted((work / fixture).rglob('*')) if p.is_file()})
            brief = (work / 'fixture/BRIEF.md').read_text()
            self.assertIn('Node: /test/runtime/node.', brief)
            self.assertIn('Playwright: /test/runtime/playwright.mjs.', brief)
            self.assertNotIn('BENCHMARK_', brief)
            for run, fixture in [('runs', 'fixture'), ('error-runs', 'error-fixture')]:
                for condition in ('single', 'swarm'):
                    site = work / run / condition / 'site'
                    self.assertTrue((site / '.git').is_dir())
                    self.assertFalse((site / 'error-judge').exists())
                    status = subprocess.run(['git', 'status', '--porcelain'], cwd=site, capture_output=True, text=True, check=True)
                    self.assertEqual(status.stdout, '')
                    for relative, digest in json.loads((work / ('protocol.json' if run == 'runs' else 'error-protocol.json')).read_text())['fixture_sha256'].items():
                        self.assertEqual(hashlib.sha256((site / relative).read_bytes()).hexdigest(), digest)
            marker = work / 'preserve-me'; marker.write_text('untouched')
            refused = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn('Refusing existing replay directory', refused.stderr)
            self.assertEqual(marker.read_text(), 'untouched')

if __name__ == '__main__':
    unittest.main()
