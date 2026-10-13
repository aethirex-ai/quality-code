import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import collect
from test_telemetry import ROOT, CHILD, OTHER, usage, event, snapshot


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.site = self.base / 'site'
        self.site.mkdir()
    def tearDown(self):
        self.temp.cleanup()
    def write_jsonl(self, path, rows):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    def rollout(self, path, sid, parent=None, model='gpt-6.1-sol'):
        meta = {'id': sid}
        if parent:
            meta['source'] = {'subagent': {'spawn': {'parent_thread_id': parent}}}
        self.write_jsonl(path, [event('session_meta', meta), event('turn_context', {'model': model}), snapshot(usage()), event('event_msg', {'type': 'task_complete'})])
    def check(self, code, phase='verification', check_id='api'):
        return {'owner': 'backend', 'check_id': check_id, 'phase': phase, 'exit_code': code}
    def test_missing_is_unknown_and_present_empty_is_zero(self):
        summary = collect.iteration_summary(self.site)
        self.assertIsNone(summary['owners']['backend']['recorded_check_runs'])
        self.assertIsNone(summary['distinct_reported_issue_ids'])
        self.assertIsNone(summary['recorded_previews'])
        self.write_jsonl(self.site / 'backend/check-runs.jsonl', [])
        self.assertEqual(collect.iteration_summary(self.site)['owners']['backend']['recorded_check_runs'], 0)
    def test_check_sequences_exclude_initial_and_preserve_pending_review(self):
        self.write_jsonl(self.site / 'backend/check-runs.jsonl', [self.check(1, 'initial'), self.check(2), self.check(3), self.check(0, 'recheck'), self.check(1, check_id='left')])
        self.write_jsonl(self.site / 'evidence/issues.jsonl', [{'id': 'a', 'owner': 'backend', 'status': 'open'}, {'id': 'a', 'owner': 'integration', 'status': 'fixed'}])
        summary = collect.iteration_summary(self.site)
        row = summary['owners']['backend']
        self.assertEqual(row['initial_scaffold_nonzero_exits'], 1)
        self.assertEqual(row['verification_nonzero_exits'], 3)
        self.assertEqual(row['observed_check_recovery_sequences'][0]['failed_runs'], 2)
        self.assertEqual(row['unrecovered_check_ids'], ['left'])
        self.assertEqual(summary['distinct_reported_issue_ids'], 1)
        self.assertTrue(summary['classification_pending_independent_review'])
    def test_preview_timer_excludes_setup_and_flags_unknown_times(self):
        rows = [{'timestamp': '1970-01-01T00:00:09+00:00'}, {'timestamp': '1970-01-01T00:00:11Z'}]
        self.write_jsonl(self.site / '.preview-events.jsonl', rows)
        result = collect.iteration_summary(self.site, 10, 20)
        self.assertEqual((result['timed_recorded_previews'], result['outside_timer_recorded_previews']), (1, 1))
        self.write_jsonl(self.site / '.preview-events.jsonl', [{}])
        self.assertIsNone(collect.iteration_summary(self.site, 10, 20)['timed_recorded_previews'])
    def test_recursive_metadata_selection_and_decimal_components(self):
        self.rollout(self.base / 'sessions/2026/10/13/root.jsonl', ROOT)
        self.rollout(self.base / 'sessions/2026/10/14/child.jsonl', CHILD, ROOT, 'gpt-6-luna')
        self.rollout(self.base / 'sessions/2026/10/14/other.jsonl', OTHER)
        with (self.base / 'sessions/2026/10/14/other.jsonl').open('a') as stream:
            stream.write('private malformed unrelated body\n')
        result = collect.native_accounting(self.base / 'sessions', ROOT, usage())
        self.assertEqual(result['session_counts'], {'root': 1, 'descendant': 1})
        self.assertEqual(result['tokens']['input_tokens'], 200)
        prices = json.loads((collect.ROOT / 'prices.json').read_text())
        cost = collect.cost_components(result, prices)
        self.assertEqual(cost['by_model']['gpt-6.1-sol']['total'], '0.000262')
        self.assertEqual(cost['estimated_total'], '0.0002752')
        self.assertEqual(result['image_calls'], 0)
        self.assertNotIn(ROOT, json.dumps(result))
        self.assertNotIn(str(self.base), json.dumps(result))
    def test_missing_or_duplicate_rollouts_withhold_complete_tokens(self):
        result = collect.native_accounting(self.base, ROOT, usage())
        self.assertIsNone(result['tokens'])
        self.assertFalse(result['tokens_complete'])
        self.assertIsNone(collect.cost_components(result, {}))
        self.rollout(self.base / 'one.jsonl', ROOT)
        self.rollout(self.base / 'two.jsonl', ROOT)
        self.assertIsNone(collect.native_accounting(self.base, ROOT, usage())['tokens'])
    def test_cli_contradiction_or_unrecognized_usage_withholds_authoritative_tokens(self):
        self.rollout(self.base / 'root.jsonl', ROOT)
        for cli, flag in (({'input_tokens': 999}, 'cli_root_usage_mismatch'),
                          ({'unexpected_counter': 100}, 'cli_usage_unrecognized')):
            with self.subTest(flag=flag):
                result = collect.native_accounting(self.base, ROOT, cli)
                self.assertIn(flag, result['flags'])
                self.assertIsNone(result['tokens'])
                self.assertFalse(result['tokens_complete'])
                self.assertEqual(result['observed_tokens'], usage())
                self.assertIsNone(result['standard_short_estimated_usd'])
                self.assertIsNone(collect.cost_components(result, {}))
        healthy = collect.native_accounting(self.base, ROOT, usage())
        self.assertTrue(healthy['tokens_complete'])
        self.assertEqual(healthy['tokens'], healthy['observed_tokens'])

    def test_impossible_native_partitions_preserve_observations_only(self):
        path = self.base / 'root.jsonl'
        for raw, flag in ((usage(cache=101), 'cached_exceeds_input'),
                          (usage(reasoning=11), 'reasoning_exceeds_output')):
            with self.subTest(flag=flag):
                self.write_jsonl(path, [event('session_meta', {'id': ROOT}),
                    event('turn_context', {'model': 'gpt-6.1-sol'}), snapshot(raw),
                    event('event_msg', {'type': 'task_complete'})])
                result = collect.native_accounting(self.base, ROOT, raw)
                self.assertIn(flag, result['flags'])
                self.assertIsNone(result['tokens'])
                self.assertFalse(result['tokens_complete'])
                self.assertEqual(result['observed_tokens'], raw)
                self.assertIsNone(result['standard_short_estimated_usd'])

    def test_freeze_retains_raw_evidence_excludes_state_and_refuses_mutation(self):
        (self.site / 'server.py').write_text('# source')
        for name in ('portal.db', 'portal.db-wal', '.env', 'private.log', 'cookies.json'):
            (self.site / name).write_text('runtime-secret')
        self.write_jsonl(self.site / 'evidence/issues.jsonl', [{'id': 'a', 'owner': 'backend'}])
        frozen = collect.freeze_evidence(self.base, self.site)
        self.assertEqual(set(frozen['sources_sha256']), {'server.py'})
        self.assertEqual((self.base / 'accounting-evidence/evidence/issues.jsonl').read_bytes(), (self.site / 'evidence/issues.jsonl').read_bytes())
        self.assertEqual(collect.freeze_evidence(self.base, self.site), frozen)
        (self.site / 'server.py').write_text('# changed')
        with self.assertRaisesRegex(ValueError, 'Frozen'):
            collect.freeze_evidence(self.base, self.site)
        self.assertEqual(json.loads((self.base / 'frozen-output-hashes.json').read_text()), frozen)
    def test_source_and_evidence_symlinks_refused(self):
        (self.site / 'secret.py').symlink_to(self.base / 'outside')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            collect.source_hashes(self.site)
        (self.site / 'secret.py').unlink()
        (self.site / 'evidence').symlink_to(self.base)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            collect.freeze_evidence(self.base, self.site)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            collect.iteration_summary(self.site)
    def test_collect_active_refused_and_completion_unknown_withheld(self):
        directory = self.base / 'runs/single'
        site = directory / 'site'
        site.mkdir(parents=True)
        (directory / 'metadata.json').write_text('{}')
        with patch.object(collect, 'ROOT', self.base):
            with self.assertRaisesRegex(ValueError, 'active'):
                collect.collect('single', self.base)
        (directory / 'metadata.json').write_text(json.dumps({'start_unix': 1, 'end_unix': 2}))
        self.write_jsonl(directory / 'events.jsonl', [{'type': 'thread.started', 'thread_id': ROOT}])
        self.rollout(self.base / 'sessions/one.jsonl', ROOT)
        (self.base / 'prices.json').write_bytes((collect.ROOT / 'prices.json').read_bytes())
        with patch.object(collect, 'ROOT', self.base):
            result = collect.collect('single', self.base / 'sessions')
        self.assertIsNone(result['cost_components_usd'])
        self.assertIn('cli_completion_missing_or_duplicated', result['flags'])
        self.assertFalse(result['tokens_complete'])
        self.assertIsNone(result['tokens'])
        self.assertEqual(result['observed_tokens'], usage())


if __name__ == '__main__':
    unittest.main()
