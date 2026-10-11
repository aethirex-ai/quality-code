import json
import pathlib
import tempfile
import unittest
from telemetry import extract, js_image_calls, FIELDS

ROOT = '00000000-0000-0000-0000-000000000001'
CHILD = '00000000-0000-0000-0000-000000000002'
GRANDCHILD = '00000000-0000-0000-0000-000000000003'
OTHER = '00000000-0000-0000-0000-000000000004'


def usage(inp=100, cache=20, out=10, reasoning=3, write=0):
    return dict(zip(FIELDS, (inp, cache, write, out, reasoning, inp + out)))


def event(kind, payload): return {'type': kind, 'payload': payload}


def snapshot(value, last=None):
    info = {'total_token_usage': value}
    if last is not None: info['last_token_usage'] = last
    return event('event_msg', {'type': 'token_count', 'info': info})


class AccountingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.directory = pathlib.Path(self.temp.name)
    def tearDown(self): self.temp.cleanup()
    def write(self, sid=ROOT, events=None, parent=None, suffix=''):
        meta = {'id': sid, 'source': 'exec'}
        if parent: meta['source'] = {'subagent': {'thread_spawn': {'parent_thread_id': parent}}}
        rows = [event('session_meta', meta)] + (events or [])
        path = self.directory / (sid + suffix + '.jsonl')
        path.write_text('\n'.join(json.dumps(v) for v in rows) + '\n')
        return path
    def model(self, name='gpt-6.1-sol'): return event('turn_context', {'model': name})
    def complete(self): return event('event_msg', {'type': 'task_complete'})
    def test_dedup_reasoning_subset_and_price(self):
        first = usage(); second = usage(200, 40, 20, 6)
        self.write(events=[self.model(), snapshot(first, first), snapshot(first, first),
                           snapshot(second, first), self.complete()])
        result = extract(self.directory, ROOT)
        self.assertEqual(result['tokens'], second)
        self.assertEqual(result['sessions'][0]['token_snapshots'], 2)
        self.assertEqual(result['standard_short_estimated_usd'], .000524)
        self.assertEqual(result['flags'], [])
    def test_malformed_payload_withholds_complete_claims(self):
        for payload in ([], None, 'invalid'):
            with self.subTest(payload=payload):
                self.write(events=[self.model(), snapshot(usage()),
                                   event('event_msg', payload), self.complete()])
                result = extract(self.directory, ROOT)
                self.assertIn('malformed_payload', result['flags'])
                self.assertIn('incomplete_or_inconsistent_cost_basis', result['flags'])
                self.assertIsNone(result['standard_short_estimated_usd'])
                self.assertIsNone(result['image_calls'])
                self.assertFalse(result['image_count_exact'])
                self.assertEqual(result['tokens'], usage())
    def test_model_change_uses_deltas(self):
        self.write(events=[self.model(), snapshot(usage()), self.model('gpt-6-luna'),
                           snapshot(usage(160, 30, 15, 4)), self.complete()])
        result = extract(self.directory, ROOT)
        self.assertEqual(result['models']['gpt-6.1-sol'], usage())
        self.assertEqual(result['models']['gpt-6-luna'], usage(60, 10, 5, 1))
    def test_tree_no_unrelated_body_read(self):
        self.write(events=[self.model(), snapshot(usage()), self.complete()])
        self.write(CHILD, [self.model('gpt-6-luna'), snapshot(usage()), self.complete()], ROOT)
        self.write(GRANDCHILD, [self.model('gpt-6-astra'), snapshot(usage()), self.complete()], CHILD)
        p = self.write(OTHER)
        with p.open('a') as stream: stream.write('this unrelated body is invalid\n')
        result = extract(self.directory, ROOT)
        self.assertEqual(result['session_counts'], {'root': 1, 'descendant': 2})
        self.assertEqual(result['tokens']['input_tokens'], 300)
        self.assertNotIn('malformed_rollout_line', result['flags'])
        serialized = json.dumps(result)
        self.assertNotIn(str(self.directory), serialized)
        self.assertNotIn(ROOT, serialized)
    def test_missing_model_and_tokens_flagged(self):
        self.write(events=[snapshot(usage()), snapshot({'input_tokens': 8})])
        result = extract(self.directory, ROOT)
        self.assertIn('unattributed_model_tokens', result['flags'])
        self.assertIn('missing_token_fields', result['flags'])
        self.assertIsNone(result['standard_short_estimated_usd'])
    def test_decreasing_and_inconsistent_counters(self):
        bad = usage(200); bad['total_tokens'] += 1
        self.write(events=[self.model(), snapshot(usage()), snapshot(usage(1, 0, 1, 0)),
                           snapshot(bad)])
        result = extract(self.directory, ROOT)
        self.assertIn('decreasing_cumulative_tokens', result['flags'])
        self.assertIn('inconsistent_total_tokens', result['flags'])
        self.assertIsNone(result['standard_short_estimated_usd'])
    def test_cache_writes_do_not_guess_price(self):
        self.write(events=[self.model(), snapshot(usage(write=5))])
        result = extract(self.directory, ROOT)
        self.assertEqual(result['tokens']['cache_write_input_tokens'], 5)
        self.assertIsNone(result['standard_short_estimated_usd'])
        self.assertIn('cache_write_partition_unverified', result['flags'])
    def test_cli_reconciles_root_only(self):
        self.write(events=[self.model(), snapshot(usage()), self.complete()])
        self.write(CHILD, [self.model(), snapshot(usage()), self.complete()], ROOT)
        self.assertEqual(extract(self.directory, ROOT, usage())['cli_root_reconciliation'], 'matched')
        mismatch = extract(self.directory, ROOT, usage(200))
        self.assertEqual(mismatch['cli_root_reconciliation'], 'mismatch')
        self.assertIsNone(mismatch['standard_short_estimated_usd'])
        self.assertIsNotNone(extract(self.directory, ROOT, usage())['standard_short_estimated_usd'])
        unknown = extract(self.directory, ROOT, {'unrecognized': 5})
        self.assertIsNone(unknown['standard_short_estimated_usd'])
    def test_missing_and_duplicate_roots(self):
        missing = extract(self.directory, ROOT)
        self.assertIn('missing_root_rollout', missing['flags'])
        self.assertFalse(missing['image_count_exact'])
        self.assertIsNone(missing['image_calls'])
        self.write(); self.write(suffix='-duplicate')
        result = extract(self.directory, ROOT)
        self.assertIn('duplicate_session_rollouts', result['flags'])
        self.assertEqual(result['tokens']['total_tokens'], 0)
        self.assertFalse(result['image_count_exact'])
        self.assertIsNone(result['image_calls'])
    def test_native_image_tool_calls_dedup(self):
        source = 'const prompt = "tools.image_gen__imagegen({})"; // tools.image_gen__imagegen({})\nconst r = await tools.image_gen__imagegen({prompt});'
        call = event('response_item', {'type': 'custom_tool_call', 'name': 'exec', 'call_id': 'c1', 'input': source})
        direct = event('response_item', {'type': 'function_call', 'name': 'image_gen.imagegen', 'call_id': 'c2', 'arguments': '{}'})
        self.write(events=[self.model(), snapshot(usage()), call, call, direct, self.complete()])
        result = extract(self.directory, ROOT)
        self.assertEqual(result['image_calls'], 2)
        self.assertTrue(result['image_count_exact'])
    def test_image_dynamic_execution_and_mentions(self):
        self.assertEqual(js_image_calls('/* tools.image_gen__imagegen({}) */ const x="tools.image_gen__imagegen({})";'), (0, False))
        self.assertEqual(js_image_calls('for (const x of xs) await tools.image_gen__imagegen(x);'), (1, True))
        self.assertEqual(js_image_calls('const f=tools.image_gen__imagegen; await f(x);'), (0, True))
        self.assertEqual(js_image_calls('function f(){return tools.image_gen__imagegen(x)}'), (1, True))
    def test_ambiguous_calls_withhold_actual_count(self):
        call = event('response_item', {'type': 'custom_tool_call', 'name': 'exec',
                     'call_id': 'x', 'input': 'for(const x of xs) await tools.image_gen__imagegen(x);'})
        self.write(events=[self.model(), snapshot(usage()), call])
        result = extract(self.directory, ROOT)
        self.assertIsNone(result['image_calls'])
        self.assertFalse(result['image_count_exact'])
        self.assertEqual(result['image_call_sites'], 1)

    def test_unobserved_completion_withholds_complete_cost(self):
        self.write(events=[self.model(), snapshot(usage())])
        result = extract(self.directory, ROOT, usage())
        self.assertIn('session_completion_unobserved', result['flags'])
        self.assertIsNone(result['standard_short_estimated_usd'])
        self.assertFalse(result['image_count_exact'])

    def spawn(self, result):
        return [event('response_item', {'type': 'function_call', 'name': 'spawn_agent',
                                       'call_id': 'spawn1', 'arguments': '{}'}),
                event('response_item', {'type': 'function_call_output', 'call_id': 'spawn1',
                                       'output': json.dumps(result)})]

    def test_matched_native_spawn_task_path(self):
        self.write(events=[self.model(), snapshot(usage()),
                           *self.spawn({'task_name': '/root/child'}), self.complete()])
        p = self.write(CHILD, [self.model(), snapshot(usage()), self.complete()], ROOT)
        rows = p.read_text().splitlines(); meta = json.loads(rows[0])
        meta['payload']['source']['subagent']['thread_spawn']['agent_path'] = '/root/child'
        rows[0] = json.dumps(meta); p.write_text('\n'.join(rows) + '\n')
        result = extract(self.directory, ROOT)
        self.assertEqual(result['spawn_reconciliation'],
                         {'successful_spawns': 1, 'matched_children': 1, 'status': 'matched'})
        self.assertIsNotNone(result['standard_short_estimated_usd'])
        self.assertNotIn('/root/child', json.dumps(result))

    def test_missing_spawn_child_withholds_totals(self):
        self.write(events=[self.model(), snapshot(usage()),
                           *self.spawn({'task_name': '/root/absent'}), self.complete()])
        result = extract(self.directory, ROOT)
        self.assertIn('missing_spawn_child', result['flags'])
        self.assertIsNone(result['standard_short_estimated_usd'])
        self.assertFalse(result['image_count_exact'])
        self.assertIsNone(result['image_calls'])

    def test_spawn_uuid_requires_correct_parent(self):
        self.write(events=[self.model(), snapshot(usage()),
                           *self.spawn({'thread_id': GRANDCHILD}), self.complete()])
        self.write(CHILD, [self.model(), snapshot(usage()), self.complete()], ROOT)
        self.write(GRANDCHILD, [self.model(), snapshot(usage()), self.complete()], CHILD)
        self.assertIn('missing_spawn_child', extract(self.directory, ROOT)['flags'])
        self.write(events=[self.model(), snapshot(usage()),
                           *self.spawn({'agent_id': CHILD}), self.complete()])
        self.assertEqual(extract(self.directory, ROOT)['spawn_reconciliation']['matched_children'], 1)

    def test_missing_spawn_output_withholds_cost(self):
        self.write(events=[self.model(), snapshot(usage()), self.spawn({'thread_id': CHILD})[0],
                           self.complete()])
        result = extract(self.directory, ROOT)
        self.assertIn('missing_spawn_output', result['flags'])
        self.assertIsNone(result['standard_short_estimated_usd'])

    def test_unknown_spawn_success_is_ambiguous(self):
        self.write(events=[self.model(), snapshot(usage()),
                           *self.spawn({'success': True}), self.complete()])
        result = extract(self.directory, ROOT)
        self.assertIn('ambiguous_spawn_result', result['flags'])
        self.assertIsNone(result['standard_short_estimated_usd'])

    def test_cli_reasoning_and_cache_write_reconciled(self):
        self.write(events=[self.model(), snapshot(usage()), self.complete()])
        for field in ('reasoning_output_tokens', 'cache_write_input_tokens'):
            result = extract(self.directory, ROOT, {field: 9})
            self.assertEqual(result['cli_root_reconciliation'], 'mismatch')
            self.assertIsNone(result['standard_short_estimated_usd'])

    def test_later_active_turn_is_incomplete(self):
        self.write(events=[self.model(), snapshot(usage()), self.complete(),
                           event('event_msg', {'type': 'task_started'})])
        self.assertIsNone(extract(self.directory, ROOT)['standard_short_estimated_usd'])

    def test_native_spawn_source_is_explicit_parentage(self):
        self.write(events=[self.model(), snapshot(usage()), self.complete()])
        p = self.write(CHILD, [self.model(), snapshot(usage()), self.complete()])
        rows = p.read_text().splitlines(); meta = json.loads(rows[0])
        meta['payload']['source'] = {'subagent': {'spawn': {'parent_thread_id': ROOT}}}
        rows[0] = json.dumps(meta); p.write_text('\n'.join(rows) + '\n')
        self.assertEqual(extract(self.directory, ROOT)['session_counts'], {'root': 1, 'descendant': 1})

    def test_invalid_partitions_withhold_price(self):
        for value, flag in [(usage(cache=101), 'cached_exceeds_input'),
                            (usage(reasoning=11), 'reasoning_exceeds_output')]:
            self.write(events=[self.model(), snapshot(value), self.complete()])
            result = extract(self.directory, ROOT)
            self.assertIn(flag, result['flags'])
            self.assertIsNone(result['standard_short_estimated_usd'])

    def test_ambiguous_child_lineage_withholds_price(self):
        self.write(events=[self.model(), snapshot(usage()), self.complete()])
        p = self.write(CHILD, [self.model(), snapshot(usage()), self.complete()], ROOT)
        rows = p.read_text().splitlines()
        meta = json.loads(rows[0])
        meta['payload']['creator'] = {'parent_thread_id': OTHER}
        rows[0] = json.dumps(meta); p.write_text('\n'.join(rows) + '\n')
        result = extract(self.directory, ROOT)
        self.assertIn('ambiguous_lineage', result['flags'])
        self.assertIn('missing_tree_node', result['flags'])
        self.assertIsNone(result['standard_short_estimated_usd'])
        self.assertFalse(result['image_count_exact'])

    def test_creator_ids_are_not_inferred_parentage(self):
        self.write(events=[self.model(), snapshot(usage()), self.complete()])
        p = self.write(CHILD)
        rows = p.read_text().splitlines(); meta = json.loads(rows[0])
        meta['payload'].update(creator_ids=[ROOT], creator_thread_id=ROOT)
        rows[0] = json.dumps(meta); p.write_text('\n'.join(rows) + '\n')
        self.assertEqual(extract(self.directory, ROOT)['session_counts'], {'root': 1})

    def test_image_result_handling_does_not_change_call_count(self):
        source = 'const r=await tools.image_gen__imagegen({}); text(r.hint ? r.hint : \"none\");'
        self.assertEqual(js_image_calls(source), (1, False))

    def test_regex_literal_withholds_count(self):
        self.assertTrue(js_image_calls('const r=/tools.image_gen__imagegen(x)/;')[1])

    def test_long_request_pricing_is_not_guessed(self):
        self.write(events=[self.model(), snapshot(usage(300000))])
        result = extract(self.directory, ROOT)
        self.assertIsNone(result['standard_short_estimated_usd'])
        self.assertIn('standard_short_pricing_inapplicable', result['flags'])


if __name__ == '__main__': unittest.main()
