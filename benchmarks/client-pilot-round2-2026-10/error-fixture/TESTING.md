# Client helper testing

## Test objectives
Validate documented pure helper behavior, integer cents, date/budget boundaries,
HTML encoding, validation, and unchanged input state.

## Product risks
Normal: contained deterministic calculations and simulated HTML output. No
production integrations, persistence, or privileged paths.

## Test levels
`tests/controls.test.mjs` supplies ordinary domain controls. Add focused Node
regressions for each actual discovered defect; avoid self-confirming assertions.

## Test data and environment
Node 20+; no dependencies, network, credentials, real customer data, current time,
randomness, or locale dependence. Fixtures are literal values in tests.

## Non-functional coverage
Input purity and validation are contract requirements. Guest badge encoding is
validated as exact output. Runtime is short and deterministic; no load tests needed.

## Manual and release evidence
No production release. Retain own commands and regression results in handoff.

## Known gaps and residual risk
Existing ordinary controls are partial and cannot establish all public contracts.

## Independent audit gate
Normal behavior requires focused builder verification. Benchmark infrastructure
integrity is reviewed separately outside this solver workspace.

## Maintenance rules
Keep added tests deterministic; confirm each defect through a minimal failing
example and post-fix regression. Command definitions live in quality.toml.
