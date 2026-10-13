import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import gate_checks


class FixedGateContract(unittest.TestCase):
    def exercise(self, reports, exits=(0, 0, 0)):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            paths = [out / 'backend.json', out / 'frontend/report.json',
                     out / 'recovery/defect-probes.json']
            for path, report in zip(paths, reports):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(report))
            completed = [subprocess.CompletedProcess([], code, '', '') for code in exits]
            with patch.object(gate_checks, 'owned_run', side_effect=completed):
                return gate_checks.gates(out / 'site', out)

    def healthy(self):
        return [{'passed': 12, 'denominator': 12},
                {'passed': 11, 'denominator': 11},
                {'passed': 3, 'supplementalCheckCount': 3,
                 'checks': [{'pass': True}] * 3}]

    def test_all_three_contracts_required(self):
        self.assertTrue(self.exercise(self.healthy())['accepted'])
        for index in range(3):
            reports = self.healthy()
            reports[index]['passed'] -= 1
            result = self.exercise(reports)
            self.assertFalse(result['accepted'])
            self.assertFalse(result['tool_incomplete'])

    def test_nonzero_exit_cannot_pass(self):
        self.assertFalse(self.exercise(self.healthy(), (0, 1, 0))['accepted'])

    def test_unknown_evidence_never_passes(self):
        reports = self.healthy()
        reports[1]['fatal'] = 'browser failed'
        result = self.exercise(reports)
        self.assertFalse(result['accepted'])
        self.assertTrue(result['tool_incomplete'])

    def test_missing_group_and_wrong_denominator_fail(self):
        for index in range(3):
            reports = self.healthy()
            reports[index] = {}
            self.assertFalse(self.exercise(reports)['accepted'])
        reports = self.healthy()
        reports[0]['denominator'] = 11
        self.assertFalse(self.exercise(reports)['accepted'])

    def test_timeout_is_recorded_as_incomplete(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(gate_checks, 'owned_run',
                              side_effect=subprocess.TimeoutExpired('fixture', 1)):
                result = gate_checks.gates(directory, Path(directory) / 'reports')
            self.assertFalse(result['accepted'])
            self.assertTrue(result['tool_incomplete'])
            self.assertEqual(len(result['checks']), 3)


if __name__ == '__main__':
    unittest.main()
