import http.client
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CREDENTIALS = {
    'c1': ('alex@harbor.test', 'HarborDemo!42'),
    'c2': ('sam@northline.test', 'NorthDemo!42'),
    's1': ('studio@aethdesign.test', 'StudioDemo!42'),
}

class LocalServer:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory(prefix='atelier-test-')
        self.db = Path(self.temp.name) / 'fixture.sqlite3'
        self.port = 0
        self.proc = None
        self.logs = open(Path(self.temp.name) / 'server.log', 'w+')
        self.start()

    def start(self):
        self.proc = subprocess.Popen([sys.executable, str(ROOT / 'server.py'), '--host', '127.0.0.1', '--port', str(self.port), '--db', str(self.db)], cwd=ROOT, stdout=subprocess.PIPE, stderr=self.logs, text=True)
        ready, _, _ = select.select([self.proc.stdout], [], [], 15)
        if not ready:
            self.stop()
            raise RuntimeError('Server did not become ready')
        line = self.proc.stdout.readline()
        if not line:
            self.logs.seek(0)
            raise RuntimeError('Server failed: ' + self.logs.read()[-2000:])
        result = json.loads(line)
        assert result['ready'] is True
        self.port = result['port']

    def stop(self):
        if self.proc:
            self.proc.terminate()
            self.proc.wait(timeout=10)
            self.proc.stdout.close()
            self.proc = None

    def restart(self):
        self.stop()
        self.start()

    def close(self):
        self.stop()
        self.logs.close()
        self.temp.cleanup()

    def request(self, path, body=None, cookie=None, method=None, headers=None, raw=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=15)
        request_headers = {}
        if cookie: request_headers['Cookie'] = cookie
        if body is not None or raw is not None: request_headers['Content-Type'] = 'application/json'
        request_headers.update(headers or {})
        data = raw if raw is not None else json.dumps(body) if body is not None else None
        conn.request(method or ('POST' if data is not None else 'GET'), path, data, request_headers)
        response = conn.getresponse()
        payload = response.read().decode()
        result = (response.status, json.loads(payload) if response.getheader('Content-Type', '').startswith('application/json') else payload, dict(response.getheaders()))
        conn.close()
        return result

    def login(self, ident):
        email, password = CREDENTIALS[ident]
        status, body, headers = self.request('/api/login', {'email': email, 'password': password})
        assert status == 200, (status, body)
        return headers['Set-Cookie'].split(';')[0]
