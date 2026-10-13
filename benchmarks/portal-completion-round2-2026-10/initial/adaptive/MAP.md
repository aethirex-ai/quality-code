# AethDesign Client Workspace map

## Product boundary
A fictional local client portal for the real AethDesign software development and UI/UX studio. `BRIEF.md` defines exact seed, API and interaction contracts; `BRAND.md` and `brand/` supply the frozen identity. Customers, accounts, projects and budgets are synthetic. Python stdlib/SQLite and dependency-free HTML/CSS/JavaScript only.

## Runtime flow
`server.py` binds loopback, initializes the requested database once and prints flushed JSON readiness after binding. The `public/` static allowlist serves `index.html`, `app.mjs`, `state.mjs`, `styles.css` and `favicon.svg`. `WorkspaceServer` also permits isolated port-0 tests. No external resources, APIs or packages are used.

## Ownership
The primary remains the persistent owner of visual direction, frontend, integration and repair. One fresh implementation helper owns `server.py` and backend tests; its work is joined before audit. Actual routing, supported model evidence, effort/context choices and limitations are in `ROUTING.json`. The parent orchestrates fresh independent full-scope reviews; builders do not issue an independent verdict.

## Contracts and state
`server.py` owns salted password verification, persisted unpredictable sessions, account-derived authorization, bounded JSON/Unicode validation, project visibility and SQLite transactions. Project mutations use `BEGIN IMMEDIATE`; immutable revisions/decisions and their activity events commit with project state. Failed mutations close/roll back the transaction. Monetary values are integer cents. Seed decisions, revisions and sessions survive process restart.

`public/state.mjs` owns asynchronous account/view generations, request sequencing, project loading, draft maps, pending mutations and feedback. Every continuation checks account scope; view-specific responses also check selected project and navigation generation. Acknowledged writes clear only matching submitted drafts and update known state before refresh. Failed refreshes acknowledge committed saves and offer GET recovery; successful recovery clears that prompt. In-flight navigation preserves newer drafts.

`public/app.mjs` renders escaped text, real forms and required test hooks. It writes per-account project/tab selections only on explicit navigation, restores them after authorization, and clears displayed data/drafts on sign-out. Passwords are transient form values and are never persisted in browser storage. Code-native commerce/merchant/SaaS concept previews explain fictional product work. `public/styles.css` owns the silver/near-black responsive system, restrained state accent, visible focus and mobile content-before-action composition. Native progress elements and CSS chart heights respect CSP.

## Security, privacy, and safety
Authenticated client boundaries are critical. Cookies use the required name, HttpOnly, Path=/ and SameSite=Lax; opaque server sessions remain authoritative. JSON-only mutations reject explicit cross-origin browser writes. Text, including nested strings, is validated before encoding/hashing/database work. Static paths are allowlisted; database/source files cannot be served. Errors are bounded. No real services, uploads, communications, payments or releases.

## Change invariants
The critical `auth-and-state` route and full/release gates remain intact. Protected briefs, references, instruments, prices and native model catalog stay unchanged. No commits or deployment. Initial audit-ready does not mean accepted. Fix blocking findings in this same builder, add relevant regressions and obtain fresh independent re-audit within the shared allowance.

## Verification
`tests/test_backend.py` covers real loopback HTTP authentication, role/owner boundaries, input validation, transactional concurrency, activity counts, CLI readiness, logout and restart persistence. `tests/test_frontend.py` runs `tests/frontend.mjs` against a fresh real backend, injecting transport failures/delays for composed recovery/account/navigation races and exercising the actual app selection renderer with a bounded DOM harness. This harness is not visual evidence.

`scripts/render_check.py` uses the parent fixed-origin browser bridge and retains reports in `evidence/renders/`; native PNG inspection supplies desktop/mobile visual evidence. `qa_check.py` retains check outcomes under backend/frontend/integration, including genuine failures; `evidence/issues.jsonl` records cause, fix and recheck. `TESTING.md` explains reproducible checks and limits. Full/release profiles run behavioral tests, JS syntax and diff checks. The independent audit packet is generated after integration verification.
