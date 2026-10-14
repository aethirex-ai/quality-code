# ServiceFlow

A locally runnable, full-stack portfolio MVP by **AethDesign**, a software-development and UI/UX design studio. **Hearth & Home** is the fictional Bristol home-services business used to demonstrate the product. There is no real client relationship, customer claim, certification or real service fulfilment. Only synthetic sample data is used.

## Requirements and exact setup

Node.js **24.15 or newer** (Node 26 used here), npm and Python 3 for the supplied browser bridge. SQLite is built into Node; no database server, credentials, paid services or AI key are needed. Run all commands from the repository root.

```sh
npm ci --cache .npm-cache
npm run migrate
npm run seed
npm run build
PORTAL_PORT=3000 npm run benchmark:start
```

Open **http://127.0.0.1:3000**. `benchmark:start` serves the **production** Vite build with Express on the exact `PORTAL_PORT` value; no automatic port fallback. In the benchmark use the existing supplied `PORTAL_PORT` instead of setting it to 3000:

```sh
npm run benchmark:start
```

For development after install/migrate/seed:

```sh
PORTAL_PORT=3000 npm run dev
```

Development uses Vite middleware on the same Express origin. `npm start` also serves the production build. Stop with Ctrl-C. Request state, history and auth secret survive server restart.

`.env.example` documents optional settings. Defaults work without a `.env` file. To customize locally, copy it to `.env`, which is ignored. `DATABASE_PATH` defaults to `./data/serviceflow.sqlite`. `BETTER_AUTH_URL`, if set, must match the exact browser origin; otherwise it is derived from `PORTAL_PORT`/`PORT` (default 3000). Prefer `127.0.0.1`, not `localhost`, to match origin enforcement. With no `BETTER_AUTH_SECRET`, the server creates a random mode-0600 secret once at `<database path>.secret` and reuses it. Do not publish the database, signing secret or `.env`.

Migrations are repeatable. Better Auth programmatic migrations manage auth tables; versioned SQL migrations manage the product tables. Seed is idempotent and creates four accounts, four services and eight representative requests/history events when no requests exist. It does not reset existing work. To make a separate fresh demonstration without overwriting data:

```sh
DATABASE_PATH=./data/fresh-demo.sqlite npm run migrate
DATABASE_PATH=./data/fresh-demo.sqlite npm run seed
DATABASE_PATH=./data/fresh-demo.sqlite PORTAL_PORT=3001 npm start
```

## Synthetic demo accounts

All use **`DemoHome2026!`**. The login page has buttons to fill the credentials; sign in remains an explicit action.

| Role | Email | Name |
| --- | --- | --- |
| Customer | `customer@serviceflow.demo` | Jamie Morgan |
| Second customer | `customer2@serviceflow.demo` | Alex Bennett |
| Provider | `provider@serviceflow.demo` | Sam Taylor |
| Admin | `admin@serviceflow.demo` | Robin Ellis |

Customer 1 and customer 2 have distinct requests. Public signup is disabled; the local seed command alone creates demo accounts through Better Auth. There is no password reset/email flow or real account onboarding in this MVP.

## Product journeys

- Public `/` and `/services`: useful fictional catalogue, indicative prices and request CTA.
- Customer `/request`: service, bounded work description, location, preferred start/end date and contact details. Preferences are enquiries, never confirmed appointments. `/dashboard` lists only the customer’s own requests; `/requests/:id` shows detail/history with server ownership checks.
- Provider/admin `/dashboard`: status totals, recent enquiries, searchable list and status filter. Detail allows valid next statuses and editable unsent reply drafts.
- Admin `/catalogue`: create/edit/activate/deactivate services and delete only unreferenced services. Referenced deletion is rejected; deactivation is offered instead. Request service name/price snapshots preserve historical meaning after edits.

Workflow: **New → Reviewing → Quoted → Booked → Completed**. Declined is available from New, Reviewing or Quoted. Booked cannot be declined; Completed/Declined are terminal. Server rejects skips, reversals and stale versions. Changes and actor/timestamp history commit in one SQLite transaction. Client operation keys and actor-scoped stored results prevent duplicate committed writes on a same-content retry; changed-content reuse is rejected. Request form values/token persist in tab session storage until success is acknowledged.

## AI-assisted draft boundary

Without `AI_API_KEY`, drafting uses a clearly labelled **deterministic server-side demo**. Drafts are editable, require review and are never sent. Drafting does not change status, record a sent message or add a successful mutation event. Customers cannot access the action.

The separate configured adapter in `src/server/drafts.ts` reads server-only `AI_API_KEY`, `AI_API_URL` (full OpenAI-compatible chat-completion endpoint) and `AI_MODEL`. A key with missing URL/model gives a safe unavailable error. No configured credentials are required or supplied here. **Verification uses injected mocked fetch only and makes no live AI requests.** The payload contains service name, redacted work description and date preference; it excludes contact fields and location, removes known contact name, emails, phone-like strings and UK postcodes from free text. Free-text redaction is conservative, not a guarantee that all personal information can be detected; staff should keep unnecessary personal data out of job descriptions. Provider output is parsed/bounded and capped at three questions. Provider failures return a safe error and leave state unchanged.

## Exact verification commands

```sh
npm test
npm run typecheck
npm run format:check
npm run build
npm run test:setup
./quality validate
./quality verify full
./quality verify release
```

`npm test` runs real HTTP auth/role/ownership/state/catalogue/idempotency/persistence tests against isolated fresh SQLite fixtures and configured-adapter mocks. Test listeners use free ports. `npm run build` includes typechecking; `npm run test:setup` verifies fresh migrations, repeat seed and production startup in isolation. See `TESTING.md` for scope and evidence.

With the benchmark’s supplied browser bridge and the production app running:

```sh
python3 preview_client.py --ready
python3 qa_check.py --owner integration --check-id browser-e2e --phase verification -- npm run test:e2e
```

The browser check creates one synthetic request per run, updates it as provider, verifies saved history and customer isolation, edits an unsent draft, and captures desktop/mobile form/catalogue/detail states. It requires the provided bridge; it is not a standalone browser installer. Native screenshots were inspected by the builder. Browser results are retained in `evidence/browser-results.json`, PNGs in `.preview-output`, and all check attempts in owner `check-runs.jsonl`. Expected negative tests are assertions, not defects; actual failures/corrections are classified in `evidence/issues.jsonl`. Evidence/runtime artifacts are gitignored but retained in the workspace.

## Architecture and limits

React/TypeScript + Vite + React Router + Express 5 + relational SQLite + **Better Auth** (library-managed password hashes/session cookies). Typed API contracts separate UI, validation/business logic, persistence/migrations and draft adapter. All business mutations require exact same-origin JSON and server authorization; Better Auth’s origin/CSRF safeguards remain enabled. Roles are read from the database, not trusted from client input. API responses are no-store. React renders supplied content as text. Production has self-only content security policy, security headers and rate limiting.

One business only: provider scope is all requests for that single business. There are no organizations, payments, live scheduling, automatic matching, SMS/email delivery, uploads, marketplace or external live integrations. “Quoted” and “Booked” are recorded workflow labels managed by staff, not a quote delivery or scheduling integration. Contact fields are captured but no contact takes place. Catalogue action records are stored for audit but have no separate UI. Search/filtering is client-side over authorized lists; there is no pagination. Local seeded credentials, loopback HTTP and single-process SQLite make this a demo, not a production deployment configuration. Automated contrast/accessibility certification, load testing and real provider quality are outside the verified scope.

**Critical risk independent gate: pending.** Full changed-scope audit packet is supplied for the parent’s fresh independent auditor; builder validation is not independent acceptance.
