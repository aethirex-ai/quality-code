# Parent browser preview bridge

Parent invocation (before builder timing):

```sh
PREVIEW_NODE=/absolute/bundled/node PREVIEW_PLAYWRIGHT_MODULE=/absolute/playwright/index.mjs python3 preview/broker.py --workspace /absolute/site --port ASSIGNED_PORT
```

The parent launches Chromium once. It never starts the backend or executes site source. The site owner starts its server with `--host 127.0.0.1 --port ASSIGNED_PORT --db /absolute/site/demo.sqlite3`. Browser HTTP traffic, including mutations, is restricted to that exact origin; redirects and other loopback ports are intercepted. WebSockets, service workers, and downloads are blocked. Each render creates and closes a fresh context, so cookies survive actions in one request but not separate requests. Backend database state remains owned by the site server.

Sandbox-side commands:

```sh
python3 /absolute/preview/client.py --workspace /absolute/site --ready
python3 /absolute/preview/client.py --workspace /absolute/site --page / --viewport 375 --actions-file actions.json
```

`--ready` means browser/broker readiness only, without contacting the backend. A render before backend startup returns `ok:false, classification:readiness`. Invalid protocol requests return `classification:protocol`; those outcomes are infrastructure/readiness evidence, not automatic product defects. Rendered pages and action failures carry `classification:product`.

`actions.json` is a workspace-relative regular non-hardlinked JSON file, maximum 8 KiB, with up to 24 actions. Supported actions: click, fill, select, check, press, scroll (scroll element into view), reload. Element actions require a CSS selector of 1–200 characters. Fill/select accept strings up to 2,000 characters; press accepts only Tab, Escape, Enter. Reload accepts only its op field. No request can supply a port, URL, JavaScript, root, or output destination. Page is `/` or an absolute same-origin path, without query, fragment, traversal, encoded percent leftovers, or scheme.

Results contain a native-view-compatible absolute screenshot path. Images are bounded to 12 MiB and randomly named beneath `.preview-output`; the descriptor-based `.preview-events.jsonl` records relative screenshot paths, actions, viewport, page, bounded errors/overflow/action results and classifications. History is bounded to 16 MiB. Password-selector values are redacted from history and visible text excerpts; console bodies, API bodies, cookies, authorization headers and token values are not collected. Only visible UI text is excerpted (1,500 characters). Requests/responses are limited to 12/16 KiB; per-render parent timeout is 65 seconds and client timeout is 75 seconds. The mailbox uses exclusive, no-follow regular-file opens, atomic publication, hardlink checks, fixed-root descriptors, random owned tokens and bounded queue entries.

Run `python3 preview/tests.py` in the parent environment with browser launch and local bind capability. Seven focused tests cover path/action/port refusal, password history, hardlinks and symlinks, owned mailbox cleanup, cookie lifetime, persistent API mutations, remote/other-port/WebSocket blocking, real desktop/mobile screenshots, and backend-unavailable classification. The synthetic browser test executes no measured solver output. Chromium runtime/module can be configured with the two environment variables above. Independent parent audit remains required before paid runs.
