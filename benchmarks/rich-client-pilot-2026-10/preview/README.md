# Fixed-workspace visual preview bridge

The parent launches a browser-capable broker for each condition workspace.
The native solver requests previews using atomic files **inside its own writable
workspace**, so `codex exec -s workspace-write` needs no permission changes,
socket allowance, networking, or approval bypass. No model/provider calls occur.

Acceptance: sandboxed clients receive 375×900 or 1440×900 PNGs, page readiness,
bounded console/page errors, and horizontal-overflow metadata. Invalid local
paths, remote URLs, extra fields, cross-condition symlinks, and other viewports
fail. Requests contain no oracle, grading, arbitrary execution, root selection,
condition selection, or output-destination interface.

## Parent initialization

Requires Python 3.10+, Node, Playwright, and installed Chromium. Runtime defaults
are portable: `node` and `playwright`. If using a bundled runtime, set
`PREVIEW_NODE` to its Node executable and `PREVIEW_PLAYWRIGHT_MODULE` to its
Playwright `index.mjs`. Private machine paths are supplied at launch only.

```sh
python3 "$PREVIEW/broker.py" --workspace "$ROOT"
```

Launch outside the solver's sandbox in the parent's approved browser environment.
One broker and separate protocol directory per condition. It prints
`{"ready":true,"transport":"mailbox","workspace":"..."}` after Chromium launch.
The client readiness op additionally verifies `.preview-mailbox` is serviced.
The parent should perform this readiness check before starting benchmark timing.
The broker serializes renders; `.preview-output` stores uniquely named PNGs.

## Native solver

No new `codex exec` flags are necessary; retain the original workspace sandbox.
Run clients with cwd set to the condition workspace or pass `--workspace`.

```sh
python3 "$PREVIEW/client.py" --ready
python3 "$PREVIEW/client.py" --page index.html --viewport 375
python3 "$PREVIEW/client.py" --page pages/contact.html --viewport 1440
```

The JSON result has the absolute PNG path, page, viewport, title,
`horizontalOverflow`, at most ten overflowing-element summaries, and at most
12 console errors and blocked requests. Use the native local image tool to view
that PNG. Captures show the 900px viewport; no full-page or arbitrary DOM query
interface is offered. Ready takes no other request fields.

## Isolation and limits

A broker captures static assets from its fixed root directory descriptor using
`O_NOFOLLOW` for every entry. Hidden paths, symlinks, hardlinks, unsupported file
extensions, and files outside that root are omitted. Bounds: 500 files, 12 MiB
per file, 64 MiB total, depth 12. Asset content is snapshotted before rendering.
The browser fulfills only that snapshot at synthetic `http://preview.local`;
no HTTP server or localhost port is opened. External HTTP/file requests,
WebSockets, service workers, and downloads are blocked. Local page JavaScript
runs normally in Chromium without Node or arbitrary broker execution access.

Request schema is immutable: `{op:"ready"}` or
`{op:"render",page:"relative.html",viewport:375|1440,actions?:[...]}`. The mailbox uses random
32-character request IDs, exclusive-create pending files, and atomic renames.
Each read/write uses a no-follow directory descriptor. Client queue limit 100
entries; server limit 200 (clean stale files before restart). Requests and
responses are bounded to 4 KiB and 16 KiB. Client waits at most 45 seconds;
render processes have a 25-second deadline. Malformed inputs return bounded
errors. Client removes its own request/response files after completion/timeout.

Screenshots are staged in the parent-controlled preview directory, then copied
via fixed-root, no-follow output directory/file descriptors. Parent must retain
separate native condition workspace roots and a read-only broker/client source
directory. This bridge is not an OS isolation boundary against an unrestricted
same-user process. Generated PNGs remain available for inspection; clean them
between runs if appropriate. No sibling workspace or grading data is opened.

## Evidence

```sh
cd "$PREVIEW"
python3 -m unittest -v tests.py
codex sandbox -P :workspace -C "$ROOT" python3 "$PREVIEW/client.py" --ready
codex sandbox -P :workspace -C "$ROOT" python3 "$PREVIEW/client.py" --viewport 375
codex sandbox -P :workspace -C "$ROOT" python3 "$PREVIEW/client.py" --viewport 1440
```

Ten tests cover request contracts, traversal/encoded traversal, URL rejection,
viewport types/range, extra/cross-condition fields, symlink rejection,
descriptor-safe snapshots, atomic mailbox round trips, cleanup and namespace
symlink refusal. Native sandbox smoke confirmed readiness and rendering through
the **default mailbox with no socket/network overrides**, including bounded
console errors and blocked remote resources.

## Optional Unix transport (sandbox helper only)

`--transport unix` on both scripts enables the original AF_UNIX implementation,
using `$ROOT/.preview.sock` (0600); keep macOS socket paths below roughly 104 bytes.
The installed `codex sandbox --help` supports exactly scoped socket allowances:

```sh
codex sandbox -P :workspace -C "$ROOT" \
  --allow-unix-socket "$ROOT/.preview.sock" \
  python3 "$PREVIEW/client.py" --transport unix --ready
```

The installed `codex exec --help` exposes neither `-P` nor `--allow-unix-socket`.
The [documented permissions profile](https://learn.chatgpt.com/docs/permissions)
`network.unix_sockets` allowance was tested inline with network disabled and
failed with EPERM without the helper socket flag. Do not claim this profile works
for native exec in this installation, and do not broaden network/socket access.
Mailbox is the default and proven native integration. No credentials, model
calls, or global configuration mutations were used in these checks.

## Interaction-state previews

Add `--actions-file actions.json` to render the final state after a local sequence.
The JSON file must be a workspace-relative regular file, at most 4 KiB. Example:

```json
[
  {"op":"fill","selector":"#name","value":"Alex"},
  {"op":"select","selector":"#kind","value":"b"},
  {"op":"check","selector":"#consent"},
  {"op":"click","selector":"#submit"},
  {"op":"press","selector":"#submit","value":"Tab"}
]
```

```sh
python3 "$PREVIEW/client.py" --page index.html --viewport 375 --actions-file actions.json
```

Optional `actions` contains at most 12 objects. Only `click`, `fill`, `select`,
`check`, `scroll`, and `press` are accepted. Every action needs a nonempty selector of at
most 200 characters; fill/select take a string `value` up to 300 characters.
Press accepts only Tab, Escape, Enter. Click/check/scroll accept no value. Scroll uses locator.scrollIntoViewIfNeeded()
and keeps the same bounded viewport screenshot. Unexpected
fields and arbitrary script/evaluate operations are refused. Each action has a
one-second timeout; execution stops on the first failure. `actionResults` records
bounded successes/failure diagnostics. Each render gets a fresh browser context
while actions in that render share state. Output also includes a bounded 1500
character visible text excerpt and the active element's tag/id/type. No hidden
contract assertions or external oracle are included. Ten tests now also cover
invalid actions, oversize selector/value/list/request rejection.


Final preflight bounds: the renderer accepts at most 96 MiB of input to accommodate
the 64 MiB static snapshot after base64 expansion, without changing image bytes.
Every handled render (including refused requests) appends a record to the fixed
workspace `.preview-events.jsonl`: UTC timestamp, page/viewport/actions, result
status, errors, overflow, action results and workspace-relative screenshot path.
Readiness operations are not logged. Records are at most 16 KiB; oversized event
metadata is omitted explicitly. History is capped at 16 MiB and fails closed with
a bounded error if full or unsafe; archive it before continuing. Source contents,
visible text excerpts and external grading data are not logged. History uses a
no-follow fixed-root file descriptor and rejects symlinks/hardlinks.
For lower sections, an action can be `{ "op":"scroll", "selector":"footer" }`.
