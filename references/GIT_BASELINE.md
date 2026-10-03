# Git baseline standard

Load this reference only for repository initialization, initial commits, ignore-rule changes, or source-control migrations.

## Establish the boundary

- Resolve the canonical project root before initialization.
- Do not create nested repositories inside an existing umbrella repository.
- Do not initialize backups, caches, generated distributions, vendor trees, or operational-data archives as source repositories.
- Give independently released products separate repositories unless an intentional monorepo owns their shared history and verification.

## Preflight before the first commit

1. Inventory source, tests, configuration, generated output, local tool state, runtime data, binaries, and archives.
2. Create project-specific ignore rules. Do not apply a universal `build/` or `dist/` rule without confirming those directories contain no source.
3. Exclude secrets, credentials, local environment files, databases, logs, caches, recordings, signing material, packaged applications, and dependency directories.
4. Preserve safe examples such as `.env.example` only after confirming they contain placeholders.
5. Inspect unignored large files and every file selected for the initial commit.
6. Run the project baseline verification and record known failures and unavailable environments in project `TESTING.md`.
7. Commit only reviewed source and reproducible configuration. Do not create or push a remote without explicit authorization.

## Existing repositories

- Preserve dirty working trees and unrelated user changes.
- Never clean, reset, stash, stage all, or create a baseline commit merely to simplify an audit.
- Compare ignore-rule changes against already tracked files; adding a pattern does not remove tracked sensitive or generated content.
- Treat history rewriting, repository splitting, large-file migration, and secret removal as destructive migrations requiring explicit approval and rollback planning.

## Audit evidence

Require:

- resolved repository root and ownership decision
- list of ignored and intentionally tracked exceptional files
- secret and sensitive-filename scan result without exposing secret values
- unignored large-file report
- baseline verification result
- reviewed staged-file list
- residual risks, including unavailable release or platform checks
