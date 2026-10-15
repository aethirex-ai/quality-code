# Visual baseline research

Reviewed 2026-10-15. Repositories were read as source material; no third-party skills were installed or scripts executed. Suggestions are paraphrased, not copied implementations. Repository claims about their own studies or effectiveness were not independently reproduced.

| Inspected source | Adopt or adapt | Exclude from universal policy |
| --- | --- | --- |
| [Taste Skill, f624f37](https://github.com/Leonxlnx/taste-skill/blob/f624f37a8c650b9cc550253104925efe4c8de246/skills/taste-skill/SKILL.md), [render critique](https://github.com/Leonxlnx/taste-skill/blob/f624f37a8c650b9cc550253104925efe4c8de246/skills/taste-skill/references/critique.md), [inspector rules](https://github.com/Leonxlnx/taste-skill/blob/f624f37a8c650b9cc550253104925efe4c8de246/skills/taste-skill/scripts/lib/rules.mjs) | Product-grounded direction, content before containers, rendered hierarchy/rhythm/substance review | Random direction selection, mandatory images/motion, font/color bans, fixed line counts and critique-round caps |
| [Vercel agent skill, 063bee9](https://github.com/vercel-labs/agent-skills/blob/063bee94c3f4df8453406c830b0a7df0f2860278/skills/web-design-guidelines/SKILL.md) | Actionable source-located findings | Treating a code-only review as rendered acceptance |
| [Vercel web guidelines, 434b7f9](https://github.com/vercel-labs/web-interface-guidelines/blob/434b7f91364665f2f733b310ec54809bf8f37937/command.md) | Focus, form retention, paste/autofill, recovery, relevant navigation state and image loading | Universal list-size/performance quotas, URL synchronization of ephemeral/private state, hiding overflow as a fix, mandatory typography conventions |
| [SudewaJay Apple skill, 57bfab7](https://github.com/SudewaJay/apple-design-skill/blob/57bfab7daf8766a9a45cfc405790e749c71eda30/apple-design/SKILL.md), [patterns](https://github.com/SudewaJay/apple-design-skill/blob/57bfab7daf8766a9a45cfc405790e749c71eda30/apple-design/references/hig-patterns.md) | Content hierarchy and contextual feedback/recovery | Apple marketing templates, required glass/capsules, fixed empty-state layouts and Apple dimensions for every website |
| [dickwu Apple skill, 904b0ee](https://github.com/dickwu/apple-design-skill/blob/904b0eedc7cc778152f545506075d5bb5219ce77/SKILL.md), [reference updater](https://github.com/dickwu/apple-design-skill/blob/904b0eedc7cc778152f545506075d5bb5219ce77/scripts/pull-hig.mjs) | Separate usability from craft judgments, flow review, concrete trade-offs and strengths worth preserving | Wholesale redistribution of bundled Apple text or automatic platform-convention transfer |

Taste, Vercel web and SudewaJay carry MIT licenses; Vercel agent-skills identifies MIT in its README. The inspected dickwu repository has no standalone explicit reuse license; its README attributes guideline text to Apple. No source code or substantial text is incorporated from these repositories.

Official [Apple accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility), [materials](https://developer.apple.com/design/human-interface-guidelines/materials) and [motion](https://developer.apple.com/design/human-interface-guidelines/motion) were checked directly. Apple describes Liquid Glass as a platform functional layer, purposeful optional motion and enlarged text support; these do not make Apple styling a universal web rule. Apply relevant [WCAG contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html), [text resizing](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html) and [target-size criteria including exceptions](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html) to web requirements.

## Acceptance examples

- Design basis: identify a verified product fact shaping actual hierarchy, content or artwork; a quiet utility can pass without a signature gimmick.
- Content structure: identify the useful question/answer/action of each section; familiar sections may pass when justified.
- Type and imagery: inspect loaded fonts, readable line breaks, enlarged text, crops/focal points and asset provenance at supported sizes. Typography-only pages can pass.
- Operation: keyboard through navigation/forms/dialogs, confirm unobscured/restored focus, retain meaningful entered values after recoverable errors and exercise recovery. Do not require forms or dialogs where none belong.
- Composition: inspect full-page hierarchy, grouping, rhythm and substance separately from mechanical compliance. Common fonts, legitimate gradients/cards and intentional whitespace do not fail merely by existing.

No automated aesthetic detector was added. Existing delivery tests check composition and packaging, not agent compliance or design quality. Subject matter, brand expression, supported devices and performance budgets remain product-specific judgments. No improvement in outcomes is claimed without experimental evidence.
