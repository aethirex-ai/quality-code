# Frozen backend contract evaluator

Run with a Python 3.11+ stdlib interpreter and local loopback capability:

```sh
python3 judge/backend/evaluate.py SITE OUTPUT.json
python3 judge/backend/test_evaluator.py
```

`SITE/server.py` is launched using the public `--host 127.0.0.1 --port 0 --db PATH` contract. Every group receives a fresh temporary SQLite path; persistence groups restart the same owned server against that path. No application imports, schema assumptions, solver sources, external services or paid calls are used. The evaluator only exercises the API contracts in `BRIEF.md`.

The denominator is always twelve named groups:

| Group | Observable requirement |
| --- | --- |
| authentication | Protected APIs, invalid credentials, forged cookies, session-derived identity, cookie attributes |
| session_lifecycle | Existing cookie survives restart; logout clears and invalidates it, including after another restart |
| client_isolation | Exact account project visibility; wrong-client reads/writes return 404 and persist nothing |
| staff_permissions | Client cannot publish; staff cannot decide; submitted roles cannot grant privileges |
| json_and_input_bounds | JSON/content-type/origin enforcement; text and integer bounds; no partial mutation; valid boundary inputs |
| comment_identity_and_activity | Literal markup, trusted author, rejected/ignored forgery, staff discussion, exactly one event per successful comment |
| revision_publication | Trimmed title/summary, current revision increment, review reopening, older revision preservation, unchanged money, one event |
| decision_transitions | Changes requested, approve, later publication; previous decision events retained and money/revision unchanged by decisions |
| conflict_atomicity | Duplicate/opposite and stale decisions/publications produce 409 and no state/history/activity changes |
| concurrent_revision_writes | Two simultaneous requests with the same expected revision produce exactly one 201, one 409 and one stored revision/event |
| restart_persistence | Revision, decision, comment, activity and session persist; subsequent publication works |
| seed_and_read_contract | Fixed seeded states/money/history; required read fields; meaningful brief/deliverable/milestone presence and chronological reads |

Exit 0 means all groups passed; exit 1 means at least one group did not pass. The report records `pass`, `fail` (product), `blocked` (authentication prerequisite), `error` (instrument) and the fixed denominator. A missing server or failure before readiness remains a product setup failure with all twelve outcomes present. Loopback capability is preflighted separately: unavailable binding is an instrument error. Report-level `error` is non-null when a group has an instrument error. Group outcomes are **not distinct bug counts**; several failures may have one cause. Blocked groups do not manufacture separate defects.

`OUTPUT.evidence/` (derived from the output filename stem) retains bounded request JSON with actual status/body and required status, group assertion messages and private stderr tails (mode 0600). Synthetic login passwords and session-cookie headers are redacted. Reproduction uses the request sequence in each group; its database begins from the exact public seed. Parallel request evidence can appear in completion order.

An evaluation has a shared 110-second work deadline, a seven-second readiness allowance, two-second request bounds and owned process-group termination. After the bounded TERM grace, group SIGKILL is unconditional even if the leader already exited. Output readers use nonblocking raw descriptors and a stop event, avoiding blocking buffered pipe closure when descendants inherit stdout/stderr. Cleanup and writing bounded evidence reserve the remainder of a 120-second local run. On a pathological host process creation or filesystem operations themselves may exceed normal OS timing; the parent runner should enforce its outer 120-second timeout. Stdout lines are bounded at 4096 bytes, retained stderr at 32 KiB and captured response bodies at 64 KiB. A response beyond the capture bound is an instrument limitation, not a product verdict. No arbitrary port/process scan or unrelated process is killed.

`test_fixture.py` is an independent positive API oracle with a compact JSON state document transactionally stored in SQLite. It intentionally has no frontend and is not a solver application. Tests copy it into an isolated temporary site. Extra harmless API fields (such as author email) are accepted. Eight negative fixture mutations target isolation, staff access, stale publication, duplicate decisions, competing writes, persistence, duplicate events and author forgery; each has an unrelated healthy control. Additional tests cover fixed framing, launch failures, prerequisite attribution, malformed success schema, unavailable loopback and owned process cleanup. The descendant regression launches a TERM-ignoring child with inherited stdout/stderr, waits for the leader to exit, checks bounded cleanup and confirms the specific owned child is no longer running. `CONTROL_RESULTS.json` records the most recent suite outcomes; its transient fixture paths are not presented as retained evidence. `CONTROL_HISTORY.jsonl` preserves prior generated controls before the AUD-001 correction; passing prior controls did not establish descendant cleanup correctness.

Limits: this is a contract sample, not a complete security or production audit. It does not inspect password hash strength, static-file traversal, browser XSS execution or frontend behavior. Persistence of immutable decisions is observable through state and retained decision events; no undocumented database layout or decisions endpoint is assumed. The competing-write probe tests one simultaneous schedule. Legal IDs and extra narrative fields remain unrestricted. A parent fresh independent evaluator audit is required before these sources freeze and before evaluating either solver.
