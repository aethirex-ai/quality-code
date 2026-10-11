# New-client fixture checks
## Test objectives
Three distinctive, responsive, usable client concepts with native imagery and safe functional demos.
## Product risks
Normal local UI with synthetic state. No real bookings, health advice, payment or deployment.
## Test levels
Focused builder checks then post-run identical browser assertions at 375/1440 and anonymous visual review. Passing DOM checks cannot prove art direction.
## Test data and environment
Static local sites, native tools, installed Node/Playwright. Browser sandbox restrictions may block builder preview; report rather than retry unchanged failures.
## Known gaps and residual risk
One paired workload, different imagery and cache/load confounds; image tokens/backend/price unavailable. No general/causal benefit or subscription savings established.

## Non-functional coverage

- Security/privacy: Not yet characterized; update when the product boundary is defined.
- Reliability/recovery: Not yet characterized; update when the product boundary is defined.
- Performance/resources: Not yet characterized; update when the product boundary is defined.
- Accessibility/compatibility: Not yet characterized; update when the product boundary is defined.
- Installation/update/rollback: Not yet characterized; update when the product boundary is defined.

## Manual and release evidence

| Scenario | Procedure | Evidence retained |
| --- | --- | --- |
| Primary user workflow | Define before release | Retain concise result with the audit evidence |

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
