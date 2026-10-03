# PROJECT_NAME testing profile

This file records project-specific test intent and known limitations. Commands and path routing live in `.quality/quality.toml`; the audit-only `audit-code-change` skill contains the global testing standard.

## Test objectives

- PRIMARY_USER_OUTCOME
- MOST_IMPORTANT_FAILURE_TO_PREVENT
- PUBLIC_OR_PERSISTED_CONTRACT_TO_PRESERVE

## Product risks

| Risk | Level | Required evidence |
| --- | --- | --- |
| RISK | critical/high/normal/low | TESTS_OR_MANUAL_EVIDENCE |

## Test levels

| Level | Location | Responsibility |
| --- | --- | --- |
| Unit/component | `PATH` | PURE_OR_CONTAINED_LOGIC |
| Integration/contract | `PATH` | BOUNDARIES_AND_COMPATIBILITY |
| System/acceptance | `PATH_OR_MANUAL` | USER_OUTCOMES |

## Test data and environment

- Default tests are deterministic and offline: YES_OR_EXCEPTIONS
- Fixtures and factories: PATHS
- Controlled time, randomness, filesystem, and network: METHOD
- Required platforms, hardware, permissions, or credentials: REQUIREMENTS
- Forbidden production dependencies during routine testing: LIST

## Non-functional coverage

- Security/privacy: COVERAGE_OR_GAP
- Reliability/recovery: COVERAGE_OR_GAP
- Performance/resources: COVERAGE_OR_GAP
- Accessibility/compatibility: COVERAGE_OR_GAP
- Installation/update/rollback: COVERAGE_OR_GAP

## Manual and release evidence

| Scenario | Procedure | Evidence retained |
| --- | --- | --- |
| SCENARIO | STEPS | LOCATION_OR_REPORT |

## Known gaps and residual risk

- GAP_OWNER_EXPIRY_AND_MITIGATION

## Independent audit gate

- Low-risk isolated presentation or copy changes receive one focused confirmation; do not run a full suite, generate an audit packet, or start a subagent by default.
- Normal-risk contained behavior receives the smallest relevant regression and changed-scope verification; no independent audit is required by default.
- High- and critical-risk changes require the configured higher profiles and a fresh-agent audit. An explicit user request can require an audit at any risk level.
- A routine local build, install, packaging step, or version bump used only to deliver or confirm a change inherits the underlying change's risk; it does not by itself trigger a release audit.
- Once an audit is triggered, continue all applicable in-scope audit work after the first finding and report every distinct evidence-backed issue.

## Maintenance rules

- During implementation, builders must loop through focused check, diagnosis, correction, and rerun until the changed behavior is stable.
- For a concrete bug, keep builder field testing minimal: use the original or smallest failing case only as needed to understand the defect, then once to confirm the fix. Add more samples only when requested or justified by risk, an unclear cause, or inconsistent results.
- Builder self-validation is mandatory for every change.
- Add a regression test for every fixed defect unless automation is technically impossible.
- Never rerun a flaky required test until green; record and resolve the instability.
- Update this profile when product risks, environments, or test responsibilities change.
- Keep command definitions only in `.quality/quality.toml` to prevent drift.
