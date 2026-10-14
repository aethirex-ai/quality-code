"""Verify documented migrate/seed/production start on a fresh isolated DB."""
import json, os, socket, sqlite3, subprocess, tempfile, time, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 with tempfile.TemporaryDirectory(prefix='serviceflow-fresh-') as temporary:
  database=Path(temporary)/'fresh.sqlite'
  with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
  env={**os.environ,'DATABASE_PATH':str(database),'PORTAL_PORT':str(port),'AI_API_KEY':'','AI_API_URL':'','AI_MODEL':''}
  env.pop('BETTER_AUTH_URL',None);env.pop('BETTER_AUTH_SECRET',None)
  for command in [['npm','run','migrate'],['npm','run','seed'],['npm','run','seed']]:
   subprocess.run(command,cwd=ROOT,env=env,check=True,capture_output=True,text=True)
  db=sqlite3.connect(database)
  for table,expected in [('user',4),('services',4),('requests',8),('schema_migrations',2)]:
   count=db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0];assert count==expected,(table,count)
  assert db.execute('SELECT COUNT(DISTINCT customerId) FROM requests').fetchone()[0]==2
  db.close();assert Path(str(database)+'.secret').stat().st_mode&0o777==0o600
  # Start the exact underlying benchmark command, own only this subprocess.
  server=subprocess.Popen(['node','--import','tsx','src/server/index.ts','--production'],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  try:
   base=f'http://127.0.0.1:{port}'
   for attempt in range(100):
    if server.poll() is not None:raise AssertionError('Fresh server failed to start')
    try:
     with urllib.request.urlopen(base+'/api/me',timeout=1) as response:assert json.load(response)=={'user':None}
     break
    except OSError:time.sleep(.1)
   else:raise AssertionError('Fresh server readiness timed out')
   with urllib.request.urlopen(base+'/api/services',timeout=3) as response:assert len(json.load(response)['services'])==4
   with urllib.request.urlopen(base+'/request',timeout=3) as response:
    assert response.status==200 and '<div id="root"></div>' in response.read().decode()
    assert "script-src 'self'" in response.headers['Content-Security-Policy']
   print('PASS fresh setup: migrations, repeatable seed, 4 users, 4 services, 8 requests, persisted signing secret, production loopback server + SPA + CSP.')
  finally:
   server.terminate()
   try:server.communicate(timeout=10)
   except subprocess.TimeoutExpired:server.kill();server.communicate()
if __name__=='__main__':main()
