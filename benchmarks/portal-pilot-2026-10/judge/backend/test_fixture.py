#!/usr/bin/env python3
"""Independent, deliberately small API oracle for evaluator tests only.

This fixture is neither a submitted application nor a solver implementation.
State is JSON stored transactionally in SQLite; no frontend is implemented.
QC_FIXTURE_MUTATION selects one deliberately broken contract for negative controls.
"""
import argparse
import datetime
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import secrets
import sqlite3
import threading
from urllib.parse import urlparse

MUTATION=os.environ.get('QC_FIXTURE_MUTATION','')
ACCOUNTS={
 'c1':{'id':'c1','name':'Alex Morgan','email':'alex@harbor.test','role':'client'},
 'c2':{'id':'c2','name':'Sam Ellis','email':'sam@northline.test','role':'client'},
 's1':{'id':'s1','name':'AethDesign Studio','email':'studio@aethdesign.test','role':'staff'},
}
PASSWORDS={'c1':'HarborDemo!42','c2':'NorthDemo!42','s1':'StudioDemo!42'}
LOCK=threading.Lock()

def timestamp(state):
    state['tick']+=1
    return (datetime.datetime(2026,1,1,tzinfo=datetime.timezone.utc)+datetime.timedelta(seconds=state['tick'])).isoformat()

def seed():
    state={'tick':0,'projects':{},'sessions':{},'credentials':{}}
    for key,password in PASSWORDS.items():
        salt=secrets.token_hex(16)
        state['credentials'][key]={'salt':salt,'hash':hashlib.pbkdf2_hmac('sha256',password.encode(),salt.encode(),10000).hex()}
    for key,client,title,cents,progress,status,current in [('p1','c1','Harbor House Identity',420000,65,'awaiting_review',1),('p2','c1','Harbor Digital Experience',780000,90,'approved',2),('p3','c2','Northline Editorial',360000,40,'awaiting_review',1)]:
        project={'id':key,'clientId':client,'title':title,'clientName':'Harbor House' if client=='c1' else 'Northline',
          'budgetCents':cents,'progress':progress,'status':status,'currentRevision':current,
          'nextMilestone':{'p1':'Identity review','p2':'Handoff preparation','p3':'Editorial review'}[key],
          'brief':'Develop a thoughtful, clear visual system for this fictional local project.',
          'deliverables':['Identity guidelines','Typography system','Production assets'],
          'timeline':[{'title':label,'status':'complete' if i==0 else 'upcoming'} for i,label in enumerate(['Discovery','Design review','Handoff'])],
          'revisions':[],'comments':[],'events':[],'decisions':[]}
        for number in range(1,current+1):
            project['revisions'].append({'number':number,'title':'Identity direction' if key=='p1' else 'Editorial system' if key=='p3' else 'Digital direction',
                'summary':'A considered first direction with a coherent visual system.','publishedAt':timestamp(state)})
        project['comments'].append({'id':key+'-seed-comment','body':'Thank you for the thoughtful direction.','author':ACCOUNTS[client],'createdAt':timestamp(state)})
        if status=='approved': project['decisions'].append({'revision':2,'decision':'approve','actor':ACCOUNTS[client],'createdAt':timestamp(state)})
        state['projects'][key]=project
    return state

def public_project(project):
    return {k:v for k,v in project.items() if k not in ('comments','events','revisions')}

class Reject(Exception):
    def __init__(self,status,message): self.status,self.message=status,message

def text(value,maximum,allow_empty=False):
    if not isinstance(value,str): raise Reject(400,'Text field must be a string')
    value=value.strip()
    if (not value and not allow_empty) or len(value)>maximum: raise Reject(400,'Text length invalid')
    return value

def number(value):
    if type(value) is not int or value<1: raise Reject(400,'Revision must be a positive integer')
    return value

def event(state,project,kind,actor,revision,**extra):
    result={'id':secrets.token_hex(10),'type':kind,'actor':actor,'revision':revision,'createdAt':timestamp(state),**extra}
    project['events'].append(result)
    if MUTATION=='double_event': project['events'].append({**result,'id':secrets.token_hex(10)})

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def respond(self,status,body,headers=()):
        payload=json.dumps(body).encode()
        self.send_response(status);self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(payload)))
        for k,v in headers: self.send_header(k,v)
        self.end_headers();self.wfile.write(payload)

    def do_GET(self): self.handle_api()
    def do_POST(self): self.handle_api()

    def handle_api(self):
        headers=[]
        try:
            body={}
            if self.command=='POST':
                if self.headers.get('Content-Type','').split(';')[0]!='application/json': raise Reject(415,'JSON required')
                origin=self.headers.get('Origin')
                if origin and origin!=f'http://127.0.0.1:{self.server.server_port}': raise Reject(403,'Origin denied')
                try: body=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))
                except (ValueError,UnicodeDecodeError): raise Reject(400,'Malformed JSON')
                if not isinstance(body,dict): raise Reject(400,'Object required')
            with LOCK:
                connection=sqlite3.connect(self.server.db)
                try:
                    connection.execute('BEGIN IMMEDIATE')
                    state=json.loads(connection.execute('SELECT value FROM state').fetchone()[0])
                    status,result,headers=self.route(state,body)
                    connection.execute('UPDATE state SET value=?',(json.dumps(state),))
                    connection.commit()
                except Exception:
                    connection.rollback();raise
                finally: connection.close()
            self.respond(status,result,headers)
        except Reject as exc: self.respond(exc.status,{'error':{'code':'denied','message':exc.message}})

    def route(self,state,body):
        path=urlparse(self.path).path
        cookies={}
        for segment in self.headers.get('Cookie','').split(';'):
            if '=' in segment:
                k,v=segment.strip().split('=',1);cookies[k]=v
        token=cookies.get('atelier_session','')
        identity=state['sessions'].get(token)
        actor=ACCOUNTS.get(identity)
        if path=='/api/login' and self.command=='POST':
            email=text(body.get('email'),300);password=text(body.get('password'),300)
            user=next((k for k,v in ACCOUNTS.items() if v['email']==email),None)
            if user is None: raise Reject(401,'Invalid credentials')
            credential=state['credentials'][user]
            digest=hashlib.pbkdf2_hmac('sha256',password.encode(),credential['salt'].encode(),10000).hex()
            if not secrets.compare_digest(digest,credential['hash']): raise Reject(401,'Invalid credentials')
            token=secrets.token_urlsafe(24);state['sessions'][token]=user
            return 200,{'user':ACCOUNTS[user]},[('Set-Cookie',f'atelier_session={token}; Path=/; HttpOnly; SameSite=Lax')]
        if not actor: raise Reject(401,'Login required')
        if path=='/api/me': return 200,{'user':actor},[]
        if path=='/api/logout':
            state['sessions'].pop(token,None)
            return 200,{},[('Set-Cookie','atelier_session=; Max-Age=0; Path=/; HttpOnly; SameSite=Lax')]
        if path=='/api/projects' and self.command=='GET':
            projects=[public_project(p) for p in state['projects'].values() if actor['role']=='staff' or p['clientId']==identity or MUTATION=='isolation']
            return 200,{'projects':projects},[]
        parts=path.split('/')
        if len(parts)<4 or parts[1:3]!=['api','projects']: raise Reject(404,'Unknown API')
        project=state['projects'].get(parts[3])
        if not project or (actor['role']!='staff' and project['clientId']!=identity and MUTATION!='isolation'): raise Reject(404,'Project unavailable')
        resource=parts[4] if len(parts)>4 else ''
        if self.command=='GET':
            if resource=='': return 200,{'project':public_project(project)},[]
            if resource in ('revisions','comments'): return 200,{resource:project[resource]},[]
            if resource=='activity': return 200,{'events':project['events']},[]
            raise Reject(404,'Unknown API')
        current=project['currentRevision']
        if resource=='comments':
            content=text(body.get('body'),2000)
            if 'author' in body and MUTATION!='author': raise Reject(400,'Unexpected author')
            author=body.get('author',actor) if MUTATION=='author' else actor
            comment={'id':secrets.token_hex(10),'body':content,'author':author,'createdAt':timestamp(state)}
            project['comments'].append(comment);event(state,project,'comment_added',actor,current,commentId=comment['id'])
            return 201,{'comment':comment},[]
        if resource=='revisions':
            if actor['role']!='staff' and MUTATION!='staff': raise Reject(403,'Staff required')
            expected=number(body.get('expectedRevision'));title=text(body.get('title'),120);summary=text(body.get('summary'),2000)
            if expected!=current and MUTATION not in ('stale','race'): raise Reject(409,'Revision changed')
            new=current+1
            revision={'number':new,'title':title,'summary':summary,'publishedAt':timestamp(state)}
            project['revisions'].append(revision);project['currentRevision']=new;project['status']='awaiting_review'
            event(state,project,'revision_published',actor,new)
            return 201,{'revision':revision,'project':public_project(project)},[]
        if resource=='decision':
            if actor['role']!='client': raise Reject(403,'Client required')
            revision=number(body.get('revision'));decision=body.get('decision')
            if decision not in ('approve','request_changes'): raise Reject(400,'Invalid decision')
            note=text(body.get('note'),2000,decision=='approve')
            if (revision!=current or project['status']!='awaiting_review') and MUTATION!='duplicate': raise Reject(409,'Review changed')
            project['status']='approved' if decision=='approve' else 'changes_requested'
            project['decisions'].append({'revision':revision,'decision':decision,'note':note,'actor':actor,'createdAt':timestamp(state)})
            event(state,project,'decision_submitted',actor,revision,decision=decision)
            return 200,{'project':public_project(project)},[]
        raise Reject(404,'Unknown API')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--host');parser.add_argument('--port',type=int);parser.add_argument('--db')
    args=parser.parse_args()
    connection=sqlite3.connect(args.db)
    connection.execute('CREATE TABLE IF NOT EXISTS state(value TEXT NOT NULL)')
    if MUTATION=='persistence': connection.execute('DELETE FROM state')
    if connection.execute('SELECT count(*) FROM state').fetchone()[0]==0:
        connection.execute('INSERT INTO state VALUES(?)',(json.dumps(seed()),))
    connection.commit();connection.close()
    server=ThreadingHTTPServer((args.host,args.port),Handler);server.db=args.db
    print(json.dumps({'ready':True,'port':server.server_port}),flush=True)
    server.serve_forever()

if __name__=='__main__': main()
