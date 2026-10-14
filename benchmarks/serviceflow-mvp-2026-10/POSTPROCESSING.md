# Optional legacy iteration parser compatibility

`postprocess.py` calls unchanged `phase_collect.collect` and temporarily wraps only its optional `legacy.iteration_summary`. The measured issue format has stable IDs but lacks the legacy parser's required `owner` classification. A `ValueError` from that optional parser becomes `state: unparsed`, the original error, `counts: null`, `raw_evidence_retained: true`, and a reference to `iteration-review.json`. The adapter does not normalize, rewrite or discard raw records, classify corrections, impute zero, or change native counter arithmetic. The independent iteration review remains the classification basis.

Other collector errors propagate. Non-ValueError parser failures propagate. The original summary function is restored in `finally` after success or failure. This is a single-call CLI adapter; concurrent in-process calls are outside its contract. The existing final-metadata guard still rejects active conditions before accounting. Use only after a condition's end is recorded:

```
python3 -B postprocess.py single --sessions-dir <explicit-native-session-directory>
```

The external native adapter uses the same behavior with an explicit `SERVICEFLOW_BENCHMARK_ROOT` module directory. No live measured instrument, app, controller or raw evidence was modified to deliver this adapter. Its new helper hashes are tracked separately in `protocol.postprocessing_helpers_sha256`; the original `phase_collect.py` and current `frozen_sources_sha256` map remain unchanged. This postprocessing compatibility correction is outside measured implementation/audit work. Helper tests use synthetic records and fake native results only.

The public `INSTRUMENTS.md` overview is updated to describe the source projections. Only its public provenance hash changes; measured native instrument bytes and native freeze hashes remain unchanged.
