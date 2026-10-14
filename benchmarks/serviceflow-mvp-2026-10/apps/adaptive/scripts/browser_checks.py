"""Real E2E journeys through the supplied same-origin browser bridge.
Requires a migrated/seeded running app at PORTAL_PORT and ready parent bridge.
No browser evaluation, external requests, or live AI calls.
"""
import json, os, sqlite3, subprocess, time, uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RESULTS=[]
ATTEMPT=uuid.uuid4().hex

def action(op,selector,**kwargs):return {'op':op,'selector':selector,**kwargs}
def login(account):return [action('click',f"button:has-text('{account}')"+(":not(:has-text('2'))" if account=='Customer' else '')),action('click',"button:has-text('Sign in')")]
def render(name,page,viewport,actions,includes=()):
 path=ROOT/'scripts'/'browser-actions'/(name+'.json')
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(actions,indent=2)+'\n')
 command=['python3','preview_client.py','--page',page,'--viewport',str(viewport),'--actions-file',str(path.relative_to(ROOT))]
 proc=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
 try:result=json.loads(proc.stdout)
 except Exception:raise AssertionError(f'{name}: unexpected browser response {proc.stdout} {proc.stderr}')
 RESULTS.append({'name':name,'command':command,'result':result})
 (ROOT/'evidence').mkdir(exist_ok=True)
 (ROOT/'evidence'/'browser-results.json').write_text(json.dumps(RESULTS,indent=2)+'\n')
 (ROOT/'evidence'/('browser-attempt-'+ATTEMPT+'.json')).write_text(json.dumps(RESULTS,indent=2)+'\n')
 assert proc.returncode==0 and result.get('ok'),f'{name}: {result}'
 assert not result.get('horizontalOverflow'),f'{name}: horizontal overflow'
 assert not result.get('errors'),f'{name}: browser errors {result.get("errors")}'
 assert not result.get('blockedRequests'),f'{name}: blocked network requests'
 assert all(a.get('ok') for a in result.get('actionResults',[])),f'{name}: failed browser action'
 for text in includes:assert text in result.get('excerpt',''),f'{name}: missing {text!r}'
 print(f'PASS {name} ({viewport}px): {result.get("screenshot")}')
 return result

def main():
 # Sample-only exact synthetic records; each run creates one distinct request.
 tag='E2E '+uuid.uuid4().hex[:8]
 description=tag+': the kitchen tap drips after closing. Please inspect the washer.'
 customer=login('Customer')+[action('click',"a:has-text('New request')"),action('select','#serviceId',value='plumbing-repairs'),action('fill','#description',value=description),action('fill','#location',value='BS6 5AA, Bristol (demo)'),action('fill','#preferredDate',value='2099-05-12'),action('fill','#contactPhone',value='07700 900123'),action('click',"button:has-text('Submit request')"),action('click',"h2:has-text('Request history')")]
 render('customer-submit','/login',1440,customer,[tag,'Request submitted','Not a confirmed appointment'])
 db=sqlite3.connect(os.environ.get('DATABASE_PATH',str(ROOT/'data'/'serviceflow.sqlite')))
 row=db.execute('SELECT id,status,version FROM requests WHERE description=?',(description,)).fetchone();assert row and row[1]=='New' and row[2]==1
 request_id=row[0];assert db.execute('SELECT COUNT(*) FROM requests WHERE description=?',(description,)).fetchone()[0]==1
 render('provider-dashboard','/login',1440,login('Provider')+[action('fill','input[aria-label="Search requests"]',value=tag)],['Jamie Morgan','All requests','Plumbing repairs'])
 provider=login('Provider')+[action('click',f'.request-table a[href="/requests/{request_id}"]'),action('select','#next-status',value='Reviewing'),action('click',"button:has-text('Save status')"),action('select','#next-status',value='Quoted'),action('click',"button:has-text('Draft reply')"),action('fill','#draft-text',value='Edited demo reply. Thank you for the details. Please review before use.'),action('click',"label:has-text('Edit your draft')")]
 render('provider-update-draft','/login',1440,provider,[tag,'Reviewing','DETERMINISTIC DEMO-GENERATED','REVIEW REQUIRED'])
 row=db.execute('SELECT status,version FROM requests WHERE id=?',(request_id,)).fetchone();assert row==('Reviewing',2),row
 hist=db.execute('SELECT action FROM activity WHERE requestId=? ORDER BY createdAt,rowid',(request_id,)).fetchall();assert hist==[('Request submitted',),('Status changed from New to Reviewing',)],hist
 render('customer-mobile-detail',f'/requests/{request_id}',375,login('Customer')+[action('click',"h2:has-text('Request history')"),{'op':'reload'},action('click',"h2:has-text('Request history')")],[tag,'Reviewing','Status changed from New to Reviewing'])
 assert db.execute('SELECT COUNT(*) FROM activity WHERE requestId=?',(request_id,)).fetchone()[0]==2
 render('customer2-ownership',f'/requests/{request_id}',375,login('Customer 2')+[action('click','[role="alert"]')],['Request not found'])
 assert tag not in RESULTS[-1]['result']['excerpt']
 render('customer-form-mobile','/login',375,login('Customer')+[action('click',"a:has-text('New request')"),action('click',"button:has-text('Submit request')"),action('click','[role="alert"]')],['Please check the highlighted fields.'])
 render('admin-catalogue-mobile','/login',375,login('Admin')+[action('click',"a:has-text('Service catalogue')"),action('click',"h3:has-text('Plumbing repairs')")],['Plumbing repairs','Active','Edit service'])
 render('admin-editor-desktop','/login',1440,login('Admin')+[action('click',"a:has-text('Service catalogue')"),action('click',"button:has-text('Add service')"),action('fill','#service-name',value='Preview only — not saved')],['Add a service','Active — available for new requests'])
 render('provider-mobile-draft',f'/requests/{request_id}',375,login('Provider')+[action('click',"button:has-text('Draft reply')"),action('fill','#draft-text',value='Mobile draft edit; review required and not sent.')],['DETERMINISTIC DEMO-GENERATED','REVIEW REQUIRED'])
 render('admin-referenced-delete','/login',1440,login('Admin')+[action('click',"a:has-text('Service catalogue')"),action('click',".catalogue-card:has(h3:has-text('Plumbing repairs')) button:has-text('Delete')"),action('click',"[role=dialog] button:has-text('Delete service')"),action('click','[role=alert]')],['This service has request history. Deactivate it instead.'])
 render('mobile-services','/services',375,[action('click',"h3:has-text('Plumbing repairs')")],['From £65','Garden care'])
 render('desktop-services','/services',1440,[action('click',"h3:has-text('Plumbing repairs')")],['From £65','Painting & decorating'])
 db.close()
 print(f'{len(RESULTS)} browser journeys passed; real submitted request {request_id} updated once with history.')
if __name__=='__main__':main()
