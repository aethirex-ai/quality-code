#!/usr/bin/env python3
"""Run ServiceFlow tests with one dated timing quarantine and a deterministic replacement."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SERVICEFLOW = ROOT / "benchmarks" / "serviceflow-mvp-2026-10"
QUARANTINE = {
    "test_id": "test_completion_runner.CompletionTests.test_native_phase_global_timeout_is_observable",
    "owner": "AethDesign",
    "reason": "A 0.2-second wall-clock timeout can expire before the synthetic child starts under concurrent benchmark load, leaving no thread-started event to parse.",
    "expires": "2026-11-14",
}
NATIVE_ROOT = "44444444-4444-4444-4444-444444444444"

sys.path.insert(0, str(SERVICEFLOW))
import run as serviceflow_run  # noqa: E402


def flatten(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def select_cases(cases, today=None):
    today = date.today() if today is None else today
    if not QUARANTINE["owner"] or not QUARANTINE["reason"]:
        raise ValueError("quarantine needs owner and reason")
    if today > date.fromisoformat(QUARANTINE["expires"]):
        raise ValueError("timing-test quarantine expired; remove or resolve it")
    matches = [case for case in cases if case.id() == QUARANTINE["test_id"]]
    if len(matches) != 1:
        raise ValueError(f"quarantine expected exactly one {QUARANTINE['test_id']!r}, found {len(matches)}")
    return [case for case in cases if case is not matches[0]]


class TimeoutReplacementTests(unittest.TestCase):
    def test_quarantine_is_exact_unique_owned_and_unexpired(self):
        matches = [case for case in DISCOVERED_CASES if case.id() == QUARANTINE["test_id"]]
        self.assertEqual(len(matches), 1)
        self.assertEqual(QUARANTINE["owner"], "AethDesign")
        self.assertTrue(QUARANTINE["reason"])
        self.assertGreaterEqual(date.fromisoformat(QUARANTINE["expires"]), date.today())

    def test_execute_phase_timeout_is_observable_with_native_event_and_snapshot(self):
        class FakePopen:
            def __init__(self, args, **kwargs):
                self.args = args
                self.kwargs = kwargs
                self.returncode = None
                self.pid = 4242
                self.timeout = None
                kwargs["stdout"].write(
                    (json.dumps({"type": "thread.started", "thread_id": NATIVE_ROOT}) + "\n").encode()
                )

            def communicate(self, *, input=None, timeout=None):
                self.timeout = timeout
                raise subprocess.TimeoutExpired(self.args, timeout)

        def terminate(process, grace=2):
            process.returncode = -15

        with tempfile.TemporaryDirectory(prefix="serviceflow-timeout-contract-") as tmp:
            root = Path(tmp).resolve()
            site = root / "site"
            site.mkdir()
            sessions = root / "sessions"
            sessions.mkdir()
            (sessions / "native-root.jsonl").write_text(
                json.dumps({"type": "session_meta", "payload": {"id": NATIVE_ROOT, "cwd": str(site)}})
                + "\n"
                + json.dumps({"type": "turn_context", "payload": {"model": "fixture-model"}})
                + "\n"
            )
            protocol = {"sessions_dir": str(sessions), "cleanup_reserve_seconds": 0.01}
            metadata = {"phases": []}
            deadline = serviceflow_run.time.monotonic() + 5
            with patch.object(serviceflow_run, "command", return_value=["fake-native-cli"]), \
                 patch.object(serviceflow_run.subprocess, "Popen", FakePopen), \
                 patch.object(serviceflow_run, "terminate_group", side_effect=terminate) as cleanup:
                phase, phase_dir = serviceflow_run.execute_phase(
                    "single", site, root, protocol, metadata, deadline, b"brief",
                    role="builder", number=2, resume=NATIVE_ROOT, env={},
                )

            self.assertEqual(phase["state"], "timed_out")
            self.assertEqual(phase["root_id"], NATIVE_ROOT)
            self.assertEqual(phase["exit_code"], -15)
            self.assertIsNone(phase["cli_usage"])
            self.assertEqual(phase["native_before"]["id"], NATIVE_ROOT)
            self.assertEqual(phase["native_after"]["id"], NATIVE_ROOT)
            self.assertEqual(phase["native_after"]["actual_models"], ["fixture-model"])
            self.assertEqual(cleanup.call_count, 1)
            process = cleanup.call_args.args[0]
            self.assertIsNotNone(process.timeout)
            self.assertGreater(process.timeout, 0)
            self.assertLessEqual(process.timeout, 5)
            persisted = json.loads((phase_dir / "metadata.json").read_text())
            self.assertEqual(persisted["state"], "timed_out")
            self.assertIsNone(persisted["cli_usage"])
            self.assertEqual(serviceflow_run.parse_events(phase_dir / "events.jsonl")[0], NATIVE_ROOT)


def main() -> int:
    loader = unittest.defaultTestLoader
    discovered = loader.discover(str(SERVICEFLOW), pattern="test_*.py", top_level_dir=str(SERVICEFLOW))
    global DISCOVERED_CASES
    DISCOVERED_CASES = list(flatten(discovered))
    if loader.errors:
        print("ERROR: ServiceFlow test discovery failed:\n" + "\n".join(loader.errors), file=sys.stderr)
        return 2
    try:
        selected = select_cases(DISCOVERED_CASES)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"QUARANTINE: {QUARANTINE['test_id']}; owner={QUARANTINE['owner']}; expires={QUARANTINE['expires']}; reason={QUARANTINE['reason']}; deterministic replacement active", flush=True)
    replacement = loader.loadTestsFromTestCase(TimeoutReplacementTests)
    suite = unittest.TestSuite([*selected, replacement])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
