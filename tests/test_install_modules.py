from __future__ import annotations
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('modular_installer', ROOT / 'scripts/install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallerModuleTests(unittest.TestCase):
    def test_each_selection_routes_only_its_optional_policy_and_preserves_local_text(self):
        for selected in (['code'], ['visuals'], ['swarms'], ['code', 'visuals', 'swarms']):
            with self.subTest(selected=selected):
                block = installer.delegation_block(ROOT, selected)
                self.assertEqual('Whole-project risk alone' in block, 'swarms' in selected)
                self.assertEqual('Quality Visuals:' in block, 'visuals' in selected)
                self.assertIn('Installed defaults: ' + ', '.join(selected), block)
                with tempfile.TemporaryDirectory() as temp:
                    target = Path(temp) / 'AGENTS.md'
                    target.write_text('# Local instructions\nKeep this custom rule.\n')
                    content = installer.merged_global(target, block, selected)
                    target.write_text(content)
                    self.assertEqual(content, installer.merged_global(target, block, selected))
                    self.assertIn('Keep this custom rule.', content)
                    self.assertEqual(content.count(installer.GLOBAL_START), 1)
                    self.assertEqual(content.count(installer.DELEGATION_START), 1)
                    if selected != ['code', 'visuals', 'swarms']:
                        self.assertIn('init . --modules ' + ','.join(selected), content)

    def test_invalid_installer_selection_is_clean_and_does_not_write(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / 'home'
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/install.py'),
                                     '--home', str(home), '--modules', 'visuals,unknown'],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertNotIn('Traceback', result.stderr)
            self.assertFalse(home.exists())

    def test_visual_only_install_delivers_review_reference_and_selected_bootstrap(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / 'home'
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/install.py'),
                                     '--home', str(home), '--modules', 'visuals'],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for relative in ('.codex/AGENTS.md', '.claude/CLAUDE.md'):
                content = (home / relative).read_text()
                self.assertIn('init . --modules visuals', content)
                self.assertIn('Quality Visuals:', content)
                self.assertNotIn('Whole-project risk alone', content)
            self.assertTrue((home / '.codex/skills/audit-code-change/references/VISUAL_AUDIT.md').is_file())
            self.assertTrue((home / '.local/bin/quality-code').is_symlink())


if __name__ == '__main__':
    unittest.main()
