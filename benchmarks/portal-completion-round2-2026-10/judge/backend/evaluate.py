#!/usr/bin/env python3
"""Frozen black-box API evaluator. No imports from the evaluated application."""
import argparse
import concurrent.futures
import http.client
import json
import os
from pathlib import Path
import queue
import select
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time

GROUPS = (
    'authentication', 'session_lifecycle', 'client_isolation', 'staff_permissions',
    'json_and_input_bounds', 'comment_identity_and_activity',
    'revision_publication', 'decision_transitions', 'conflict_atomicity',
    'concurrent_revision_writes', 'restart_persistence', 'seed_and_read_contract',
)
ACCOUNTS = {
    'c1': ('alex@harbor.test', 'HarborDemo!42', 'client'),
    'c2': ('sam@northline.test', 'NorthDemo!42', 'client'),
    's1': ('studio@aethdesign.test', 'StudioDemo!42', 'staff'),
}

class ProductFailure(Exception): pass
class InstrumentFailure(Exception): pass
class PrerequisiteFailure(Exception): pass

def require(ok, message):
    if not ok: raise ProductFailure(message)

def fields(value, names, label):
    require(isinstance(value,dict),label+' must be an object')
    require(all(k in value for k in names),label+' is missing required fields: '+', '.join(names))
    return value

def typed(value, text_keys=(), integer_keys=(), label='API value'):
    require(all(isinstance(value[k],str) for k in text_keys),label+' has invalid text field types')
    require(all(type(value[k]) is int for k in integer_keys),label+' has invalid integer field types')

def project_shape(project):
    fields(project,('id','title','clientName','status','currentRevision','budgetCents','progress','nextMilestone'),'Project')
    typed(project,('id','title','clientName','status','nextMilestone'),('currentRevision','budgetCents','progress'),'Project')

def no_secrets(value):
    if isinstance(value,dict):
        forbidden={'password','passwordhash','password_hash','passwordverifier','password_verifier','sessiontoken','session_token','sessions'}
        require(not any(str(k).lower() in forbidden for k in value),'API response exposes account/session secret fields')
        for item in value.values(): no_secrets(item)
    elif isinstance(value,list):
        for item in value: no_secrets(item)

def read_shape(path, body):
    """Validate only public required read fields, leaving all extras unrestricted."""
    if path=='/api/me':
        user=fields(body.get('user'),('id','name','email','role'),'User')
        typed(user,('id','name','email','role'),label='User')
    elif path=='/api/projects':
        values=body.get('projects');require(isinstance(values,list),'Projects must be a list')
        for value in values: project_shape(value)
    elif path.endswith('/revisions'):
        values=body.get('revisions');require(isinstance(values,list),'Revisions must be a list')
        for value in values:
            fields(value,('number','title','summary','publishedAt'),'Revision')
            typed(value,('title','summary','publishedAt'),('number',),'Revision')
    elif path.endswith('/comments'):
        values=body.get('comments');require(isinstance(values,list),'Comments must be a list')
        for value in values:
            fields(value,('id','body','author','createdAt'),'Comment')
            fields(value['author'],('id','name','role'),'Comment author')
            typed(value,('body','createdAt'),label='Comment')
            typed(value['author'],('id','name','role'),label='Comment author')
    elif path.endswith('/activity'):
        values=body.get('events');require(isinstance(values,list),'Events must be a list')
        for value in values:
            fields(value,('id','type','actor','revision','createdAt'),'Activity event')
            fields(value['actor'],('id','name','role'),'Activity actor')
            typed(value,('type','createdAt'),('revision',),'Activity event')
            typed(value['actor'],('id','name','role'),label='Activity actor')
    elif path.startswith('/api/projects/'):
        project=fields(body.get('project'),('id','title','clientName','status','currentRevision','budgetCents','progress','nextMilestone','brief','deliverables','timeline'),'Project detail')
        project_shape(project);typed(project,('brief',),label='Project detail')
        require(isinstance(project['deliverables'],list) and all(isinstance(v,str) for v in project['deliverables']),'Deliverables must be a list of strings')
        require(isinstance(project['timeline'],list),'Timeline must be a list')
        for value in project['timeline']:
            fields(value,('title','status'),'Timeline entry');typed(value,('title','status'),label='Timeline entry')

class Server:
    def __init__(self, site, directory, deadline):
        self.site, self.directory, self.deadline = site, Path(directory), deadline
        self.db = self.directory / 'state.sqlite'
        self.process = None
        self.port = None
        self.stderr = bytearray()
        self.threads = []
        self.reader_stop = None

    def start(self):
        if time.monotonic() >= self.deadline: raise InstrumentFailure('Total evaluation deadline reached')
        path = self.site / 'server.py'
        if not path.is_file(): raise ProductFailure('Required server.py is missing')
        try:
            self.process = subprocess.Popen(
                [sys.executable, str(path), '--host', '127.0.0.1', '--port', '0', '--db', str(self.db)],
                cwd=self.site, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, start_new_session=True,
            )
        except OSError as exc: raise InstrumentFailure('Could not create owned server process: ' + str(exc))
        ready = queue.Queue(maxsize=1)
        process = self.process
        reader_stop = threading.Event()
        self.reader_stop = reader_stop
        for stream in (process.stdout, process.stderr): os.set_blocking(stream.fileno(),False)
        def chunks(stream):
            # Read raw nonblocking descriptors: BufferedReader.close() must never
            # wait on a reader holding its lock while a descendant retains a pipe.
            descriptor=stream.fileno()
            while not reader_stop.is_set():
                readable,_,_=select.select([descriptor],[],[],.1)
                if not readable: continue
                try: chunk=os.read(descriptor,4096)
                except BlockingIOError: continue
                if not chunk: break
                yield chunk
        def read_stdout():
            pending=bytearray();discard=False
            for chunk in chunks(process.stdout):
                for part in chunk.splitlines(keepends=True):
                    if not discard: pending.extend(part)
                    if len(pending)>4096: pending.clear();discard=True
                    if not part.endswith(b'\n'): continue
                    line=bytes(pending);pending.clear()
                    if discard: discard=False;continue
                    try: item = json.loads(line)
                    except (ValueError, UnicodeDecodeError): continue
                    if isinstance(item, dict) and item.get('ready') is True and type(item.get('port')) is int:
                        if 0 < item['port'] <= 65535:
                            try: ready.put_nowait(item['port'])
                            except queue.Full: pass
        def read_stderr():
            for chunk in chunks(process.stderr):
                self.stderr.extend(chunk)
                if len(self.stderr) > 32768: del self.stderr[:-32768]
        self.threads = [threading.Thread(target=f, daemon=True) for f in (read_stdout, read_stderr)]
        for thread in self.threads: thread.start()
        until = min(self.deadline, time.monotonic() + 7)
        while time.monotonic() < until:
            try:
                self.port = ready.get(timeout=min(.1, max(.001, until-time.monotonic())))
                return
            except queue.Empty:
                if self.process.poll() is not None:
                    raise ProductFailure('Server exited before readiness, code ' + str(self.process.returncode))
        raise ProductFailure('No valid readiness JSON within seven seconds')

    def stop(self):
        process = self.process
        if process is None: return
        # The process group belongs exclusively to this evaluator; terminate descendants too.
        try: os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError: pass
        try: process.wait(timeout=1)
        except subprocess.TimeoutExpired: pass
        # Leader exit does not imply group exit: descendants may ignore TERM and
        # retain stdout/stderr. Always finish cleanup of this exclusive group.
        try: os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        self.reader_stop.set()
        try: process.wait(timeout=.5)
        except subprocess.TimeoutExpired: raise InstrumentFailure('Owned server did not exit after group SIGKILL')
        finally:
            for thread in self.threads: thread.join(timeout=.2)
            process.stdout.close();process.stderr.close()
            self.process = None

    def restart(self):
        self.stop()
        self.start()

class Probe:
    def __init__(self, server):
        self.server = server
        self.cookies = {}
        self.evidence = []
        self.lock = threading.Lock()

    def request(self, method, path, body=None, user=None, raw=None, headers=None, cookie=None):
        if time.monotonic() >= self.server.deadline: raise InstrumentFailure('Total evaluation deadline reached')
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        request_headers = {'Content-Type': 'application/json'} if data is not None else {}
        if user: request_headers['Cookie'] = self.cookies.get(user, '')
        if cookie is not None: request_headers['Cookie'] = cookie
        request_headers.update(headers or {})
        connection = http.client.HTTPConnection('127.0.0.1', self.server.port,
            timeout=min(2, max(.01, self.server.deadline-time.monotonic())))
        record = {'method': method, 'path': path, 'identity': user,
                  'body': body if path != '/api/login' else {'email': (body or {}).get('email'), 'password': '[synthetic redacted]'}}
        if raw is not None: record['raw'] = raw.decode(errors='replace')[:256]
        record['headers'] = {k:v for k,v in request_headers.items() if k.lower() != 'cookie'}
        if cookie is not None: record['cookie_override'] = '[present]' if cookie else '[empty]'
        try:
            connection.request(method, path, body=data, headers=request_headers)
            response = connection.getresponse()
            response_headers = response.getheaders()
            payload = response.read(65537)
            record['actual_status'] = response.status
            if len(payload) > 65536: raise InstrumentFailure('API response exceeds bounded evaluator capture limit (64 KiB); contract verdict unavailable')
            try: parsed = json.loads(payload)
            except (ValueError, UnicodeDecodeError):
                record['actual_body'] = payload.decode(errors='replace')[:1000]
                raise ProductFailure('API response is not JSON')
            record['actual_body'] = parsed
            require(isinstance(parsed,dict), 'API response must be a JSON object')
            no_secrets(parsed)
            require(any(k.lower() == 'content-type' and 'application/json' in v.lower() for k,v in response_headers), 'API response lacks JSON content type')
            require(not any(k.lower()=='access-control-allow-origin' and (v=='*' or v=='https://unrelated.test') for k,v in response_headers), 'API enables permissive cross-origin access')
            return response.status, parsed, response_headers
        except (OSError, http.client.HTTPException) as exc:
            record['transport_error'] = str(exc)
            raise ProductFailure('Server request failed: ' + str(exc))
        finally:
            connection.close()
            with self.lock: self.evidence.append(record)

    def expect(self, method, path, status=200, **kwargs):
        result = self.request(method, path, **kwargs)
        with self.lock:
            # Concurrent evidence ordering need not match request return ordering.
            for record in reversed(self.evidence):
                if record['method'] == method and record['path'] == path and 'required_status' not in record:
                    record['required_status'] = status
                    break
        require(result[0] == status, f'{method} {path}: required {status}, actual {result[0]}')
        if status >= 400:
            error = result[1].get('error') if isinstance(result[1], dict) else None
            require(isinstance(error, dict) and all(isinstance(error.get(k), str) and error[k].strip() for k in ('code','message')), 'Error must contain useful code/message strings')
        elif method=='GET': read_shape(path,result[1])
        elif path.endswith('/comments'):
            comment=fields(result[1].get('comment'),('id','body','author','createdAt'),'New comment')
            fields(comment['author'],('id','name','role'),'New comment author')
        elif path.endswith('/revisions'):
            fields(result[1].get('revision'),('number','title','summary','publishedAt'),'New revision')
            fields(result[1].get('project'),('id','status','currentRevision'),'Published project')
        elif path.endswith('/decision'):
            fields(result[1].get('project'),('id','status','currentRevision'),'Decided project')
        return result[1]

    def login(self, user, prerequisite=True):
        email, password, role = ACCOUNTS[user]
        try:
            status, body, headers = self.request('POST', '/api/login', {'email':email,'password':password})
            require(status == 200, f'Seed account {user} cannot log in: {status}')
            identity=fields(body.get('user'),('id','name','email','role'),'Login user')
            require(identity.get('id') == user and identity.get('role') == role, 'Login identity is incorrect')
            cookies = [v for k,v in headers if k.lower() == 'set-cookie' and v.startswith('atelier_session=')]
            require(bool(cookies), 'Login omitted atelier_session cookie')
            self.cookies[user] = cookies[-1].split(';',1)[0]
            return cookies[-1]
        except ProductFailure as exc:
            if prerequisite: raise PrerequisiteFailure(str(exc)) from exc
            raise

    def project(self, project='p1', user='c1'):
        return self.expect('GET', f'/api/projects/{project}', user=user)['project']
    def events(self, project='p1', user='c1'):
        return self.expect('GET', f'/api/projects/{project}/activity', user=user)['events']
    def revisions(self, project='p1', user='c1'):
        return self.expect('GET', f'/api/projects/{project}/revisions', user=user)['revisions']
    def comments(self, project='p1', user='c1'):
        return self.expect('GET', f'/api/projects/{project}/comments', user=user)['comments']
    def publish(self, expected=1, title='New direction', summary='A carefully revised direction', status=201):
        return self.expect('POST', '/api/projects/p1/revisions', status=status, user='s1', body={'expectedRevision':expected,'title':title,'summary':summary})
    def decide(self, revision=1, decision='approve', note='', status=200, user='c1'):
        return self.expect('POST', '/api/projects/p1/decision', status=status, user=user, body={'revision':revision,'decision':decision,'note':note})

def exactly_one(before, after, kind, actor, revision):
    require(len(after) == len(before)+1, 'Successful mutation must append exactly one activity event')
    old = {e['id'] for e in before}
    added = [e for e in after if e['id'] not in old]
    require(len(added) == 1, 'Activity event IDs must be stable and unique')
    event = added[0]
    require(event.get('type') == kind and event.get('actor',{}).get('id') == actor and event.get('revision') == revision, 'Activity type/actor/revision does not match mutation')
    return event

def authentication(p):
    for path in ('/api/me','/api/projects','/api/projects/p1','/api/projects/p1/revisions','/api/projects/p1/comments','/api/projects/p1/activity'):
        p.expect('GET',path,status=401)
    p.expect('POST','/api/projects/p1/comments',status=401,body={'body':'Denied'})
    p.expect('POST','/api/login',status=401,body={'email':'alex@harbor.test','password':'wrong'})
    p.expect('GET','/api/me',status=401,cookie='atelier_session=c1; role=staff; userId=s1')
    cookie = p.login('c1',False)
    require('httponly' in cookie.lower() and 'samesite=lax' in cookie.lower() and 'path=/' in cookie.lower(), 'Session cookie flags do not match contract')
    user = p.expect('GET','/api/me',user='c1')['user']
    require(all(user.get(k)==v for k,v in {'id':'c1','name':'Alex Morgan','email':'alex@harbor.test','role':'client'}.items()),'Authenticated identity is incorrect')
    forged=p.expect('GET','/api/me',cookie=p.cookies['c1']+'; role=staff; userId=s1')['user']
    require(forged['id']=='c1' and forged['role']=='client','Additional cookie fields altered authenticated identity')
    first = p.cookies['c1']; p.login('c1',False)
    require(first != p.cookies['c1'], 'Separate logins must issue unpredictable fresh sessions')

def session_lifecycle(p):
    p.login('c1'); original=p.cookies['c1']
    p.server.restart()
    p.expect('GET','/api/me',user='c1')
    status, body, headers=p.request('POST','/api/logout',body={},user='c1')
    require(status==200,'Authenticated logout must return 200')
    require(any(k.lower()=='set-cookie' and v.startswith('atelier_session=') and ('max-age=0' in v.lower() or 'expires=' in v.lower() or v.split(';')[0]=='atelier_session=') for k,v in headers),'Logout must clear cookie')
    p.expect('GET','/api/me',status=401,cookie=original)
    p.server.restart(); p.expect('GET','/api/me',status=401,cookie=original)

def client_isolation(p):
    for user in ACCOUNTS: p.login(user)
    for user, ids in [('c1',{'p1','p2'}),('c2',{'p3'}),('s1',{'p1','p2','p3'})]:
        require({v['id'] for v in p.expect('GET','/api/projects',user=user)['projects']}==ids,'Project listing leaks or omits client projects')
    before=p.comments('p3','s1'); events=p.events('p3','s1')
    for suffix in ('','/revisions','/comments','/activity'):
        p.expect('GET','/api/projects/p3'+suffix,status=404,user='c1')
        p.expect('GET','/api/projects/p1'+suffix,status=404,user='c2')
    p.expect('POST','/api/projects/p3/comments',status=404,user='c1',body={'body':'cross-client'})
    p.expect('POST','/api/projects/p3/decision',status=404,user='c1',body={'revision':1,'decision':'approve','note':''})
    require(p.comments('p3','s1')==before and p.events('p3','s1')==events,'Denied cross-client writes persisted changes')
    p.expect('GET','/api/projects/unknown',status=404,user='s1')

def staff_permissions(p):
    p.login('c1'); p.login('s1')
    before=p.revisions(); events=p.events(); project=p.project()
    p.expect('POST','/api/projects/p1/revisions',status=403,user='c1',body={'expectedRevision':1,'title':'Forged','summary':'Forged','role':'staff','userId':'s1'})
    p.decide(status=403,user='s1')
    require(p.revisions()==before and p.events()==events and p.project()==project,'Denied staff/client operation changed state')
    p.publish()
    require(p.project()['currentRevision']==2,'Authorized staff cannot publish')

def json_and_input_bounds(p):
    p.login('c1'); p.login('s1'); before=p.events()
    p.expect('POST','/api/login',status=400,body={'email':5,'password':[]})
    p.expect('POST','/api/projects/p1/comments',status=400,user='c1',raw=b'{')
    p.expect('POST','/api/projects/p1/comments',status=415,user='c1',raw=b'body=test',headers={'Content-Type':'text/plain'})
    p.expect('POST','/api/projects/p1/comments',status=403,user='c1',body={'body':'cross-origin'},headers={'Origin':'https://unrelated.test'})
    for value in (None,5,[],{},'   ','x'*2001):
        p.expect('POST','/api/projects/p1/comments',status=400,user='c1',body={'body':value})
    for value in (True,1.5,'1',0):
        p.expect('POST','/api/projects/p1/revisions',status=400,user='s1',body={'expectedRevision':value,'title':'Okay','summary':'Okay'})
        p.decide(revision=value,status=400)
    for title,summary in [(' ', 'Okay'),('x'*121,'Okay'),('Okay','x'*2001),([], 'Okay'),('Okay',False)]:
        p.publish(title=title,summary=summary,status=400)
    for decision,note in [('unknown',''),('request_changes',' '),('approve','x'*2001),('approve',None)]:
        p.decide(decision=decision,note=note,status=400)
    # JSON escapes may decode to unpaired UTF-16 surrogates. Reject these before
    # hashing/UTF-8 persistence, while accepting paired astral Unicode.
    snapshots=(p.project(),p.revisions(),p.comments(),p.events())
    for invalid in ('\ud800','\udfff','prefix\ud800suffix','\ud800x\udc00'):
        for field in ('email','password'):
            credentials={'email':'alex@harbor.test','password':'HarborDemo!42',field:invalid}
            p.expect('POST','/api/login',status=400,body=credentials)
        p.expect('POST','/api/projects/p1/comments',status=400,user='c1',body={'body':invalid})
        p.publish(title=invalid,summary='Okay',status=400)
        p.publish(title='Okay',summary=invalid,status=400)
        p.decide(decision='approve',note=invalid,status=400)
        p.decide(decision='request_changes',note=invalid,status=400)
        require((p.project(),p.revisions(),p.comments(),p.events())==snapshots,'Unpaired surrogate changed project/history/comments/activity')
    require(p.events()==before and p.project()['currentRevision']==1,'Invalid inputs produced partial state/events')
    unicode='Café 漢字 \U0001f680'
    for field in ('email','password'):
        credentials={'email':'alex@harbor.test','password':'HarborDemo!42',field:unicode}
        p.expect('POST','/api/login',status=401,body=credentials)
    before_unicode=p.events()
    result=p.expect('POST','/api/projects/p1/comments',status=201,user='c1',body={'body':unicode})
    require(result['comment']['body']==unicode and p.comments()[-1]['body']==unicode,'Healthy Unicode comment did not round trip')
    exactly_one(before_unicode,p.events(),'comment_added','c1',1)
    result=p.publish(title=unicode,summary=unicode)
    require(result['revision']['title']==unicode and result['revision']['summary']==unicode,'Healthy Unicode revision did not round trip')
    before_unicode=p.events()
    p.decide(revision=2,decision='request_changes',note=unicode)
    require(p.project()['status']=='changes_requested','Healthy Unicode decision was not accepted')
    exactly_one(before_unicode,p.events(),'decision_submitted','c1',2)

    p.expect('POST','/api/projects/p1/comments',status=201,user='c1',body={'body':'x'*2000},headers={'Origin':f'http://127.0.0.1:{p.server.port}'})
    p.publish(expected=2,title='t'*120,summary='s'*2000)

def comment_identity_and_activity(p):
    p.login('c1'); p.login('s1'); before=p.events(); old=p.comments()
    literal='<img src=x onerror="alert(1)"> & <script>test</script>'
    result=p.expect('POST','/api/projects/p1/comments',status=201,user='c1',body={'body':literal})['comment']
    require(result['body']==literal and all(result['author'].get(k)==v for k,v in {'id':'c1','name':'Alex Morgan','role':'client'}.items()),'Literal comment or session-derived author incorrect')
    comments=p.comments(); require(len(comments)==len(old)+1 and comments[-1]['body']==literal,'Comment did not persist in chronological order')
    exactly_one(before,p.events(),'comment_added','c1',1)
    before=p.events();before_comments=p.comments()
    status,body,_=p.request('POST','/api/projects/p1/comments',user='c1',body={'body':'forgery probe','author':{'id':'s1','name':'Studio','role':'staff'},'role':'staff'})
    require(status==201 or 400<=status<500,'Forged fields must be ignored or rejected')
    if status==201:
        comment=fields(body.get('comment'),('id','body','author','createdAt'),'Forgery probe comment')
        author=fields(comment['author'],('id','name','role'),'Forgery probe author')
        require(author['id']=='c1' and author['role']=='client','Forged comment author accepted')
        exactly_one(before,p.events(),'comment_added','c1',1)
    else:
        error=fields(body.get('error'),('code','message'),'Forgery rejection')
        require(all(isinstance(error[k],str) and error[k].strip() for k in ('code','message')),'Forgery rejection error strings invalid')
        require(p.events()==before and p.comments()==before_comments,'Rejected author forgery persisted a change')
    before=p.events()
    p.expect('POST','/api/projects/p1/comments',status=201,user='s1',body={'body':'Staff reply'})
    require(p.comments()[-1]['author']['id']=='s1','Staff discussion author incorrect')
    exactly_one(before,p.events(),'comment_added','s1',1)

def revision_publication(p):
    p.login('c1');p.login('s1');before=p.events();old=p.revisions();money=p.project()['budgetCents']
    result=p.publish(title='  Revised identity  ',summary='  Updated typography  ')
    require(result['revision']['number']==2 and result['revision']['title']=='Revised identity' and result['revision']['summary']=='Updated typography','Revision response does not match trimmed input')
    project=result['project'];require(project['status']=='awaiting_review' and project['currentRevision']==2,'Publishing failed to open current review')
    history=p.revisions(); require(history[:-1]==old and history[-1]['number']==2,'Publishing altered or lost previous revisions')
    require(p.project()['budgetCents']==money,'Publishing changed budget cents')
    exactly_one(before,p.events(),'revision_published','s1',2)

def decision_transitions(p):
    p.login('c1');p.login('s1'); before=p.events(); money=p.project()['budgetCents']
    p.decide(decision='request_changes',note='  Please improve spacing.  ')
    project=p.project();require(project['status']=='changes_requested' and project['currentRevision']==1 and project['budgetCents']==money,'Request changes state/current revision/budget incorrect')
    event=exactly_one(before,p.events(),'decision_submitted','c1',1)
    require(event.get('decision')=='request_changes','Decision event lacks decision')
    p.publish();p.decide(revision=2)
    require(p.project()['status']=='approved' and p.project()['currentRevision']==2,'Approve transition incorrect')
    p.publish(expected=2)
    require(p.project()['status']=='awaiting_review' and p.project()['currentRevision']==3,'Publishing after approval did not reopen review')
    decisions=[e for e in p.events() if e['type']=='decision_submitted']
    require(any(e.get('revision')==1 and e.get('decision')=='request_changes' for e in decisions) and any(e.get('revision')==2 and e.get('decision')=='approve' for e in decisions),'Earlier decisions lost after publication')

def conflict_atomicity(p):
    p.login('c1');p.login('s1');p.decide(); state=p.project(); events=p.events(); history=p.revisions()
    p.decide(status=409);p.decide(decision='request_changes',note='opposite',status=409)
    require(p.project()==state and p.events()==events and p.revisions()==history,'Duplicate/opposite decision changed state or event count')
    p.publish();state=p.project();events=p.events();history=p.revisions()
    p.publish(expected=1,status=409);p.decide(revision=1,status=409)
    require(p.project()==state and p.events()==events and p.revisions()==history,'Stale revision/decision caused partial mutation')

def concurrent_revision_writes(p):
    p.login('s1'); before=p.events(user='s1');barrier=threading.Barrier(2)
    def write(title):
        barrier.wait(timeout=2)
        return p.request('POST','/api/projects/p1/revisions',user='s1',body={'expectedRevision':1,'title':title,'summary':'Competing revision'})
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(write,title) for title in ('Direction A','Direction B')]
        results=[f.result(timeout=5) for f in futures]
    require(sorted(r[0] for r in results)==[201,409],'Competing expectedRevision writes must produce exactly one 201 and one 409')
    require([r['number'] for r in p.revisions(user='s1')]==[1,2] and p.project(user='s1')['currentRevision']==2,'Race inserted duplicate revision or incorrect current revision')
    exactly_one(before,p.events(user='s1'),'revision_published','s1',2)

def restart_persistence(p):
    p.login('c1');p.login('s1');p.publish();p.decide(revision=2,decision='request_changes',note='Persist this decision')
    p.expect('POST','/api/projects/p1/comments',status=201,user='c1',body={'body':'Persist this discussion'})
    snapshots=(p.project(),p.revisions(),p.comments(),p.events())
    p.server.restart()
    require((p.project(),p.revisions(),p.comments(),p.events())==snapshots,'Restart lost or reinitialized persisted state')
    p.publish(expected=2);require(p.project()['currentRevision']==3,'Persisted state cannot advance after restart')

def seed_and_read_contract(p):
    p.login('s1')
    for project_id,title,budget,progress,status,current in [('p1','Harbor Commerce Platform',420000,65,'awaiting_review',1),('p2','Harbor Merchant Console',780000,90,'approved',2),('p3','Northline SaaS Workspace',360000,40,'awaiting_review',1)]:
        project=p.project(project_id,'s1')
        require(all(project.get(k)==v for k,v in {'id':project_id,'title':title,'budgetCents':budget,'progress':progress,'status':status,'currentRevision':current}.items()),'Seed project values incorrect')
        require(type(project['budgetCents']) is int and type(project['currentRevision']) is int,'Money and revision must be integer values')
        require(isinstance(project.get('brief'),str) and project['brief'].strip(),'Project brief missing')
        require(len(project.get('deliverables',[]))>=3 and all(isinstance(v,str) and v.strip() for v in project['deliverables']),'Deliverables contract incomplete')
        require(len(project.get('timeline',[]))>=3 and all(isinstance(v.get('title'),str) and isinstance(v.get('status'),str) for v in project['timeline']),'Timeline contract incomplete')
        revisions=p.revisions(project_id,'s1');require([r['number'] for r in revisions]==list(range(1,current+1)),'Seed revision history incorrect')
        for r in revisions: require(all(isinstance(r.get(k),str) and r[k].strip() for k in ('title','summary','publishedAt')),'Revision read schema incomplete')
        comments=p.comments(project_id,'s1');require(bool(comments),'Seed discussion comment missing')
        for comment in comments: require(all(k in comment for k in ('id','body','author','createdAt')),'Comment schema incomplete')
        for events in (p.events(project_id,'s1'),comments,revisions):
            key='publishedAt' if events is revisions else 'createdAt'
            require([e[key] for e in events]==sorted(e[key] for e in events),'Read ordering is not chronological')
        require(not any(k in project for k in ('password','passwordHash','password_hash','session_token','sessions')),'Project response exposes account/session secrets')

def evaluate(site, output):
    site=Path(site).resolve();output=Path(output).resolve();output.parent.mkdir(parents=True,exist_ok=True)
    artifact=output.parent/(output.stem+'.evidence');artifact.mkdir(exist_ok=True)
    start=time.monotonic();deadline=start+110
    report={'schema':1,'kind':'backend_contract_evaluation','site':str(site),'denominator':len(GROUPS),'groups':[],
            'independence':'Each group uses a fresh database; prerequisites are blocked, not additional distinct defects.',
            'deadline_seconds':110,'error':None}
    preflight_error=None
    # Separate an unavailable local-network capability from application startup.
    if (site/'server.py').is_file():
        try:
            with socket.socket() as test_socket: test_socket.bind(('127.0.0.1',0))
        except OSError as exc: preflight_error='Evaluator loopback preflight failed: '+str(exc)
    for name in GROUPS:
        row={'id':name,'status':'not_run','error':None,'evidence':str(artifact/(name+'.json'))}
        probe=None;server=None
        try:
            if preflight_error: raise InstrumentFailure(preflight_error)
            with tempfile.TemporaryDirectory(prefix='atelier-judge-') as directory:
                server=Server(site,directory,deadline);server.start();probe=Probe(server)
                try:
                    globals()[name](probe)
                    row['status']='pass'
                finally: server.stop()
        except PrerequisiteFailure as exc:
            row.update(status='blocked',error={'kind':'prerequisite','message':str(exc),'root_group':'authentication'})
        except ProductFailure as exc:
            row.update(status='fail',error={'kind':'product','message':str(exc)})
        except (InstrumentFailure,Exception) as exc:
            row.update(status='error',error={'kind':'instrument','message':type(exc).__name__+': '+str(exc)})
            report['error']={'kind':'instrument','message':'At least one group could not complete reliably; see groups'}
        finally:
            if server: server.stop()
            evidence={'group':name,'result':row,'requests':probe.evidence if probe else []}
            Path(row['evidence']).write_text(json.dumps(evidence,indent=2)+'\n')
            # Logs are bounded, private evidence, never surfaced as product response details.
            log=artifact/(name+'.stderr.log');log.write_bytes(server.stderr if server else b'');log.chmod(0o600)
        report['groups'].append(row)
    report['passed']=sum(g['status']=='pass' for g in report['groups'])
    report['elapsed_seconds']=round(time.monotonic()-start,3)
    # No defect count: contract failures can share one underlying defect.
    output.write_text(json.dumps(report,indent=2)+'\n')
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('site');parser.add_argument('output')
    args=parser.parse_args();result=evaluate(args.site,args.output)
    print(json.dumps({'passed':result['passed'],'denominator':result['denominator'],'output':str(Path(args.output).resolve()),'error':result['error']}))
    return 0 if result['passed']==result['denominator'] else 1

if __name__=='__main__': raise SystemExit(main())
