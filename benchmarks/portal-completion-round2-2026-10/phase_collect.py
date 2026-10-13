"""Exact native phase/lineage accounting; resumed cumulative roots counted once.

Private transcripts are selected only by explicit native IDs and ancestry. Unknown
or inconsistent counters withhold totals and prices rather than imputing them.
"""
import argparse
import hashlib
import json
from pathlib import Path
import collect as legacy
import telemetry

ROOT = Path(__file__).resolve().parent
FIELDS = telemetry.FIELDS


def source_hashes(site):
    """Product/source inventory excludes generated evidence, runtime and secrets."""
    result = legacy.source_hashes(site)
    return {path: digest for path, digest in result.items()
            if not (path.startswith(('.quality/audit/', '.quality/audits/', 'evidence/',
                                     'backend/check-', 'frontend/check-', 'integration/check-',
                                     '.preview-', 'artifacts/', 'output/', 'test-results/'))
                    or path in ('.quality/audit-packet.json', '.quality/audit-result.json')
                    or Path(path).suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp', '.pdf')
                    and path.startswith(('screenshots/', 'reports/')))}


def validated_counter(value):
    flags = set()
    result = telemetry.validate_usage(value, flags)
    if flags or result is None:
        raise ValueError('Invalid authoritative native counter: ' + ','.join(sorted(flags)))
    return result


def reconcile_phases(phases):
    """Reconcile CLI per-phase increments or evidenced cumulative snapshots."""
    flags = set()
    roots = {}
    summaries = []
    seen_auditors = set()
    builder = None
    for phase in phases:
        row = {key: phase.get(key) for key in ('number', 'role', 'root_id', 'state', 'elapsed_seconds')}
        summaries.append(row)
        root = phase.get('root_id')
        if not telemetry.UUID.fullmatch(root or ''):
            flags.add('phase_root_missing'); continue
        if phase.get('state') != 'completed':
            flags.add('phase_completion_unobserved')
        role = phase.get('role')
        if role == 'auditor':
            if root == builder or root in seen_auditors or phase.get('resume_root'):
                flags.add('audit_independence_violated')
            seen_auditors.add(root)
        elif role == 'builder':
            if root in seen_auditors or builder and root != builder:
                flags.add('builder_restart_or_role_collision')
            if builder and phase.get('resume_root') != builder:
                flags.add('builder_exact_resume_missing')
            if not builder and phase.get('resume_root'):
                flags.add('initial_builder_is_resume')
            builder = root
        else:
            flags.add('unknown_phase_role')
        try:
            after = phase['native_after']
            if after['id'] != root:
                raise ValueError('Snapshot root mismatch')
            final = validated_counter(after['cumulative_usage'])
            previous = roots.get(root)
            if previous:
                before = phase['native_before']
                if before['id'] != root or before['cumulative_usage'] != previous['cumulative_usage']:
                    raise ValueError('Resume baseline changed between owned phases')
                if before['rollout_sha256'] != previous['rollout_sha256'] or before['rollout_bytes'] != previous['rollout_bytes']:
                    raise ValueError('Resume rollout changed outside phase')
                initial = validated_counter(before['cumulative_usage'])
                if after['rollout_bytes'] < before['rollout_bytes']:
                    raise ValueError('Resume transcript truncated')
            else:
                if phase.get('native_before') is not None:
                    raise ValueError('Foreign native baseline')
                initial = dict.fromkeys(FIELDS, 0)
            delta = {k: final[k] - initial[k] for k in FIELDS}
            validated_counter(delta)
            cli = phase.get('cli_usage')
            required_cli = ('input_tokens', 'cached_input_tokens', 'output_tokens')
            if not isinstance(cli, dict) or not all(type(cli.get(k)) is int and cli[k] >= 0 for k in required_cli):
                raise ValueError('CLI completion counters missing')
            keys = [k for k in FIELDS if k in cli]
            if any(type(cli[k]) is not int for k in keys):
                raise ValueError('CLI counter is not integer')
            increment_match = all(cli[k] == delta[k] for k in keys)
            cumulative_match = all(cli[k] == final[k] for k in keys)
            if not increment_match and not cumulative_match:
                raise ValueError('CLI/native phase counters mismatch')
            row.update(observed_native_delta=delta,
                       cli_counter_basis='phase_increment' if increment_match else 'root_cumulative',
                       actual_models=after.get('actual_models', []))
            roots[root] = after
        except (KeyError, TypeError, ValueError) as exc:
            row['accounting_error'] = str(exc)
            flags.add('phase_counter_reconciliation_failed')
    if not builder or not seen_auditors:
        flags.add('required_builder_or_independent_auditor_missing')
    return roots, summaries, flags


def explicit_tree_ids(sessions, root):
    # Native metadata inventory avoids loading unrelated transcript bodies.
    from run import session_index
    entries = session_index(sessions)
    selected = {root}
    while True:
        found = {sid for sid, rows in entries.items()
                 if any(telemetry.parent_ids(meta) & selected for _, meta in rows)}
        if found <= selected:
            return selected
        selected |= found


def collect(condition, sessions):
    if condition not in ('single', 'adaptive'):
        raise ValueError('Unknown condition')
    directory = ROOT / 'runs' / condition
    meta = json.loads((directory / 'metadata.json').read_text())
    if not isinstance(meta.get('end_unix'), (float, int)):
        raise ValueError('Refusing complete accounting for active condition')
    roots, phases, flags = reconcile_phases(meta.get('phases', []))
    accounts = []
    selected = set()
    for root, snapshot in roots.items():
        tree_ids = explicit_tree_ids(sessions, root)
        if selected & tree_ids:
            flags.add('overlapping_owned_native_trees')
        selected |= tree_ids
        # Root cumulative total is authoritative exactly once, across all resumes.
        account = legacy.native_accounting(sessions, root, snapshot['cumulative_usage'])
        accounts.append({'root_id': root, 'account': account})
        flags.update(account['flags'])
        if not account['tokens_complete']:
            flags.add('native_tree_tokens_incomplete')
    models = {}
    observed = dict.fromkeys(FIELDS, 0)
    for tree in accounts:
        account = tree['account']
        for model, usage in account['models'].items():
            bucket = models.setdefault(model, dict.fromkeys(FIELDS, 0))
            for field in FIELDS:
                bucket[field] += usage[field]
                observed[field] += usage[field]
    # Unknown model attribution also prevents authoritative totals/cost claims.
    incomplete = bool(flags - {'standard_short_pricing_inapplicable', 'unknown_model_price',
                               'image_execution_ambiguous', 'incomplete_or_inconsistent_cost_basis'})
    exact_cost = not incomplete and all(t['account']['standard_short_estimated_usd'] is not None for t in accounts)
    image_exact = not incomplete and all(t['account']['image_calls'] is not None for t in accounts)
    max_request = max((session['max_observed_request_input'] for tree in accounts for session in tree['account']['sessions']), default=0)
    combined_price = telemetry.estimate_price(models, set(flags), max_request) if exact_cost else None
    result = {'schema_version': 2, 'condition': condition, 'completion_state': meta.get('state', 'INCOMPLETE'),
              'initial_builder_seconds': meta.get('initial_builder_seconds'),
              'elapsed_seconds_including_audits_repairs_and_cleanup': meta['elapsed_seconds'],
              'initial_vs_accepted_comparable': meta.get('state') == 'PASS',
              'phases': phases, 'owned_root_ids': sorted(roots), 'owned_native_ids': sorted(selected),
              'implementation_root_count': 1 if meta.get('builder_root') else 0,
              'required_independent_auditor_count': len(meta.get('auditor_roots', [])),
              'trees': accounts, 'models': models, 'observed_tokens': observed,
              'tokens_complete': not incomplete, 'tokens': None if incomplete else observed,
              'standard_short_estimated_usd': combined_price,
              'image_calls': sum(t['account']['image_calls'] for t in accounts) if image_exact else None,
              'flags': sorted(flags),
              'accounting_policy': 'Each explicit native root and descendant counted once; resume snapshots reconciled with CLI phase counters. Required fresh auditors included. Missing/inconsistent evidence withholds totals and prices.'}
    result['cost_components_usd'] = legacy.cost_components(result, json.loads((ROOT / 'prices.json').read_text()))
    result['iteration_evidence'] = legacy.iteration_summary(directory / 'site', meta.get('start_unix'), meta['end_unix'])
    write_path = directory / 'telemetry.json'
    write_path.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('condition', choices=['single', 'adaptive'])
    parser.add_argument('--sessions-dir', required=True)
    args = parser.parse_args()
    result = collect(args.condition, args.sessions_dir)
    print(json.dumps({key: result[key] for key in ('completion_state', 'tokens', 'standard_short_estimated_usd', 'flags')}))
