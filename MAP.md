# Quality Code project map

Last verified: 2026-10-04

## Product boundary

A Python bootstrap and verification toolkit plus reusable coding-agent instructions. Canonical engine: `scripts/quality_code.py`; installer: `scripts/install.py`; templates: `assets/project/`. Public explanation: `README.md` and `docs/`; `docs/index.html` is the static branded reader edition. No production service or customer data.

## Runtime flow

CLI arguments → project detection → template merge or TOML routing → local verification / JSON audit packet. Installation → global agent instruction blocks / skill copies / launcher symlink.

## Ownership

AethDesign maintains the standard and public edition. `scripts/` owns behavior; `assets/` owns project defaults; `references/` and `SKILL.md` own independent review instructions; `tests/` verifies contracts. `.quality/quality.py` is a generated copy of the engine and must match it.

## Contracts and state

CLI subcommands: init, adopt, upgrade, validate, verify, context, audit-packet. TOML configuration version 1, standard version 3. Audit result schema version 1. Project instructions preserve unmanaged text; map/testing merges preserve existing sections. Installer updates home configuration and creates a checkout-linked launcher.

## Security, privacy, and safety

Verification runs configured executables with user permissions. No sandbox. Preserve existing content and refuse an unmanaged wrapper. Do not publish private paths, credentials, local settings, or customer data. Installer is not transactional; document its writes and collision behavior.

## Change invariants

- Highest specific matched risk wins; fallback covers unmatched paths.
- Missing required evidence is not a passing audit.
- Builder verification cannot replace required independent review.
- Delegation uses native discovery with safe fallbacks; model and effort choices remain provider-neutral.
- Keep engine/local copy and schema/template copy identical.
- Distribution copies retain LICENSE and exclude Git history, local state, tests, and public documentation.

## Verification

`./quality validate` checks structure. `./quality verify full` runs offline stdlib unit/integration tests, distribution synchronization and documentation checks, and Git whitespace checks. Fast and changed profiles also run toolkit tests because the engine is small. Release uses the full profile; it performs no remote writes.

## Do not edit casually

Bootstrap, upgrade, installer, configuration defaults, agent policy, and CI affect preservation or public behavior. Independent audit required. Public publication is explicitly authorized by the repository owner for this initial edition.

## Context routing

`.quality/quality.toml` routes tooling and instructions to high risk and CI to critical risk. Default documentation is normal. Audit packets are temporary handoffs outside committed source.
