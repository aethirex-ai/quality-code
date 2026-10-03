#!/usr/bin/env python3
"""Check public distribution parity and local Markdown references, offline."""
from pathlib import Path
import re
from urllib.parse import unquote

root = Path(__file__).resolve().parents[1]
for source, copy in (('scripts/quality_code.py', '.quality/quality.py'), ('LICENSE', '.quality/LICENSE'),
                     ('assets/project/.quality/audit-result.schema.json', '.quality/audit-result.schema.json')):
    if (root / source).read_bytes() != (root / copy).read_bytes():
        raise SystemExit(f'FAIL: distribution drift: {source} != {copy}')
for document in root.rglob('*.md'):
    if '.git' in document.parts:
        continue
    for target in re.findall(r'\]\(([^)]+)\)', document.read_text()):
        if ':' in target or target.startswith('#'):
            continue
        local = unquote(target.split('#', 1)[0])
        if local and not (document.parent / local).exists():
            raise SystemExit(f'FAIL: broken reference in {document.relative_to(root)}: {target}')
print('PASS: distribution parity and local Markdown references')
