from pathlib import Path
import os,subprocess
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
ROOT=Path(__file__).resolve().parent
class Links(HTMLParser):
 def __init__(self):super().__init__();self.urls=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  for k in ('src','href'):
   if a.get(k):self.urls.append(a[k])
for client,pages in {'lighting':['index.html','collection.html','planner.html'],'expedition':['index.html','journeys.html','builder.html']}.items():
 for name in pages:
  p=ROOT/client/name;assert p.is_file(),f'Missing {client}/{name}'
  parser=Links();parser.feed(p.read_text())
  for url in parser.urls:
   v=urlsplit(url)
   assert not v.scheme and not v.netloc,f'External resource {url}'
   if not v.path:continue
   q=(p.parent/unquote(v.path)).resolve();assert q.is_relative_to(ROOT),f'Escaping resource {url}'
   if q.is_dir():q=q/'index.html'
   assert q.is_file(),f'Missing resource {url} from {p.relative_to(ROOT)}'
print('PASS: six routes and local resources')

node=os.environ.get('BENCHMARK_NODE','node')
for client in ('lighting','expedition'):
 test=ROOT/client/'tests/behavior.test.mjs'
 assert test.is_file(),f'Missing meaningful client regression suite: {test.relative_to(ROOT)}'
 subprocess.run([node,'--test',str(test)],cwd=ROOT,check=True)
print('PASS: both client regression suites')
