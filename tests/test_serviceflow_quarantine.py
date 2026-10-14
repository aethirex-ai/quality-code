from datetime import date
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("serviceflow_quarantine", ROOT / "scripts/check_serviceflow_regressions.py")
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


class Case:
    def __init__(self, name): self.name = name
    def id(self): return self.name


class QuarantineTests(unittest.TestCase):
    def test_only_exact_target_is_removed(self):
        target = Case(checks.QUARANTINE["test_id"])
        controls = [Case("other.Healthy.test"), Case(checks.QUARANTINE["test_id"] + "_similar")]
        self.assertEqual(checks.select_cases([controls[0], target, controls[1]], date(2026, 10, 14)), controls)

    def test_missing_duplicate_and_expired_fail_closed(self):
        target = Case(checks.QUARANTINE["test_id"])
        for cases, today in (([], date(2026,10,14)), ([target,target], date(2026,10,14)),
                             ([target], date(2026,11,15))):
            with self.subTest(cases=len(cases), today=today), self.assertRaises(ValueError):
                checks.select_cases(cases, today)

    def test_actual_phase_timeout_contract_without_startup_race(self):
        case = checks.TimeoutReplacementTests("test_execute_phase_timeout_is_observable_with_native_event_and_snapshot")
        result = unittest.TestResult()
        case.run(result)
        self.assertTrue(result.wasSuccessful(), str(result.errors) + str(result.failures))
