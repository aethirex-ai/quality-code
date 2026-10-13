# Completion and capture correction / 13 October 2026

The original pair measured initial audit-ready builds, **not completion through Quality Code's independent acceptance gate**. Its common prompt explicitly deferred independent review until both outputs froze and prohibited post-grade repairs. Both builders correctly reported their gate pending. The later independent app audit failed both snapshots. Consequently the 16m08s/41m52s and API-equivalent prices are initial-build measurements; independently accepted time/cost are unknown. Publication PASS means truthful evidence publication, not application acceptance. The existing workflow already requires fixing blocking findings and fresh re-audit; the benchmark stopped that loop.

## Confirmed surviving causes

- Single's conflict recovery guards account generation before a refetch but misses the check after its awaited response. Existing account-switch and conflict tests exercised the paths separately.
- Single's type/length validation accepts lone Unicode surrogates; later encoding/database work returns 500. The original invalid-input tests omit this boundary.
- Adaptive's acknowledged POST and failed detail refresh share one error path. It restores the draft and allows duplicate retry after the save. Normal persistence checks do not cover that composed error path.

Adaptive had corrected Unicode handling during development, and single had corrected save/refresh feedback. These are different coverage histories, not a general delegation-quality finding. Historical app sources and failures remain unchanged.

## Original visual scores are capture-confounded

Fresh diagnosis with unchanged source reproduces the displaced adaptive sidebar and visible hidden skip link in full-page screenshots after scrolling. At 1440px, after filling the form, scrollY is 399; the actual viewport sidebar y is 0 and the unfocused skip link top is -70. Full-page capture instead shows sidebar at 399 and the hidden link at 329. The ordinary viewport renders both correctly. The effect also occurs in mobile captures. The adaptive original empty staff draft separately resulted from editing before asynchronous selected-tab rendering settled.

[Full-page diagnostic](../../docs/benchmarks/portal-pilot-2026-10/diagnostic-captures/adaptive-1440-filled-focus-full.png) and [ordinary viewport diagnostic](../../docs/benchmarks/portal-pilot-2026-10/diagnostic-captures/adaptive-1440-filled-focus-viewport.png) show the same fresh diagnostic state. They are not replacements or new graded outputs. Original 24 captures and blind scores remain preserved. The original 4.4/3.9 score difference mixes actual choices with capture artifacts; no corrected pair has been re-scored, so no visual superiority conclusion is established.

Genuine differences remain: adaptive repeats large artwork before every tab and puts mobile decision/publishing forms before selected content; single has clearer content order and form guidance. Both kept one persistent visual owner, but the prompt allowed independent art direction and they stopped at different times. Total build time does not isolate design effort or prove delegation caused those differences.

## Brand and next-test correction

The common brief explicitly invented AethDesign Atelier and prescribed identity/editorial project narratives. That direction came from the benchmark author. The actual [AethDesign landing page](https://www.aethdesign.com/) presents a software/web/app and UI/UX studio. The next comparison supplies identical dated text and desktop/mobile references from the real landing page, with commerce/SaaS project content. It includes per-condition independent gates, repairs, fresh re-audits and owned cleanup in completion time/tokens; initial and accepted-or-capped states are retained separately. Exhausted budgets remain incomplete. Settled matched viewport captures and explicit brand-fit review replace the confounded capture interpretation.
