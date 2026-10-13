# Client workspace completion pilot — no accepted winner

The next matched prompt used [AethDesign’s real website](https://www.aethdesign.com/) as its software-development and UI/UX studio reference. Both subjects started from the same blank corpus. Single-agent implementation disabled both native delegation toolsets; adaptive implementation could choose a small team or bounded swarm while keeping a persistent visual owner.

**Both outputs are INCOMPLETE. Neither passed a final independent application gate.** This is a capped exploratory trial, not evidence of a quality, speed, complete-cost or subscription-usage advantage. [Structured results](results.json), [usage reconciliation](usage-diagnostic.json), [independent correction review](iteration-review.json) and [anonymous visual review](blind-visual-review.json) preserve the evidence.

## What actually happened

| Observation | Single | Adaptive |
| --- | --- | --- |
| Initial build | Timed out, 2,402.014 measured seconds | Completed, 980.854 measured seconds |
| Independent application review | Not reached | First canonical FAIL; second review timed out without a canonical verdict |
| Builder repair after review | Not reached | Same builder resumed; 377.347 seconds |
| Runner monotonic duration | 2,405.091 seconds | 3,547.664 seconds |
| Calendar duration | 5,012.116 seconds | 3,547.669 seconds |
| Accepted completion time | Unknown / not accepted | Unknown / not accepted |
| Final post-clock backend sample | 12/12 | 12/12 |
| Final post-clock browser sample | 10/11; missing stylesheet | 10/11; previous decision history not visible |
| Supplemental recovery | Raw 3/3; 2 clean, 1 transport-ambiguous | 3/3 clean in retained report |
| Final captured source files | 30 | 39 |

The single stream reported an idle-timeout reconnect during construction, with no observed later recovery or completed turn. Its stylesheet was never retained. The large calendar/monotonic discrepancy is preserved; neither clock isolates active computation. A clean speed comparison is unavailable.

The adaptive subject used one direct backend owner and no hierarchy. Primary and reviewers used **gpt-6.1-sol/high**; the backend child explicitly used **gpt-6.1-sol/medium**, in a fresh scoped context. Cheaper models and scoped model selection were available. The builder judged authentication and transaction work to require the workhorse; that is its judgment, not proof that cheaper models were unqualified. **Cheap-model output routing was not exercised.** Medium effort does not change the model’s API unit price.

The child’s maximum observed request input was 38,292 tokens, versus 163,866 for the persistent builder. These are supplied-input observations, not configured context-window capacities or a causal efficiency comparison.

## Bugs and iterations

The [first canonical audit](audits/adaptive-02.json) reproduced one response-snapshot concurrency cause in two endpoints: a decision or publication committed, then reread state changed by a later transaction. The repair captured each response inside the write transaction and passed deterministic interleaving regressions. A separate repair corrected acknowledged activity display. The authorized project switcher was a checker-driven accommodation to an overview assumption; it is not evidence of lost stored data.

The independent trace review records **five adaptive product correction cycles**: three during construction and two during repair. It separates one visual refinement, two tooling correction cycles and one navigation accommodation. Assertions, model turns and repeated viewport failures are not additional bugs. No completed product fix/recheck cycle is evidenced in the interrupted valid control; that does not prove zero bugs.

The second auditor independently observed three remaining cause clusters before its 20-minute stage cap:

- Review history/feedback delivery: stored decisions remain intact, but previous outcomes and the client’s note are not usefully delivered in the revision/product views. No exact undocumented JSON key is presumed mandatory.
- Save acknowledgment across navigation: leaving and returning before a pending write finishes can skip the data reconciliation/recovery after acknowledging it.
- Legal long-title rendering: a valid 120-character title expanded document width to 2,522 pixels at a 375-pixel viewport, and 2,650 at 1440.

These have concrete reproduction/source evidence in [the independent review](iteration-review.json). The incomplete reviewer did **not** submit a canonical FAIL or PASS. No further repair occurred. There is no comparable independent control audit or complete defect oracle, so this does not measure bug-finding recall or prove one topology safer.

## Where the reported cost comes from

[Official dated Standard API prices](https://developers.openai.com/api/docs/pricing) provide a conditional equivalent, not an account invoice. Every observed actor used the same model: $2/million ordinary input, $0.10/million cached input and $10/million output for the reported short-context calls. Reported cache writes were zero. Reasoning is already included in output.

| Reported subset | Single | Adaptive |
| --- | ---: | ---: |
| Input | 202,804 | 14,130,067 |
| Cached input, included above | 155,136 | 13,487,616 |
| Output | 19,763 | 132,652 |
| Reasoning output, included above | 1,084 | 42,142 |
| Conditional proxy for these observations only | $0.3084796 | $3.9601836 |
| Complete consumption / complete cost | Unknown | Unknown |

**Do not compare these prices as complete run costs.** Canceled/in-flight/retried unreported consumption is unknown, never zero. The collector’s empty control observations and omitted stopped-auditor observations are selection artifacts; the independent reconciliation restores known partial counters while correctly withholding authoritative totals.

Adaptive’s known subset partitions as follows:

| Owned role | Conditional proxy | Share of known subset |
| --- | ---: | ---: |
| Persistent builder, initial + repair counted once | $1.5196724 | 38.37% |
| Backend child | $0.2917596 | 7.37% |
| First independent auditor | $0.9280744 | 23.44% |
| Second independent auditor, partial | $1.2206772 | 30.82% |

Auditors account for **54.26%** of the known proxy. Across all roles, ordinary input contributes $1.284902, cached input $1.3487616 and output $1.32652. Caching reduces unit cost, but its large volume remains material. Even a zero-cost backend helper would remove only its observed 7.37% share before any changed review/retry behavior. The test did not shift most output to a cheaper model, so it cannot validate that hypothesis.

## Visual evidence

A fresh anonymous reviewer inspected all **24 required and 8 additional** settled viewport captures, plus the same frozen studio references. After review, label A mapped to single and B to adaptive. The adaptive artifact received 4/5 presentation, typography and layout, and 5/5 coherence and studio fit. The control received 1/5 presentation because it is unstyled and unfinished. These are captured-artifact judgments, not evidence that delegation improves design. Normal seed-state screenshots do not test long-title overflow or prove backend correctness. Historical full-page scores are not comparable.

## Method and preparation limits

Each condition had one 90-minute total allowance, initial-build cap 40 minutes, audit-stage cap 20, repair-stage cap 15 and at most four audit rounds. Builder descendants, fixed checks, fresh reviewers, repairs and cleanup belong inside the condition clock. **The hard stage caps stopped work while global time remained:** the control never reached its reserved gate work; adaptive’s second report could not finish. Both remained incomplete rather than falsely accepted. The next protocol should distinguish soft stage planning from the global hard deadline and validate transport/cap behavior before another paid pair; no such change or outcome-selected rerun is applied to these records.

A preceding instrument-invalid single build completed, then its audit request was rejected because the matched model required an explicitly typed formatter field. A cheaper schema capability probe had accepted it. All 285 attempt files and original instruments were retained; both subjects restarted from the same blank corpus after matched-model preflight and a fresh independent instrument gate. Its reported completed-builder proxy **$1.2726912** is preparation, excluded from comparison. Rejected audit consumption and complete preparation cost remain unknown.

Shared brand capture, instrumentation, capability/preflight work, final read-only diagnostics, visual grading and publication are outside measured condition spend, not free. No subscription percentages were read. No image-generation calls occurred in this code-native portal pair. Public sources preserve native hashes; brand-capture runtime paths and report-private locations are adapted. The replay runner also fixes a post-trial Darwin zero-grace reaping race; [the exact measured runner](runner-native.py) remains preserved and no measured outcome changed. These are fictional local prototypes; GitHub Pages serves screenshots, not their Python backend.
