# Frozen frontend evaluator candidate

Run with the bundled Node runtime:

```
node judge/frontend/evaluate.mjs SITE OUTPUT
```

SITE contains `server.py`, launched with loopback host, ephemeral port and a fresh temporary database. OUTPUT receives `report.json`, bounded private server logs, and PNGs. Evaluator exit 0 means all 11 browser groups passed; exit 1 means functional failures/not-run or failed/missing screenshots; exit 2 means a distinct fatal setup/capture error. Missing server/Chromium/readiness capabilities do not reduce the 11-group or 12-shot denominator. A browser pass does not replace backend authorization/security/state or independent visual assessments.

The fixed browser groups, in order, are:

1. `auth_identity_isolation`: invalid feedback, valid login, logout, second-client identity and no stale first-client text.
2. `authorized_cards`: exact c1/c2/staff visible project IDs, 2/1/3 respectively.
3. `detail_budget`: semantic project navigation, p1 title, raw 420000 cents, EUR 4200 display, back navigation.
4. `meaningful_content`: meaningful brief and >=3 meaningful deliverables/timeline entries.
5. `literal_comment_persistence`: literal markup, no injected DOM/execution, visible author, reload retention.
6. `decision_validation_persistence`: empty request note cannot finalize, valid note finalizes, useful feedback, unavailable decision controls and reload persistence.
7. `staff_publish_reopens_history_activity`: publication advances revision, reopens client review, preserves history/previous note and mutation activity, reload retention.
8. `client_staff_controls_hidden`: client cannot see staff publication fields/buttons. Unauthenticated controls are also checked in group 1.
9. `accessibility_focus_landmarks_attribution`: real labeled visible form controls, visible Tab focus, main/navigation landmarks and visible fictional attribution.
10. `responsive_widths`: no document horizontal overflow on overview and project tabs at 375px/1440px for relevant client/staff views.
11. `runtime_http_health`: page runtime errors, non-resource console errors, failed requests and unexpected HTTP >=400. Only known expected invalid-login, unauthenticated-me and blank-decision statuses are exempted; 500 never exempted.

These are frontend observable groups, not exhaustive WCAG or security checks. Groups 5/6/7 form a purposeful sequential state journey; a failed earlier mutation may cause later downstream failures. Groups run even after ordinary failures and keep the fixed denominator. No URL glob matching is used. Requests and source output are bounded; page operations wait for semantic hooks/text with 5-second deadlines and navigation 10 seconds. Launch readiness has 10 seconds; process shutdown always targets the exclusive detached POSIX process group with bounded TERM/KILL, even if its leader exited; inherited pipes are destroyed after termination. Darwin zombie-only EPERM is resolved by bounded numeric ps state; an EPERM with any live owned-group member still fails. Local loopback/browser execution may require the host's existing approval mechanism.

## Exact common screenshot plan

Screenshots use a separate new server database, not the functional probe's mutated database. Each width has a fresh browser context, and screenshots never submit mutations. Both subjects receive exactly the same plan at height 1000; full-page PNGs preserve content. Width order is 375 then 1440; names use `{width}-{view}.png`:

- `client-dashboard`: Alex signed in, initial overview.
- `project-brief`: p1 initial brief tab.
- `project-revisions`: p1 initial revisions tab.
- `project-discussion`: p1 initial discussion tab.
- `staff-dashboard`: studio signed in, initial overview.
- `staff-publish`: p1 initial revisions tab, title `Refined identity direction`, summary `The wordmark spacing and color balance have been refined for client review.` filled but unsubmitted.

Capture entries retain failed/missing slots. The screenshot manifest is not a visual score; anonymous independent assessment follows. Screenshots must not be replaced or selectively rerun based on aesthetic outcome.

## Checker proof

`fixture/` is a minimal synthetic frontend with stub backend, not a measured app or reference implementation. `selftest.mjs OUTPUT` verifies healthy 11/11 and 12 screenshots, then seeds independent defects for identity leakage, money metadata, correct-cents/wrong-euro-scale display, unsafe markup, whitespace decision validity, revision refresh, staff controls, labels, overflow, runtime and HTTP failures. Each target must fail while authorized-card healthy controls still pass. Missing-server setup retains all 11 not-run denominator entries and fatal separately. Proof JSON/logs are local artifacts; no oracle or judge files belong inside solver workspaces.

Only judge/frontend/** is owned here. Root owns final independent audit and freeze digest. Any change after proof requires relevant verification and fresh independent review before freezing; no post-grading repairs.

## Preflight audit regressions

`regression.mjs OUTPUT` tests actual TERM-ignoring descendants inheriting stdout/stderr with both an exited and a running leader, requiring descendant termination and cleanup below 2.3 seconds; an actual live-group permission-denial control must remain an error. It tests common dot/comma/space/apostrophe grouping and decimal formats, browser healthy US/German/French/plain amounts, and a wrong-scale visible amount while raw cents remain correct. It retains the 11-group/12-shot plan. `displayedEuroCents` validates the displayed numeric value; raw `data-total-cents` is checked separately. AUD-001/AUD-002 independent re-audit remains required.

## Recorded navigation amendment

The original evaluator is retained in `evaluate-original.mjs`; `evaluate-reload-only.mjs` preserves the intermediate repair, and `evaluate.mjs` contains final semantic detail/tab readiness waits. All11 group definitions and assertions stay fixed. The parent report records original8/11 each, intermediate11/11 vs10/11 and final11/11 each. Original captures are never replaced. See [amendment](../../navigation-amendment.json); `navigation-regression.mjs` and `tab-regression.mjs` reproduce delayed healthy navigation and targeted negative controls on disposable fixtures.
