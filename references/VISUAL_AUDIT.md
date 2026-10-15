# Independent visual audit

Apply this protocol when Quality Visuals is selected, or when the user/project explicitly requires this review. Use the selected project baseline already supplied in AGENTS.md. Retrieve only missing relevant detail from the canonical [visual module](../assets/modules/visuals.md). Do not impose unselected optional modules or replace stricter project requirements.

## Scope and independence

New pages/frontends and substantial visual redesigns require a fresh independent visual reviewer. Low-risk isolated copy/static-style changes retain the focused builder lane unless a stricter requirement applies. A builder or material implementation director cannot issue the independent verdict. Confirm scope against the actual diff and acceptance criteria: absence of `--visual` does not waive a gate. Preserve code-risk verification separately.

Use the raw changed scope, intended audience/brand, acceptance criteria, applicable baseline, available rendered app and test instructions. Do not accept the builder's conclusions as evidence. User annotations are acceptance evidence; approved exceptions must be explicit and documented. Historical benchmark outputs and scores remain frozen.

## Evidence and checks

Inspect every changed screen at representative desktop and mobile sizes. Review full-page composition plus relevant close-up states, long/missing content and boundary widths. Exercise relevant links, navigation, keyboard focus, forms and loading/empty/error/success states. Screenshots establish appearance, not working controls. A build, DOM assertion or passing backend test cannot replace rendered visual and interaction evidence.

Evaluate these dimensions together:

- Content usefulness and specificity: real offer/task, meaningful distinctions and section-level questions/answers, no redundant slogan eyebrows, reassurance, decorative numbering or filler sections.
- Composition: clear focal hierarchy, alignment/grouping and full-page rhythm; coherent type/color/spacing roles, loaded fonts, readable line breaks/measure, appropriate containers and content-proportionate CTAs. Check imagery purpose, rights/accuracy, crop and legibility; meaningful icons/arrows and authored UI prose punctuation.
- Responsive and accessible operation: readable contrast/type including enlarged text, semantic labels, unobscured focus and dialog/error focus handling, keyboard/touch and gesture alternatives, sensible mobile order and layout-change widths, no clipping or cramped controls. Apply relevant web/platform criteria; do not invent universal dimensions.
- Product completeness: real destinations/actions and link behavior, relevant navigation state, autofill/paste and retained form values, applicable states with exercised recovery, realistic content, appropriate page titles/assets/not-found behavior and loading performance. Essential content remains available with reduced motion.
- Ownership and trust: accurate relevant ownership/contact/privacy information and working links, actual data/deployment context, no fabricated testimonials/business/legal facts. Missing owner-approved information required for public launch blocks that launch; never invent text to clear the gate.

Inspect the rendered focal hierarchy, alignment, rhythm, substance and mobile composition separately from mechanical compliance. Explain concrete strengths to preserve as well as defects; no fixed aesthetic score, image count or novelty quota establishes quality. Automated checks flag measurable risks and support inspection; they do not establish good design. Reuse unchanged passing evidence when its source/state coverage still applies; recheck fixes and relevant integration effects instead of repeating unrelated investigations.

These are a starting baseline. Deliberate brand choices, necessary category labels, actual ordered steps, meaningful cards and purposeful whitespace are valid. Identify an observable failure instead of declaring an aesthetic preference a defect. Conversely, a baseline violation does not become optional just because it concerns appearance or content.

## Full-remake comparison

When the request is a full remake or rethink, inspect the original request and original/final renders at matching representative widths. The builder's reduced checklist cannot narrow that intent. Read the short design basis as a claim to test against product facts and the actual output, not as an approved design or independent evidence.

Record these decisions in the audit evidence:

- Which important information, actions and relationships shape the new hierarchy? Identify what was removed, merged, reordered, replaced or deliberately retained and whether that serves the actual audience/task.
- Does the difference go beyond palette, type, imagery, rounded containers and rewritten slogans? Reused useful structures are valid when supported by the content; cosmetic changes alone do not establish a full remake. Do not require every screen or usable interaction to change gratuitously.
- Inspect both close-ups and the entire page for cumulative generic patterns. Inventory the actual retained eyebrows/slogans, decorative arrows/icons, numbered panels, cards and emphasis treatments, with screen/location examples and their function. Check the heading and supporting text together for repeated information. Do not excuse ornament solely as branding, consistency, navigation or an aesthetic preference; identify its contribution in context. A blanket phrase ban or zero-count target is not a design review.
- Test prominent copy for specificity: if it fits unrelated businesses unchanged, does nearby concrete information make it useful, or is it substituting for the offer/task? Check decorative imagery and controls with the same standard. Do not invent business facts or demand unsupported claims to make copy distinctive.
- Give separate conclusions for functional/product completeness, baseline content/composition and full-remake intent. No need to change the result schema: put this evidence in the existing checks/findings. A passing build, attractive photograph, improved average impression or fewer markers cannot substitute for an unmet dimension. Owner ratings are attributed feedback, not independent scores or gate evidence.

Identify concrete unmet requirements and their effect, rather than failing a familiar pattern because it is common. Missing required before/after renders or interaction evidence is BLOCKED; an evidenced cosmetic-only remake or unjustified repeated filler is FAIL. Review the whole affected scope initially. On re-review, verify fixes and their impact on full-page composition and relevant integrations; matching the reported lines alone is insufficient. Preserve prior verdicts and historical benchmark scores when requirements or owner feedback change.

## Verdict and correction

Use the audit skill's structured PASS/FAIL/BLOCKED result. Findings identify the requirement, affected screen, viewport/state, evidence, user impact and correction needed. Separate preferences and approved exceptions. Do not average scores to hide a blocking defect. The visual check is not comprehensive accessibility, security or legal certification.

Blocking findings must be fixed before completion, then re-rendered and rechecked in affected states. Obtain independent re-review of blocking findings and relevant integration regressions. Missing required render, interaction or independent-review evidence remains BLOCKED. Report unverified behavior plainly; do not infer a pass from a helper's completion or audit-packet generation.
