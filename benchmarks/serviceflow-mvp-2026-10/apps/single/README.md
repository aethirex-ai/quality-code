# ServiceFlow

A working full-stack portfolio demonstration for **Hearth & Home**, one fictional local home-services business in Bristol. The customer site, request tracking and staff tools demonstrate AethDesign's software-development and UI/UX work. **AethDesign is the studio, not the service provider.** No real client relationship, customer, testimonial or delivered outcome is implied.

React + TypeScript + Vite; Express; Better Auth email/password and database sessions; SQLite through better-sqlite3; Zod contracts. All business data is relational and local. No paid service or credential is required.

## Local setup

Use Node.js **22.13+** (tested with 26.5.0), npm and Python 3 for the supplied QA/browser helpers. The lockfile pins package versions. The SQLite package includes platform binaries; unsupported platforms may need a C/C++ toolchain.

Run from this directory:

```sh
npm --cache .npm-cache ci
cp .env.example .env
npm run db:migrate
npm run db:seed
npm run build
npm run start
```

Open **http://127.0.0.1:3000**. The app binds only to loopback. No silent port fallback occurs. For a different ordinary port, change both `PORT` and `APP_ORIGIN` in `.env`.

`BETTER_AUTH_SECRET` may be left blank: the server generates a random local secret at `data/.auth-secret` with mode 0600 and reuses it after restart. The database, secret and `.env` are ignored. Do not delete the secret if you want existing session cookies to keep working. No secret is bundled into the frontend.

On npm versions that require explicit native-script approval, the package manifest already permits the pinned SQLite/esbuild scripts. On older npm versions normal install scripts run. The optional macOS watcher extension is not required by this app.

For local UI development after migration/seeding:

```sh
npm run dev
```

This builds the frontend and starts the TypeScript server through Node’s loader, serving the built client with the same restrictive CSP as production. Rebuild and reload after UI changes; restart after server changes. No HMR or WebSocket transport is used. Production remains `npm run build` followed by `npm run start`.

## Benchmark start

```sh
npm run benchmark:start
```

This starts the **production build**, not the development server. When injected, `PORTAL_PORT` controls both loopback port and trusted app origin, overriding the copied example's port/origin. Setup and build must already be complete. It serves `http://127.0.0.1:$PORTAL_PORT`. Without that variable it uses the ordinary `.env` configuration.

## Synthetic demo accounts

All four use **`ServiceFlow2026!`**. Login offers account-fill buttons; no public registration, email verification, password-reset emails or real email sending exists.

| Role | Email | Name |
| --- | --- | --- |
| Customer | `alex@demo.local` | Alex Morgan |
| Customer | `jamie@demo.local` | Jamie Taylor |
| Provider | `provider@demo.local` | Sam Green |
| Admin | `admin@demo.local` | Robin Ellis |

Seeded: four services and six requests spanning all six statuses. Phone numbers and contacts are synthetic. The second customer exists to demonstrate ownership isolation. Migration and seed scripts can be repeated without resetting committed application state. Existing seed requests are not duplicated or moved back to their original status. Browser verification may add further synthetic enquiries.

## Product journeys

- Public landing: catalogue descriptions, indicative prices and Request a service. No testimonials or fabricated credentials.
- Customer: sign in, submit work/location/date preference/contact details, then inspect only your own requests and chronological history. Direct/API access to the other customer's details returns a generic 404.
- Provider: status totals, recent enquiries, search/filter, request details, actor/time history and permitted workflow actions. This is the only service business, so all provider requests belong to it.
- Admin: provider capabilities plus catalogue create/edit/activate/deactivate/delete and a catalogue activity log. Referenced services cannot be deleted; deactivate them instead. Requests retain service name/description/price snapshots.
- Staff draft assistant: deterministic server-side reply, up to three missing-information questions, editable text, review checkbox and copy action. Nothing is ever sent and drafting does not mutate status/history.

Dates and ranges are **preferences, not appointments**. Both phone and email are required contact fields in this demo. Prices are free-text indicative labels, never charges. No business-area hard postcode restriction is imposed: the team reviews each location. Quoted/Booked statuses represent staff workflow only; this MVP does not calculate quotes or schedule appointments.

Status workflow: **New → Reviewing → Quoted → Booked → Completed**. Declined is allowed only from New, Reviewing or Quoted. Completed and Declined are terminal; Booked cannot decline. Skips, reverse moves and stale versions are explicitly rejected without recording a successful action.

## Persistence and server boundaries

Better Auth owns password hashing, session storage and signed HttpOnly SameSite cookies. Server actors/roles come from the session and database, never request bodies. Every application read/write enforces its role or ownership contract. Mutation requests require the exact trusted Origin, acceptable Fetch Metadata and JSON; Better Auth's own origin/CSRF mechanisms remain enabled. Production headers include a restrictive CSP. Untrusted content is rendered as text by React.

Status/catalogue mutations and actor/timestamp activity commit in one SQLite transaction. Owner-scoped retry keys and persisted payload fingerprints deduplicate committed business writes. Version checks reject conflicting edits. UI request form data and pending retry keys survive reload in tab-scoped sessionStorage, scoped to the account; sign-out clears local storage. Status/service save results update the view directly, so a separate refresh failure does not replay the saved mutation. Explicit reload controls show read errors.

Application schema: `user_roles`, `services`, `requests`, `activity`, `mutation_receipts`, `schema_migrations`. Better Auth manages `user`, `session`, `account`, `verification`. `migrations/001_application.sql` is the versioned application migration; `db:migrate` also runs library-managed auth migrations.

## Optional configured AI adapter

Leave `AI_API_KEY` and `AI_MODEL` blank for normal demo use. No AI credential is requested, and all benchmark checks use fallback or injected mocks.

`src/server/ai.ts` contains a separate server-only configured adapter for the OpenAI Chat Completions structured-output protocol. Its key and model come from environment variables. No model identifier is assumed. Missing keys select deterministic drafts; incomplete settings, unavailable provider or invalid output select a clearly labeled deterministic fallback. The provider payload includes only service snapshot, redacted work description and preferred dates. Dedicated contact fields, location, identifiers and history are excluded. Raw provider exceptions and secrets are not logged. Names/addresses freely typed in a work description cannot be reliably anonymized; use only synthetic data in this portfolio demo.

Mocked tests verify the configured request headers/body and output parsing without making live requests. Live provider behavior, model availability and sending integrations are intentionally unverified. Review any generated text before copying it.

## Checks

```sh
npm run typecheck
npm test
npm run format:check
npm run build
npm run test:process
./quality validate
./quality verify full
./quality verify release
```

Full runs TypeScript and all Vitest tests; release runs a production build and an isolated fresh-database **real process restart** check. `test:process` repeats migrations/seed, verifies production assets, signs in with real Better Auth cookies, submits/updates an enquiry, restarts the server, checks ownership/session/history/retry persistence, and checks source development serving. It uses a free loopback port and removes only its own temporary database/process.

Real-browser coverage, with the app already running and the supplied preview bridge ready:

```sh
python3 preview_client.py --ready
npm run test:e2e
npm run test:boundary
```

This submits a uniquely labeled synthetic enquiry as Alex, updates it to Reviewing and drafts as the provider, then reloads and checks history as Alex on mobile. Each bridge request gets fresh cookies; the script spaces logins to respect production authentication limits. It asserts every browser action, expected content, runtime errors and document overflow. It writes raw metadata and action files under `evidence/`; manual PNG inspection remains a separate builder requirement. These browser commands require the supplied benchmark bridge and are not standalone Playwright installation commands.

Client recovery regressions additionally interrupt a real committed response body and mount actual UI components with out-of-order reads and navigation. `test:boundary` submits maximum-length accepted synthetic text, checks mobile/desktop details and customer/staff overviews, and preserves its historical request while deactivating the added test service. It requires the same running app/bridge and respects production login limits.

See [TESTING.md](TESTING.md), [MAP.md](MAP.md), [evidence/browser-report.md](evidence/browser-report.md), and owner `check-runs.jsonl` files for observed checks and retained failures. `evidence/issues.jsonl` separates product defects, visual refinements, tooling failures and expected negative checks.

## Boundaries and review status

This is a local demonstration with fixed demo accounts, no registration/recovery/real notifications, a single business, no payments, scheduling, matching, uploads, marketplace or organizations. Draft edits are local and intentionally not saved or sent. No deployment or external live integration has been performed. Assistive-technology usability beyond semantic/focus checks and live AI behavior are not established by the current evidence.

**Audit-ready does not mean independently accepted.** Authentication/authorization/persistence are critical risk. The builder runs full/release checks and prepares the complete changed-scope packet; the parent supplies a fresh independent full-scope auditor and returns findings to the persistent builder.

## References

The supplied frozen screenshots and text establish studio context. Actual studio: [AethDesign](https://www.aethdesign.com/). Auth follows [Better Auth's Express integration](https://better-auth.com/docs/integrations/express) and [database/migrations documentation](https://better-auth.com/docs/concepts/database). The configured draft adapter follows the [official OpenAI Chat Completions reference](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create), using the OpenAI Docs skill. No reference assets imply a real service-business client relationship.
