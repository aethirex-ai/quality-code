"""Record bounded local builder-check evidence, preserving every failure/recheck."""
import argparse,json,subprocess,time,re,uuid,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def run(owner,check_id,phase,issue_id,command):
 if owner not in ('backend','frontend','integration'):raise ValueError('Unknown owner')
 for value in [check_id]+([issue_id] if issue_id else []):
  if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',value):raise ValueError('Unsafe check or issue ID')
 if phase not in ('initial','verification','recheck') or not command:raise ValueError('Invalid phase or empty command')
 folder=ROOT/owner;folder.mkdir(exist_ok=True)
 if folder.is_symlink():raise ValueError('Owner folder cannot be a symlink')
 log=folder/'check-runs.jsonl'
 if log.is_symlink():raise ValueError('Check log cannot be a symlink')
 start=time.time();timed_out=False
 try:
  result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=120)
  code=result.returncode;out=result.stdout;err=result.stderr
 except subprocess.TimeoutExpired as e:
  code=124;timed_out=True;out=(e.stdout or b'').decode(errors='replace') if isinstance(e.stdout,bytes) else (e.stdout or '');err=(e.stderr or b'').decode(errors='replace') if isinstance(e.stderr,bytes) else (e.stderr or '')
 except OSError as e:
  code=127;out='';err=type(e).__name__+': '+str(e)
 record={'record_id':str(uuid.uuid4()),'owner':owner,'check_id':check_id,'phase':phase,'issue_id':issue_id,'command':command,'start_unix':start,'elapsed_seconds':time.time()-start,'exit_code':code,'timed_out':timed_out,'stdout':out[-3000:],'stderr':err[-3000:],'stdout_truncated':len(out)>3000,'stderr_truncated':len(err)>3000}
 with log.open('a') as f:f.write(json.dumps(record)+'\n')
 print(json.dumps({k:record[k] for k in ['owner','check_id','phase','issue_id','exit_code','elapsed_seconds','stdout','stderr','stdout_truncated','stderr_truncated']}))
 return code
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--owner',required=True);p.add_argument('--check-id',required=True);p.add_argument('--phase',default='verification',choices=['initial','verification','recheck']);p.add_argument('--issue-id');p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args();command=a.command[1:] if a.command[:1]==['--'] else a.command;sys.exit(run(a.owner,a.check_id,a.phase,a.issue_id,command))
