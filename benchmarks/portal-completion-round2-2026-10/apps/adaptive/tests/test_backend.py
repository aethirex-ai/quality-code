"""Real loopback HTTP regressions against isolated SQLite databases."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from unittest.mock import patch
import http.client
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest

import server


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.temp.name) / 'workspace.sqlite3')
        self.start()

    def start(self):
        self.app = server.WorkspaceServer('127.0.0.1', 0, self.db)
        self.port = self.app.server_port
        self.thread = threading.Thread(target=self.app.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        self.app.shutdown(); self.app.server_close(); self.thread.join(timeout=2)

    def tearDown(self):
        self.stop(); self.temp.cleanup()

    def request(self, method, path, body=None, cookie=None, headers=None, raw=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=10)
        request_headers = {'Content-Type':'application/json'}
        if cookie: request_headers['Cookie'] = cookie
        if headers: request_headers.update(headers)
        payload = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        connection.request(method, path, payload, request_headers)
        response = connection.getresponse()
        data = response.read()
        result = (response.status, json.loads(data) if response.getheader('Content-Type','').startswith('application/json') else data, dict(response.getheaders()))
        connection.close()
        return result

    def login(self, role='client'):
        email, password = {'client':('alex@harbor.test','HarborDemo!42'), 'other':('sam@northline.test','NorthDemo!42'), 'staff':('studio@aethdesign.test','StudioDemo!42')}[role]
        status, data, headers = self.request('POST','/api/login',{'email':email,'password':password})
        self.assertEqual(status,200)
        self.assertEqual(data['user']['role'], 'staff' if role=='staff' else 'client')
        return headers['Set-Cookie'].split(';')[0]

    def get(self, path, cookie):
        status, data, _ = self.request('GET',path,cookie=cookie)
        self.assertEqual(status,200)
        return data

    def counts(self, pid='p1'):
        with sqlite3.connect(self.db) as conn:
            return tuple(conn.execute('SELECT COUNT(*) FROM '+table+' WHERE project_id=?',(pid,)).fetchone()[0] for table in ('revisions','decisions','comments','events'))

    def test_auth_visibility_and_no_secret_data(self):
        self.assertEqual(self.request('GET','/api/projects')[0],401)
        self.assertEqual(self.request('POST','/api/login',{'email':'alex@harbor.test','password':'bad'})[0],401)
        for role, ids in [('client',['p1','p2']),('other',['p3']),('staff',['p1','p2','p3'])]:
            cookie=self.login(role)
            projects=self.get('/api/projects',cookie)['projects']
            self.assertEqual([p['id'] for p in projects],ids)
            self.assertNotIn('verifier',json.dumps(projects))
            self.assertNotIn('password',json.dumps(self.get('/api/me',cookie)))
        client=self.login()
        self.assertEqual(self.request('GET','/api/projects/p3',cookie=client)[0],404)
        self.assertEqual(self.request('GET','/api/projects/missing',cookie=client)[0],404)
        for section in ['comments','revisions','activity']:
            self.assertEqual(self.request('GET','/api/projects/p3/'+section,cookie=client)[0],404)
        self.assertEqual(self.request('GET','/api/projects',cookie='atelier_session=c1; role=staff')[0],401)

    def test_seed_exact_narrative_money_and_hashes(self):
        cookie=self.login('staff')
        for pid, cents, status, current in [('p1',420000,'awaiting_review',1),('p2',780000,'approved',2),('p3',360000,'awaiting_review',1)]:
            p=self.get('/api/projects/'+pid,cookie)['project']
            self.assertEqual((p['budgetCents'],p['status'],p['currentRevision']),(cents,status,current))
            self.assertGreater(len(p['brief']),50)
            self.assertGreaterEqual(len(p['deliverables']),3)
            self.assertGreaterEqual(len(p['timeline']),3)
            self.assertEqual(len(self.get('/api/projects/'+pid+'/comments',cookie)['comments']),1)
            numbers=[r['number'] for r in self.get('/api/projects/'+pid+'/revisions',cookie)['revisions']]
            self.assertEqual(numbers,list(range(1,current+1)))
        with sqlite3.connect(self.db) as conn:
            rows=conn.execute('SELECT salt,verifier FROM users').fetchall()
            self.assertEqual(len({r[0] for r in rows}),3)
            self.assertTrue(all(len(r[0])==32 and len(r[1])==64 for r in rows))
            self.assertNotIn(b'HarborDemo!42',Path(self.db).read_bytes())

    def test_session_and_mutation_survive_restart_logout_invalidates(self):
        cookie=self.login()
        self.assertEqual(self.request('POST','/api/projects/p1/comments',{'body':'Persisted across restart ✨'},cookie)[0],201)
        self.stop(); self.start()
        self.assertEqual(self.get('/api/me',cookie)['user']['id'],'c1')
        self.assertEqual(self.get('/api/projects/p1/comments',cookie)['comments'][-1]['body'],'Persisted across restart ✨')
        status, _, headers=self.request('POST','/api/logout',{},cookie)
        self.assertEqual(status,200)
        self.assertIn('Max-Age=0',headers['Set-Cookie'])
        self.assertEqual(self.request('GET','/api/me',cookie=cookie)[0],401)

    def test_cookie_attributes_and_origin_json_guards(self):
        _,_,headers=self.request('POST','/api/login',{'email':'alex@harbor.test','password':'HarborDemo!42'})
        for part in ('atelier_session=', 'Path=/', 'HttpOnly', 'SameSite=Lax'): self.assertIn(part,headers['Set-Cookie'])
        cookie=headers['Set-Cookie'].split(';')[0]
        before=self.counts()
        for origin in ('https://evil.test','null','http://localhost:'+str(self.port),'http://127.0.0.1:9999','http://127.0.0.1:'+str(self.port)+'/bad'):
            self.assertEqual(self.request('POST','/api/projects/p1/comments',{'body':'Denied'},cookie,{'Origin':origin})[0],403)
        self.assertEqual(self.request('POST','/api/projects/p1/comments',{'body':'Denied'},cookie,{'Content-Type':'text/plain'})[0],415)
        self.assertEqual(self.counts(),before)
        self.assertEqual(self.request('POST','/api/projects/p1/comments',{'body':'Same origin'},cookie,{'Origin':'http://127.0.0.1:'+str(self.port)})[0],201)

    def test_decision_duplicate_and_new_revision_are_atomic(self):
        client=self.login(); staff=self.login('staff'); before=self.counts()
        result=self.request('POST','/api/projects/p1/decision',{'revision':1,'decision':'request_changes','note':' Add checkout detail '},client)
        self.assertEqual(result[0],200)
        self.assertEqual(result[1]['project']['status'],'changes_requested')
        self.assertEqual(result[1]['project']['budgetCents'],420000)
        self.assertEqual(self.counts(),(before[0],before[1]+1,before[2],before[3]+1))
        for decision in ('approve','request_changes'):
            self.assertEqual(self.request('POST','/api/projects/p1/decision',{'revision':1,'decision':decision,'note':'Repeated'},client)[0],409)
        self.assertEqual(self.request('POST','/api/projects/p1/revisions',{'expectedRevision':1,'title':'Checkout refinement','summary':'Detailed mobile checkout and recovery states.'},staff)[0],201)
        self.assertEqual(self.get('/api/projects/p1',client)['project']['status'],'awaiting_review')
        self.assertEqual(self.request('POST','/api/projects/p1/decision',{'revision':1,'decision':'approve','note':''},client)[0],409)
        self.assertEqual(self.request('POST','/api/projects/p1/decision',{'revision':2,'decision':'approve','note':''},client)[0],200)
        with sqlite3.connect(self.db) as conn:
            self.assertEqual(conn.execute('SELECT revision,decision,note FROM decisions WHERE project_id=? ORDER BY revision',('p1',)).fetchall(),[(1,'request_changes','Add checkout detail'),(2,'approve','')])
        events=self.get('/api/projects/p1/activity',client)['events']
        self.assertEqual([e['type'] for e in events][-3:],['decision_submitted','revision_published','decision_submitted'])
        self.assertEqual(events[-1]['actor']['id'],'c1')

    def test_concurrent_publish_exactly_one_commit(self):
        cookie=self.login('staff'); before=self.counts()
        def publish(_):
            return self.request('POST','/api/projects/p1/revisions',{'expectedRevision':1,'title':'Concurrent revision','summary':'One canonical revision.'},cookie)[0]
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(publish,range(2))),[201,409])
        after=self.counts()
        self.assertEqual(after,(before[0]+1,before[1],before[2],before[3]+1))
        self.assertEqual(self.get('/api/projects/p1',cookie)['project']['currentRevision'],2)

    def test_concurrent_decisions_exactly_one_commit(self):
        cookie=self.login(); before=self.counts()
        def decide(decision):
            return self.request('POST','/api/projects/p1/decision',{'revision':1,'decision':decision,'note':'Concurrent review'},cookie)[0]
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(decide,['approve','request_changes'])),[200,409])
        self.assertEqual(self.counts(),(before[0],before[1]+1,before[2],before[3]+1))

    def interleaved_mutation_response(self, kind):
        client = self.login(); staff = self.login('staff')
        committed = threading.Event(); release = threading.Event()
        original_connection = server.connection
        hold_lock = threading.Lock(); held = False

        class ScheduledConnection:
            def __init__(self, conn): self.conn = conn; self.target_write = False
            def __getattr__(self, name): return getattr(self.conn, name)
            def execute(self, sql, parameters=()):
                if kind == 'decision' and sql.startswith('UPDATE projects SET status='):
                    self.target_write = True
                if kind == 'publication' and sql.startswith('UPDATE projects SET current_revision=') and parameters[0] == 2:
                    self.target_write = True
                return self.conn.execute(sql, parameters)
            def commit(self):
                nonlocal held
                self.conn.commit()
                with hold_lock:
                    pause = self.target_write and not held
                    if pause: held = True
                if pause:
                    committed.set()
                    if not release.wait(8): raise RuntimeError('Scheduled response was not released')

        @contextmanager
        def scheduled_connection(db):
            with original_connection(db) as conn: yield ScheduledConnection(conn)

        before = self.counts()
        with patch.object(server, 'connection', scheduled_connection), ThreadPoolExecutor(max_workers=1) as pool:
            if kind == 'decision':
                first = pool.submit(self.request, 'POST', '/api/projects/p1/decision', {'revision':1,'decision':'approve','note':''}, client)
            else:
                first = pool.submit(self.request, 'POST', '/api/projects/p1/revisions', {'expectedRevision':1,'title':'Revision two','summary':'First publication snapshot.'}, staff)
            try:
                self.assertTrue(committed.wait(5), 'First write must commit before the second write')
                expected = 1 if kind == 'decision' else 2
                second = self.request('POST', '/api/projects/p1/revisions', {'expectedRevision':expected,'title':'Later publication','summary':'Independent transaction completed before first response.'}, staff)
                self.assertEqual(second[0], 201)
            finally: release.set()
            response = first.result(timeout=5)
        self.assertEqual(response[0], 200 if kind == 'decision' else 201)
        result = response[1]['project']
        self.assertEqual(result['currentRevision'], 1 if kind == 'decision' else 2)
        self.assertEqual(result['status'], 'approved' if kind == 'decision' else 'awaiting_review')
        self.assertEqual(result['budgetCents'], 420000)
        event = response[1]['event']
        self.assertEqual(event['type'], 'decision_submitted' if kind == 'decision' else 'revision_published')
        self.assertEqual(event['revision'], result['currentRevision'])
        events = self.get('/api/projects/p1/activity', client)['events']
        self.assertEqual([stored for stored in events if stored['id'] == event['id']], [event])
        if kind == 'publication': self.assertEqual(response[1]['revision']['number'], result['currentRevision'])
        final = self.get('/api/projects/p1', client)['project']
        self.assertEqual(final['currentRevision'], 2 if kind == 'decision' else 3)
        self.assertEqual(final['status'], 'awaiting_review')
        after = self.counts()
        self.assertEqual(after[3], before[3] + 2)
        self.assertEqual(after[0], before[0] + (1 if kind == 'decision' else 2))
        self.assertEqual(after[1], before[1] + (1 if kind == 'decision' else 0))

    def test_decision_response_snapshot_survives_later_publication(self):
        self.interleaved_mutation_response('decision')

    def test_publication_response_snapshot_survives_later_publication(self):
        self.interleaved_mutation_response('publication')

    def test_role_boundaries_and_forged_authorship(self):
        client=self.login(); staff=self.login('staff'); other=self.login('other'); before=self.counts()
        self.assertEqual(self.request('POST','/api/projects/p1/revisions',{'expectedRevision':1,'title':'Forged','summary':'Denied','role':'staff'},client)[0],403)
        self.assertEqual(self.request('POST','/api/projects/p1/decision',{'revision':1,'decision':'approve','note':''},staff)[0],403)
        self.assertEqual(self.request('POST','/api/projects/p1/comments',{'body':'Denied'},other)[0],404)
        self.assertEqual(self.counts(),before)
        result=self.request('POST','/api/projects/p1/comments',{'body':' <img src=x onerror=alert(1)> ✨ ','author':{'id':'s1','role':'staff'}},client)
        self.assertEqual(result[0],201)
        self.assertEqual(result[1]['comment']['author']['id'],'c1')
        self.assertEqual(result[1]['comment']['body'],'<img src=x onerror=alert(1)> ✨')
        self.assertEqual(self.counts(),(before[0],before[1],before[2]+1,before[3]+1))

    def test_invalid_json_and_field_boundaries_no_partial_mutations(self):
        client=self.login(); staff=self.login('staff'); before=self.counts()
        for raw in (b'{',b'[]',b'null',b'{"body":NaN}',b'\xff',b'{"body":"\\ud800"}',b'{"body":"ok","extra":{"\\udfff":"bad"}}'):
            self.assertEqual(self.request('POST','/api/projects/p1/comments',cookie=client,raw=raw)[0],400,raw)
        for body in ('', '   ', 'x'*2001, None, 5, [], '\udfff'):
            self.assertEqual(self.request('POST','/api/projects/p1/comments',{'body':body},client)[0],400)
        for number in (0,-1,True,'1',1.0,None):
            self.assertEqual(self.request('POST','/api/projects/p1/revisions',{'expectedRevision':number,'title':'Title','summary':'Summary'},staff)[0],400)
            self.assertEqual(self.request('POST','/api/projects/p1/decision',{'revision':number,'decision':'approve','note':''},client)[0],400)
        for data in ({'revision':1,'decision':'request_changes','note':'  '},{'revision':1,'decision':'invalid','note':''},{'revision':1,'decision':'approve','note':'x'*2001}):
            self.assertEqual(self.request('POST','/api/projects/p1/decision',data,client)[0],400)
        for key in ('title','summary'):
            payload={'expectedRevision':1,'title':'Title','summary':'Summary'}
            payload[key]='\ud800'
            self.assertEqual(self.request('POST','/api/projects/p1/revisions',payload,staff)[0],400)
        self.assertEqual(self.counts(),before)

    def test_login_surrogates_rejected_before_hash_and_healthy_unicode(self):
        for key in ('email','password'):
            data={'email':'alex@harbor.test','password':'HarborDemo!42'}; data[key]='\ud800'
            self.assertEqual(self.request('POST','/api/login',data)[0],400)
        for data in ({'email':3,'password':'ok'},{'email':'ok','password':False},{'email':' ','password':'ok'}):
            self.assertEqual(self.request('POST','/api/login',data)[0],400)
        cookie=self.login()
        self.assertEqual(self.request('POST','/api/projects/p1/comments',{'body':'Überprüfung — 日本語 🚀'},cookie)[0],201)
        self.assertEqual(self.get('/api/projects/p1/comments',cookie)['comments'][-1]['body'],'Überprüfung — 日本語 🚀')

    def test_static_allowlist_and_loopback_only(self):
        for path in ('/server.py','/BRIEF.md','/../server.py','/%2e%2e/server.py','/demo.sqlite3','/brand/anything'):
            self.assertEqual(self.request('GET',path)[0],404)
        with self.assertRaises(ValueError): server.WorkspaceServer('0.0.0.0',0,self.db)

    def test_cli_port_zero_readiness_and_persisted_cookie(self):
        command=[sys.executable,str(Path(server.__file__)),'--host','127.0.0.1','--port','0','--db',str(Path(self.temp.name)/'cli.sqlite3')]
        process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
        try:
            ready=json.loads(process.stdout.readline())
            self.assertTrue(ready['ready']); self.assertGreater(ready['port'],0)
            conn=http.client.HTTPConnection('127.0.0.1',ready['port'],timeout=5)
            conn.request('POST','/api/login',json.dumps({'email':'alex@harbor.test','password':'HarborDemo!42'}),{'Content-Type':'application/json'})
            response=conn.getresponse(); self.assertEqual(response.status,200)
            cookie=response.getheader('Set-Cookie').split(';')[0]; response.read(); conn.close()
        finally:
            process.terminate(); process.wait(timeout=5); process.stdout.close()
        process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
        try:
            ready=json.loads(process.stdout.readline())
            conn=http.client.HTTPConnection('127.0.0.1',ready['port'],timeout=5)
            conn.request('GET','/api/me',headers={'Cookie':cookie})
            response=conn.getresponse(); self.assertEqual(response.status,200)
            self.assertEqual(json.loads(response.read())['user']['id'],'c1'); conn.close()
        finally:
            process.terminate(); process.wait(timeout=5); process.stdout.close()


if __name__=='__main__': unittest.main()
