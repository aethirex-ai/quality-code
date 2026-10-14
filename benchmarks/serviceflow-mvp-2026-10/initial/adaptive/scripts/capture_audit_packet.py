"""Save the Quality Code CLI's full packet without truncating tool output."""
import json, subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
command=['./quality','audit-packet','--criteria-file','AUDIT_CRITERIA.md']
result=subprocess.run(command,cwd=root,capture_output=True,text=True,check=True)
packet=json.loads(result.stdout)
folder=root/'evidence';folder.mkdir(exist_ok=True)
path=folder/'audit-packet.json';path.write_text(json.dumps(packet,indent=2)+'\n')
assert packet['risk']=='critical' and packet['independent_audit_required']
assert set(packet['required_profiles'])=={'full','release'}
print(f"Saved full changed-scope packet: {path.relative_to(root)} ({len(packet['changed_files'])} files; critical; independent gate pending)")
