# ServiceFlow MVP: completion without stage deadlines

Both sessions reached **independent local-app PASS** after repairs and full-scope re-audits. Adaptive chose one direct backend helper while the primary continuously owned the frontend and integration. Every primary and auditor used the same native model at high effort; the helper used that same model at medium effort. No cheaper-model implementation or recursive swarm was exercised.

| Observation | Single | Adaptive |
| --- | ---: | ---: |
| Initial builder | 42.33 min | 22.08 min |
| Calendar through accepted completion | 145.35 min | 116.11 min |
| Controller execution intervals | 134.22 min | 88.85 min |
| Fresh independent audit roots | 4 | 4 |
| Observed distinct defects | 10 | 5 (4 app behavior + 1 verification delivery) |
| Evidenced product correction/recheck cycles | 11 | 5 |
| Reported input tokens | 46,325,274 | 32,137,917 |
| Cached input, already included above | 44,899,584 | 30,824,832 |
| Reported output tokens | 293,883 | 217,650 |
| Conditional mixed-tier API equivalent | $11.3628 | $7.8852 |

These observations come from one ordered, partly overlapping pair. Calendar time contains interruptions, controller amendments and report correction. Controller execution intervals exclude recorded gaps but include setup/check/cleanup within the running subject controller; they are wall time, not CPU time or pure model latency. Other account activity and shared infrastructure can affect speed. The initial builder row is not accepted completion.

## Product and acceptance

[The same prompt](APP_PROMPT.txt) asked for a fictional home-services MVP with customer enquiries, a small catalogue, Better Auth, relational persistence, customer/provider/admin roles, server-side ownership and mutation authorization, enforced workflow and history, service administration, and editable unsent reply drafts. Both independently selected React/TypeScript, Express, SQLite and Better Auth. Both followed Quality Code; this is not a comparison with an agent that lacks the standard.

The [accepted source projections](apps/) run locally using their own READMEs, migrations and seeds. No key or paid service is required. Live AI was not called: the deterministic labeled fallback is usable offline, while injected mocks exercise the optional configured server-only adapter. No image-generation tool was used in either subject. The [gallery](https://aethirex-ai.github.io/quality-code/benchmarks/serviceflow-mvp-2026-10/) serves screenshots, not authenticated backends.

Acceptance includes fresh setup, required full/release profiles, real auth and ownership boundaries, invalid role/CSRF/workflow writes, catalogue permissions, activity/transaction behavior, retry and stale-state recovery, restart persistence, AI fallback/privacy boundaries and rendered desktop/mobile states. [Independent report summaries and raw report hashes](app-audits.json) identify the final gates. The original builder READMEs can still say that independent review is pending: those immutable handoff bytes predate the subsequent audits; the report summaries supply the final acceptance state.

No observed independent finding remains in the accepted versions. That is a scoped local MVP result, not a claim of production readiness, complete vulnerability detection, legal compliance, formal accessibility certification or verified live AI behavior. Free-text personal-data redaction remains heuristic. Use synthetic data only.

## Repairs and iteration quality

The independent [iteration classification](iteration-review.json) groups actual root causes and evidenced fix/recheck cycles. Single had 10 distinct observed defects and 11 cycles; one wrapping defect needed two successive corrections. Adaptive had four application-behavior defects and one verification-delivery defect, each with an evidenced correction/recheck cycle. Visual refinements, tooling errors, expected negative tests, model turns and repeated assertions are separate.

Single corrections covered configuration/origin handling, navigation and mobile layout, reply question limits, committed-write retry recovery, stale reads, identity-specific drafts and configured-draft privacy/question selection. Adaptive corrections covered a login/navigation race, two distinct privacy-redaction roots, clean-source browser-artifact generation and valid long catalogue content at mobile width. The incorrectly oversized 103-character fixture was properly rejected; fixing that fixture did not fix an additional app bug.

The counts describe recorded construction/review work. They do not measure latent bugs, comprehensive defect recall or independent defect-finding sensitivity against a hidden oracle. Test counts differ in granularity and are not quality scores. Both accepted gates examined the same agreed product contracts.

## Where the token cost went

Input totals already include cached input. Output totals already include reasoning tokens. Adding either subset again would double-count usage. Exact native session snapshots, CLI increment/cumulative bases, resume prefixes, descendant lineage and per-request counters reconcile in [usage.json](usage.json). Each final request delta equals its native last-request record and sums to the phase/session/tree totals.

| Conditional Standard API component | Single USD | Adaptive USD |
| --- | ---: | ---: |
| Uncached input | 3.028668 | 2.626170 |
| Cached input | 5.1991552 | 3.0824832 |
| Output, including reasoning | 3.135025 | 2.176500 |
| **Total** | **11.3628482** | **7.8851532** |

| Work category | Single USD | Adaptive USD |
| --- | ---: | ---: |
| Initial implementation | 2.4642400 | 1.6242180 |
| Original-builder repairs | 3.0365954 | 1.3910924 |
| Independent audits, including invalid reports and correction | 5.8620128 | 4.8698428 |
| Invalid-scope audit subset, already included | 2.5817504 | 0.8337768 |

The adaptive report-only correction adds 0.6257720 USD within its audit subtotal. Its failed launcher startup made no model request: empty CLI events and identical native snapshots establish zero native token growth; its elapsed interval remains recorded. Preparation, formatter probes, outer orchestration, comparative grading, capture production and publication sit outside the subject accounting and are not free.

The frozen rates were rechecked against [official Standard pricing](https://developers.openai.com/api/docs/pricing) on 14 October 2026. Native request-level evidence permits a conditional mixed-tier estimate: input above 272,000 tokens uses the frozen long-context tier, with cached input treated as a subset. Single has 23 such requests, all during builder repair/revalidation (22 in phase3 and one in phase6), and none in initial implementation; adaptive has none. An all-short estimate for single is withheld. The mixed-tier estimate uses reported request-input counters as the pricing threshold basis; it is an API price equivalent, not a provider invoice, product subscription meter or proof of subscription savings. No unreported cache-write charge is invented.

The observed lower adaptive cost reflects less aggregate reported work in this pair and different context growth, despite an extra helper. It cannot establish that cheaper implementation owners save money: none was used. Context growth is a plausible contributor to single's repair expense; one pair cannot isolate it from the amount and nature of repair work or other runtime effects.

## Preserved instrument and report failures

The first auditor formatter used obsolete portal metadata. Later long acceptance text truncated, and generated authentication-secret filenames entered the source inventory. Those canonical results were refused; concrete reproductions remained supplemental, original-builder repairs continued and fresh complete independent audits followed. The original task and full acceptance documents remained unchanged. A short acceptance-hash identity and pre-read credential exclusions corrected the instruments. Earlier private snapshots containing generated runtime credentials are never published wholesale.

Adaptive's final full auditor initially marked an intentional server shutdown (exit130) as a passing test. The strict gate correctly refused that contradictory report. The same original independent auditor corrected its own report after confirming retained evidence, without changing app source or repeating the full audit. The original report, shutdown fact, failed pre-model configuration startup, resumed turn, counter snapshots and time gaps remain retained. The builder did not provide an audit verdict. [Recovery contract and independently gated amendment](REPORT_RECOVERY.md) document the narrow correction; it is not a waiver of app acceptance.

The legacy optional iteration parser also lacked a required field in single's issue records. [The postprocessing adapter](POSTPROCESSING.md) reports that optional classification as unparsed instead of converting it to zero; native token arithmetic remains unchanged and the separate independent iteration review supplies classification.

## Visual comparison

A fresh reviewer inspected all 32 anonymous final screenshots before seeing the condition mapping or any cost/model/timing information. Five equally weighted categories score hierarchy, typography/readability, consistency, desktop and mobile composition on 0–5 scales with half-point increments. [The complete review](visual-review.json) retains state-specific strengths and weaknesses; [capture provenance](capture-manifest.json) records dimensions, loaded-state/overflow observations and exact PNG hashes.

| Visual category | Single (anonymous B) | Adaptive (anonymous A) |
| --- | ---: | ---: |
| Hierarchy | 4.5 | 4.5 |
| Typography/readability | 4.5 | 4 |
| Consistency across states | 4.5 | 4.5 |
| Desktop composition | 4.5 | 4 |
| Mobile composition | 4.5 | 4 |
| **Total /25** | **22.5** | **21** |

The reviewer preferred single's mobile service/form layouts and desktop balance. Adaptive retained coherent styling, but several mobile rows were denser and its desktop draft editor was narrow. These qualitative preferences remain in the frozen result; the apps were not changed to improve the scores. A screenshot review does not verify keyboard operation, backend correctness, contrast ratios or comprehensive accessibility. No horizontal overflow was recorded in these normal-state captures. Console records include HTTP401 resource errors, without complete endpoint attribution; per-capture counts remain disclosed.

External capture setup needed a corrected npm path and in-memory role-cookie reuse after a real authentication rate limit rejected repeated logins. Final captures use fresh isolated sources/databases and production builds, and source hashes were rechecked after rendering. Those external tooling attempts did not alter measured app source or count as app correction cycles.

## Reproducibility and limits

[Protocol and hashes](protocol.json), [metric definitions](METRICS.md), [portable instruments](INSTRUMENTS.md), [source projections](source-manifests/) and per-request accounting are inspectable. Retained source bytes equal frozen inventories. Dependencies, databases, runtime signing secrets and benchmark-only handoff/routing reports are excluded by name before byte reads, with explicit exclusion manifests. App source was not altered to clean up its report or improve comparative screenshots. Explicit publication-only reference notes satisfy two immutable single-app README links to an excluded generated browser report; manifests hash those notes separately from measured source.

This is one exploratory pair with a single qualitative visual reviewer and differing implementation/test choices. Both conditions used Quality Code and had access to the same acceptance basis; the adaptive condition's optional team choice is the treatment. There is no causal superiority, production certification, comprehensive error-finding score, cheaper-model result or subscription-consumption conclusion.
