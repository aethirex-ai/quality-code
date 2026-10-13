"""Post-run portal accounting. Native transcripts remain private.

Raw check counts/recoveries are observations awaiting independent cause review,
not defect counts. Cached input and reasoning output are subsets, not additions.
"""
import argparse
import hashlib
import json
import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import telemetry

ROOT = Path(__file__).resolve().parent
OWNERS = ('backend', 'frontend', 'integration')
EVIDENCE = tuple(f'{owner}/check-runs.jsonl' for owner in OWNERS) + (
    'evidence/issues.jsonl', '.preview-events.jsonl')
EXCLUDED_PARTS = {'.git', '__pycache__', '.preview-mailbox', 'node_modules',
                  '.codex', '.agents', '.aws', '.venv', 'venv'}


def records(path):
    if path.is_symlink():
        raise ValueError('Evidence cannot be a symlink')
    if not path.exists():
        return None
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError('Evidence records must be objects')
    return rows


def evidence_path(site, relative):
    for n in range(len(Path(relative).parts) + 1):
        if (site / Path(*Path(relative).parts[:n])).is_symlink():
            raise ValueError('Evidence symlinks forbidden')
    return site / relative


def iteration_summary(site, start_unix=None, end_unix=None):
    issues = records(evidence_path(site, 'evidence/issues.jsonl'))
    grouped = {}
    for row in issues or []:
        if not isinstance(row.get('id'), str) or not row['id'] or row.get('owner') not in OWNERS:
            raise ValueError('Issue requires stable id and known owner')
        grouped.setdefault(row['id'], []).append(row)
    owners = {}
    for owner in OWNERS:
        checks = records(evidence_path(site, f'{owner}/check-runs.jsonl'))
        waiting, cycles = {}, []
        for row in checks or []:
            if (row.get('owner') != owner or not isinstance(row.get('check_id'), str)
                    or row.get('phase') not in ('initial', 'verification', 'recheck')
                    or type(row.get('exit_code')) is not int):
                raise ValueError('Invalid check history record')
            if row['phase'] == 'initial':
                continue
            key = row['check_id']
            if row['exit_code'] != 0:
                waiting.setdefault(key, []).append(row)
            elif key in waiting:
                cycles.append({'check_id': key, 'failed_runs': len(waiting.pop(key)),
                               'recheck_phase': row['phase'], 'issue_id': row.get('issue_id')})
        owners[owner] = {
            'check_history_present': checks is not None,
            'recorded_check_runs': len(checks) if checks is not None else None,
            'initial_scaffold_nonzero_exits': sum(r['exit_code'] != 0 and r['phase'] == 'initial' for r in checks) if checks is not None else None,
            'verification_nonzero_exits': sum(r['exit_code'] != 0 and r['phase'] != 'initial' for r in checks) if checks is not None else None,
            'passing_runs': sum(r['exit_code'] == 0 for r in checks) if checks is not None else None,
            'observed_check_recovery_sequences': cycles if checks is not None else None,
            'unrecovered_check_ids': sorted(waiting) if checks is not None else None,
            'reported_issue_ids': sorted(k for k, rows in grouped.items() if any(r['owner'] == owner for r in rows)) if issues is not None else None}
    previews = records(evidence_path(site, '.preview-events.jsonl'))
    timed = outside = None
    if previews is not None and start_unix is not None and end_unix is not None:
        timed = outside = 0
        try:
            for row in previews:
                moment = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
                if moment.tzinfo is None:
                    raise ValueError('Preview time lacks zone')
                if start_unix <= moment.timestamp() <= end_unix:
                    timed += 1
                else:
                    outside += 1
        except (KeyError, TypeError, ValueError):
            timed = outside = None
    return {'owners': owners, 'issue_history_present': issues is not None,
            'distinct_reported_issue_ids': len(grouped) if issues is not None else None,
            'latest_reported_statuses': {k: rows[-1].get('status') for k, rows in grouped.items()} if issues is not None else None,
            'preview_history_present': previews is not None,
            'recorded_previews': len(previews) if previews is not None else None,
            'timed_recorded_previews': timed, 'outside_timer_recorded_previews': outside,
            'preview_timing_unknown': previews is not None and timed is None,
            'classification_pending_independent_review': True,
            'limits': 'Raw observations only. Independent review must distinguish product defects, visual refinements, tooling errors, expected negative/construction failures, duplicate causes and unresolved final errors.'}


def native_accounting(sessions, root, usage):
    """Select by explicit metadata lineage across dates before reading bodies."""
    entries = {}
    for path in sorted(Path(sessions).rglob('*.jsonl')):
        if path.is_symlink():
            continue
        try:
            with path.open() as stream:
                first = json.loads(stream.readline())
            meta = first.get('payload')
            if first.get('type') == 'session_meta' and isinstance(meta, dict) and isinstance(meta.get('id'), str):
                entries.setdefault(meta['id'], []).append((path, meta))
        except (OSError, ValueError, AttributeError):
            continue
    selected = {root}
    while True:
        found = {sid for sid, rows in entries.items() if any(telemetry.parent_ids(meta) & selected for _, meta in rows)}
        if found <= selected:
            break
        selected |= found
    hashes = []
    with tempfile.TemporaryDirectory(prefix='portal-accounting-') as folder:
        for sid in sorted(selected):
            for path, _ in entries.get(sid, []):
                # The temporary links expose only selected bodies to the extractor.
                index = len(hashes)
                (Path(folder) / f'{index}.jsonl').symlink_to(path.resolve())
                hashes.append({'role': 'root' if sid == root else 'descendant',
                               'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        account = telemetry.extract(folder, root, usage)
    incomplete = {'missing_root_rollout', 'duplicate_session_rollouts', 'missing_tree_node',
                  'missing_spawn_child', 'ambiguous_lineage', 'ambiguous_spawn_result',
                  'missing_spawn_output', 'missing_token_telemetry', 'missing_token_fields',
                  'missing_token_snapshot', 'malformed_rollout_line', 'malformed_payload',
                  'decreasing_cumulative_tokens', 'session_completion_unobserved',
                  'inconsistent_total_tokens', 'invalid_or_negative_tokens',
                  'snapshot_delta_differs_from_last_usage', 'cli_root_usage_mismatch',
                  'cli_usage_unrecognized', 'cached_exceeds_input',
                  'reasoning_exceeds_output', 'cache_write_partition_unverified'}
    account['tokens_complete'] = not bool(incomplete & set(account['flags']))
    account['observed_tokens'] = account['tokens']
    if not account['tokens_complete']:
        account['tokens'] = None
    account['native_evidence_sha256'] = hashes
    account['native_evidence_policy'] = 'Selected native logs retained privately at their original location; only hashes/aggregate counters published.'
    return account


def cost_components(account, prices):
    """Compute each dated price component independently with Decimal."""
    if account['standard_short_estimated_usd'] is None:
        return None
    if (prices.get('currency') != 'USD' or prices.get('unit_tokens') != 1000000
            or not prices.get('checked_date') or prices.get('rate_order') !=
            ['ordinary_input', 'cached_input', 'cache_write_input', 'output']):
        raise ValueError('Unrecognized dated pricing basis')
    total = {key: Decimal(0) for key in ('uncached_input', 'cached_input', 'output_including_reasoning')}
    components = {}
    for model, tokens in account['models'].items():
        rates = [Decimal(str(v)) for v in prices['models'][model]['short']]
        if len(rates) != 4 or any(not v.is_finite() or v < 0 for v in rates):
            raise ValueError('Invalid rates')
        if tokens['cache_write_input_tokens'] or tokens['cached_input_tokens'] > tokens['input_tokens'] or tokens['reasoning_output_tokens'] > tokens['output_tokens']:
            raise ValueError('Unverified token partition')
        row = {'uncached_input': Decimal(tokens['input_tokens'] - tokens['cached_input_tokens']) * rates[0] / 1000000,
               'cached_input': Decimal(tokens['cached_input_tokens']) * rates[1] / 1000000,
               'output_including_reasoning': Decimal(tokens['output_tokens']) * rates[3] / 1000000}
        components[model] = {k: str(v) for k, v in row.items()}
        components[model]['total'] = str(sum(row.values()))
        for key in total:
            total[key] += row[key]
    estimate = sum(total.values())
    if abs(estimate - Decimal(str(account['standard_short_estimated_usd']))) > Decimal('0.0000000005'):
        raise ValueError('Independent Decimal price mismatch')
    return {'checked_date': prices['checked_date'], 'source': prices['source'],
            'by_model': components, 'total': {k: str(v) for k, v in total.items()},
            'estimated_total': str(estimate), 'exclusions': prices['exclusions']}


def source_hashes(site):
    hashes = {}
    for path in sorted(site.rglob('*')):
        relative = path.relative_to(site)
        if any(part in EXCLUDED_PARTS for part in relative.parts) or str(relative) in EVIDENCE:
            continue
        if path.is_symlink():
            raise ValueError('Source symlinks require independent privacy review')
        if not path.is_file():
            continue
        # Runtime credentials/state and private logs are not publishable source.
        if path.suffix.lower() in ('.db', '.sqlite', '.sqlite3', '.log') or path.name.endswith(('-wal', '-shm', '-journal')) or path.name.startswith('.env') or 'cookie' in path.name.lower() or any(part in ('cookies', 'private-logs', 'runtime') for part in relative.parts):
            continue
        hashes[str(relative)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def freeze_evidence(directory, site):
    hashes = {}
    for relative in EVIDENCE:
        path = evidence_path(site, relative)
        hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    manifest = {'sources_sha256': source_hashes(site), 'raw_evidence_sha256': hashes,
                'excluded_runtime_state': True}
    frozen = directory / 'frozen-output-hashes.json'
    if frozen.exists() and json.loads(frozen.read_text()) != manifest:
        raise ValueError('Frozen output/evidence changed; refusing to replace original')
    raw = directory / 'accounting-evidence'
    if raw.is_symlink() or any((raw / relative).parent.is_symlink() for relative in EVIDENCE):
        raise ValueError('Evidence destination directory symlink forbidden')
    for relative, digest in hashes.items():
        if digest is None:
            continue
        target = raw / relative
        if target.is_symlink():
            raise ValueError('Evidence destination symlink forbidden')
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise ValueError('Preserved raw evidence changed')
    raw.mkdir(exist_ok=True)
    for relative, digest in hashes.items():
        if digest is not None:
            target = raw / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.write_bytes((site / relative).read_bytes())
    if not frozen.exists():
        frozen.write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


def collect(condition, sessions):
    if condition not in ('single', 'adaptive'):
        raise ValueError('Unknown condition')
    directory = ROOT / 'runs' / condition
    meta = json.loads((directory / 'metadata.json').read_text())
    if not isinstance(meta.get('end_unix'), (int, float)):
        raise ValueError('Refusing complete accounting for active condition')
    events = records(directory / 'events.jsonl')
    if events is None:
        raise ValueError('Missing native root events')
    roots = [e['thread_id'] for e in events if e.get('type') == 'thread.started']
    completions = [e.get('usage') for e in events if e.get('type') == 'turn.completed']
    if len(roots) != 1:
        raise ValueError('Expected exactly one native root')
    account = native_accounting(sessions, roots[0], completions[0] if len(completions) == 1 else None)
    if len(completions) != 1 or not isinstance(completions[0], dict):
        account['flags'] = sorted(set(account['flags']) | {'cli_completion_missing_or_duplicated'})
        account['standard_short_estimated_usd'] = None
        account['tokens_complete'] = False
        account['tokens'] = None
    account['cost_components_usd'] = cost_components(account, json.loads((ROOT / 'prices.json').read_text()))
    account['iteration_evidence'] = iteration_summary(directory / 'site', meta.get('start_unix'), meta['end_unix'])
    freeze_evidence(directory, directory / 'site')
    (directory / 'telemetry.json').write_text(json.dumps(account, indent=2) + '\n')
    return account


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('condition', choices=['single', 'adaptive'])
    parser.add_argument('--sessions-dir', required=True, help='Native session root, including dated subdirectories')
    args = parser.parse_args()
    result = collect(args.condition, args.sessions_dir)
    print(json.dumps({key: result[key] for key in ('tokens', 'models', 'standard_short_estimated_usd', 'cost_components_usd', 'image_calls', 'flags')}))
