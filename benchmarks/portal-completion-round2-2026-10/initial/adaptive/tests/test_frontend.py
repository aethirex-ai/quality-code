"""Dependency-free JS controller tests against the real HTTP/SQLite server."""
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
import server

class FrontendIntegrationTests(unittest.TestCase):
    def test_frontend_integrated_state_and_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            app = server.WorkspaceServer('127.0.0.1', 0, str(Path(directory)/'frontend.sqlite3'))
            thread = threading.Thread(target=app.serve_forever, daemon=True)
            thread.start()
            try:
                result = subprocess.run(['node', 'tests/frontend.mjs', 'http://127.0.0.1:'+str(app.server_port)], cwd=Path(__file__).resolve().parents[1], text=True, capture_output=True, timeout=45)
                print(result.stdout)
                self.assertEqual(result.returncode, 0, result.stdout+'\n'+result.stderr)
            finally:
                app.shutdown(); app.server_close(); thread.join(timeout=2)
