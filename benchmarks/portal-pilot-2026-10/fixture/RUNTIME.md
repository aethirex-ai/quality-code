# Local runtime and generic preview

Python 3.14.7 with stdlib SQLite; Node: node. No dependency installation. The native profile retains workspace filesystem protection and permits only 127.0.0.1/localhost command network traffic through the active proxy. Do not bypass proxies or sandbox controls. Native Chromium is blocked by Mach IPC permissions; use the parent preview bridge.

The parent starts the browser/broker before your timer. You create and start the actual backend when ready. `PORTAL_PORT` supplies the assigned port; this server serves the preview:

```sh
python3 server.py --host 127.0.0.1 --port "$PORTAL_PORT" --db demo.sqlite3
```

Your own isolated tests may use port 0 and fresh databases. The preview uses the assigned port. It never starts or executes your backend/source.

```sh
python3 preview_client.py --workspace . --ready
python3 preview_client.py --workspace . --page / --viewport 375 --actions-file actions.json
```

The other supported width is 1440. Readiness confirms the browser/broker, not the backend. Inspect returned PNGs with native image/file tools, not just metadata. Action files are valid JSON, at most 8KiB/24 actions: click/fill/select/check/press/scroll/reload. CSS selector length <=200, value <=2000, keys Tab/Escape/Enter only. No arbitrary JavaScript, URL, port, root or output setting. Each request starts with a fresh cookie context; login and later actions in the same request share cookies. Backend state persists between requests. Page paths are safe absolute same-origin paths without query/fragment; navigate query URLs through actual controls. Login sequence: fill login-email, fill login-password, click login-submit.

Backend-unavailable results are readiness evidence, malformed requests are protocol errors, and rendered/interaction failures need product diagnosis. Do not automatically count them as website bugs. The bridge blocks other origins, downloads and WebSockets. Visible text excerpts are capped at 1500 characters; media stays in files. A preview has a 75-second client timeout. Use purposeful flows rather than duplicate inspections.

```sh
python3 qa_check.py --owner backend --check-id auth-regression --phase verification -- python3 -m unittest tests.test_auth
```

Owners are backend/frontend/integration; phases initial/verification/recheck. Optional --issue-id links a correction. Records live in OWNER/check-runs.jsonl. Append stable owner/id issue updates to evidence/issues.jsonl as BRIEF specifies. Missing command launch errors are exit 127; expected scaffold/negative cases are distinct from product defects.

Preserve protected APP_PROMPT, BRIEF, BUDGET, RUNTIME, MODEL_COSTS, NATIVE_MODELS, qa_check.py, preview_client.py and verify_app.py. Implement source/tests and tailor actual profiles without lowering auth/state risk or gates. Parent independent audit remains pending after frozen outputs; no external release inside this builder session.
