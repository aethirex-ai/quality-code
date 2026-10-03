# Testing standard

This audit-only standard defines the minimum evidence for accepting a change. Project `TESTING.md` files add context; they may strengthen but not weaken it without an explicit, recorded exception.

Basis: ISTQB Certified Tester Foundation Level v4.0.1, adapted for agent-driven software work: <https://istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf>.

## Testing principles

1. **Tests reveal defects; they do not prove correctness.** Report residual risk and untested behavior even after all checks pass.
2. **Exhaustive testing is impossible.** Select tests by product risk, affected contracts, change impact, and defect history.
3. **Test early.** Review acceptance criteria, design, contracts, migrations, and failure behavior before relying on execution.
4. **Defects cluster.** Give extra attention to complex, frequently changed, incident-prone, highly coupled, or security-sensitive areas.
5. **Tests wear out.** Add regression cases for defects, vary data and boundaries, and periodically challenge mature suites with mutation or forced-failure checks.
6. **Testing is context-dependent.** Select test levels, techniques, environments, and evidence for the actual product and risk.
7. **Absence of defects is not product success.** Validate stakeholder outcomes and operational behavior, not only written implementation requirements.

## Builder validation and independent audit

Quality has a mandatory builder layer and a risk-gated independent layer:

1. **Builder validation:** Every change receives proportionate builder validation. Run the narrowest relevant test or static check, diagnose failures, correct the work, and rerun until stable. Add regression tests for changed behavior when they provide meaningful protection, then run the verification required by the selected risk lane.
2. **Independent audit:** High- and critical-risk changes receive a fresh-agent audit that independently reproduces required checks. Low- and normal-risk changes do not receive one by default. The user may explicitly require an audit at any risk level.

Builder field and exploratory testing must be proportional. For a concrete reported defect, use the original or smallest failing case only as needed to understand the mechanism, then once after the change to confirm the fix. Run the smallest relevant automated regression check. Do not cycle through additional ad hoc samples unless the user or acceptance criteria requests broader coverage, or risk, an unclear cause, or inconsistent results justify expansion. This limit does not reduce an independently triggered auditor's risk-based completeness duty.

When the independent gate applies, its audit supplements rather than replaces builder testing. Builder self-review is useful evidence, but it cannot satisfy that gate or issue the independent `PASS`.

## Independent audit trigger

- **Low:** builder only by default. Use one focused visual, static, or targeted confirmation. Do not run a full suite, generate an audit packet, or start a subagent merely because code changed.
- **Normal:** builder validation and the smallest changed-scope verification by default. Do not start an independent audit unless the user asks or unresolved evidence raises the actual risk to high.
- **High and critical:** independent audit is mandatory after the builder completes the configured higher verification profiles.
- **Explicit request:** a user may force an independent audit at any risk level.
- **Delivery mechanics:** a routine local build, install, packaging step, or version bump that only delivers or confirms an otherwise low- or normal-risk change inherits that change's risk. Actual changes to build, signing, deployment, migration, rollback, security, or release behavior are classified on their own impact.
- **Completeness after entry:** once an audit is triggered, finding one defect does not end it; the auditor continues all applicable in-scope activities and reports every distinct evidence-backed issue.

## Test basis and traceability

Use the following as the test basis, in priority order:

1. acceptance criteria and explicit user intent
2. public contracts, schemas, migrations, and compatibility promises
3. `MAP.md` boundaries and invariants
4. project `TESTING.md` risks and known gaps
5. existing behavior demonstrated by tests, fixtures, releases, or production evidence
6. the implementation only after the expected behavior is established

Trace each material acceptance criterion and affected risk to at least one item of evidence. Implementation-shaped tests alone are insufficient when they do not demonstrate required behavior.

## Risk classification

Use the highest applicable level.

### Critical

Potential data loss, security or privacy breach, incorrect financial behavior, irreversible migration, authentication or authorization failure, privileged helper or OS safety behavior, changes to production deployment or signing behavior, payment, encryption, destructive operation, or release rollback failure.

Required evidence:

- focused tests for changed behavior and failure paths
- full automated verification
- contract, integration, migration, recovery, or security tests as applicable
- independent examination of rollback and operational failure behavior
- required platform or manual evidence; return `BLOCKED` when it cannot be obtained

### High

Public API or IPC changes, persistence, concurrency, background lifecycle, external-provider parsing, entitlements, changes to build or packaging logic, cross-platform behavior, or broad shared components.

Required evidence:

- focused tests including boundaries and negative cases
- full automated verification
- relevant integration or contract tests
- explicit residual-risk statement

### Normal

Ordinary feature logic with contained impact and a reversible failure mode.

Required evidence:

- focused unit or component tests
- changed-scope verification
- regression coverage for affected behavior
- independent audit only when explicitly requested or evidence raises the risk

### Low

Isolated display copy or labels, non-behavioral text, comments, formatting, static style, or isolated metadata with no runtime behavior, data, build, release, localization-contract, legal, accessibility, billing, security, or agent-instruction effect.

Required evidence:

- static inspection
- one focused visual, static, or targeted confirmation
- no full suite or independent audit by default

When uncertain between two levels, use the higher level until evidence justifies lowering it.

## Required audit activities

### Completeness rule

Discovering one defect sufficient for `FAIL` does not complete the audit. Continue every applicable in-scope static and dynamic activity and report all distinct evidence-backed issues. If one activity is blocked, continue unaffected work and identify the untested area. Stop early only when a genuine blocker prevents further reliable examination or continuing would require unauthorized destructive, external, or out-of-scope action.

### Static testing

Inspect:

- acceptance criteria for ambiguity, contradiction, and testability
- diff scope for unrelated changes and accidental generated output
- control flow, error handling, cleanup, retries, timeouts, and cancellation
- trust boundaries, input validation, authorization, secrets, and sensitive logging
- state transitions, persistence compatibility, migrations, and rollback
- dependency direction, coupling, duplication, dead paths, and misleading names
- map, test, documentation, and configuration drift

Formatting preferences are not findings unless they affect correctness, maintainability, consistency, accessibility, or an enforced project rule.

### Dynamic testing

Select applicable levels:

- unit or component
- component integration
- system or end-to-end
- contract or compatibility
- acceptance
- confirmation of the reported defect
- regression of affected and neighboring behavior

Default verification must be deterministic and offline. Live providers, production services, credentials, hardware, signing, notarization, purchases, or destructive environments require explicit authorization and separate evidence.

### Test techniques

Use techniques suited to the change:

- equivalence partitions for representative valid and invalid classes
- boundary values for lengths, ranges, times, quotas, limits, and empty states
- decision tables for interacting rules and permissions
- state-transition tests for lifecycle and persistence behavior
- branch-focused white-box tests for safety and failure logic
- error guessing based on incidents, hotspots, and platform behavior
- exploratory charters for user workflows not captured by automation

Do not chase a universal coverage percentage. Use coverage to find omissions. Critical decision logic should demonstrate relevant branches and failure paths; changed lines being executed is not enough.

## Non-functional selection

Test when implicated by the change:

- security and privacy
- reliability, recovery, idempotency, and fault tolerance
- performance, resource use, and responsiveness
- accessibility and keyboard behavior
- platform, browser, locale, timezone, and data compatibility
- installation, update, packaging, signing, and rollback
- observability without secret or personal-data leakage

## Test quality

A useful automated test must:

- fail for the defect or missing behavior it is intended to detect
- assert externally meaningful outcomes or stable contracts
- control time, randomness, network, filesystem, and environment where practical
- produce a reproducible failure with actionable output
- avoid depending on test order or mutable shared state

Every bug fix requires a regression test unless automation is technically impossible. When impossible, record the manual procedure, reason, owner, and residual risk.

## Flaky tests

Never obtain a pass by rerunning until green. A flaky required test makes the audit `BLOCKED` or `FAIL` according to its demonstrated product impact. Quarantine requires an owner, reason, replacement coverage, and expiry date.

## Entry criteria

Begin the final audit only when:

- acceptance criteria and diff scope are available
- the builder reports implementation complete and has finished its test/fix loops
- the builder has run the required pre-audit verification profiles
- required local dependencies are available or their absence is known
- the project identifies generated, archived, and sensitive areas

## Exit criteria

Return `PASS` only when:

- every acceptance criterion has evidence
- required verification profiles pass independently
- no critical or high finding remains
- required regression tests exist and demonstrate the behavior
- worktree changes caused by the audit are absent
- untested areas and residual risk are explicitly reported

Return `BLOCKED` when a required environment or artifact prevents reliable evaluation. Return `FAIL` when the change or its evidence is inadequate.

## Defect evidence

Each finding must contain:

- stable identifier and severity
- concise behavior-focused title
- affected file and line when available
- environment and preconditions
- reproduction or failing check
- expected and actual result
- impact and violated criterion or boundary
- required action, not a speculative rewrite
