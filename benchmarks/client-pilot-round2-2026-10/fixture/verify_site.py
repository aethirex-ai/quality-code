from pathlib import Path
from html.parser import HTMLParser
class Assets(HTMLParser):
 def __init__(self): super().__init__(); self.paths=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag in ('img','script','link'):
   p=a.get('src') if tag!='link' else a.get('href')
   if p and not p.startswith(('#','data:','http:','https:')): self.paths.append(p)
for category in ('hotel','studio','landscape'):
 page=Path(category)/'index.html'; assert page.is_file(),str(page)
 parser=Assets();parser.feed(page.read_text())
 for asset in parser.paths: assert (page.parent/asset).is_file(),str(page.parent/asset)
print('PASS: three page files and referenced local assets exist')
