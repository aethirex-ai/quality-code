# AethDesign Atelier: paired app-building results

Adaptive ownership finished this one portal build **61.4% sooner**, with a **22.3% lower hypothetical coding API equivalent**. The single-agent frontend scored higher in anonymous screenshot review. Both outputs retain independently reproduced defects: neither passed the independent app gate or qualifies as a production client portal.

This is one exploratory matched pair, run adaptive first on a shared host. The common prompt builds a real Python/SQLite API and dependency-free browser interface: client/studio authentication, isolated projects, budgets, briefs, revision decisions, comments, immutable history and staff publication. Model choice, implementation and topology vary together; this experiment cannot isolate a causal delegation effect or establish subscription savings.

[Inspect the desktop/mobile gallery](../../docs/benchmarks/portal-pilot-2026-10/index.html), [structured results](results.json), [exact common prompt](APP_PROMPT.txt), [contracts](BRIEF.md) and [replay instructions](README.md).

| Measurement | Single agent | Adaptive ownership |
| --- | ---: | ---: |
| Native coding tree elapsed, including owned cleanup | 2,511.819s / 41m 52s | 968.399s / 16m 08s |
| Fixed backend contract groups | 12/12 | 12/12 |
| Original fixed frontend groups | 8/11 | 8/11 |
| Symmetric navigation-corrected frontend groups | 11/11 | 11/11 |
| Original fixed screenshot slots captured | 12/12 | 12/12 |
| Anonymous visual mean | 4.4/5 | 3.9/5 |
| Historical product causes corrected | 4 (3 observed, 1 source diagnosis) | 3 (2 observed, 1 source diagnosis) |
| Product cause-linked successful fix/recheck cycles | 4 | 3 |
| Successful correction/recheck episodes, all categories | 12 | 8 |
| Unsuccessful corrective attempts | 2 | 1 |
| Recorded builder checks / nonzero exits | 55 / 9 | 42 / 4 |
| Final independently reproduced distinct defects | 2 | 1 |
| Aggregate input tokens, including cached subset | 4,614,607 | 3,418,721 |
| Cached input tokens (subset, not added again) | 4,455,168 | 3,258,112 |
| Uncached input tokens | 159,439 | 160,609 |
| Output tokens, including reasoning subset | 90,904 | 65,402 |
| Reasoning output tokens (subset) | 32,163 | 11,965 |
| Hypothetical Standard API coding equivalent | $1.6734348 | $1.3010492 |
| Native build sessions | 1 root | 1 root + 1 direct backend helper |
| Image-generation calls | 0 | 0 |

## Actual delegation and cost

Both primary sessions used the same natively advertised `gpt-6.1-sol` model and high effort. Adaptive kept frontend/design/integration with one persistent primary and delegated backend plus its regression tests to **one fresh, scoped helper using that same model and effort**. It created no nested swarm and selected no cheaper implementation model. Capacity was a ceiling, not a target. The standard remains provider-neutral; these identifiers are dated trial observations.

The adaptive primary accounts for 2,807,446 input / 2,689,024 cached / 45,889 output tokens; its helper adds 611,275 input / 569,088 cached / 19,513 output. All reported descendant usage is included. Native CLI/root counters and explicit successful child creation reconcile without accounting flags; the [independent accounting review](evidence/usage-audit.json) verifies the components and seals. The helper was given fresh scoped context; max observed request input was 46,084 tokens versus 123,199 for its primary and 159,473 for the single root. Those are supplied request sizes, not configured context windows or proof of an optimal context policy.

At the [dated official pricing basis](https://developers.openai.com/api/docs/pricing), the observed model rates were $2/million uncached input, $0.10/million cached input and $10/million output. Cached input is subtracted from total input before pricing uncached input; reasoning is already included in output. Cache-write counters were zero.

| Coding cost component | Single | Adaptive |
| --- | ---: | ---: |
| Uncached input | $0.318878 | $0.321218 |
| Cached input | $0.4455168 | $0.3258112 |
| Output including reasoning | $0.90904 | $0.65402 |
| Total | $1.6734348 | $1.3010492 |

The $0.3723856 difference consists of $0.25502 less output and $0.1197056 less cached input, offset by $0.00234 more uncached input. Of 25,502 fewer output tokens, 20,198 are reasoning tokens; regular output drops from 58,741 to 53,437. This pair supports an observed benefit of scoped parallel ownership, but does **not** test the theory that cheaper implementation models caused the savings.

These are hypothetical API prices for native coding-session counters, not invoices. Setup, instrument repair, parent evaluation, independent audits, publication, other tool charges and the invalid attempt below are excluded. Excluded work is not free. Neither subscription percentages nor provider limit consumption were measured.

## Frontend evaluation and remaining defects

The original evaluator reports remain unchanged. It immediately inspected detail visibility after reload, then attempted overview-only project links; retained asynchronous detail routes produced false failures. The three single failures concern comment persistence, decision persistence and publication/history. Adaptive has two corresponding link timeouts plus a publication revision failure whose tab-readiness chronology is diagnosed below. A reload/detail-only amendment first produced single 11/11 and adaptive 10/11, retained separately. Instrumented chronology then showed the adaptive evaluator filling revision fields before the tab became selected; the pending render reset those premature values and no publication POST occurred. The final symmetric amendment waits for advertised selected-tab semantics as well as settled detail navigation. It produces 11/11 for both, preserves all behavioral assertions, and is tested with delayed healthy routes/tabs and negative controls. [Amendment evidence](navigation-amendment.json) and original/first/final reports remain separate; measured app bytes are never repaired after grading.

Independent real-browser journeys confirmed literal comment rendering/reload, blank request validation, successful approval/reload, staff publication preserving decision history and stale decision conflict with retained drafts and no extra activity. Those passing paths do not clear all error/race paths.

The [independent app audit](evidence/independent-app-audit.json) reports **FAIL** for both frozen apps:

- **Single — account-switch race:** a delayed conflict refresh from the former client can replace the new client's view with the former client's project while the new identity remains visible. This is a critical privacy defect in displayed client state, despite normal server isolation checks passing.
- **Single — malformed Unicode:** unpaired-surrogate text in login and mutation fields returns 500 instead of a bounded 400. Healthy Unicode succeeds and failed writes retain atomic rollback. Multiple affected fields share one validation cause.
- **Adaptive — saved mutation/failed refresh:** a comment POST succeeds, then a failed project refresh presents only a generic fetch failure and enables retry. The audit confirmed retry creates a second persisted comment. This is one distinct success/error-state cause, not two separate bugs.

Frozen experimental sources remain inspectable under [single](apps/single/README.md) and [adaptive](apps/adaptive/README.md). They should not be used with real client data. GitHub Pages serves screenshots and this report; no backend is deployed. We retain negative results rather than silently fixing measured outputs.

## Iterations are causes, not raw failures

The [independent correction reconciliation](iteration-review.json) separates product defects, visual refinements, tooling/QA errors, expected construction failures, duplicate manifestations and missing evidence. A cycle requires a corrective change and relevant recheck; repeated passing checks or native model turns are not new repair cycles. Several causes can share a patch/check batch.

Single fixed save-versus-refresh feedback, studio queue counting, authenticated error document title and default-port host compatibility; the last began as a source-only diagnosis. Adaptive fixed Unicode validation, mobile joined words and delayed account-response handling; the last began as a source-only diagnosis. Its six original Unicode assertion failures and native probe are one genuine product cause. A misplaced regression assertion was a separate QA error. Those historical fixes do not mean every related final path is correct.

Preview schema misuse, password-redacted excerpts and bounded excerpt misses are retained as tooling causes rather than product bugs. Builder-independent auth/state gates were explicitly unavailable within the timed runs. The parent independent gate then found the final issues above; no builder supplied its own independent verdict.

## Anonymous visual review

One fresh reviewer inspected all 24 original captures before receiving the randomized A/B mapping. A was adaptive and B single. Five equally weighted dimensions use 0–5 in half steps. [Complete anonymous review](blind-visual-review.json) and [released mapping](blind-visual-map.json) preserve evidence and limitations.

| Dimension | Single | Adaptive |
| --- | ---: | ---: |
| Visual identity / portfolio impression | 4.5 | 4.5 |
| Typography / hierarchy | 4.5 | 4.0 |
| Composition / coherence | 4.5 | 3.5 |
| Responsive usability | 4.0 | 3.5 |
| Forms / state clarity | 4.5 | 4.0 |

Both have strong studio identity. Single's selected content and forms have clearer mobile order; adaptive repeats large artwork before actionable content and has a displaced publishing sidebar in one capture. Captured skip-link overlays affect both. Their trigger and normal-use frequency are unproven; scores describe the supplied rendered states, not universal behavior or measured accessibility compliance.

## Isolation correction and provenance

The first intended single-agent attempt actually spawned a backend helper because modern native coordination remained enabled despite legacy disable settings. It was stopped after **419.351s**, retained and excluded **before any product grading**. Its root has no observed final completion, so authoritative complete tokens and price are withheld. Partial counters are retained in structured results and are not treated as zero or a complete invoice.

The completed adaptive output was carried forward byte-for-byte. A fresh control starts from the same original 18-file corpus/common prompt and explicitly disables both modern and legacy delegation capabilities. Native capability preflight found no delegation tools/calls; the completed valid root has zero successful spawns. Original/corrected protocols, original runner and the correction are retained. This is a condition-validity repair, not an outcome-selected retry.

[Output provenance](output-provenance.json) records identical frozen/published app and screenshot hashes. [Replay source provenance](replay-source-provenance.json) records portable host-path normalization separately from original native hashes. Native transcripts, private session identifiers, databases, cookies, runtime logs and unrelated work are not published. New opted-in trials require a new dated workspace, native discovery and seal; historical evidence is not overwritten.
