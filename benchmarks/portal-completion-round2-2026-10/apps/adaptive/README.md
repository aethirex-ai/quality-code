# AethDesign Client Workspace

A fictional local project portal for AethDesign, a software development and UI/UX studio. Includes secure client/studio sessions, project briefs, revisions, review decisions, discussion and activity. All accounts, customers and budgets are synthetic.

Run with Python stdlib only:

```sh
python3 server.py --host 127.0.0.1 --port 8000 --db demo.sqlite3
```

Open the printed loopback port. Port 0 allocates an available port. The server prints a flushed JSON readiness line and preserves database state and sessions across restart. The sign-in page offers buttons that fill the synthetic demo credentials from BRIEF.md.

Run `./quality verify full` and `./quality verify release`. See TESTING.md for browser evidence and focused checks, MAP.md for architecture, and ROUTING.json for ownership. Initial builder delivery is audit-ready; independent acceptance remains pending the parent-orchestrated gate.
