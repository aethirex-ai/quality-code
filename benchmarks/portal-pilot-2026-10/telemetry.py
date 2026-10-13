"""Read-only, sanitized Codex rollout accounting. No rollout text is emitted.

Snapshot deltas are authoritative; reasoning is a subset of output, cached is
subset of input. Unknown counters/model assignments are flagged, never imputed.
Image call counts are static executable call sites, with dynamic execution
ambiguity flagged. Prices supplied by benchmark protocol, USD / million.
"""
import argparse
import collections
import json
import pathlib
import re

FIELDS = ('input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
          'output_tokens', 'reasoning_output_tokens', 'total_tokens')
# Dated experimental rates, not provider/model defaults in the standard.
PRICES = {name: tuple(value['short']) for name, value in json.loads(pathlib.Path(__file__).with_name('prices.json').read_text())['models'].items()}
UUID = re.compile(r'^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$')


def parent_ids(meta):
    """Only explicit parent keys in source/creator are lineage evidence."""
    out = set()
    def visit(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in ('parent_thread_id', 'parent_session_id') and isinstance(child, str):
                    out.add(child)
                elif isinstance(child, (dict, list)):
                    visit(child)
        elif isinstance(value, list):
            for child in value: visit(child)
    visit(meta.get('source')); visit(meta.get('creator'))
    for key in ('parent_thread_id', 'parent_session_id'):
        if isinstance(meta.get(key), str): out.add(meta[key])
    return out


def agent_paths(meta):
    out = set()
    def visit(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key == 'agent_path' and isinstance(child, str): out.add(child)
                elif isinstance(child, (dict, list)): visit(child)
        elif isinstance(value, list):
            for child in value: visit(child)
    visit(meta.get('source')); visit(meta.get('creator'))
    return out


def discover(directory, root):
    """Read first lines only until explicitly identified as root/descendant."""
    entries = collections.defaultdict(list)
    for path in sorted(pathlib.Path(directory).glob('*.jsonl')):
        try:
            with path.open() as stream: first = json.loads(stream.readline())
            meta = first.get('payload', {})
            if first.get('type') == 'session_meta' and isinstance(meta.get('id'), str):
                entries[meta['id']].append((path, meta))
        except (OSError, ValueError):
            continue  # Unrelated malformed files carry no proven lineage.
    selected = {root}
    while True:
        found = {sid for sid, rows in entries.items()
                 if any(parent_ids(meta) & selected for _, meta in rows)}
        if found <= selected: break
        selected |= found
    return {sid: entries.get(sid, []) for sid in sorted(selected)}


def js_image_calls(source):
    """Lex strings/comments away; do not count prompt text or tool definitions."""
    # Template interpolation cannot safely be evaluated by this static scanner.
    template_ambiguity = any('${' in template and 'image_gen__imagegen' in template
                             for template in re.findall(r'`(?:\\.|[^`\\])*`', source))
    token = re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`')
    code = token.sub(' ', source)
    # Regex literals and computed accesses need a real JS parser; withhold
    # exact execution counts rather than mistake literal syntax for a call.
    regex_image_ambiguity = bool(re.search(
        r'/(?![/*])(?:\\.|[^/\\\n])*image_gen__imagegen(?:\\.|[^/\\\n])*/', code))
    matches = list(re.finditer(r'\btools\s*\.\s*image_gen__imagegen\s*\(', code))
    count = len(matches)
    ambiguous = template_ambiguity or regex_image_ambiguity or any(re.search(
        r'\b(for|while|if|switch|function)\b|=>|\?\s*[^.]', code[:match.start()])
        for match in matches)
    # Aliases/computed tool access cannot be reliably counted.
    ambiguous |= bool('image_gen__imagegen' in code and not count)
    return count, ambiguous


def validate_usage(raw, flags):
    if not isinstance(raw, dict):
        flags.add('missing_token_snapshot'); return None
    missing = [key for key in FIELDS if key not in raw]
    if missing:
        flags.add('missing_token_fields'); return None
    if any(type(raw[k]) is not int or raw[k] < 0 for k in FIELDS):
        flags.add('invalid_or_negative_tokens'); return None
    if raw['total_tokens'] != raw['input_tokens'] + raw['output_tokens']:
        flags.add('inconsistent_total_tokens')
    if raw['cached_input_tokens'] > raw['input_tokens']:
        flags.add('cached_exceeds_input')
    if raw['reasoning_output_tokens'] > raw['output_tokens']:
        flags.add('reasoning_exceeds_output')
    if raw['cache_write_input_tokens']:
        flags.add('cache_write_partition_unverified')
    return {k: raw[k] for k in FIELDS}


def extract_session(path, role):
    flags = set(); models = {}; previous = dict.fromkeys(FIELDS, 0)
    model = None; snapshots = 0; seen_calls = {}; images = 0
    role_counts = collections.Counter(); max_request = 0; completed = False
    spawn_calls = set(); spawn_outputs = {}; spawn_evidence = []
    with pathlib.Path(path).open() as stream:
        for line in stream:
            try: event = json.loads(line)
            except ValueError:
                flags.add('malformed_rollout_line'); continue
            payload = event.get('payload', {}); kind = event.get('type')
            if not isinstance(payload, dict):
                flags.add('malformed_payload'); continue
            if kind == 'turn_context':
                model = payload.get('model')
                if not isinstance(model, str) or not re.fullmatch(r'[a-zA-Z0-9_.:/-]{1,100}', model):
                    model = None; flags.add('missing_or_invalid_model')
            if kind == 'event_msg' and payload.get('type') in ('task_started', 'turn_started', 'turn_start'):
                completed = False
            if kind == 'event_msg' and payload.get('type') in ('task_complete', 'turn_complete'):
                completed = True
            if kind == 'event_msg' and payload.get('type') == 'token_count':
                info = payload.get('info')
                raw = info.get('total_token_usage') if isinstance(info, dict) else None
                usage = validate_usage(raw, flags)
                if usage is None: continue
                delta = {k: usage[k] - previous[k] for k in FIELDS}
                if any(v < 0 for v in delta.values()):
                    flags.add('decreasing_cumulative_tokens'); continue
                if not any(delta.values()): continue
                validate_usage(delta, flags)
                if isinstance(info.get('last_token_usage'), dict):
                    last = validate_usage(info['last_token_usage'], flags)
                    if last is not None and last != delta:
                        flags.add('snapshot_delta_differs_from_last_usage')
                max_request = max(max_request, delta['input_tokens'])
                bucket = model or 'unknown'
                if model is None: flags.add('unattributed_model_tokens')
                totals = models.setdefault(bucket, dict.fromkeys(FIELDS, 0))
                for key in FIELDS: totals[key] += delta[key]
                previous = usage; snapshots += 1
            if kind == 'response_item':
                if payload.get('type') == 'function_call' and payload.get('name') in (
                        'spawn_agent', 'collaboration.spawn_agent'):
                    if isinstance(payload.get('call_id'), str): spawn_calls.add(payload['call_id'])
                    else: flags.add('ambiguous_spawn_result')
                if payload.get('type') == 'function_call_output':
                    call_id = payload.get('call_id')
                    if call_id in spawn_calls:
                        output = payload.get('output')
                        if call_id in spawn_outputs:
                            if spawn_outputs[call_id] != output: flags.add('ambiguous_spawn_result')
                        else:
                            spawn_outputs[call_id] = output
                            try: result = json.loads(output) if isinstance(output, str) else output
                            except ValueError: result = None
                            if isinstance(result, dict) and result.get('error'):
                                pass  # Explicit unsuccessful spawn creates no child obligation.
                            elif isinstance(result, dict):
                                evidence = {}
                                if isinstance(result.get('task_name'), str) and result['task_name'].startswith('/root/'):
                                    evidence['task_name'] = result['task_name']
                                for key in ('thread_id', 'agent_id'):
                                    if isinstance(result.get(key), str) and UUID.fullmatch(result[key]):
                                        evidence[key] = result[key]
                                if evidence: spawn_evidence.append(evidence)
                                else: flags.add('ambiguous_spawn_result')
                            else: flags.add('ambiguous_spawn_result')
                if payload.get('role') in ('assistant', 'user', 'system', 'developer'):
                    role_counts[payload['role']] += 1
                if payload.get('type') not in ('custom_tool_call', 'function_call'): continue
                name = payload.get('name', '')
                if name not in ('exec', 'functions.exec', 'image_gen.imagegen', 'image_gen__imagegen'):
                    continue
                callid = payload.get('call_id') or payload.get('id')
                signature = (name, payload.get('input', payload.get('arguments', '')))
                if callid in seen_calls:
                    if seen_calls[callid] != signature: flags.add('conflicting_tool_call_id')
                    continue
                if callid is None: flags.add('missing_tool_call_id')
                else: seen_calls[callid] = signature
                if name in ('image_gen.imagegen', 'image_gen__imagegen'):
                    images += 1
                else:
                    source = signature[1]
                    if not isinstance(source, str): flags.add('invalid_custom_tool_input'); continue
                    count, ambiguous = js_image_calls(source)
                    images += count
                    if ambiguous: flags.add('image_execution_ambiguous')
    if spawn_calls - spawn_outputs.keys(): flags.add('missing_spawn_output')
    if not snapshots: flags.add('missing_token_telemetry')
    if not completed: flags.add('session_completion_unobserved')
    return {'role': role, 'models': models, 'message_roles': dict(role_counts),
            '_spawn_evidence': spawn_evidence,
            'token_snapshots': snapshots, 'image_call_sites': images,
            'max_observed_request_input': max_request, 'flags': sorted(flags)}


def estimate_price(models, flags, max_request):
    if max_request > 272000: flags.add('standard_short_pricing_inapplicable'); return None
    unreliable = {'missing_token_fields', 'invalid_or_negative_tokens', 'inconsistent_total_tokens',
                  'decreasing_cumulative_tokens', 'snapshot_delta_differs_from_last_usage',
                  'missing_token_telemetry', 'missing_root_rollout', 'duplicate_session_rollouts',
                  'malformed_rollout_line', 'malformed_payload', 'missing_token_snapshot',
                  'session_completion_unobserved', 'cli_root_usage_mismatch',
                  'cli_usage_unrecognized', 'cached_exceeds_input',
                  'reasoning_exceeds_output', 'unattributed_model_tokens',
                  'missing_or_invalid_model', 'ambiguous_lineage', 'missing_tree_node',
                  'missing_spawn_child', 'ambiguous_spawn_result', 'missing_spawn_output'}
    if flags & unreliable:
        flags.add('incomplete_or_inconsistent_cost_basis'); return None
    cost = 0.0
    for model, usage in models.items():
        if model not in PRICES: flags.add('unknown_model_price'); return None
        if usage['cache_write_input_tokens']:
            flags.add('cache_write_partition_unverified'); return None
        if usage['cached_input_tokens'] > usage['input_tokens']: return None
        inp, cached, _, out = PRICES[model]
        cost += ((usage['input_tokens'] - usage['cached_input_tokens']) * inp +
                 usage['cached_input_tokens'] * cached + usage['output_tokens'] * out) / 1e6
    return round(cost, 9)


def extract(directory, root, cli_usage=None):
    if not UUID.fullmatch(root): raise ValueError('root must be a thread UUID')
    selected = discover(directory, root); sessions = []; flags = set()
    expected_spawns = matched_spawns = 0
    matched_child_ids = set()
    for sid, rows in selected.items():
        if not rows: flags.add('missing_root_rollout'); continue
        if len(rows) != 1:
            flags.add('duplicate_session_rollouts'); continue  # No arbitrary winner.
        if sid != root:
            parents = parent_ids(rows[0][1])
            if len(parents) != 1:
                flags.add('ambiguous_lineage')
            if parents - selected.keys():
                flags.add('missing_tree_node')
        session = extract_session(rows[0][0], 'root' if sid == root else 'descendant')
        sessions.append(session); flags.update(session['flags'])
        for evidence in session.pop('_spawn_evidence'):
            expected_spawns += 1
            matches = []
            for child_id, child_rows in selected.items():
                if child_id == sid or len(child_rows) != 1: continue
                meta = child_rows[0][1]
                if parent_ids(meta) != {sid}: continue
                if 'task_name' in evidence and evidence['task_name'] not in agent_paths(meta): continue
                if any(evidence[key] != child_id for key in ('thread_id', 'agent_id') if key in evidence): continue
                matches.append(child_id)
            if len(matches) == 1:
                if matches[0] in matched_child_ids:
                    flags.add('ambiguous_spawn_result')
                else:
                    matched_child_ids.add(matches[0]); matched_spawns += 1
            elif not matches: flags.add('missing_spawn_child')
            else: flags.add('ambiguous_spawn_result')
    models = {}; totals = dict.fromkeys(FIELDS, 0)
    for session in sessions:
        for model, usage in session['models'].items():
            bucket = models.setdefault(model, dict.fromkeys(FIELDS, 0))
            for key in FIELDS: bucket[key] += usage[key]; totals[key] += usage[key]
    reconciliation = 'not_supplied'
    if cli_usage is not None:
        reconciliation = 'matched'
        roots = [s for s in sessions if s['role'] == 'root']
        root_totals = {k: sum(v[k] for s in roots for v in s['models'].values()) for k in FIELDS}
        mapping = {key: key for key in FIELDS}
        compared = False
        for source, target in mapping.items():
            if source in cli_usage:
                compared = True
                if type(cli_usage[source]) is not int or cli_usage[source] != root_totals[target]:
                    reconciliation = 'mismatch'; flags.add('cli_root_usage_mismatch')
        if not compared: reconciliation = 'unrecognized'; flags.add('cli_usage_unrecognized')
    image_inexact = {'image_execution_ambiguous', 'missing_tool_call_id',
                     'conflicting_tool_call_id', 'missing_root_rollout',
                     'duplicate_session_rollouts', 'missing_tree_node',
                     'ambiguous_lineage', 'session_completion_unobserved',
                     'malformed_rollout_line', 'malformed_payload', 'invalid_custom_tool_input',
                     'missing_spawn_child', 'ambiguous_spawn_result', 'missing_spawn_output'}
    max_request = max((s['max_observed_request_input'] for s in sessions), default=0)
    price = estimate_price(models, flags, max_request) if models else None
    return {'schema_version': 1, 'session_counts': dict(collections.Counter(s['role'] for s in sessions)),
            'models': models, 'tokens': totals, 'sessions': sessions,
            'image_calls': (None if image_inexact & flags
                            else sum(s['image_call_sites'] for s in sessions)),
            'image_call_sites': sum(s['image_call_sites'] for s in sessions),
            'image_count_exact': not bool(image_inexact & flags),
            'cli_root_reconciliation': reconciliation,
            'spawn_reconciliation': {'successful_spawns': expected_spawns,
                                     'matched_children': matched_spawns,
                                     'status': ('unverified' if {'missing_spawn_child', 'ambiguous_spawn_result',
                                                                'missing_spawn_output'} & flags else 'matched')},
            'standard_short_estimated_usd': price, 'flags': sorted(flags)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sessions-dir', required=True)
    parser.add_argument('--root-thread-id', required=True)
    parser.add_argument('--cli-usage-json', help='JSON file containing turn.completed usage or event')
    args = parser.parse_args()
    usage = None
    if args.cli_usage_json:
        with open(args.cli_usage_json) as stream: usage = json.load(stream)
        usage = usage.get('usage', usage)
    print(json.dumps(extract(args.sessions_dir, args.root_thread_id, usage), indent=2, sort_keys=True))


if __name__ == '__main__': main()
