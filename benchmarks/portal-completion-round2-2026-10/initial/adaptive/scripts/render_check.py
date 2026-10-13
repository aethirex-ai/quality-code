"""Run the fixed-origin preview and retain bounded real-browser observations."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('name');parser.add_argument('--viewport',type=int,choices=(375,1440),default=1440)
    parser.add_argument('--actions');parser.add_argument('--contains',action='append',default=[])
    args=parser.parse_args()
    command=[sys.executable,'preview_client.py','--workspace','.','--viewport',str(args.viewport)]
    if args.actions:command+=['--actions-file',args.actions]
    result=subprocess.run(command,text=True,capture_output=True,timeout=80)
    data=json.loads(result.stdout)
    directory=Path('evidence/renders');directory.mkdir(parents=True,exist_ok=True)
    report=directory/(args.name+'.json');report.write_text(json.dumps(data,indent=2)+'\n')
    errors=[]
    if result.returncode or not data.get('ok'):errors.append('Preview failed: '+str(data))
    if data.get('horizontalOverflow'):errors.append('Horizontal overflow: '+str(data.get('overflowingElements')))
    if data.get('errors'):errors.append('Browser errors: '+str(data['errors']))
    if data.get('blockedRequests'):errors.append('Unexpected external requests: '+str(data['blockedRequests']))
    if any(not a.get('ok') for a in data.get('actionResults',[])):errors.append('Failed browser action')
    for needle in args.contains:
        if needle not in data.get('excerpt',''):errors.append('Expected visible text missing from bounded excerpt: '+needle)
    print(json.dumps({'report':str(report),'screenshot':data.get('screenshot'),'actions':data.get('actionResults'), 'viewport':args.viewport,'errors':errors}))
    return 1 if errors else 0
if __name__=='__main__':sys.exit(main())
