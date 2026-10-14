# Report-only correction of an existing independent audit

`report_recovery.py` implements a narrow method for correcting the original phase 8 auditor's canonical report. The original full audit reported PASS with no findings, but represented an intentionally interrupted server cleanup as a passing check with exit 130. Strict validation rejected that contradiction. The correction prompt preserves the actual cleanup evidence and requires successful assertion evidence from the same auditor's retained work. It forbids invented exit-zero results, hidden failed required checks, source changes, delegation, product fixes and a new full audit. Uncertainty must yield FAIL or BLOCKED.

The controller resumes the exact original independent auditor root with the matched model/high effort, read-only sandbox and delegation disabled. Preconditions prove completed metadata, root independence, protected freeze, matching current/final/audited sources, accepted structural gates and the immutable final source snapshot. The corrected complete report must still pass the unchanged strict validator, including full source coverage and actual required full/release evidence.

Original phase report/events/metadata files stay unchanged. Each correction archives the prior aggregate metadata, original phase object and hashes, and retains its own command, events, report, native before/after counters and elapsed interval. Verified increment or cumulative CLI counters reconcile with the authoritative native root. The aggregate remains one original independent auditor phase/root, with cumulative consumption counted once and native elapsed intervals added. Failed/nonzero/mismatched corrections retain their evidence and counters and cannot become accepted completion. Calendar gaps remain in total elapsed time; active-controller time adds only the new monotonic interval.

The first correction controller's named permission settings conflicted with its read-only sandbox and failed during startup. The updated controller removes all named permission overrides. Its retry path permits only the exact retained exit-1 configuration error with empty events, unchanged native counter/rollout snapshots, immutable original archives and unchanged source. It restores accounting provenance in memory, retains the failed segment/time, and creates a new correction directory. It does not rewrite original evidence or infer zero usage without the explicit no-growth proof. Historical canonical errors remain in archives/correction history; the current aggregate receives corrected canonical metadata only after strict validation.

`report-recovery-native-audit-summary.json` is a field-allowlisted summary of the independent native-controller audit; its original full-report hash is retained. `report-recovery-parser-probe.json` records a parser-only check. Neither includes private report/command bodies, session identifiers or personal paths. These artifacts attest the native controller bytes. The adapted portable controller requires independent publication acceptance and an exact portable-controller proof; the historical native proof cannot authorize it. Its default module directory is this package; an explicit `SERVICEFLOW_BENCHMARK_ROOT` override is available. Runtime discovery uses `run.runtime_protocol`. The default proof path is package-local `report-recovery-publication-proof.json`, with `SERVICEFLOW_REPORT_RECOVERY_AUDIT` override. The proof is deliberately not supplied by the historical summary.

Portable regression tests use owned synthetic data only:

```
python3 -B -m unittest test_report_recovery -v
```

Method publication and its tests do not execute a native auditor correction or establish application acceptance. The separate results report owns actual outcomes.
