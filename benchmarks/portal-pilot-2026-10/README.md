# AethDesign Atelier / Paired client portal benchmark

A complete local client portal with Python/SQLite authentication and state, plus a dependency-free browser interface. The same prompt compares one agent with native delegation disabled against an agent allowed to choose adaptive ownership. This is a recorded experiment, not a prescribed model topology.

[Complete results](RESULTS.md), [structured accounting](results.json), [independent correction history](iteration-review.json) and [anonymous visual review](blind-visual-review.json) preserve both immutable outputs, including remaining defects. The public gallery presents screenshots; GitHub Pages does not run the Python backend.

## Capability isolation correction

The first control attempt unexpectedly spawned a backend helper: the shared runner enabled modern `multi_agent_v2` despite the legacy disable settings. It was stopped at 419.351 seconds and retained before any product grading. The completed adaptive output remains unchanged. A fresh control disables both toolsets and starts from the original corpus; a small native [capability probe](isolation-preflight-proof.json) found no delegation tools or calls. [Original runner](runner-original.py) and [original protocol](protocol-original.json) remain inspectable. The current runner uses corrected isolation. This is a condition-validity correction, not an outcome-selected retry.

## Workload and instrument

[Common prompt](APP_PROMPT.txt), [contracts](BRIEF.md), [shared budget](BUDGET.md), [recorded protocol](protocol.json), [dated prices](prices.json) and [native catalog](native-model-catalog.json). Model identifiers and prices are observations from this dated trial; the Quality Code standard has no fixed provider/model ranking.

The [published replay provenance](replay-source-provenance.json) preserves original native and published hashes. Local tool paths are normalized to environment controls/portable commands. Generated backend control results write outside historical evidence. Native transcripts, real session identifiers, cookies, databases and private runtime logs are excluded.

## Offline accounting checks

From this folder, with Python 3.11+ and Git:

```sh
python3 -B -m unittest discover -s . -p 'test_*.py' -v
```

These checks use synthetic native records and temporary files; they do not call a model or reconstruct measured usage from screenshots. Cached input is a subset of input, reasoning is a subset of output. Incomplete or contradictory evidence withholds authoritative totals and a complete price estimate.

## Backend and browser control replay

Backend controls need Python, loopback access and permission to inspect/terminate their own process groups:

```sh
python3 -B judge/backend/test_evaluator.py
```

The generated report defaults to the system temporary directory; set `PORTAL_CONTROL_OUTPUT` for another output file. [Backend evaluator documentation](judge/backend/README.md) describes the 12 fixed contract groups and negative controls.

Browser checks require your own local Node, Playwright and Chromium installation:

```sh
BENCHMARK_PLAYWRIGHT_IMPORT=playwright node judge/frontend/selftest.mjs /tmp/portal-frontend-controls
BENCHMARK_PLAYWRIGHT_IMPORT=playwright node judge/frontend/regression.mjs /tmp/portal-frontend-regressions
BENCHMARK_PLAYWRIGHT_IMPORT=playwright node judge/frontend/navigation-regression.mjs /tmp/portal-navigation-controls
BENCHMARK_PLAYWRIGHT_IMPORT=playwright node judge/frontend/tab-regression.mjs /tmp/portal-tab-controls
PREVIEW_NODE=node PREVIEW_PLAYWRIGHT_MODULE=playwright python3 preview/tests.py
```

[Frontend documentation](judge/frontend/README.md) describes the 11 sampled behavior groups and fixed 12 screenshot slots. Group failures can cascade and are not distinct bug counts. [Navigation amendment](navigation-amendment.json) retains the original evaluator, intermediate/final reports, selected-tab chronology and delayed healthy/negative controls. Successful approval/stale-conflict browser branches need supplemental diagnosis outside those denominators. [Preview documentation](preview/README.md) describes the fixed-origin, bounded mailbox used equally by both native builders.

## New opted-in native trial

`run.py` launches logged-in native Codex and consumes native account usage; it is never a CI command. The recorded settings/catalog are dated evidence. To conduct a new trial, copy these sources into a separate dated workspace, rediscover native support/effort/capacity and prices, prepare clean matching workspaces, retain a new protocol and seal it before launch. Do not overwrite this historical protocol or silently reuse unavailable models.

Inspect the modern native permission profile and alpha feature support for your runtime. The recorded trial retained workspace filesystem protections and allowed only localhost command traffic; its parent Chromium preview was a documented workaround for blocked native browser IPC. Configure local `PREVIEW_NODE` and `PREVIEW_PLAYWRIGHT_MODULE` paths. Both complete outputs must freeze before external grading, with no grading feedback or post-grade repairs.

This pair measures coding sessions and all explicit descendants, including builder corrections and owned cleanup. Parent setup, instrumentation repairs, external evaluation, independent audits and publication are outside that boundary. They are not zero cost. API-equivalent coding prices do not measure subscription consumption or total project cost.
