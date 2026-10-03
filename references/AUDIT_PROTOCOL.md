# Independent audit protocol

This protocol begins only when the project's risk gate requires an independent audit or the user explicitly requests one. Do not invoke it merely because a file containing code changed. Once invoked, apply the full protocol; the entry gate limits frequency, not audit completeness.

## Independence boundary

Use a fresh audit agent. Give it the repository, acceptance criteria, raw diff scope, and generated audit packet. Do not provide the builder conversation, intended verdict, suspected bugs, or builder conclusions.

The audit is a second layer, not the project's first test pass. The builder remains responsible for iterative testing, debugging, regression coverage, and full pre-handoff verification. The auditor independently repeats and challenges that evidence.

The auditor must not:

- implement or repair the change
- edit project tests or documentation
- accept builder test output without reproduction
- widen the task beyond affected behavior and credible adjacent risk
- mark missing required evidence as a pass

## Inputs

Require:

- project root
- explicit acceptance criteria
- Git base, commit range, or named changed files
- `MAP.md`, project `TESTING.md`, and `.quality/quality.toml` when present
- audit packet from `./quality audit-packet --criteria "..."`

If Git is unavailable, audit only an explicit file set and report the lost history/diff evidence as residual risk. If scope is ambiguous, return `BLOCKED`.

## Procedure

### 1. Preserve the evidence surface

Record `git status --short` before testing. Do not clean, reset, stash, stage, commit, or reformat. At completion, compare the status and relevant file hashes. The final report must state whether the worktree remained unchanged.

### 2. Establish expected behavior

Translate each acceptance criterion into observable outcomes. Identify affected contracts, state transitions, trust boundaries, compatibility promises, and failure behavior before analyzing implementation details.

### 3. Inspect progressively

Read in this order:

1. changed-file list and diff summary
2. raw diff
3. named map sections
4. affected tests and contracts
5. neighboring implementation required to evaluate behavior
6. history or generated inventory only when a specific question requires it

### 4. Classify risk

Use the project risk map and the global testing standard. Raise the classification when the diff crosses an undocumented boundary or affects a wider surface than declared.

### 5. Perform static review

Review correctness, omissions, negative paths, error recovery, security, compatibility, tests, and maintainability. Ignore harmless personal style preferences.

### 6. Reproduce verification

Run required profiles independently. Prefer the project `quality` command. Run targeted tests before full suites so failures remain diagnosable. Preserve exact commands, exit codes, and concise evidence; keep full logs out of the agent context unless diagnosing a failure.

Use a temporary directory outside the repository for one-off reproductions. Do not add permanent tests during the audit.

### 7. Challenge the tests

Confirm important tests can fail for the relevant defect. Inspect assertions, negative cases, boundaries, and fixtures. For critical logic, use a safe temporary mutation or equivalent forced-failure reasoning when feasible, then prove the repository remains unchanged.

### 8. Complete the in-scope search

A finding sufficient for `FAIL` sets the minimum verdict; it is not a stopping condition. Continue all applicable static review, required verification profiles, targeted reproductions, and credible adjacent-risk checks within the declared scope. Report every distinct issue supported by evidence, ordered by severity.

If one activity is blocked, continue every unaffected activity. Record what was completed, what remains untested, and exactly how the blocker limits the result. Stop early only when a genuine blocker prevents any further reliable examination, or when continuing would require destructive, external, or out-of-scope action without authorization.

Do not inflate the report with duplicates, style preferences, or speculative concerns. Completeness means finding as many independent, actionable, in-scope issues as the available evidence supports.

### 9. Decide

- `PASS`: evidence satisfies every criterion and no blocking finding remains.
- `FAIL`: a defect, missing required test, unmet criterion, or policy violation exists.
- `BLOCKED`: missing environment, artifact, permission, or reliable scope prevents a defensible result.

Low-severity observations may accompany `PASS`. Critical or high findings always produce `FAIL`. Required checks not run produce `BLOCKED`, not `PASS`.

## Re-audit

After remediation, audit the new diff plus the prior findings. Reproduce the relevant checks again. Do not assume a described fix resolves the finding. A change authored by the auditor must be audited by a different fresh agent.

## Output discipline

Return one object matching the project audit-result schema. Findings must be evidence-first, ordered by severity, and free of general praise or implementation narration. If there are no findings, return an empty findings list rather than inventing reassurance.
