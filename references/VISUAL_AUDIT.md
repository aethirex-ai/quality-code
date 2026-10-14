# Independent visual audit

Apply this protocol when Quality Visuals is selected, or when the user/project explicitly requires this review. Use the selected project baseline already supplied in AGENTS.md. Retrieve only missing relevant detail from the canonical [visual module](../assets/modules/visuals.md). Do not impose unselected optional modules or replace stricter project requirements.

## Scope and independence

New pages/frontends and substantial visual redesigns require a fresh independent visual reviewer. Low-risk isolated copy/static-style changes retain the focused builder lane unless a stricter requirement applies. A builder or material implementation director cannot issue the independent verdict. Confirm scope against the actual diff and acceptance criteria: absence of `--visual` does not waive a gate. Preserve code-risk verification separately.

Use the raw changed scope, intended audience/brand, acceptance criteria, applicable baseline, available rendered app and test instructions. Do not accept the builder's conclusions as evidence. User annotations are acceptance evidence; approved exceptions must be explicit and documented. Historical benchmark outputs and scores remain frozen.

## Evidence and checks

Inspect every changed screen at representative desktop and mobile sizes. Review full-page composition plus relevant close-up states, long/missing content and boundary widths. Exercise relevant links, navigation, keyboard focus, forms and loading/empty/error/success states. Screenshots establish appearance, not working controls. A build, DOM assertion or passing backend test cannot replace rendered visual and interaction evidence.

Evaluate these dimensions together:

- Content usefulness and specificity: real offer/task, meaningful distinctions, no redundant slogan eyebrows, reassurance, decorative numbering or filler sections.
- Composition: appropriate containers, purposeful whitespace, coherent hierarchy/type/imagery, content-proportionate cards and CTAs, meaningful icons/arrows, authored UI prose punctuation.
- Responsive and accessible operation: readable contrast/type, semantic labels, visible focus, keyboard/touch operation, sensible mobile order, no clipping or cramped controls.
- Product completeness: real destinations/actions, applicable states, realistic content, appropriate page titles/assets/not-found behavior and loading performance.
- Ownership and trust: accurate relevant ownership/contact/privacy information and working links, actual data/deployment context, no fabricated testimonials/business/legal facts. Missing owner-approved information required for public launch blocks that launch; never invent text to clear the gate.

These are a starting baseline. Deliberate brand choices, necessary category labels, actual ordered steps, meaningful cards and purposeful whitespace are valid. Identify an observable failure instead of declaring an aesthetic preference a defect. Conversely, a baseline violation does not become optional just because it concerns appearance or content.

## Verdict and correction

Use the audit skill's structured PASS/FAIL/BLOCKED result. Findings identify the requirement, affected screen, viewport/state, evidence, user impact and correction needed. Separate preferences and approved exceptions. Do not average scores to hide a blocking defect. The visual check is not comprehensive accessibility, security or legal certification.

Blocking findings must be fixed before completion, then re-rendered and rechecked in affected states. Obtain independent re-review of blocking findings and relevant integration regressions. Missing required render, interaction or independent-review evidence remains BLOCKED. Report unverified behavior plainly; do not infer a pass from a helper's completion or audit-packet generation.
