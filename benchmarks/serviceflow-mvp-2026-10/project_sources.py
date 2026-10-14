"""Create a byte-exact public projection of a frozen application inventory.

Runtime credentials are excluded by path BEFORE reading bytes. All retained files
must match the immutable inventory. Never point this at a live workspace.
"""
import argparse,hashlib,json,re
from pathlib import Path, PurePosixPath
SECRET_NAMES={'.auth-secret','.env','.env.local','.env.production','cookies.json','cookie.txt','tokens.json'}
def excluded(name):
 p=PurePosixPath(name)
 return any(x in SECRET_NAMES for x in p.parts) or any(x in ('node_modules','.git','.npm-cache','runtime') for x in p.parts) or p.suffix in ('.sqlite','.sqlite3','.db','.pem','.key','.secret')
def project(snapshot,destination):
 snapshot=Path(snapshot).resolve();destination=Path(destination)
 manifest=json.loads((snapshot/'manifest.json').read_text());hashes=manifest['sources_sha256'];plan=[];omitted=[]
 for name,expected in sorted(hashes.items()):
  p=PurePosixPath(name)
  if p.is_absolute() or '..' in p.parts or '\\' in name:raise ValueError('Unsafe source path')
  if name in ('ROUTING.json','AUDIT_READY.md'):omitted.append({'path':name,'reason':'Benchmark-only handoff report omitted before byte read; public routing and audit evidence are recorded separately'});continue
  if excluded(name):omitted.append({'path':name,'reason':'Private runtime artifact, excluded before byte read'});continue
  source=snapshot/'sources'/name
  if any(parent.is_symlink() for parent in [source,*source.parents] if parent!=Path('/')):raise ValueError('Source symlink forbidden')
  body=source.read_bytes()
  if hashlib.sha256(body).hexdigest()!=expected:raise ValueError('Frozen source hash mismatch: '+name)
  if source.suffix.lower() not in ('.png','.jpg','.jpeg','.webp'):
   text=body.decode('utf-8')
   if any('/'+marker in text for marker in ('Users/','private/tmp/','Applications/')) or re.search(r'(?:sk-proj-|sk-live-)[A-Za-z0-9_-]{10,}',text):raise ValueError('Private path or credential marker: '+name)
  plan.append((name,expected,body,source.stat().st_mode&0o777))
 destination.mkdir(parents=True,exist_ok=False)
 retained={}
 for name,digest,body,mode in plan:
  target=destination/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body);target.chmod(mode);retained[name]=digest
 return {'schema_version':1,'source_file_count':len(retained),'sources_sha256':retained,'excluded_artifacts':omitted,'projection_policy':'Retained file bytes equal original immutable inventory. Runtime artifacts excluded by name before reading. Source is unchanged; public projection is explicit.'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('snapshot');p.add_argument('destination');p.add_argument('manifest');a=p.parse_args();result=project(a.snapshot,a.destination);Path(a.manifest).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'retained':result['source_file_count'],'excluded':[x['path'] for x in result['excluded_artifacts']]}))
