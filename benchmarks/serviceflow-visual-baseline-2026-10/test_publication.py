"""Negative controls for publication state and accounting semantics."""
import copy
import json
import unittest
import pathlib
import tempfile
import replay_source
import check_publication as publication


class PublicationControls(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((publication.DOCS / 'results.json').read_text())

    def test_current_public_projection(self):
        self.assertGreaterEqual(publication.validate_publication(), 32)

    def test_replay_all_stages_and_refuse_existing_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            for condition in ['single', 'adaptive']:
                for stage in ['initial', 'accepted']:
                    destination = pathlib.Path(temporary) / f'{condition}-{stage}'
                    replay_source.replay(condition, stage, destination)
                    with self.assertRaisesRegex(ValueError, 'must not exist'):
                        replay_source.replay(condition, stage, destination)

    def test_final_phase_tokens_and_gate_layers_must_reconcile(self):
        data = copy.deepcopy(self.data)
        data['apps'][0]['phase_breakdown'][0]['usage']['input_tokens'] += 1
        with self.assertRaisesRegex(AssertionError, 'Phase counters'):
            publication.validate_results(data)
        data = copy.deepcopy(self.data)
        data['apps'][0]['supplemental_review_verdict'] = 'FAIL'
        with self.assertRaisesRegex(AssertionError, 'Both review layers'):
            publication.validate_results(data)

    def test_late_single_correction_requires_its_own_gate(self):
        data = copy.deepcopy(self.data)
        data['apps'][0]['publication_followup_verdict'] = 'FAIL'
        with self.assertRaisesRegex(AssertionError, 'Late Single correction'):
            publication.validate_results(data)
        data = copy.deepcopy(self.data)
        data['apps'][0]['phase_breakdown'][-1]['model_settings'][0]['reasoning_effort'] = 'high'
        with self.assertRaisesRegex(AssertionError, 'Observed effort mismatch'):
            publication.validate_results(data)

    def test_original_app_cannot_be_used_as_replay_destination(self):
        destination = publication.ROOT / 'benchmarks/serviceflow-mvp-2026-10/apps/single/replay-child'
        with self.assertRaisesRegex(ValueError, 'outside the frozen original'):
            replay_source.replay('single', 'accepted', destination)
        self.assertFalse(destination.exists())

    def test_pending_totals_cannot_masquerade_as_final(self):
        data = copy.deepcopy(self.data)
        data['complete'] = False
        data['apps'][0]['total_text_proxy_usd'] = 13.22
        with self.assertRaisesRegex(AssertionError, 'Pending final totals'):
            publication.validate_results(data)

    def test_cached_input_is_not_additional_input(self):
        data = copy.deepcopy(self.data)
        data['apps'][0]['initial_usage']['cached_input_tokens'] = data['apps'][0]['initial_usage']['input_tokens'] + 1
        with self.assertRaisesRegex(AssertionError, 'Cached input is a subset'):
            publication.validate_results(data)

    def test_duplicate_stage_cannot_replace_missing_evidence(self):
        data = copy.deepcopy(self.data)
        data['apps'][0]['captures'].append(copy.deepcopy(data['apps'][0]['captures'][0]))
        with self.assertRaisesRegex(AssertionError, 'Duplicate capture state'):
            publication.validate_results(data)

    def test_complete_requires_current_acceptance_and_all_stages(self):
        data = copy.deepcopy(self.data)
        data['complete'] = True
        data['apps'][0]['final_verdict'] = 'FAIL'
        with self.assertRaisesRegex(AssertionError, 'Complete requires final PASS'):
            publication.validate_results(data)


if __name__ == '__main__':
    unittest.main()
