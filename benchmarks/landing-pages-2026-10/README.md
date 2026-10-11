# Landing-page pilot: single agent versus bounded swarm

This exploratory AethDesign workload compares two ways of building the same three fictional business landing pages: a considered-living shop, a local joinery studio, and a seasonal restaurant.

Both conditions start from the same frozen fixture, use the same primary model and reasoning setting, receive the same functional contracts, and have a 20-minute wall-clock allowance. Each page requires two original native image generations. The control performs all work in one model session; the swarm may delegate through native collaboration tools within a shared allowance of three active descendants plus the primary agent.

The measured unit is the complete three-page portfolio. Per-page image counts are reported separately. This is one paired workload, not a replicated experiment or evidence of general efficiency gains.

## Measurement boundaries

Elapsed time includes the solver's image generation, implementation, coordination and builder verification. Setup, capability probes, independent grading and measurement auditing are outside the solver interval and are excluded from its token subtotal. A timed-out or incomplete condition remains a recorded outcome; its pages are not repaired before grading.

Coding-session usage comes from native session telemetry for the primary and every identified descendant, including failed or unused branches. It includes the coding model's prompts, image inspection and tool interaction; it does not expose the image generator's own usage. Input tokens include cached input. Reasoning tokens are a subset of output in the observed telemetry and are reported without charging them twice. Repeated cumulative snapshots are deduplicated. Missing usage is flagged rather than treated as zero.

The native image tool returns an image and output path, but does not expose an exact model identity, generation tokens or a per-call price. Report image attempts, successful outputs and failures/retries by page and condition. The initial espresso-cup capability probe is excluded. Do not describe the image backend as a verified specific model.

Monetary figures, when available, are hypothetical Standard API equivalents of reported coding tokens using the dated [OpenAI pricing table](https://developers.openai.com/api/docs/pricing). They exclude image-generation charges, other tool charges and benchmark orchestration. They are not subscription consumption, invoices or total production cost. Cached tokens receive the cached rate; ordinary input receives the ordinary rate. Unverified cache-write semantics or an unpriced model block a complete estimate.

## Quality assessment

The same frozen browser evaluator checks document semantics, metadata, loaded local imagery, mobile and desktop overflow, runtime errors, visible fictional attribution, form labeling and the required demo interactions. Screenshots use 1440px desktop and 375px mobile widths.

A separate reviewer receives anonymous labels and the same screenshots for both subjects, without timing or token figures. Each page is scored from 0 to 5 for visual hierarchy, identity and art direction, typography and spacing, responsive composition, and professional credibility. Those scores are one reviewer's judgments, supported by concrete observations; they are not objective proof of design quality. Automated checks and visual review remain separate.

## Limits

The conditions produce different generated imagery. Run order, provider cache warmth, shared-host activity, service load and model nondeterminism can affect results. Native CLI behavior may differ from the desktop runtime. The tested concurrency cap limits the hierarchy that can actually form. Report the observed tree; a swarm label alone does not demonstrate that recursive delegation occurred.

The outcome can support a claim about this recorded run only. Repeated, counterbalanced trials across several workloads would be needed before making broader quality, speed or savings claims.


## Recorded result and local replay

Read [the measured result](RESULTS.md) and inspect [sanitized measurements](results.json). Native raw logs are deliberately omitted. Twenty-seven offline collector regressions can be rerun without provider calls:

```sh
python3 -B -m unittest discover -s benchmarks/landing-pages-2026-10 -p test_telemetry.py -v
```

A replay needs a compatible native Codex CLI with image generation and collaboration, the reported root model, Quality Code templates matching revision `eaace6377201317d648583f9d8ab1948437a3504`, Git, Node and Playwright/Chromium. It is not a provider-neutral benchmark runner. Native model/tool availability can change; unavailable features cannot be silently substituted while calling the run equivalent.

```sh
python3 benchmarks/landing-pages-2026-10/prepare.py \
  --work-dir /tmp/aethdesign-replay \
  --node /absolute/path/to/node \
  --playwright-import /absolute/path/to/playwright/index.mjs
cd /tmp/aethdesign-replay
python3 run.py single
python3 run.py swarm
BENCHMARK_PLAYWRIGHT_IMPORT=/absolute/path/to/playwright/index.mjs node evaluate.mjs single
BENCHMARK_PLAYWRIGHT_IMPORT=/absolute/path/to/playwright/index.mjs node evaluate.mjs swarm
python3 collect.py single --sessions-dir /absolute/path/to/benchmark/session-day
python3 collect.py swarm --sessions-dir /absolute/path/to/benchmark/session-day
```

The published fixture replaces machine-specific dependency hints with placeholders, which preparation fills. The published evaluator uses a configurable Playwright import and normalized file URLs; its assertions are unchanged. `protocol.json` retains the original pre-run evaluator and fixture hashes, while `publication-source-sha256.json` fingerprints the normalized published files. Replay preparation records its actual fixture hashes separately. Provider output is nondeterministic; exact images, code, time and tokens are not reproducible guarantees.

The runner preserves the original 20-minute timeout and configuration, uses the native ChatGPT login and does not contain an API key or a direct model API client. The price snapshot is dated 11 October 2026; replay estimates using it remain historical equivalents unless rates are explicitly reverified and updated. Browser grading may require a host context that permits local servers and Chromium startup.
