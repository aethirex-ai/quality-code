# Round two: new clients and an error-finding test

This AethDesign follow-up contains two independent paired workloads. Both use the revised Quality Code policy, the same native root model/effort within a pair, equal frozen starting fixtures and the same allowance within that pair. The measured unit is the whole task, not each page/function treated as an independent trial.

- **Portfolio:** a maritime editorial boutique hotel, a bold cobalt/yellow fitness studio and a Swiss editorial landscape practice. Both subjects build all three, with exactly two successful native photographs per page, a maximum of three attempts per page and a shared twenty-minute solver allowance. Adaptive swarm runs first, reversing the first pilot's order. Native collaboration may use primary plus up to three active descendants; capacity is a ceiling, not a required count or hierarchy.
- **Defect review:** independent fresh sessions review and fix three deterministic JavaScript client-helper modules against public contracts, write concrete findings and their own regressions, within a shared ten-minute allowance. Single runs first. Seed count, oracle and hidden evaluator remain outside solver scope until both attempts end. Ground truth includes eight intentionally independent defects plus healthy controls; additional legitimate findings require evidence review rather than being automatically false positives.

The single condition disables native delegation and forbids extra model sessions. Adaptive delegation can choose zero helpers for small work or direct/hierarchical owners when justified. Record actual topology, models/effort and supplied context; do not pretend the label guarantees a swarm. No post-run repairs are allowed before grading.

## Accounting

Timed solver usage includes each native root and every explicitly linked descendant, image inspection, tools, coordination, retries and builder checks. Setup, capability probes, external grading and publication audit are excluded. Native wall time includes waiting for image/tool calls. Cumulative usage is deduplicated; input includes cached input, output includes reasoning, and neither subset is double-charged. Missing or inconsistent evidence withholds complete price/image claims.

Hypothetical **Standard API coding equivalents**, when fully supported, use the dated [official rates](https://developers.openai.com/api/docs/pricing). They are not invoices, subscription percentages or total experiment costs. The native image generator exposes no verified backend, tokens or charges; count attempts/successes/retries by page and subject. Display derivatives are not extra generations.

## Quality and error-finding

The frozen browser evaluator repeats the first pilot's document/resource/demo-interaction assertions at 375px and 1440px, adapted to new clients/selectors. Anonymous screenshots receive the same five-category visual rubric. Scores remain a qualitative review, separate from functionality and error detection.

For defect review, independently execute hidden seed and healthy groups on frozen outputs. Match FINDINGS.json to concrete raw baseline defects using file/function, faulty cause and observed/required behavior. Distinct detected seeds, unresolved seeds, duplicates, false positives, legitimate additional findings, hidden fixes and regressions are separate measures. A self-reported fix is not a behavioral pass. Ordinary tests initially cover healthy cases and do not reveal the seeds. Baseline/oracle and individual-fix isolation validate the evaluator before any measured attempt.

## Limits

This is one pair for each of two workloads, with uncontrolled service/cache/shared-host load, different generated imagery, alpha native tooling and qualitative reviewer variability. New clients/styles and revised rules changed together from the first pilot; cross-pilot differences cannot isolate the policy's effect. Within-pair comparisons are observations, not general superiority, causal evidence or proof of subscription savings. The defect test uses small deterministic modules; it does not measure arbitrary large-repository debugging, security auditing or all input cases.

Raw logs remain private. Source hashes, sanitized counters, anonymous reviews, task contracts and executable offline instrumentation remain inspectable. The runtime can inject fixed instructions/tool/skill metadata even with fresh scoped context; no smaller configured context window is claimed.

## Offline checks and fresh replay

Published `fixture/` and `error-fixture/` are the frozen starting inputs. `error-judge/` contains the independent post-run evaluator, seed descriptions and completed baseline/oracle/isolation preflight evidence; keep it outside solver workspaces. It contains no measured error-run outcome. `replay-source-provenance.json` preserves original source hashes alongside sanitized-copy hashes. Recorded protocol hashes identify original measured bytes; preparation records those separately and computes hashes for the new replay copies. Machine-specific Node/Playwright paths are placeholders in the published brief.

Run the offline regressions from this directory:

```sh
python3 -B -m unittest test_telemetry.py test_prepare.py
```

Prepare a new, nonexistent directory with your installed runtime paths:

```sh
python3 prepare.py --work-dir /absolute/new/replay --node /absolute/path/to/node --playwright-import /absolute/path/to/playwright/index.mjs
```

Preparation invokes no providers. It creates independent committed starting fixtures at `runs/{single,swarm}/site` and `error-runs/{single,swarm}/site`, leaves the judge outside them, and refuses any existing replay directory. `run.py` is a separate opt-in native logged-in CLI execution step; each condition refuses an already-started run. The fresh replay is another observation, not a reconstruction of original generated images or measured outcomes. Set `BENCHMARK_PLAYWRIGHT_IMPORT` to the supplied Playwright module path when running the design evaluator.

The completed single-design collector reports `image_calls: null` with `image_execution_ambiguous` because a single syntactic image call occurs inside an asynchronous map. [The separate read-only transcript supplement](single-image-transcript-supplement.json) reconstructs its six literal jobs, six successful native returns and matching delivered original hashes. This preserves the automated unknown and does not relax fail-closed handling for arbitrary control flow. Image backend, tokens and price remain unknown.
