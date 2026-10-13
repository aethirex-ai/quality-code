from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import sqlite3
import unittest
from tests.support import LocalServer, CREDENTIALS

class PortalContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = LocalServer()
        cls.cookies = {role: cls.server.login(role) for role in CREDENTIALS}

    @classmethod
    def tearDownClass(cls):
        cls.server.close()

    def req(self, path, body=None, role='c1', **kwargs):
        return self.server.request(path, body, cookie=self.cookies.get(role), **kwargs)

    def events(self, ident):
        return self.req(f'/api/projects/{ident}/activity', role='s1')[1]['events']

    def test_auth_verifiers_cookie_logout_and_forgery(self):
        status, payload, headers = self.server.request('/api/login', {'email': 'alex@harbor.test', 'password': 'HarborDemo!42', 'role': 'staff'})
        self.assertEqual(status, 200)
        self.assertEqual(payload['user']['role'], 'client')
        cookie = headers['Set-Cookie']
        for flag in ['HttpOnly', 'SameSite=Lax', 'Path=/']:
            self.assertIn(flag, cookie)
        self.assertNotIn('password', json.dumps(payload))
        self.assertEqual(self.server.request('/api/me', cookie='atelier_session=c1; role=staff')[0], 401)
        self.assertEqual(self.server.request('/api/projects')[0], 401)
        self.assertEqual(self.server.request('/api/login', {'email':'alex@harbor.test','password':'wrong'})[0], 401)
        self.assertEqual(self.server.request('/api/logout', {}, cookie=cookie)[0], 200)
        self.assertEqual(self.server.request('/api/me', cookie=cookie)[0], 401)
        with sqlite3.connect(self.server.db) as db:
            verifiers = db.execute('SELECT salt,verifier FROM users').fetchall()
            self.assertEqual(len(set(salt for salt, _ in verifiers)), 3)
            self.assertTrue(all(len(salt)==32 and len(verifier)==64 for salt,verifier in verifiers))
            self.assertNotIn('HarborDemo!42', repr(verifiers))

    def test_client_isolation_seed_and_static_boundary(self):
        for role, expected in [('c1',['p1','p2']),('c2',['p3']),('s1',['p1','p2','p3'])]:
            status, body, _ = self.req('/api/projects',role=role)
            self.assertEqual(status,200)
            self.assertEqual([p['id'] for p in body['projects']],expected)
        for suffix in ['', '/revisions','/comments','/activity']:
            self.assertEqual(self.req('/api/projects/p3'+suffix,role='c1')[0],404)
            self.assertEqual(self.req('/api/projects/p1'+suffix,role='c2')[0],404)
        self.assertEqual(self.req('/api/projects/missing')[0],404)
        self.assertEqual(self.req('/api/projects/p3/comments',{'body':'forbidden'})[0],404)
        for path in ['/server.py','/demo.sqlite3','/../BRIEF.md','/%2e%2e/server.py']:
            self.assertEqual(self.server.request(path)[0],404)
        self.assertEqual(self.server.request('/projects/p1')[0],200)
        p = self.req('/api/projects/p1')[1]['project']
        self.assertEqual(p['budgetCents'],420000)
        self.assertGreaterEqual(len(p['deliverables']),3)
        self.assertGreaterEqual(len(p['timeline']),3)
        self.assertTrue(p['brief'])

    def test_json_origin_field_validation_and_no_partial_events(self):
        before = len(self.events('p3'))
        self.assertEqual(self.req('/api/projects/p3/comments',{'body':'x'},role='c2',headers={'Origin':'https://evil.test'})[0],403)
        self.assertEqual(self.req('/api/projects/p3/comments',role='c2',raw='body=x',headers={'Content-Type':'text/plain'})[0],415)
        for raw in ['{', '[]', 'null', '{"body":NaN}', '{"body":123}', '{"body":true}', '{"body":"   "}', json.dumps({'body':'x'*2001})]:
            with self.subTest(raw=raw[:50]):
                status, result, _ = self.req('/api/projects/p3/comments',role='c2',raw=raw)
                self.assertEqual(status,400)
                self.assertIn('code',result['error'])
        for bad in [None,False,{},1.0,'1']:
            self.assertEqual(self.req('/api/projects/p3/revisions',{'expectedRevision':bad,'title':'Test','summary':'Summary'},role='s1')[0],400)
        for data in [{'email': False,'password':'x'}, {'email':'x','password':[]}, {'email':' ','password':'x'}]:
            self.assertEqual(self.server.request('/api/login',data)[0],400)
        self.assertEqual(len(self.events('p3')),before)
        self.assertEqual(self.req('/api/projects/p1/revisions', {'expectedRevision':1,'title':'Forged','summary':'No'},role='c1')[0],403)
        self.assertEqual(self.req('/api/projects/p3/decision', {'revision':1,'decision':'approve','note':''},role='s1')[0],403)

    def test_comment_literal_text_author_and_single_activity(self):
        before=len(self.events('p1'))
        body='<img src=x onerror="alert(1)"> & a thoughtful note'
        status,result,_=self.req('/api/projects/p1/comments',{'body':body,'author':{'id':'s1','role':'staff'}})
        self.assertEqual(status,201)
        self.assertEqual(result['comment']['body'],body)
        self.assertEqual(result['comment']['author']['id'],'c1')
        comments=self.req('/api/projects/p1/comments')[1]['comments']
        self.assertEqual(comments[-1]['id'],result['comment']['id'])
        events=self.events('p1')
        self.assertEqual(len(events),before+1)
        self.assertEqual(events[-1]['type'],'comment_added')
        self.assertEqual(events[-1]['commentId'],result['comment']['id'])
        self.assertEqual(events[-1]['actor']['id'],'c1')

    def test_decisions_duplicate_conflict_and_immutable_history(self):
        # Independent mutable seed p3; other tests only validate its failed writes.
        before=len(self.events('p3'))
        self.assertEqual(self.req('/api/projects/p3/decision',{'revision':1,'decision':'request_changes','note':'   '},role='c2')[0],400)
        status,result,_=self.req('/api/projects/p3/decision',{'revision':1,'decision':'request_changes','note':'  More room for field photography.  '},role='c2')
        self.assertEqual(status,200)
        self.assertEqual(result['project']['status'],'changes_requested')
        self.assertEqual(result['project']['budgetCents'],360000)
        self.assertEqual(result['project']['currentRevision'],1)
        for decision in ['approve','request_changes']:
            self.assertEqual(self.req('/api/projects/p3/decision',{'revision':1,'decision':decision,'note':'Again'},role='c2')[0],409)
        self.assertEqual(len(self.events('p3')),before+1)
        status,result,_=self.req('/api/projects/p3/revisions',{'expectedRevision':1,'title':'  Refined editorial  ','summary':'More space for images.'},role='s1')
        self.assertEqual(status,201)
        self.assertEqual(result['revision']['title'],'Refined editorial')
        self.assertEqual(result['project']['status'],'awaiting_review')
        self.assertEqual(result['project']['currentRevision'],2)
        self.assertEqual(self.req('/api/projects/p3/decision',{'revision':1,'decision':'approve','note':''},role='c2')[0],409)
        self.assertEqual(self.req('/api/projects/p3/decision',{'revision':2,'decision':'approve','note':''},role='c2')[0],200)
        revisions=self.req('/api/projects/p3/revisions',role='c2')[1]['revisions']
        self.assertEqual([r['number'] for r in revisions],[1,2])
        self.assertEqual(revisions[0]['decision']['note'],'More room for field photography.')
        self.assertEqual(revisions[0]['decision']['decision'],'request_changes')
        self.assertEqual(revisions[1]['decision']['decision'],'approve')
        self.assertEqual(len(self.events('p3')),before+3)

    def test_publish_race_exactly_one_success_and_no_failed_events(self):
        before=len(self.events('p2'))
        payload={'expectedRevision':2,'title':'Delivery refinement','summary':'Final responsive detail.'}
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _: self.req('/api/projects/p2/revisions',payload,role='s1'), range(2)))
        self.assertEqual(sorted(r[0] for r in results),[201,409])
        self.assertEqual(len(self.events('p2')),before+1)
        project=self.req('/api/projects/p2')[1]['project']
        self.assertEqual(project['status'],'awaiting_review')
        self.assertEqual(project['currentRevision'],3)
        revisions=self.req('/api/projects/p2/revisions')[1]['revisions']
        self.assertEqual([r['number'] for r in revisions],[1,2,3])
        self.assertEqual(revisions[1]['decision']['decision'],'approve')

class RestartPersistence(unittest.TestCase):
    def test_restart_keeps_cookie_comments_decisions_and_revisions(self):
        server=LocalServer()
        try:
            client=server.login('c1');staff=server.login('s1')
            self.assertEqual(server.request('/api/projects/p1/comments',{'body':'Persist this exact note'},cookie=client)[0],201)
            self.assertEqual(server.request('/api/projects/p1/decision',{'revision':1,'decision':'approve','note':'Proceed'},cookie=client)[0],200)
            self.assertEqual(server.request('/api/projects/p1/revisions',{'expectedRevision':1,'title':'Second direction','summary':'A durable new review'},cookie=staff)[0],201)
            server.restart()
            self.assertEqual(server.request('/api/me',cookie=client)[0],200)
            self.assertEqual(server.request('/api/me',cookie=staff)[0],200)
            project=server.request('/api/projects/p1',cookie=client)[1]['project']
            self.assertEqual((project['currentRevision'],project['status']),(2,'awaiting_review'))
            self.assertEqual(server.request('/api/projects/p1/comments',cookie=client)[1]['comments'][-1]['body'],'Persist this exact note')
            revisions=server.request('/api/projects/p1/revisions',cookie=client)[1]['revisions']
            self.assertEqual(revisions[0]['decision']['note'],'Proceed')
            events=server.request('/api/projects/p1/activity',cookie=client)[1]['events']
            self.assertEqual([e['type'] for e in events][-3:],['comment_added','decision_submitted','revision_published'])
            self.assertEqual(server.request('/api/logout',{},cookie=client)[0],200)
            server.restart()
            self.assertEqual(server.request('/api/me',cookie=client)[0],401)
            self.assertEqual(len(server.request('/api/projects',cookie=staff)[1]['projects']),3)
        finally:
            server.close()

class InputAndDecisionBoundaries(unittest.TestCase):
    def setUp(self):
        self.server=LocalServer()
        self.client=self.server.login('c1')
        self.staff=self.server.login('s1')

    def tearDown(self):
        self.server.close()

    def test_invalid_revision_and_decision_fields_are_atomic(self):
        def post(suffix,data,cookie):
            return self.server.request('/api/projects/p1/'+suffix,data,cookie=cookie)[0]
        def events():
            return self.server.request('/api/projects/p1/activity',cookie=self.client)[1]['events']
        before=events()
        valid={'expectedRevision':1,'title':'New direction','summary':'A meaningful summary'}
        for field,values in [('expectedRevision',[True,0,-1,'1',1.5,None]),('title',[False,None,'','   ','x'*121]),('summary',[[],{},None,'\n\t','x'*2001])]:
            for value in values:
                with self.subTest(field=field,value=str(value)[:20]):
                    data={**valid,field:value}
                    self.assertEqual(post('revisions',data,self.staff),400)
        valid={'revision':1,'decision':'approve','note':''}
        for field,values in [('revision',[False,0,-1,'1',1.0,None]),('decision',[True,{},[],None,'approved']),('note',[None,False,[],{},'x'*2001])]:
            for value in values:
                with self.subTest(field=field,value=str(value)[:20]):
                    self.assertEqual(post('decision',{**valid,field:value},self.client),400)
        self.assertEqual(events(),before)
        p=self.server.request('/api/projects/p1',cookie=self.client)[1]['project']
        self.assertEqual((p['status'],p['currentRevision'],p['budgetCents']),('awaiting_review',1,420000))
        self.assertEqual(len(self.server.request('/api/projects/p1/revisions',cookie=self.client)[1]['revisions']),1)

    def test_competing_client_decisions_exactly_one_event(self):
        def decide(decision):
            return self.server.request('/api/projects/p1/decision',{'revision':1,'decision':decision,'note':'A considered review'},cookie=self.client)[0]
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses=list(pool.map(decide,['approve','request_changes']))
        self.assertEqual(sorted(statuses),[200,409])
        events=self.server.request('/api/projects/p1/activity',cookie=self.client)[1]['events']
        self.assertEqual(len([e for e in events if e['type']=='decision_submitted']),1)
        revision=self.server.request('/api/projects/p1/revisions',cookie=self.client)[1]['revisions'][0]
        self.assertEqual(revision['decision']['author']['id'],'c1')
        self.assertEqual(revision['decision']['note'],'A considered review')

    def test_request_bounds_host_and_same_origin_browser_write(self):
        from server import allowed_host
        # HTTP omits the explicit port in a Host header at the default port.
        self.assertTrue(allowed_host('127.0.0.1',80))
        self.assertTrue(allowed_host('localhost',80))
        self.assertFalse(allowed_host('evil.test',80))
        self.assertFalse(allowed_host('127.0.0.1',8080))
        p='/api/projects/p1/comments'
        self.assertEqual(self.server.request('/api/me',cookie=self.client,headers={'Host':'evil.test'})[0],403)
        for origin in ['null','http://evil.test',f'https://127.0.0.1:{self.server.port}']:
            self.assertEqual(self.server.request(p,{'body':'forbidden'},cookie=self.client,headers={'Origin':origin})[0],403)
        self.assertEqual(self.server.request(p,raw='x'*16385,cookie=self.client)[0],400)
        self.assertEqual(self.server.request(p,raw='{"body":'+'['*1100+'0'+']'*1100+'}',cookie=self.client)[0],400)
        status,result,headers=self.server.request(p,{'body':'  A same-origin browser note.  '},cookie=self.client,headers={'Origin':f'http://127.0.0.1:{self.server.port}','Content-Type':'application/json; charset=utf-8'})
        self.assertEqual(status,201)
        self.assertEqual(result['comment']['body'],'A same-origin browser note.')
        self.assertNotIn('Access-Control-Allow-Origin',headers)
        self.assertEqual(len(self.server.request('/api/projects/p1/activity',cookie=self.client)[1]['events']),2)
