---
name: audit-code-change
description: Independently audit a completed code, configuration, dependency, migration, build, or release change and return a strict evidence-backed verdict. Use only when explicitly invoked for a fresh-agent audit after implementation; do not use while building the change or for self-review.
---

# Audit Code Change

Perform a read-only, independent audit of a completed change. Treat builder claims and prior test output as untrusted evidence until reproduced.

Do not use this skill merely because code changed. Invoke it only when the user explicitly requests an independent audit or the project's configured risk gate requires one. Low- and normal-risk work remains with the builder by default. Once invoked, complete the full in-scope audit even after the first failing finding.

## Required inputs

Obtain:

- repository or project root
- acceptance criteria
- Git base or explicit diff scope
- generated audit packet, when the project provides `./quality audit-packet`

If the scope cannot be determined without guessing, return `BLOCKED` instead of widening it silently.

## Load context progressively

1. Read the raw diff and changed files first.
2. Read only `MAP.md` sections named by the audit packet or implicated by the diff.
3. Read project `TESTING.md` for project risks and known gaps.
4. Read [TESTING.md](references/TESTING.md) and [AUDIT_PROTOCOL.md](references/AUDIT_PROTOCOL.md) completely.
5. Read [GIT_BASELINE.md](references/GIT_BASELINE.md) only when auditing repository initialization, an initial commit, ignore rules, or a source-control migration.
6. Inspect additional source, tests, history, or contracts only when evidence requires it.

Do not load generated inventories, full test logs, unrelated maps, or the builder conversation by default.

## Audit

1. Record the initial worktree state.
2. Confirm acceptance criteria are testable and trace them to changed behavior.
3. Classify product risk using the project configuration and the testing standard.
4. Perform static review of the diff, contracts, failure paths, security boundaries, and maintainability hazards.
5. Independently run the required verification profiles and targeted reproductions.
6. Check that tests would fail for the relevant defect, not merely execute changed lines.
7. Report missing evidence, untested behavior, and residual risk.
8. Continue every applicable in-scope audit activity after finding a defect. A condition sufficient for `FAIL` determines the verdict but does not complete the audit. Report every distinct evidence-backed issue found unless a genuine blocker prevents further examination.
9. Confirm the worktree state is unchanged by the audit.

Do not edit production code, project tests, configuration, generated files, or documentation. Create temporary reproductions outside the repository when useful. A missing regression test is a finding for the builder, not permission for the auditor to implement it.

## Verdict

Return exactly one verdict:

- `PASS`: all required checks passed, no blocking finding remains, and residual risk is stated.
- `FAIL`: at least one reproducible defect, unmet acceptance criterion, missing required test, or policy violation exists.
- `BLOCKED`: required evidence or a required environment is unavailable, so a reliable verdict is impossible.

Never convert unavailable testing into `PASS`. Never use confidence language as a substitute for evidence.

## Output

Return one JSON object conforming to [audit-result.schema.json](assets/project/.quality/audit-result.schema.json). Keep findings evidence-first and concise. Include file and line when available, the exact check or reproduction, required action, untested areas, and residual risk.
