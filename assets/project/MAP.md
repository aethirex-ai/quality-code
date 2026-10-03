# PROJECT_NAME map

Last verified: YYYY-MM-DD

This compact map records stable boundaries and risk. Keep generated inventories outside this file under `.quality/`. Git history is the document version; do not add manual revision numbers.

## Product boundary

- **Purpose:** USER_OUTCOME
- **Canonical implementation:** CANONICAL_PATHS
- **Entry points:** ENTRY_POINTS
- **Legacy or archived areas:** LEGACY_PATHS
- **Generated areas:** GENERATED_PATHS

## Runtime flow

```text
INPUT -> COMPONENT -> STATE_OR_SERVICE -> OUTPUT
```

## Ownership

| Area | Canonical paths | Responsibility |
| --- | --- | --- |
| AREA | `PATH` | RESPONSIBILITY |

## Contracts and state

- **Public interfaces:** API_IPC_CLI_SCHEMA_CONTRACTS
- **Persistence:** DATABASE_FILES_SETTINGS_CACHES
- **External systems:** PROVIDERS_SERVICES_PLATFORM_APIS
- **Compatibility promises:** VERSIONS_MIGRATIONS_ALIASES

## Security, privacy, and safety

- **Trust boundaries:** INPUT_AUTHORIZATION_BOUNDARIES
- **Sensitive data:** DATA_CLASSIFICATION_AND_STORAGE
- **Privileged or destructive behavior:** PRIVILEGED_OPERATIONS_OR_NONE
- **Required fail-closed behavior:** FAILURE_INVARIANTS

## Change invariants

- INVARIANT_ONE
- INVARIANT_TWO
- Files or contracts that must change together: CO_CHANGE_RULES

## Verification

- Fast: `./quality verify fast`
- Changed scope: `./quality verify changed`
- Full: `./quality verify full`
- Release: `./quality verify release`
- Project-specific manual evidence: MANUAL_EVIDENCE

## Do not edit casually

- HIGH_RISK_AREA_AND_REASON
- MIGRATION_OR_COMPATIBILITY_BOUNDARY
- RELEASE_OR_SECURITY_BOUNDARY

## Context routing

Detailed path-to-risk, test, and map-section routing lives in `.quality/quality.toml`. Update it when ownership or risk changes. Generated inventories must be regenerated rather than hand-edited.
