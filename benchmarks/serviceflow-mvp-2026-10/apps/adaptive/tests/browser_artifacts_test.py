"""Browser verification must initialize ignored artifacts from clean source."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


class BrowserArtifactsTest(unittest.TestCase):
    def test_render_initializes_and_reuses_missing_artifact_directories(self):
        source = Path(__file__).resolve().parents[1] / 'scripts' / 'browser_checks.py'
        spec = importlib.util.spec_from_file_location('browser_checks_artifact_regression', source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory(prefix='serviceflow-browser-artifacts-') as temporary:
            root = Path(temporary)
            self.assertFalse((root / 'scripts' / 'browser-actions').exists())
            preview = {'ok': True, 'excerpt': 'Synthetic ready page', 'horizontalOverflow': False, 'errors': [], 'blockedRequests': [], 'actionResults': [{'ok': True}], 'screenshot': 'mocked-preview.png'}

            def fake_preview(command, **kwargs):
                # The generated file must exist before contacting the browser bridge.
                action_path = root / command[command.index('--actions-file') + 1]
                self.assertTrue(action_path.is_file())
                self.assertEqual(kwargs['cwd'], root)
                return SimpleNamespace(returncode=0, stdout=json.dumps(preview), stderr='')

            with patch.object(module, 'ROOT', root), patch.object(module.subprocess, 'run', side_effect=fake_preview):
                first = [{'op': 'click', 'selector': 'h1'}]
                module.render('clean-source', '/', 375, first, ['Synthetic ready page'])
                path = root / 'scripts' / 'browser-actions' / 'clean-source.json'
                self.assertEqual(json.loads(path.read_text()), first)
                second = [{'op': 'click', 'selector': 'h2'}]
                module.render('clean-source', '/', 375, second, ['Synthetic ready page'])
                self.assertEqual(json.loads(path.read_text()), second)
                self.assertEqual(len(json.loads((root / 'evidence' / 'browser-results.json').read_text())), 2)


if __name__ == '__main__':
    unittest.main()
