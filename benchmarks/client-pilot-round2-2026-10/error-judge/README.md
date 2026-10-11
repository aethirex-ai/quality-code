# Private evaluator for client helper review

Keep this directory outside every solver workspace. It contains seed identities,
reproductions, the oracle, and hidden acceptance checks. Give solvers only a copy
of `../error-fixture` and its review instructions. Seed identities and count must
not enter solver prompts, histories, files, or test output during the measured run.

Run `node evaluate.mjs /absolute/path/to/solver-workspace` after the solver freezes
its output. The evaluator imports only that workspace's three public modules;
assertions are literal independently authored expectations from public contracts.
It never imports the oracle, reads seed metadata, or trusts FINDINGS.json to score
behavior. Exit 0 requires all seed groups and all healthy groups to pass. Import
or syntax failure is a failed evaluation and must be recorded rather than retried
until green; no structured score is emitted for an unloadable workspace.

`seeds.json` records exact baseline locations, cause, reproduction, observed output,
and required behavior. Locations apply to the frozen baseline, not edited copies.
A fresh evaluator must inspect solver FINDINGS.json against raw baseline evidence:
check its file/function, concrete cause, reproducible observed versus required
behavior, and actual action. Count distinct matched defects once; reject invented
issues and duplicate claims. Discovery accuracy is separate from executable fix
counts. The seed list does not define all possible legitimate findings: assess
additional contract violations on evidence and report them separately rather
than labeling every unmatched finding a false positive. FINDINGS.json is intentionally never used as self-certified fix evidence.

Evidence:
- `baseline-results.json`: 0/8 resolved groups, 9/9 healthy groups passing.
- `oracle-results.json`: 8/8 resolved groups, 9/9 healthy groups passing.
- `isolation-results.json`: each individual fix resolves only its own group and
  retains healthy controls; this establishes test-group independence.
- `baseline-manifest.json`: SHA-256 for every frozen solver-fixture file.

Reproduce corrected-copy checks with `python3 prepare_oracle.py`, then
`node evaluate.mjs oracle`. This overwrites the judge-only oracle and metadata.
Run `python3 verify-isolation.py` to reproduce independence checks. Baseline
`node evaluate.mjs ../error-fixture` intentionally exits 1. Fixture ordinary
controls and syntax checks pass via its `./quality verify full` profile.

No production services, real people, external writes, dependencies, clocks, or
random inputs. Scope is contained deterministic helpers. The judge integrity
and artifact separation still require the primary's fresh independent audit.
Hidden tests sample boundary and healthy behavior; they are not an exhaustive
proof for all valid safe-integer combinations or every invalid object shape.
