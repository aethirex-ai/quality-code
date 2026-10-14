"""Repeatable real-browser customer -> provider -> customer journey using the supplied bridge.
Run against a migrated, seeded, running local app. Writes synthetic demo enquiries only.
"""
import json,subprocess,uuid,datetime,time
from pathlib import Path
run_id=uuid.uuid4().hex[:10]
folder=Path('evidence/actions');folder.mkdir(exist_ok=True)
def login(email):return [{'op':'fill','selector':'#email','value':email},{'op':'fill','selector':'#password','value':'ServiceFlow2026!'},{'op':'click','selector':'.login-panel .button'}]
def journey(name,actions,expect,viewport='1440'):
 # Respect the library's production sign-in rate window across fresh browser cookies.
 time.sleep(11)
 file=folder/('e2e-'+name+'.json');file.write_text(json.dumps(actions))
 cmd=['python3','scripts/preview-check.py','--id','e2e-'+name,'--page','/login','--viewport',viewport,'--actions-file',str(file)]
 for text in expect:cmd+=['--expect',text]
 if subprocess.call(cmd):raise SystemExit(1)
# Scope the action checks to the specific new enquiry, then confirm actor/history after reload.
marker='E2E '+run_id+': repair two cupboard hinges and fit one shelf.'
journey('customer-submit',login('alex@demo.local')+[
 {'op':'click','selector':'.page-intro a.button'},
 {'op':'select','selector':'#serviceId','value':'small-repairs'},
 {'op':'fill','selector':'#description','value':marker},
 {'op':'fill','selector':'#location','value':'BS3 1AB · Synthetic Bristol'},
 {'op':'fill','selector':'#preferredFrom','value':(datetime.date.today()+datetime.timedelta(days=14)).isoformat()},
 {'op':'fill','selector':'#contactPhone','value':'07700 900123'},
 {'op':'click','selector':'.form-submit .button'},
 {'op':'click','selector':'.timeline'}],['Request received.',marker,'Request submitted'])
journey('provider-update',login('provider@demo.local')+[
 {'op':'click','selector':'.recent-card:first-child'},
 {'op':'click','selector':'.status-panel button.button'},
 {'op':'click','selector':'.detail-heading .status-reviewing'},
 {'op':'click','selector':'.draft-panel button.button'},
 {'op':'click','selector':'#reply-draft'}],[marker,'Status changed: New → Reviewing','Deterministic demo-generated draft.'])
journey('customer-reload',login('alex@demo.local')+[
 {'op':'click','selector':'.customer-request:first-child'},
 {'op':'reload'},
 {'op':'click','selector':'.timeline'}],[marker,'Reviewing','Sam Green','Status changed: New → Reviewing'],'375')
print('Real-browser customer submission, provider update/draft, and customer reload/history passed. Run '+run_id)
