# What the first pilot actually revealed

The first workload's token increase is fully accounted for: descendants added 1,488,749 input tokens, while the primary used 242,116 fewer, leaving a net increase of 1,246,633. Of that increase, 1,155,968 was cached input; cached input is a subset of input, not another charge on top. Recorded usage snapshots increased from 31 to 76, and outer tool calls from 30 to 71. This is aggregate native solver usage, not subscription-limit consumption.

| Recorded session | Input | Cached subset | Uncached input | Output | Usage snapshots |
| --- | ---: | ---: | ---: | ---: | ---: |
| Single primary | 1,654,596 | 1,530,624 | 123,972 | 31,776 | 31 |
| Swarm primary | 1,412,480 | 1,350,528 | 61,952 | 18,128 | 31 |
| Restaurant lead | 487,027 | 418,176 | 68,851 | 10,784 | 15 |
| Craftsman owner | 640,386 | 587,392 | 52,994 | 13,733 | 17 |
| Nested interaction helper | 361,336 | 330,496 | 30,840 | 2,786 | 13 |

Every spawn requested fresh task context. That did not eliminate fixed runtime context: children received the project/global instructions, skills catalog and sometimes model-switch guidance. Several re-read entire project instructions and briefs. The nested helper repeated inventories and communicated/waited; its checks were subsequently rerun by its lead and the primary. Some integration checking was appropriate; the recorded overlap shows an opportunity to tighten ownership, not proof that every repeated check was unnecessary.

The small helper's input footprint was substantial, but its API-equivalent cost was only $0.00778196. It was not the main monetary cost driver. Applying the primary model's rates as an accounting reference, the total $0.31866916 coding increase decomposes into $0.18133 additional uncached input, $0.1155968 additional cached input, $0.13655 additional output, and a −$0.11480764 routing offset for the cheaper helper. This is a bookkeeping identity, not a causal savings estimate for removing that helper. [Independent arithmetic](pilot-accounting-decomposition.json) uses Decimal calculations and the dated [official Standard rates](https://developers.openai.com/api/docs/pricing).

Both primaries printed full native media results through textual output, which included base64. The tool truncated it: reported pre-truncation output sizes are not retained request-token counts. Both portfolios included six native image-inspection blocks. Avoiding full media-result dumps is sensible output hygiene; the logs do not support assigning all extra usage to base64. Authored spawn briefs are encrypted at rest, so their exact plaintext size/content cannot be independently assessed.

The single reviewer’s lower swarm score came from visible product issues: an unusually tall blurred drawer crop on mobile, cramped paired form fields, and a vase dominating a lamp listing. Restaurant totals tied. Passing functional assertions did not catch these visual weaknesses. Different generated images, one reviewer and one workload pair prevent a claim that delegation or a particular model caused the difference.

## Revised rules to test

The standard now favors complete coherent direct owners, with useful primary work and the smallest justified team. Hierarchy remains available for substantial independent work; it is not a required shape. Helpers use narrow references and concise result formats, bound tool output, avoid dumping media results and do not re-read already supplied policy without a concrete need. The primary checks integration and final product quality without repeating every helper investigation. Native-supported model/effort selection, safety, risk lanes and independent gates remain intact.

Global defaults now route to the complete project policy with a compact safe fallback instead of loading a second full delegation policy. This reduces duplicated supplied instructions; it does not configure a smaller model context window or remove runtime overhead. Visual acceptance explicitly includes content/imagery fit, mobile composition, readable contrast and form ergonomics. Diagnosis requires concrete reproductions, negative/boundary cases and healthy controls rather than a large finding count.

The new experiment compares the revised adaptive approach with a single agent on **new** client types and styles. Policy, briefs and imagery differ from the first pilot, so cross-pilot changes cannot isolate the policy's effect. The within-workload paired comparison is the meaningful new observation; repeated counterbalanced trials and a same-task topology ablation would be stronger evidence.

Inspect the [sanitized raw diagnosis](pilot-diagnosis.json) and [first pilot evidence](../landing-pages-2026-10/RESULTS.md).
