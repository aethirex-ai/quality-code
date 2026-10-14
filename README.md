<p align="center"><a href="https://www.aethdesign.com/"><img src="docs/assets/quality-code-banner.svg" alt="AethDesign Quality Standards: Quality Code, Quality Visuals and Quality Swarms" width="100%"></a></p>

<p align="center">
  <a href="https://github.com/aethirex-ai/quality-code/actions/workflows/verify.yml"><img alt="Verify toolkit" src="https://github.com/aethirex-ai/quality-code/actions/workflows/verify.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-222222"></a>
  <img alt="Python 3.11 or newer" src="https://img.shields.io/badge/python-3.11%2B-222222">
  <img alt="Standard version 3" src="https://img.shields.io/badge/standard-v3-222222">
  <a href="https://www.aethdesign.com/"><img alt="Built by AethDesign" src="https://img.shields.io/badge/by-AethDesign-C0C0C0"></a>
</p>

# AethDesign Quality Standards

Three composable standards for agent-assisted software work, published with the Quality Code bootstrap toolkit.

| Standard | Purpose | Instruction download |
| --- | --- | --- |
| **Quality Code by AethDesign** | Risk lanes, project context, behavioral verification and independent audits | [Code ZIP](docs/downloads/quality-code-by-aethdesign.zip) |
| **Quality Visuals by AethDesign** | Useful content, intentional composition, complete interfaces and a blocking independent visual gate | [Visuals ZIP](docs/downloads/quality-visuals-by-aethdesign.zip) |
| **Quality Swarms by AethDesign** | Native model selection, coherent task owners, bounded teams and shared context/usage budgets | [Swarms ZIP](docs/downloads/quality-swarms-by-aethdesign.zip) |

[Download all three without duplicates](docs/downloads/quality-standards-by-aethdesign.zip). Each ZIP contains one composed AGENTS.md, a manifest, instructions and the MIT license. These are **instruction-only packs**; clone this repository for the executable CLI and audit skill. Do not stack downloaded AGENTS files: choose the combined pack or compose your selection with the CLI. All selections include one shared foundation and preserve stricter existing requirements.

[Choose modules and understand installation](docs/MODULES.md) · [Read the case study](https://aethirex-ai.github.io/quality-code/) · [Visual baseline and audit](docs/QUALITY_VISUALS.md) · [Technical case study](docs/CASE_STUDY.md)

## The quality contract

| Change risk | Builder evidence | Independent audit |
| --- | --- | --- |
| **Low** · isolated copy or static presentation | One focused confirmation | Only when requested |
| **Normal** · contained, reversible behavior | Relevant regression tests and changed-scope checks | Only when requested or risk increases |
| **High** · public contracts, persistence, shared components | Focused tests and full verification | Required |
| **Critical** · security, payments, destructive operations | Full and release profiles, relevant failure and recovery evidence | Required |

This table describes Quality Code. Selected Quality Visuals additionally requires independent visual review for new frontends/pages and substantial redesigns; isolated low-risk copy/static-style changes retain the focused lane. The highest applicable risk wins. A passing command does not prove the product is correct. Missing required evidence stays visible.

## Quick start

Requires **Python 3.11+**, **Git**, and a POSIX shell for the `./quality` wrapper. The Python CLI has no third-party dependencies.

```sh
git clone https://github.com/aethirex-ai/quality-code.git
cd quality-code

# Bootstrap with all three standards (the default):
python3 scripts/quality_code.py init /path/to/new-project
# Or preserve and adopt an existing project:
python3 scripts/quality_code.py adopt /path/to/existing-project

# Or choose just the modules you need:
python3 scripts/quality_code.py adopt /path/to/another-project --modules code,visuals

cd /path/to/your-project
./quality validate
./quality context src/auth/session.py
./quality verify changed
```

**Before relying on the gate:** tailor `MAP.md`, `TESTING.md`, and `.quality/quality.toml` to the actual product. Detected profiles are starting points; `git diff --check` alone is not behavioral verification. Profile names do not guarantee different test coverage. Inspect every command before executing it, including detected package scripts.

For a higher-risk completed change:

```sh
./quality verify full
./quality audit-packet --criteria "Describe the observable outcome and failure behavior" > /tmp/quality-audit-packet.json
```

Give the packet, explicit diff scope, and this repository’s audit skill to a fresh agent. The packet is a handoff, not an audit or a passing verdict. Critical work also requires `./quality verify release` and any applicable platform evidence.

[Full installation and agent setup →](docs/GETTING_STARTED.md)

## What a project receives

| File | Purpose |
| --- | --- |
| `AGENTS.md` | Shared workflow and risk lanes |
| `CLAUDE.md` | Imports the shared project instructions |
| `MAP.md` | Compact boundaries, invariants, and context routing |
| `TESTING.md` | Product risks, evidence requirements, and known gaps |
| `.quality/quality.toml` | Verification commands and path-to-risk routes |
| `quality` + `.quality/quality.py` | Project-local verification and audit handoff CLI |
| `.quality/LICENSE` | Preserves the toolkit license notice in generated projects |
| `.quality/audit-result.schema.json` | Structured `PASS`, `FAIL`, or `BLOCKED` results |

Existing instruction text is merged. Existing map and testing sections are preserved. An unrelated `quality` executable or pre-existing runtime/schema/license under `.quality/` is a collision, not permission to overwrite it. A parent Git repository is reused.

## Quality Visuals

The [starting visual baseline](docs/QUALITY_VISUALS.md) rejects unjustified slogan eyebrows, arrows on every redirect, decorative numbering, half-empty containers and filler sections. It requires specific content, coherent desktop/mobile composition, usable states and accurate ownership/privacy information. Fresh independent visual review blocks completion on evidenced defects; missing review evidence stays BLOCKED. These rules require judgment and are not a complete design system or a claim to detect AI authorship.

## Quality Swarms

The selected Swarms module supplies provider-neutral subagent guidance. Agents use native runtime discovery and capability metadata to select accessible models and supported effort controls for each bounded task. No model names or fixed rankings are prescribed. Selection considers expected total usage, latency, retries, skill requirements, and product risk. Helper counts and spawn timing follow ready independent work, native capacity, shared resources, and coordination budget; unavailable discovery falls back to the current model.

Optional workstream hierarchies share one budget across all descendants. Every handoff uses the smallest sufficient context, with full-history inheritance avoided when supported; context-window settings are used only when the runtime exposes them.

The primary agent owns integration and validation. Implementation helpers cannot supply the required independent audit. See [the delegation policy](docs/DELEGATION.md) for the decision process, fallbacks, and examples.

## Why AethDesign publishes this

We want the way we build to be inspectable. This repository turns our coding-agent bootstrap into a reusable engineering practice: define the outcome, understand the boundary, test proportionately, and separate implementation from independent review when the risk demands it.

Visually coupled work keeps one persistent design owner with a small useful helper team. Substantial independent coding work may use bounded swarms; mixed apps preserve visual ownership and explicit API/state contracts. Model selection stays native and provider-neutral, and measured corrections remain part of the cost.

The [case study](docs/CASE_STUDY.md) explains the decisions and limitations. A [recorded delegation pilot](benchmarks/landing-pages-2026-10/RESULTS.md) adds measured time, coding-session tokens, image counts and anonymous design review, including the observed cost trade-off. The [new-client follow-up and isolated error-finding comparison](benchmarks/client-pilot-round2-2026-10/RESULTS.md) tests the revised delegation rules on different styles and explicit JavaScript contracts. The [richer two-client pilot](benchmarks/rich-client-pilot-2026-10/RESULTS.md) tests cheaper full-client implementation owners and tracks corrections: faster and lower coding-price equivalent in one pair, with lower visual scores and a remaining persistence defect. The [fullstack client portal pair](benchmarks/portal-pilot-2026-10/RESULTS.md) then compares frontend/backend contracts, remaining defects, cause-linked corrections, time and native coding tokens: one coherent backend helper, with continuous frontend ownership. The [brand-grounded completion follow-up](benchmarks/portal-completion-round2-2026-10/RESULTS.md) keeps audit/repair work inside the condition clock: both outcomes remained incomplete, complete costs are unknown, and the backend helper used the same model. The [uncapped ServiceFlow MVP comparison](benchmarks/serviceflow-mvp-2026-10/RESULTS.md) follows the same-prompt implementations through repairs and independent acceptance, retaining invalid reports and reporting calendar time separately from controller execution intervals. These are exploratory observations; they do not claim production defect reduction, certification, subscription savings, or universal agent compliance.

**AethDesign builds products, platforms, and websites.** Explore our work at [aethdesign.com](https://www.aethdesign.com/?utm_source=github&utm_medium=repository&utm_campaign=quality-code).

## Check the toolkit itself

```sh
./quality validate
./quality verify full
```

The tests use temporary projects and isolated home directories. CI runs the same full profile on Python 3.11–3.14 on Ubuntu and macOS. A configured workflow is not evidence of a successful hosted run; inspect the repository’s Actions results after publication.

## Contribute

Read [CONTRIBUTING.md](CONTRIBUTING.md), [the project map](MAP.md), and [TESTING.md](TESTING.md). Report vulnerabilities through [SECURITY.md](SECURITY.md). The tooling, documentation, and templates are available under the [MIT license](LICENSE).
