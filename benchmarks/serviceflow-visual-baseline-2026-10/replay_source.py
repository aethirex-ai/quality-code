#!/usr/bin/env python3
"""Reconstruct a public UI snapshot in a new local directory, without private harness."""
import argparse
import json
import pathlib
import shutil
import subprocess
import check_publication as checks


def replay(condition, stage, destination):
    if condition not in {'single', 'adaptive'} or stage not in {'initial', 'accepted'}:
        raise ValueError('Unknown condition or stage')
    destination = pathlib.Path(destination).resolve()
    if destination.exists():
        raise ValueError('Destination must not exist; preserve existing work')
    source = checks.ROOT / 'benchmarks/serviceflow-mvp-2026-10/apps' / condition
    if destination.is_relative_to(source):
        raise ValueError('Destination must be outside the frozen original app')
    manifest_path = checks.CASE / 'source' / condition / stage / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    patch = checks.within(manifest_path.parent, manifest['patch'])
    if checks.digest(patch) != manifest['patch_sha256']:
        raise ValueError('Patch hash mismatch')
    for entry in manifest['source_changes']:
        if entry['before_sha256'] is not None and checks.digest(checks.within(source, entry['path'])) != entry['before_sha256']:
            raise ValueError('Original source hash mismatch')
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns('.git', 'node_modules', '.env', '*.sqlite', '*.sqlite-*', '*.secret', '.npm-cache', '.preview-output', '__pycache__'))
    subprocess.run(['git', 'apply', '--check', str(patch)], cwd=destination, check=True, capture_output=True)
    subprocess.run(['git', 'apply', str(patch)], cwd=destination, check=True, capture_output=True)
    for entry in manifest['assets']:
        target = checks.within(destination, entry['path'])
        if entry.get('remove_asset'):
            target.unlink()
        else:
            base = checks.CASE if manifest.get('asset_paths_relative_to') == 'case directory' else manifest_path.parent
            asset = checks.within(base, entry['asset'])
            if checks.digest(asset) != entry['after_sha256']:
                raise ValueError('Asset hash mismatch')
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(asset, target)
    inventory = json.loads((checks.CASE / 'source-inventory.json').read_text())
    selected = next(item for item in inventory['stages'] if item['condition'] == condition and item['stage'] == stage)
    for entry in selected['files']:
        if checks.digest(checks.within(destination, entry['path'])) != entry['sha256']:
            raise ValueError('Reconstructed UI hash mismatch')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--condition', choices=['single', 'adaptive'], required=True)
    parser.add_argument('--stage', choices=['initial', 'accepted'], required=True)
    parser.add_argument('--destination', required=True)
    args = parser.parse_args()
    print(f'PASS: reconstructed {args.condition}/{args.stage} in {replay(args.condition, args.stage, args.destination)}')
