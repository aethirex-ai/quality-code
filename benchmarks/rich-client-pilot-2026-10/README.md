# Rich two-client native coding pilot

Read [RESULTS.md](RESULTS.md) and [results.json](results.json). Recorded model names/rates are dated experimental evidence, not standard defaults. Browser diagnosis and qualitative review distinguish real defects from evaluator limitations.

## Frozen evidence

- [Brief](BRIEF.md), [protocol](protocol.json), [price evidence](prices.json), [routing](routing-evidence.json)
- Original and MIME-corrected `*-objective-*.json`; [documented evaluator repair](evaluation-amendment.json)
- `*-telemetry.json`, `*-frozen-output-hashes.json`, `*-image-transcript-supplement.json`
- [Iteration reconciliation](iteration-review.json), [browser reproduction](browser-diagnosis.json), [form diagnosis](single-form-diagnosis.json)
- [Anonymous review](visual-review.json), [map](blind-map.json), [screenshots](screenshots/)
- [Live frozen portfolios](https://aethirex-ai.github.io/quality-code/benchmarks/rich-client-pilot-2026-10/)

Raw native transcripts/check commands/session identities remain private. Review references identify archived evidence; they are not public downloadable logs. Public served assets retain measured bytes. [Replay provenance](replay-source-provenance.json) distinguishes host-path normalization from original frozen hashes.

## Offline instrument checks

Python 3.11+, Git and Node; Chromium/Playwright needed only for browser evaluation. From this folder:

```sh
python3 -B -m unittest discover -s . -p 'test_*.py' -v
python3 -B preview/tests.py
BENCHMARK_PLAYWRIGHT_IMPORT=playwright node test_evaluator.mjs
BENCHMARK_PLAYWRIGHT_IMPORT=playwright node test_mime_evaluator.mjs
```

The replay fixture test deliberately preserves the original evaluation setup; see the MIME correction before interpreting measured `.mjs` results. Native model telemetry is not reconstructed from screenshots.

## Browser replay

With local Playwright installed/configured, check a frozen served tree without changing it:

```sh
BENCHMARK_PLAYWRIGHT_IMPORT=playwright node evaluator-mime-corrected.mjs ../../docs/benchmarks/rich-client-pilot-2026-10/single /tmp/rich-single-evaluation
```

The original evaluator remains available for comparison. Its exact URL matcher, image expectation and 800ms deadline remain in both versions; review the supplemental diagnosis rather than treating every failed assertion as a product bug.

## New native trial

`run.py` consumes native account usage and starts local Chromium. Review its dated catalog/settings, runtime access, skills, pricing, preview limits and 35-minute all-tree budget first. This is an opt-in experiment, not a CI step. It uses the native logged-in CLI, no direct API key. Models in `protocol.json` are recorded observations: rediscover support for a new trial and retain a new protocol rather than silently changing this one.

Create clean `runs/single/site` and `runs/swarm/site` from `fixture/`, initialize a baseline Git commit, tailor `RUNTIME.md` to actual local Node/Playwright/skill paths, and make `codex` available in PATH. Configure `PREVIEW_NODE` and `PREVIEW_PLAYWRIGHT_MODULE`; run each condition sequentially. Runner refuses an already-started condition. Evaluate only after both finish; do not give grading feedback during timed work or repair measured outputs afterward. Collect native logs from the exact dated sessions directory (flat discovery), including explicit descendants; missing evidence withholds a coding price estimate. Preserve every failure and disclose differences from this recorded native environment.
