"""Synchronous registrations for trusted Python/Node gate resource launches."""
import json
import os
import sys
import subprocess
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run import kernel_process_identity, process_inventory


def register(pid, parent):
    rows = process_inventory()
    row = rows.get(pid)
    owner = rows.get(parent)
    if row is None:
        status = subprocess.run(['ps', '-p', str(pid), '-o', 'stat='], capture_output=True, text=True, timeout=3)
        state = status.stdout.strip()
        if status.returncode not in (0, 1) or state and not state.startswith(('Z', 'X')):
            raise RuntimeError('Gate child creation identity unavailable while resource may remain live')
        return False
    if owner is None or row['parent'] != parent:
        raise RuntimeError('Gate child registration parent ownership uncertain')
    record = {'pid': pid, 'identity': row['identity'], 'group': row['group'], 'parent': parent,
              'parent_identity': owner['identity']}
    data = (json.dumps(record, separators=(',', ':')) + '\n').encode()
    for ledger in json.loads(os.environ.get('CODEX_GATE_LEDGERS', '[]')):
        descriptor = os.open(ledger, os.O_WRONLY | os.O_APPEND)
        try:
            if os.write(descriptor, data) != len(data):
                raise RuntimeError('Gate child registration incomplete')
        finally:
            os.close(descriptor)
    return True


if __name__ == '__main__':
    register(int(sys.argv[1]), int(sys.argv[2]))
