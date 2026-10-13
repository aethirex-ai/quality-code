# AethDesign client workspace: completion pilot

**Two incomplete outcomes; no accepted-quality, speed or complete-cost winner.** The actual-studio prompt and gate/repair loop replace the old portal pilot’s incorrect atelier context and pre-gate freeze. The control stalled during construction; adaptive repaired its first audited defect, then a fresh review timed out with further observed issues.

[Results and limits](RESULTS.md) · [structured results](results.json) · [usage](usage-diagnostic.json) · [iterations](iteration-review.json) · [anonymous visuals](blind-visual-review.json) · [gallery](https://aethirex-ai.github.io/quality-code/benchmarks/portal-completion-round2-2026-10/).

## Inspectable workload

[Common prompt](APP_PROMPT.txt), [contracts](BRIEF.md), [actual studio context](BRAND.md), [budget](BUDGET.md), [dated recorded protocol](protocol.json), [prices](prices.json) and [native catalog](native-model-catalog.json). The generic Quality Code policy has no fixed provider/model ranking. Recorded actors used one model at different efforts; this trial did not test cheaper-model routing or a nested swarm.

The [blank fixture](fixture/) retains 25 original source hashes. [Instrument provenance](replay-source-provenance.json) preserves 61 native/published hashes; brand capture paths are portable, and the replay runner has a post-trial zero-grace zombie-reaping correction. [Exact measured runner](runner-native.py) remains preserved; neither trial was rerun. [Controlled evaluator proofs](instrument-controls/provenance.json), [sanitized report provenance](report-provenance.json) and [independent preflight](preflight-audit.json) are separate from application acceptance. Raw native transcripts/IDs, personal runtime metadata, cookies and databases are excluded.

## Frozen local prototypes

[Single final](apps/single/) is unfinished and lacks its stylesheet. [Adaptive final](apps/adaptive/) is styled but unaccepted, with observed review-history, navigation-acknowledgment and long-title issues. [Adaptive initial](initial/adaptive/) preserves the pre-repair response race. [Source manifests](source-manifests/) identify exact bytes; do not overwrite measured outputs when experimenting.

Run a copy of either final app with Python 3.11+ and a fresh disposable database:

```sh
cd apps/adaptive
python3 server.py --host 127.0.0.1 --port 8000 --db /tmp/aeth-client-workspace-demo.sqlite3
```

Open localhost port 8000. Synthetic accounts: `alex@harbor.test` / `HarborDemo!42`, `sam@northline.test` / `NorthDemo!42`, `studio@aethdesign.test` / `StudioDemo!42`. Both use fictional data; the demonstration is not a completed production client portal.

## Offline instrumentation and diagnostics

From this folder:

```sh
python3 -B -m unittest discover -s . -p 'test_*.py' -v
python3 -B preview/tests.py Contracts
```

Owned-cleanup tests need host process inspection; no command above calls a model. Local loopback/Chromium checks require appropriate permissions and your own Node/Playwright installation. See [backend documentation](judge/backend/README.md), [browser documentation](judge/frontend/README.md) and [preview protocol](preview/README.md).

[Single diagnostics](diagnostics/single/summary.json) and [adaptive diagnostics](diagnostics/adaptive/summary.json) occurred after frozen/capped condition clocks. Their [single provenance](single-diagnostic-provenance.json) and [adaptive provenance](adaptive-diagnostic-provenance.json) preserve source checks, report adaptations and viewport PNG hashes. A raw recovery pass with a recorded late transport error remains qualified. Diagnostic passes cannot turn either condition into an independent app PASS.

## Another opted-in experiment

`run.py` consumes native account usage and is never a CI command. This published protocol is historical, with local runtime locations sanitized. Copy instruments into a separate dated workspace, rediscover native model/tool/effort support, verify actual selected child models and formatter with the matched models, prepare fresh matching corpora and seal a new protocol before launch. Review stage/global deadline and reconnect behavior first. Retain every interrupted attempt and unknown counter; never silently reuse this history or select a better outcome after grading.
