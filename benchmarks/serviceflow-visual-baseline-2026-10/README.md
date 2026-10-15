# ServiceFlow frontend remake trial

This is an observational follow-up to the [ServiceFlow MVP experiment](../serviceflow-mvp-2026-10/). It records two frontend remakes of different existing apps. It does not change that experiment's original outputs or scores.

Both corrected apps have passed the prior broad gates and their additional same-reviewer supplemental content re-reviews. Final native-tree accounting is reconciled. Static-gallery publication review remains a separate gate. Earlier FAIL/BLOCKED outcomes, originals and first handoffs stay visible.

The [static comparison gallery](../../docs/benchmarks/serviceflow-visual-baseline-2026-10/) contains frozen originals, first reported handoffs and independently re-reviewed final corrections. Its [results](../../docs/benchmarks/serviceflow-visual-baseline-2026-10/results.json) are the machine-readable presentation record. [Supplemental findings](reviews/supplemental-content.json) preserve both FAIL outcomes in sanitized form.

## Question and method

Can each agent produce a useful frontend remake from the installed standards and this identical minimal instruction?

> Fully remake the frontend of this ServiceFlow app.

The exact UTF-8 prompt includes a trailing newline. SHA-256: `ac741b838e4c1cf81a1a40f072dd41795b411062b4428ea96562f9f1a72733de`.

No target layout, reference design, visual annotations or requested-fix list was supplied. Existing app context and installed Quality Code, Visuals and Swarms standards were available. Both roots used `gpt-6.1-sol` at high reasoning effort. The runs occurred in fixed order, single then adaptive, without elapsed caps, phase deadlines or an audit-round limit.

The single condition used no helper during its first workflow. Adaptive chose one fresh independent reviewer, with internal review and repairs before its first reported handoff. It did not choose an implementation swarm or a cheaper implementation model. “First handoff” means the primary builder's first reported completion before parent-provided feedback, including any internally chosen helper work. Later audit feedback and repairs resumed the exact builder roots.

The frozen protocol called for independent review after handoff. An observation addendum records the decision to reuse a valid evidenced independent gate selected by adaptive before handoff, instead of duplicating its entire investigation. Missing or invalidated gates still require review. The original protocol was not rewritten.

Original apps and first handoffs remain unchanged. The single first parent audit found stretched long-content cards, redundant labels and missing browser-submission evidence. A later browser re-review was blocked by lost preview capability. Recovery and subsequent review produced an earlier broad PASS. Adaptive's internally chosen review and later parent validation also produced a broad PASS. Fresh supplemental content review then found four single and five adaptive finding families, including redundant supporting prose and adaptive accuracy contradictions about shared-account access and quote viewing. Those reviews failed. Each exact builder root made one coherent supplemental correction batch. The same respective independent reviewer inspected the frozen delta and fresh desktop/mobile renders and returned PASS with no remaining findings. The narrow reviewers inspected builder full/release logs; they did not independently rerun the unchanged functional/security investigation.

## Timing and accounting boundary

The single first workflow took 16m 01s, with a known text-token Standard API-equivalent proxy of $1.7486296. Adaptive's first workflow took 30m 53s, with $5.1725212, including its chosen reviewer. These are rounded display times; exact seconds and native counters are in the results record.

Final totals include the measured builder roots, descendants, resumed correction turns and independent reviews. Single recorded $24.2602914 and adaptive $11.1585184 in known text-token proxies. [Phase accounting](accounting.json) retains all increments, model attribution, native durations and parent/interphase gaps. Controller interruption and recovery remain visible in elapsed time. End-to-end intervals were 11,092.390 seconds for single and 4,337.697 seconds for adaptive. They include 5,140.434 and 1,803.079 seconds respectively outside native phase intervals. Single waited while adaptive ran during the parent-controlled sequence. These wall intervals are not a fair model-speed ranking. Parent orchestration, browser service, setup, presentation, publication and comparison work are outside those native trees; their unknown cost is excluded, not assumed free. One image-generation call was observed per first workflow. Billed image usage is unknown and excluded.

Cached input is part of input, and reasoning output is part of output. Neither is added a second time. Cumulative native snapshots and resumed trees require deduplication. The proxy prices uncached input, cached input and output with the recorded Standard schedule and request-specific context thresholds. Builder roots and the internally chosen reviewer used gpt-6.1-sol at observed high effort. Parent supplemental and focused reviewers used gpt-6-astra at observed medium effort; their higher-rate requests remain included and identified per phase. It treats noncached input as ordinary input because cache-write classification is unavailable. It is conditional, not a bill, subscription percentage or savings estimate. Price references were checked on 2026-10-14: [official pricing](https://developers.openai.com/api/docs/pricing) and [model reference](https://developers.openai.com/api/docs/models/gpt-6.1-sol).

## Reading the screenshots

The gallery samples landing, sign-in, service request and customer overview at CSS widths 1440 and 375. Originals come from the unchanged earlier benchmark. First-handoff source is frozen. Adaptive first-stage images were captured later by replaying that source with a fresh presentation database, not at handoff time. Synthetic records and timestamps differ between stages, so this is not a pixel-difference test.

Every published capture has an exact byte hash in [capture-provenance.json](../../docs/benchmarks/serviceflow-visual-baseline-2026-10/capture-provenance.json). The gallery may clip measured empty capture-canvas margins caused by browser zoom; the raw image link retains the unchanged file. Private DOM records were collected just before screenshots and can contain transient loading text absent from the image. They are not claimed to be perfectly synchronized. Source and actual screenshot evidence govern visual claims. Final capture collection waited for loading to settle.

The first assembled-publication review subsequently failed on a missed Single shared-account access assurance. Earlier content PASS remains historical. A late exact-root correction changed only request/privacy copy, followed by four fresh affected renders and focused independent PASS. [That history](reviews/publication-followup.json) distinguishes the app-delta review from the required assembled-publication re-audit. The additional native repair/review usage, elapsed time, defect family and cycle are included.

## Source replay

`source/<condition>/initial/manifest.json` describes a UI-only patch against the corresponding frozen `benchmarks/serviceflow-mvp-2026-10/apps/<condition>/` app. It records exact before/after SHA-256 values, patch hash and binary asset hashes. The [complete UI inventory](source-inventory.json) also retains the unchanged selected-file hashes for each frozen stage. Initial and final source stages are separate. The `accepted` directory contains the independently re-reviewed post-handoff correction; its manifest records PASS and the supplemental review hash. The broad and supplemental gate scopes are distinct.

Use a fresh destination for each snapshot. `replay_source.py` always starts from the corresponding frozen original app, applies **either** its initial **or** accepted patch, copies the declared binary asset and verifies every selected UI-file hash. Do not apply the accepted patch on top of the initial patch.

From this repository root, reconstruct and run the single final snapshot:

```sh
python3 -B benchmarks/serviceflow-visual-baseline-2026-10/replay_source.py --condition single --stage accepted --destination ../serviceflow-single-accepted
cd ../serviceflow-single-accepted
npm --cache .npm-cache ci
cp .env.example .env
npm run db:migrate
npm run db:seed
npm run build
npm run start
```

Open `http://127.0.0.1:3000`. Node.js 22.13 or newer is required by the original single app; its native SQLite package may need a supported platform binary or compiler. Stop that local server before running the adaptive example on the same port. From this repository root:

```sh
python3 -B benchmarks/serviceflow-visual-baseline-2026-10/replay_source.py --condition adaptive --stage accepted --destination ../serviceflow-adaptive-accepted
cd ../serviceflow-adaptive-accepted
npm ci --cache .npm-cache
npm run migrate
npm run seed
npm run build
PORTAL_PORT=3000 npm run benchmark:start
```

The adaptive app requires Node.js 24.15 or newer. To inspect a first handoff, select `--stage initial` and a different unused destination, such as `../serviceflow-single-initial`. Existing destinations are refused without overwriting them. Both apps run locally with synthetic shared demo accounts and no paid provider credentials. The replay utility does not install dependencies, launch servers or run paid models.

All four reconstruction commands were exercised in temporary directories and every selected UI hash matched. Setup/run commands were checked against the frozen package scripts and original app READMEs; the corrected builder workspaces passed full/release checks. A clean-machine dependency download was not repeated for publication. Browser harness commands in the original app documentation require separate private trial capabilities and are not part of this source replay.

The projection includes only `index.html`, `src/client/` and `public/`. It omits private runtime/browser harness files, standards injected for the run, native transcripts, databases, credentials, generated test data and measurement helpers. It supports inspection and local UI reconstruction, not a complete rerun of paid native sessions or a claim that every raw trial artifact is public. The exporter checked patch application and exact textual reconstruction from the frozen checkpoint. The offline checker independently repeats the public reconstruction check.

## Integrity and review

Run `python3 -B benchmarks/serviceflow-visual-baseline-2026-10/check_publication.py` to check local links, referenced bytes, exact source reconstruction, stage/capture uniqueness, counter subsets and pending/final invariants. Run the focused negative controls with `python3 -B -m unittest discover -s benchmarks/serviceflow-visual-baseline-2026-10 -p 'test_*.py' -v`. These checks do not establish visual or functional acceptance. The repository's release profile and a fresh independent publication/visual review remain required before release.

[Correction classification](iteration-summary.json) records conservative observed lower bounds: single has four distinct defect families and four evidenced correction/recheck cycles; adaptive has six families and five cycles. Repeated copy findings are grouped into one family. Counts are not quality scores or estimates of general efficacy.

## Limits and ownership

There is one run per different starting app, no repeated sample and no untreated baseline-control arm. Internal workflow choices, execution order, caching, host conditions, recovery and gate orchestration differ. Do not infer a causal baseline effect, a swarm advantage, general superiority, a speed/cost winner or subscription savings.

ServiceFlow and the depicted home-services businesses are fictional demonstrations. AethDesign maintains this experiment; no customer relationship or completed service job is claimed. The gallery serves static captures and recorded data, with no login, enquiry form, analytics integration or local-database connection. GitHub Pages receives hosting requests under [GitHub's privacy statement](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement). Contact the [repository maintainers](https://github.com/aethirex-ai/quality-code/issues) about these public files. Runnable source remains a local demonstration with shared sample accounts, not a production service.
