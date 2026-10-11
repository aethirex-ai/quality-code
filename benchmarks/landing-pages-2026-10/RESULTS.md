# AethDesign: one measured delegation pilot

**11 October 2026 · Quality Code v3 · One paired three-page workload**

The bounded swarm finished 41.3% sooner in this run. Its coding-session input rose 75.3%, output rose 43.0%, and its hypothetical Standard API coding subtotal rose 44.3%. Both portfolios passed the same 58 browser assertions. One anonymous reviewer preferred the single agent's visual result overall.

| Measure | Single agent | Bounded swarm |
| --- | ---: | ---: |
| Elapsed solver time | 15m 52s | 9m 19s |
| Input tokens (includes cached) | 1,654,596 | 2,901,229 |
| Cached input tokens (subset) | 1,530,624 | 2,686,592 |
| Output tokens (includes reasoning) | 31,776 | 45,431 |
| Coding Standard API equivalent | $0.7188 | $1.0374 |
| Frozen browser checks | 58 / 58 | 58 / 58 |
| Blind visual mean / 5 | 4.33 | 4.10 |
| Image generation attempts | 6 successful, 0 retries | 6 successful, 0 retries |

The workload was FORME, a fictional considered-living shop; KERN, a fictional Berlin joinery studio; and LUMA, a fictional restaurant. Each subject built all three from the same fixture under the same 20-minute wall-clock allowance. The root model was the same in both conditions. Time includes solver image generation, building and validation; setup, independent grading and measurement audit are excluded.

## Usage and routing

The single agent used the reported `gpt-6.1-sol` model with high effort. The swarm used that model/effort for its primary and two page leads, plus `gpt-6-luna` with medium effort for a restaurant-interaction helper. The primary built the shop and index; a craftsman helper built KERN; the restaurant lead built LUMA and delegated its JavaScript/tests to its own helper. Four agents participated, within the configured primary-plus-three-descendants ceiling. All three spawn calls used fresh task-scoped context (`fork_turns: none`). No smaller model context window was configured.

Model selection was made through the native catalog and supported runtime controls. These names record the experiment; they are not model rankings or hardcoded choices in the Quality Code policy. The native CLI was `0.162.0-alpha.17.2`; experimental model-catalog context was enabled for both conditions.

| Swarm reported model | Input | Cached subset | Output | Standard API coding equivalent |
| --- | ---: | ---: | ---: | ---: |
| gpt-6.1-sol | 2,539,893 | 2,356,096 | 42,645 | $1.02965360 |
| gpt-6-luna | 361,336 | 330,496 | 2,786 | $0.00778196 |

Cumulative session snapshots were deduplicated and every explicitly linked descendant was included. Each root's totals reconcile to its native CLI completion record. Input includes cached input; output includes reasoning. Reasoning output was 5,210 tokens for the single agent and 6,456 across the swarm, with no second charge. Cache writes were zero in both conditions.

The coding estimate uses the dated [OpenAI Standard pricing table](https://developers.openai.com/api/docs/pricing): per million tokens, `gpt-6.1-sol` ordinary input $2, cached input $0.10, output $10; `gpt-6-luna` ordinary input $0.10, cached input $0.01, output $0.50. All observed requests fit the short-context tier. For each model, the calculation is `(input − cached) × input rate + cached × cached rate + output × output rate`, divided by one million. Important totals were also recomputed independently from the selected counters and transcribed rates.

These figures are coding-session API equivalents. They exclude the image generator's own charges and other tool charges, are not actual invoices, and cannot measure subscription-limit consumption. Native service/cache behavior is not assumed to equal API billing behavior.

## Images

| Page | Single attempts / successes | Swarm attempts / successes |
| --- | ---: | ---: |
| Shop | 2 / 2 | 2 / 2 |
| Craftsman | 2 / 2 | 2 / 2 |
| Restaurant | 2 / 2 | 2 / 2 |

All twelve page generations succeeded without retries. Native-call counts reconcile to the attempt manifests and local outputs. The preliminary espresso-cup probe is excluded. The native image tool did not expose a precise backend model, generation tokens or a per-call price, so no specific image model or monetary image subtotal is claimed. Original images and display derivatives count as one generation, not separate calls.

## Quality

A fresh reviewer saw twelve anonymous desktop/mobile screenshots, without code, timing, usage, condition identity or builder conclusions. Each page received five 0–5 ratings for hierarchy, art direction, type/spacing, responsive composition and visible professional finish. The table reports an equal-weight mean of fifteen qualitative ratings per subject; this is one reviewer's judgment, not an objective quality scale.

| Page | Single reviewer total / 25 | Swarm reviewer total / 25 |
| --- | ---: | ---: |
| Shop | 21.5 | 20.0 |
| Craftsman | 21.5 | 19.5 |
| Restaurant | 22.0 | 22.0 |

The reviewer found both portfolios polished, with the control stronger in mobile pacing and form composition. The swarm's KERN detail photograph occupied an unusually long mobile section, and some paired mobile fields were cramped. The shop also illustrated a lamp chiefly with a vase. Those observations explain the reviewer's preference; they do not establish that delegation caused the differences.

Both subjects passed 58/58 identical browser checks at 375px and 1440px: metadata and landmarks, loaded local images, no horizontal overflow, fictional attribution, labeled forms, bag increments, valid demonstration confirmations, keyboard focus reaching a control, runtime/HTTP errors and external requests. This coverage does not establish complete accessibility compliance, production readiness, conversion performance or all viewport behavior.

Both solvers' browser validation was blocked by the same sandbox restrictions. They used static and offline interaction checks; a separate local Chromium evaluator graded the frozen outputs after both timed attempts. No post-run repairs were fed back into the measured sites.

## Interpretation and limits

This run supports a concrete trade-off: a shorter solver interval with a larger token footprint and coding API equivalent. It supplies no evidence of lower subscription-limit consumption or a quality gain from the hierarchy. Shared budgets and scoped contexts remain useful controls, but they do not guarantee savings.

The experiment has one workload pair, one visual reviewer, different generated imagery, uncontrolled provider cache warmth and shared-host/service load, and an alpha native CLI. External instrumentation ran during part of the control attempt and is excluded from its solver totals; its possible effect on shared load is unmeasured. Run order was single then swarm. These constraints prevent a causal or general advantage claim. A repeated, counterbalanced study including direct delegation would be needed to separate architecture effects from incidental solver choices and service variability.

## Inspect the evidence

- [Live fictional portfolios and screenshots](https://aethirex-ai.github.io/quality-code/benchmarks/landing-pages-2026-10/), [gallery source](../../docs/benchmarks/landing-pages-2026-10/index.html)
- [Frozen protocol](protocol.json), [complete sanitized measurements](results.json), [dated price snapshot](prices.json)
- [Anonymous review and evidence](visual-review.json), [unblinding map](blind-map.json)
- [Single telemetry](single-telemetry.json), [swarm telemetry](swarm-telemetry.json)
- [Single image accounting](single-images.json), [swarm image accounting](swarm-images.json)
- [Measurement method and replay instructions](README.md)

Raw native logs stay private. The published data includes counters, sanitized ancestry, source hashes and executable regression tests, without credentials or personal filesystem paths.
