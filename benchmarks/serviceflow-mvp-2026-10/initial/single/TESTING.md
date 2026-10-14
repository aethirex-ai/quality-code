# ServiceFlow verification

Risk is **critical**: authentication, authorization and persistent state. Builder checks do not constitute independent acceptance. The parent will perform the fresh independent full-scope gate.

## Automated verification
- `npm run typecheck` checks all client/server/shared/script/test TypeScript.
- `npm test` executes Vitest validation, AI transport mocks and real Express/Better Auth/SQLite integration tests. Integration tests use an isolated temporary database, actual password sign-in and session cookies; no paid services or live AI. Negative tests deliberately assert 401/403/404/409/415/422 outcomes.
- `./quality verify full` runs `npm run verify:full` (typecheck + test) and whitespace checks.
- `./quality verify release` runs `npm run verify:release` (typecheck + Vite/esbuild production build + fresh database/process restart/source-development-serving checks) and whitespace checks.
- `npm run db:migrate` applies auth/application migrations. `npm run db:seed` creates synthetic sample data without resetting state. Both can be repeated.

Tests cover normalized input, real dates, malformed/oversized text, field forgery, auth/signup surface, all role/ownership read/write classes, cross-site/missing-origin/non-JSON actions, full workflow/terminal/skip/reverse/stale conflicts, concurrent updates, activity rollback, durable retry keys, database reopen with sessions/history, admin CRUD/activation/version conflicts, inactive/deleted selection, referenced deletion and service snapshots. AI tests cover no-key fallback, missing-information questions, PII minimization, configured adapter success, invalid/excessive output, exceptions/status failures and incomplete settings, all with mocked network only.

## Browser and visual verification
The supplied `preview_client.py` uses the ready parent browser bridge. It starts each journey with fresh cookies. App must already be running at the PORTAL_PORT origin. Commands and outcome metadata are recorded through qa_check.py; safe action lists and screenshots are retained under evidence/. Inspect desktop (1440) and mobile (375) landing, form, customer dashboard/detail, staff dashboard/detail/draft, and admin catalogue. Exercise customer submission, provider status update, customer reload/history, admin service controls, keyboard focus and visible validation/empty states. Record concrete evidence in evidence/browser-report.md; unavailable or failed renders remain unverified until corrected.

## Persistence and fresh setup
README setup uses pinned lockfile, explicit migration/seed and production build. `npm run test:process` performs the isolated real process test. `npm run test:e2e` uses the running app and supplied bridge with paced logins. Fresh-database process restart checks must use a temporary database and owned loopback listener. Confirm existing sessions, request status/history and retry receipts after restart; never reset the demonstration database to make a failing test pass.

## Evidence and gate
Retain every check with `python3 qa_check.py --owner integration --check-id <id> --phase verification -- <command>`; owners may be frontend/backend/integration. Use `--phase recheck --issue-id <id>` for corrections. evidence/issues.jsonl records category and reproduction/fix/recheck details. Generate `./quality audit-packet --criteria-file evidence/acceptance.txt`. Do not mark the app independently accepted: the gate is parent-managed and pending.
