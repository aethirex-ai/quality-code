# Verification and handoff

Run `python3 server.py --host 127.0.0.1 --port "$PORTAL_PORT" --db demo.sqlite3` for the parent preview. A new database gets the exact synthetic BRIEF fixtures; existing data is retained. Isolated tests use temporary databases and port 0. No dependency installation is needed.

## Automated checks

- `python3 -B -m unittest tests.test_backend`: 14 real HTTP tests for exact fixture/money, hashing/cookies, persisted sessions/restart/logout, client/staff visibility, forged author/role denial, JSON/origin/text bounds including lone surrogates and healthy emoji, atomic duplicate/concurrent mutations, deterministic post-commit response interleavings, exactly-one events, static allowlist and CLI readiness.
- `python3 -B -m unittest tests.test_frontend`: Node tests against a fresh actual server/SQLite database. Covers normal saves, literal markup/Unicode, permission denial, navigation/reload state, unsent/newer drafts, acknowledged comment/decision/publication and their immediate activity followed by failed refresh, GET-only recovery, delayed old-account conflict refresh overlapping logout/login, and delayed old-account successful save. A DOM harness exercises the actual app renderer's selection restoration; it does not claim rendered verification.
- `./quality verify full` and `./quality verify release`: required critical profiles; run the entire discovered behavioral suite through the protected `verify_app.py`, both JavaScript syntax checks and `git diff --check`.

All meaningful executions are wrapped in `qa_check.py`. Raw check runs remain in `backend/check-runs.jsonl`, `frontend/check-runs.jsonl`, and `integration/check-runs.jsonl`. `evidence/issues.jsonl` retains observed defect/tooling/refinement histories and rechecks. Intentional invalid-input requests that return expected errors are healthy negative controls, not failed product checks.

## Actual browser evidence

`python3 scripts/render_check.py NAME --viewport 375|1440 --actions evidence/NAME-actions.json` calls the unmodified parent preview bridge. Action objects use `op`, `selector`, and `value` where appropriate. Each request has a fresh cookie context; actions within a request share it. Reports persist in `evidence/renders/`, screenshots in `.preview-output/`. The script checks action completion, browser errors, external requests and horizontal overflow. Native image inspection is recorded separately in `evidence/visual-review.md`.

Executed journeys include login, exact authorized overview, brief/milestones/deliverables, client changes request, staff new revision, client approval and reload, literal discussion text and reload, activity, logout/account switch and studio overview. Desktop and mobile are inspected, including the mobile selected-review-before-form order and keyboard focus. The assigned demo database retains these synthetic browser mutations; isolated tests always seed a fresh database.

## Observed corrections

- UI-001: CSP blocked inline progress/chart dimensions. Replaced style attributes with native progress and CSS rules, then inspected the corrected 65% bar; focused frontend source contract passes.
- REC-001: successful refresh left the earlier recovery prompt visible. A failing assertion was retained; recovery now clears that prompt and the targeted test passes.
- NAV-001: loading-screen render erased project/tab selection during reload. Both the actual browser flow and app renderer regression failed before correction; explicit-navigation persistence and both rechecks pass.
- TOOL-001: preview action field schema was initially wrong. Three protocol-only rejections are retained; `op` resolves it. These did not execute the product flow.
- VIS-001: neutralized excessive green panel/text tint toward the frozen silver/near-black studio identity.

## Independent gate

Critical risk requires full/release evidence and a scoped audit packet, then parent-orchestrated fresh independent review. The initial builder handoff is audit-ready with the independent gate pending. No builder check or screenshot asserts independent PASS. Repairs and fresh re-audits share the one BUDGET allowance. Local synthetic verification does not certify external production deployment.

## Repair 01 (fresh independent re-audit pending)

AUD-001 reproduced both response races in deterministic actual HTTP/SQLite tests: pause immediately after the first commit, complete the second publication, then release the first response. Both assertions failed before repair. Successful project snapshots are now materialized before commit; the interleaving recheck passes and verifies the returned activity matches persisted activity.

AUD-999 covered supplied fixed-gate reload navigation and activity assertions. Restored detail now keeps a visible, authorized compact project list and open-project controls at both widths. Mutation responses return the actual persisted activity event, so acknowledged changes appear in history immediately even when follow-up refresh is delayed or fails. Three composed local-activity assertions failed before frontend event consumption and now pass. Actual browser comment/decision/publication, reload and reopening through project-list controls are rechecked at 375/1440. The fixed parent gate itself must be rerun independently; builder evidence is not its verdict.

Common protected corpus hashes are retained and checked with `evidence/repair-01-protected-manifest.json`. Repair code ownership stays with the primary; no new helper context is needed for this small coupled correction. Fresh full-scope independent review remains required.
