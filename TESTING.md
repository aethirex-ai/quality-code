# Quality Code testing profile

## Test objectives

Prove the CLI can bootstrap a usable project, preserve existing content during adoption, refuse wrapper collisions, route actual configured paths, produce scoped audit packets, and surface verification failures. Confirm installation in an isolated home directory and restrict skill distribution to intended files.

## Product risks

| Risk | Level | Evidence |
| --- | --- | --- |
| Bootstrap or upgrade overwrites content | High | Temporary-project preservation and runtime/schema/license collision tests |
| Risk route hides a higher-risk area | High | Mixed-path fallback and parent-Git scope regression tests |
| Failed verification looks successful | High | Failing executable and unknown-profile tests |
| Installer ships private local state | High | Allowlist distribution and retained license tests |
| CI cannot run the advertised checks | Critical | Local equivalent; hosted matrix after publication |

## Test levels

Stdlib `unittest` integration tests invoke real CLI processes with temporary directories. Pure merge/routing tests assert public invariants. Repository checks assert generated engine/schema parity and local documentation links.

## Test data and environment

Offline by default. Python 3.11+ and Git required. Fixtures contain synthetic project text; installer uses an isolated home. No credentials, customer data, live providers, or production environments. Unit tests must not mutate the repository.

## Non-functional coverage

Preservation and fail-visible verification are covered. Ubuntu and macOS CI is configured; only the local platform is validated before publication. Performance, Windows wrappers, adversarial filesystem/symlink behavior, and concurrent writers are not characterized.

## Manual and release evidence

Review banner rendering, README readability, initial source inventory, secret filename/value-pattern scan, and large-file inventory before the first commit. A passing configured workflow is not implied until hosted Actions runs.

## Known gaps and residual risk

The installer is not transactional. It refreshes managed skill copies and writes home settings before a potential launcher collision. Path routing and agent instructions require project-specific judgment. The tool does not enforce merge protection or validate a final auditor verdict. Documentation does not claim certification or measured outcome improvement.

## Independent audit gate

Scripts, templates, schemas, and agent policy require a fresh read-only audit after full verification. CI changes also require release verification. See `SKILL.md` and `references/AUDIT_PROTOCOL.md`.

## Maintenance rules

Behavioral fixes need focused regression tests. Do not retry flaky checks until green. Keep `.quality/quality.py` synchronized with `scripts/quality_code.py` and the project-local schema synchronized with its template.
