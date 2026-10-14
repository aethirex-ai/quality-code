"""Pre-audit deliverable checks only. This is not a functional app verdict."""
import json,sys
from pathlib import Path

def inspect(site):
 site=Path(site);checks=[]
 def check(name,passed,evidence):checks.append({'name':name,'passed':bool(passed),'evidence':evidence})
 for name in ['package.json','README.md','.env.example']:
  check(name,(site/name).is_file(),'Required documented deliverable exists; content reviewed by independent auditor.')
 try:
  package=json.loads((site/'package.json').read_text());scripts=package.get('scripts',{})
  for name in ['build','benchmark:start']:
   check('script:'+name,isinstance(scripts.get(name),str)and bool(scripts[name].strip()),'Required executable project script declared; functionality independently reviewed.')
 except (ValueError,OSError)as e:check('package_manifest',False,type(e).__name__)
 return {'schema':1,'kind':'structural pre-audit gate, not functional acceptance','accepted':all(c['passed']for c in checks),'tool_incomplete':False,'checks':checks}
if __name__=='__main__':
 result=inspect(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True);(out/'structural.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));sys.exit(0 if result['accepted']else 1)
