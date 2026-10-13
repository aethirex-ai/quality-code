import json,os,threading,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from broker import Broker,validate_request,record_preview,serve_mailbox,process_request,redact_request
from client import mailbox_request,read_actions
NODE=os.environ.get('PREVIEW_NODE','node')
MODULE=os.environ.get('PREVIEW_PLAYWRIGHT_MODULE','playwright')
class Contracts(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
 def req(self,**kwargs):return dict(op='render',page='/',viewport=375,**kwargs)
 def test_paths(self):
  for path in ['/','/clients/1','/login']:
   self.assertEqual(validate_request(dict(op='render',page=path,viewport=375),self.root),(path,375))
  for path in ['https://x/','//localhost:3000/','/%2e%2e/secret','/%252e%252e/x','/a\\b','/a?token=x','/.env','/x#y','/\n']:
   with self.subTest(path=path),self.assertRaises(ValueError):validate_request(dict(op='render',page=path,viewport=375),self.root)
 def test_actions(self):
  validate_request(self.req(actions=[{'op':'reload'},{'op':'fill','selector':'#password','value':'x'*2000}]),self.root)
  for a in [[{'op':'evaluate','selector':'body'}],[{'op':'press','selector':'body','value':'Meta+A'}],[{'op':'fill','selector':'x','value':'x'*2001}],[{'op':'reload','selector':'x'}],[{'op':'click','selector':'x'}]*25]:
   with self.assertRaises(ValueError):validate_request(self.req(actions=a),self.root)
  for field in ['port','url','output','root','script']:
   with self.assertRaises(ValueError):validate_request(self.req(**{field:'x'}),self.root)
 def test_history_password_and_hardlink(self):
  fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY);self.addCleanup(os.close,fd)
  server=SimpleNamespace(root=self.root,root_fd=fd)
  request=self.req(actions=[{'op':'fill','selector':'#login-password','value':'topsecret'}])
  record_preview(server,request,{'ok':True,'screenshot':str(self.root/'.preview-output/a.png')})
  history=self.root/'.preview-events.jsonl';self.assertNotIn('topsecret',history.read_text());self.assertIn('[REDACTED]',history.read_text())
  self.assertEqual(json.loads(history.read_text())['result']['screenshot'],'.preview-output/a.png')
  os.link(history,self.root/'hardlink')
  with self.assertRaises(ValueError):record_preview(server,request,{'ok':True})
  history.unlink();history.symlink_to(self.root/'hardlink')
  with self.assertRaises(OSError):record_preview(server,request,{'ok':True})
 def test_mailbox_and_owned_cleanup(self):
  fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY);stop=threading.Event();server=SimpleNamespace(root=self.root,root_fd=fd,ready=True)
  thread=threading.Thread(target=serve_mailbox,args=(server,stop),daemon=True);thread.start()
  try:
   for _ in range(100):
    if (self.root/'.preview-mailbox').exists():break
    time.sleep(.01)
   unrelated=self.root/'.preview-mailbox/unrelated';unrelated.write_text('owned by another caller')
   self.assertTrue(mailbox_request(self.root,{'op':'ready'})['ready'])
   self.assertEqual([x.name for x in (self.root/'.preview-mailbox').iterdir()],['unrelated'])
   self.assertFalse(mailbox_request(self.root,self.req(port=9999))['ok'])
  finally:stop.set();thread.join(2);os.close(fd)
  unrelated.unlink();(self.root/'.preview-mailbox').rmdir();(self.root/'other').mkdir();(self.root/'.preview-mailbox').symlink_to(self.root/'other',target_is_directory=True)
  with self.assertRaises(OSError):mailbox_request(self.root,{'op':'ready'})
 def test_actions_file_security(self):
  (self.root/'actions.json').write_text('[{"op":"reload"}]')
  self.assertEqual(read_actions(self.root,'actions.json'),[{'op':'reload'}])
  for name in ['../actions.json','/actions.json','x\\actions.json']:
   with self.assertRaises(ValueError):read_actions(self.root,name)
  (self.root/'linked.json').symlink_to(self.root/'actions.json')
  with self.assertRaises(OSError):read_actions(self.root,'linked.json')
  os.link(self.root/'actions.json',self.root/'hard.json')
  with self.assertRaises(RuntimeError):read_actions(self.root,'hard.json')
  (self.root/'big.json').write_text('x'*8193)
  with self.assertRaises(RuntimeError):read_actions(self.root,'big.json')
 def test_ports_symlink_output(self):
  for port in [80,0,65536,True]:
   with self.assertRaises(ValueError):Broker(self.root,self.root/'.preview.sock',NODE,MODULE,port,False)
  (self.root/'.preview-output').symlink_to(self.root/'other')
  with self.assertRaises(ValueError):Broker(self.root,self.root/'.preview.sock',NODE,MODULE,34567,False)
class BrowserSmoke(unittest.TestCase):
 def test_real_loopback_cookie_api_persistence_and_remote_block(self):
  state={'count':0,'leaks':0}
  class App(BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def do_GET(self):
    if self.path=='/count':
     self.send_response(200);self.end_headers();self.wfile.write(str(state['count']).encode());return
    body=f'''<h1>Portal smoke</h1><input id="login-password" type="password"><button id="login" onclick="fetch('/login',{{method:'POST'}}).then(()=>document.querySelector('h1').textContent='Signed in')">Log in</button><button id="inc" onclick="fetch('/increment',{{method:'POST'}}).then(()=>location.reload())">Increment</button><p id="count">{state['count']}</p><button id="outside" onclick="fetch('http://localhost:{leak.server_port}/leak').catch(()=>{{}});fetch('https://example.com/leak').catch(()=>{{}});new WebSocket('ws://127.0.0.1:{leak.server_port}/socket')">External</button>'''
    self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(body.encode())
   def do_POST(self):
    if self.path=='/login':self.send_response(200);self.send_header('Set-Cookie','session=synthetic; HttpOnly; SameSite=Lax')
    elif self.path=='/increment' and 'session=synthetic' in self.headers.get('Cookie',''):state['count']+=1;self.send_response(200)
    else:self.send_response(401)
    self.end_headers();self.wfile.write(b'ok')
  class Leak(BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def do_GET(self):state['leaks']+=1;self.send_response(200);self.end_headers()
  leak=ThreadingHTTPServer(('127.0.0.1',0),Leak);app=ThreadingHTTPServer(('127.0.0.1',0),App)
  for s in [leak,app]:threading.Thread(target=s.serve_forever,daemon=True).start()
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);broker=Broker(root,root/'.preview.sock',NODE,MODULE,app.server_port,False)
   try:
    broker.check_ready()
    actions=[{'op':'fill','selector':'#login-password','value':'smoke-secret'},{'op':'click','selector':'#login'},{'op':'click','selector':'#inc'},{'op':'reload'},{'op':'click','selector':'#outside'}]
    result=process_request(broker,dict(op='render',page='/',viewport=375,actions=actions))
    self.assertTrue(result['ok'],result);self.assertTrue(all(a['ok'] for a in result['actionResults']),result);self.assertEqual(state['count'],1);self.assertEqual(state['leaks'],0);self.assertGreaterEqual(len(result['blockedRequests']),2);self.assertTrue(Path(result['screenshot']).exists());self.assertNotIn('smoke-secret',(root/'.preview-events.jsonl').read_text())
    result2=process_request(broker,dict(op='render',page='/',viewport=1440,actions=[{'op':'click','selector':'#inc'},{'op':'reload'}]))
    self.assertTrue(result2['ok'],result2);self.assertEqual(state['count'],1)
    app.shutdown();app.server_close()
    result3=process_request(broker,dict(op='render',page='/',viewport=375))
    self.assertFalse(result3['ok']);self.assertEqual(result3['classification'],'readiness')
   finally:
    broker.close_renderer()
    os.close(broker.root_fd)
  leak.shutdown();leak.server_close()
if __name__=='__main__':unittest.main()
