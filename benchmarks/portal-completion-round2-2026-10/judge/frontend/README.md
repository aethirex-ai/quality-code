# Completion-pilot browser checks

The frozen [evaluator](evaluate.mjs) checks eleven observable groups: identity isolation, authorized projects, budget display, meaningful content, literal comment persistence, decision validation/persistence, studio publication/history/activity, hidden unauthorized controls, focus/labels/landmarks, responsive overflow, and runtime/resource health. Groups can share causes or cascade; they are not distinct bug counts. A sampled browser pass does not replace an independent application audit.

Use your own Node, Playwright and Chromium installation with loopback/process permissions:

```sh
BENCHMARK_PLAYWRIGHT_IMPORT=playwright node judge/frontend/evaluate.mjs SITE OUTPUT
BENCHMARK_PLAYWRIGHT_IMPORT=playwright node judge/frontend/defect-probes.mjs SITE OUTPUT
```

The three supplemental recovery probes cover healthy Unicode/comments/account identity, a delayed conflict refresh across account switching, and a committed comment followed by failed dataset reads. Read both the reported status and `instrumentErrors`: an error recorded after the assertion can leave a raw pass that must be qualified. Do not call it a clean pass or infer an application defect from a transport instrumentation error.

Captures use settled **viewport** screenshots at 375×1000 and 1440×1000, blurred focus and top scroll. Twelve required states are client dashboard, project brief, revisions, discussion, studio dashboard and publication, at both widths. Publication fields receive the same software-project draft without submitting it. Four additional login/mobile content/form views are reported separately. Missing captures remain missing. These captures differ from the historical full-page pilot; its scores cannot be compared.

Healthy/negative controls include [selftest](selftest.mjs), [capture regression](capture-regression.mjs), [revision-format neutrality](revision-regression.mjs), [canceled transport](defect-probes-regression.mjs), and alternate refresh strategies. They are instrument controls, not measured client apps. The preflight passed the controlled cases; the later single diagnostic exposed the qualified transport result described above.
