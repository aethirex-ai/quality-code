"""Synthetic evaluator proof fixture only; intentionally not a measured application."""
import argparse,json,os,threading
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--host');p.add_argument('--port',type=int);p.add_argument('--db');args=p.parse_args()
mode=os.environ.get('FRONTEND_FIXTURE_MODE','healthy'); lock=threading.Lock(); sessions={}
accounts={'alex@harbor.test':('HarborDemo!42','c1','Alex Morgan','client'),'sam@northline.test':('NorthDemo!42','c2','Sam Ellis','client'),'studio@aethdesign.test':('StudioDemo!42','s1','AethDesign Studio','staff')}
titles=['Harbor House Identity','Harbor Digital Experience','Northline Editorial']
projects=[dict(id=f'p{i+1}',title=t,clientId='c2' if i==2 else 'c1',budgetCents=[420000,780000,360000][i],status='approved' if i==1 else 'awaiting_review',currentRevision=2 if i==1 else 1) for i,t in enumerate(titles)]
state={'projects':projects,'comments':{p['id']:[] for p in projects},'events':{p['id']:[] for p in projects},'history':{p['id']:[] for p in projects}}
if Path(args.db).exists():state=json.loads(Path(args.db).read_text())
def save():Path(args.db).write_text(json.dumps(state))
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def reply(self,status,data,cookie=None):
  raw=json.dumps(data).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)))
  if cookie:self.send_header('Set-Cookie',cookie)
  self.end_headers();self.wfile.write(raw)
 def user(self):return sessions.get(self.headers.get('Cookie','').split('atelier_session=')[-1].split(';')[0])
 def do_GET(self):
  if self.path=='/':
   raw=Path(__file__).with_name('index.html').read_text().replace('__MODE__',mode).encode();self.send_response(200);self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
  u=self.user()
  if self.path=='/api/me':return self.reply(200 if u else 401,{'user':u} if u else {'error':{'message':'Sign in'}})
  if not u:return self.reply(401,{})
  if self.path=='/api/projects':return self.reply(200,{'projects':[p for p in state['projects'] if u['role']=='staff' or p['clientId']==u['id']]})
  parts=self.path.split('/');pid=parts[3] if len(parts)>3 else None;project=next((p for p in state['projects'] if p['id']==pid),None)
  if not project:return self.reply(404,{})
  if len(parts)==4:return self.reply(200,{'project':project,'comments':state['comments'][pid],'events':state['events'][pid],'history':state['history'][pid]})
  return self.reply(500,{})
 def do_POST(self):
  body=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))) or '{}');u=self.user()
  if self.path=='/api/login':
   a=accounts.get(body.get('email'))
   if not a or body.get('password')!=a[0]:return self.reply(401,{'error':{'message':'Credentials invalid'}})
   token=a[1];u=dict(id=a[1],name=a[2],role=a[3]);sessions[token]=u;return self.reply(200,{'user':u},f'atelier_session={token}; Path=/; HttpOnly; SameSite=Lax')
  if self.path=='/api/logout':
   if u:sessions.pop(u['id'],None)
   return self.reply(200,{},'atelier_session=; Path=/; Max-Age=0')
  if not u:return self.reply(401,{})
  parts=self.path.split('/');pid=parts[3];kind=parts[4];project=next(p for p in state['projects'] if p['id']==pid)
  with lock:
   if kind=='comments':
    c={'body':body['body'],'author':u};state['comments'][pid].append(c);event='comment_added'
   elif kind=='decision':
    if not body['note'].strip():return self.reply(400,{'error':{'message':'Describe changes'}})
    project['status']='changes_requested';state['history'][pid].append('Changes requested: '+body['note']);event='decision_submitted'
   else:
    project['currentRevision']+=1;project['status']='awaiting_review';event='revision_published'
   state['events'][pid].append({'type':event});save()
  return self.reply(201 if kind!='decision' else 200,{'project':project})
server=ThreadingHTTPServer((args.host,args.port),Handler);print(json.dumps({'ready':True,'port':server.server_port}),flush=True);server.serve_forever()
