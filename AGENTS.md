<!-- quality-code:start -->
## Quality-code workflow

For any change affecting code, configuration, dependencies, tests, builds, data, releases, or agent behavior:

1. Read only the `MAP.md` sections relevant to touched files.
2. State observable acceptance criteria before implementation.
3. Replace bootstrap gaps in `MAP.md` and `TESTING.md`; ensure `.quality/quality.toml` profiles run the project's real tests and checks. `git diff --check` alone is not behavioral evidence.
4. Classify the highest actual product risk. An explicit higher-risk route in `.quality/quality.toml` cannot be downgraded. A routine local build, install, or version bump used only to deliver or confirm a change inherits the underlying change's risk.
5. **Low — builder only:** isolated copy, label, display text, comments, formatting, or static style with no behavior, data, accessibility, localization-contract, legal, billing, security, build, release, or agent-instruction effect. Make the smallest change and perform one focused visual, static, or targeted confirmation. Do not run the full suite, generate an audit packet, or start a subagent unless the user explicitly requests it or evidence raises the risk.
6. **Normal — contained behavior:** use proportionate test/fix loops, add or update the smallest relevant regression test, and run the smallest changed-scope verification that covers the behavior. Do not request an independent audit by default; do so only when the user asks or unresolved uncertainty raises the risk to high.
7. **High or critical — independent gate:** run the required higher verification profiles, generate `./quality audit-packet --criteria "<criteria>"`, and start a fresh agent with the audit skill (`$audit-code-change` in Codex or `/audit-code-change` in Claude Code). Once started, the audit remains exhaustive within scope.
8. Builder validation is mandatory in every lane. For a concrete bug, field-test the original or smallest failing case only as needed to understand it, then once to confirm the fix. Add more cases only when requested or justified by risk, an unclear cause, or inconsistent results.
9. Resolve blocking audit findings and request re-audit when an independent audit was required. Otherwise hand off after the lane's evidence passes, with residual risk stated when material.

For review, diagnosis, or planning, inspect and report without implementing. Ask before destructive actions, external writes, releases, purchases, or material scope expansion.
<!-- quality-code:end -->
