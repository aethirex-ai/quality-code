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

For new/substantial frontend work, inspect the pre-implementation design basis and early desktop/mobile composition observation. Test the proposed direction and credible alternative against product facts and the rendered hierarchy; a retrospective justification or obviously unsuitable alternative is insufficient. Inspect concept/product fit, focal hierarchy, alignment, rhythm, substance and mobile composition separately from functional correctness and mechanical compliance. Explain concrete strengths to preserve as well as defects; no fixed aesthetic score, image count or novelty quota establishes quality. Automated checks flag measurable risks and support inspection; they do not establish good design. Reuse unchanged passing evidence when its source, viewport/state and integration coverage still apply. Batch related checks and use raw evidence paths with concise results; recheck fixes and relevant integration effects instead of repeating unrelated investigations or regenerating unchanged packets.

These are a starting baseline. Deliberate brand choices, necessary category labels, actual ordered steps, meaningful cards and purposeful whitespace are valid. Identify an observable failure instead of declaring an aesthetic preference a defect. Conversely, a baseline violation does not become optional just because it concerns appearance or content.

## Composition review and remake comparison

For every new/substantially redesigned frontend, inspect both close-ups and the entire page for cumulative generic patterns. Inventory retained eyebrows/slogans, ornamental arrows/icons, numbered panels, cards and emphasis treatments with screen/location examples and their specific function. Check heading/supporting text pairs for repetition. Branding, consistency, navigation or polish alone do not justify ornament; a blanket phrase ban or zero-count target does not establish quality. Test prominent copy and imagery for product specificity without demanding fabricated facts. Familiar structures, meaningful cards, actual sequences and purposeful expression can be justified.

Give separate conclusions for functional/product completeness and concept/content/composition. Scores, if requested, keep those dimensions distinct and cannot replace findings or gate evidence. Explain strengths to preserve. Owner ratings remain attributed feedback, not independent scores.

Inspect the shared-canvas hierarchy and representative container/control patterns: unboxed text/image entries, actions and integrated fields must be considered before default boxes. Judge the need for a box or changed background separately from the function of its contents; "selectable object", "clickable action" and "creates separation" are insufficient alone. Check that retained surfaces support a specific task/state, legibility or product-specific narrative and preserve whole-page coherence. Changing a rectangle to a pill, circle or rounded panel alone does not resolve unnecessary containment. Preserve recognizable controls, labels, input/error boundaries, focus and targets. Review reused patterns together; do not demand a written alternative or extra counterfactual render for every instance, or impose a blanket ban on useful cards, control boundaries or contrasting surfaces.

For a full remake, additionally inspect the original request and original/final renders at matching widths. The builder's reduced checklist cannot narrow that intent. Identify which information/actions shaped the hierarchy and what was removed, merged, reordered, replaced or deliberately retained. Check that the result goes beyond palette, type, imagery, rounded containers and rewritten slogans, allowing justified retained structures and interactions. Record a separate remake-intent conclusion. Missing required before/after evidence is BLOCKED; an evidenced cosmetic-only remake is FAIL.

Review the whole affected scope initially. On re-review, verify fixes and their impact on full-page composition and relevant integrations; matching the reported lines alone is insufficient. Preserve prior verdicts and historical benchmark scores when requirements or owner feedback change.

## Verdict and correction

Use the audit skill's structured PASS/FAIL/BLOCKED result. Classify every observed weakness as a baseline violation requiring correction, a justified treatment with its specific contribution, an optional preference, or missing required evidence marked BLOCKED. Do not bury a known violation in a score or weakness paragraph. Findings identify the requirement, affected screen, viewport/state, evidence, user impact and correction needed. Keep approved exceptions explicit. Do not average scores to hide a blocking defect. The visual check is not comprehensive accessibility, security or legal certification.

Blocking findings must be fixed before completion, then re-rendered and rechecked in affected states. Obtain independent re-review of blocking findings and relevant integration regressions. Missing required render, interaction or independent-review evidence remains BLOCKED. Report unverified behavior plainly; do not infer a pass from a helper's completion or audit-packet generation.
