# Quality Code testing profile

## Test objectives

Verify new and upgraded projects receive provider-neutral delegation instructions without losing custom context. Migration from standard v2 must preserve configured verification commands and update the local engine and version together. Installer tests also cover fresh and stale global swarm/context policy delivery, surrounding user instruction preservation, repeated installation, and malformed-marker rejection before global writes. Instruction delivery is tested; actual model choices, compliance, and efficiency require evidence from the host runtime.

Prove the CLI can bootstrap a usable project, preserve existing content during adoption, refuse wrapper collisions, route actual configured paths, produce scoped audit packets, and surface verification failures. Confirm installation in an isolated home directory and restrict skill distribution to intended files.

## Product risks

| Risk | Level | Evidence |
| --- | --- | --- |
| Bootstrap or upgrade overwrites content | High | Temporary-project preservation and runtime/schema/license collision tests |
| Risk route hides a higher-risk area | High | Mixed-path fallback and parent-Git scope regression tests |
| Failed verification looks successful | High | Failing executable and unknown-profile tests |
| Installer ships private local state | High | Allowlist distribution and retained license tests |
| CI cannot run the advertised checks | Critical | Local equivalent; hosted matrix after publication |

## Test levels

Stdlib `unittest` integration tests invoke real CLI processes with temporary directories. Pure merge/routing tests assert public invariants. Repository checks assert generated engine/schema parity and local documentation links.

## Test data and environment

Offline by default. Python 3.11+ and Git required. Fixtures contain synthetic project text and a frozen, reviewed v2 bootstrap distribution from commit `1b421119e98bf7e13e0e94d3f976236f0046c37c`; installer uses an isolated home. No credentials, customer data, live providers, or production environments. Unit tests must not mutate the repository.

## Non-functional coverage

Preservation and fail-visible verification are covered. Ubuntu and macOS CI is configured; only the local platform is validated before publication. Performance, Windows wrappers, adversarial filesystem/symlink behavior, and concurrent writers are not characterized.

## Manual and release evidence

Review banner rendering, README readability, initial source inventory, secret filename/value-pattern scan, and large-file inventory before the first commit. A passing configured workflow is not implied until hosted Actions runs.

Reader edition: check `docs/index.html` at desktop and 375px mobile widths. Confirm embedded fonts, visible keyboard focus, local section links and no horizontal overflow. Preserve technical caveats; there is no JavaScript or external font request. Markdown remains a source-readable alternative because GitHub strips custom CSS.

## Delegation pilot evidence

Twenty-seven offline telemetry regressions validate cumulative deduplication, explicit ancestry, model attribution, overlapping cached/reasoning counters, incomplete evidence, conditional price refusal and image-call ambiguity. Full/release profiles include them. The recorded pilot reconciles native root completion usage, all descendant rollouts, native image calls and manifests; an independent manual arithmetic path verifies pricing. A frozen two-width browser evaluator produces screenshots and functional assertions, followed by one anonymous visual reviewer. Recorded outputs remain unchanged before grading. Local dependency paths are normalized only in published replay sources, with both original and published hashes retained.

One workload pair, different imagery, cache/service/shared-host variation, an alpha CLI, one qualitative reviewer and missing image billing limit interpretation. Image/subscription cost is not measured. Public claims and sanitized source inventory require fresh independent review before publication.

## Round-two evidence

Freeze equal new-client fixtures and evaluator before each native attempt; preserve timed outputs before independent grading. Run one paired hotel/studio/landscape design workload and one separate paired JavaScript contract-defect review. Validate hidden evaluator baseline, corrected oracle, healthy controls and single-fix isolation before execution. Independently match concrete findings to baseline causes, distinguishing detection, executable repairs, duplicates, false positives and legitimate additional defects. Replay preparation and missing evidence receive offline regressions. Publish sanitized provenance and counters, never native logs or personal paths. Browser/visual grading follows both timed conditions. Cross-pilot changes in both brief and policy prevent causal attribution to the revised rules.

## Known gaps and residual risk

The installer is not transactional. It refreshes managed skill copies and writes home settings before a potential launcher collision. Path routing and agent instructions require project-specific judgment. The tool does not enforce merge protection or validate a final auditor verdict. Documentation does not claim certification or measured outcome improvement.

## Independent audit gate

Scripts, templates, schemas, and agent policy require a fresh read-only audit after full verification. CI changes also require release verification. See `SKILL.md` and `references/AUDIT_PROTOCOL.md`.

## Maintenance rules

Behavioral fixes need focused regression tests. Do not retry flaky checks until green. Keep `.quality/quality.py` synchronized with `scripts/quality_code.py` and the project-local schema synchronized with its template.

## Rich-client pilot instrumentation

The rich-client folder adds offline telemetry, immutable-evidence/accounting, runner cleanup and QA-history regression tests plus bounded preview bridge tests. Browser-only evaluator tests require local Playwright/Chromium, including a module MIME reproduction/control. They run separately from CI's dependency-free offline profile. Published objective results retain the original evaluator failure and symmetric MIME-only correction; targeted diagnoses distinguish cascades and limitations. Measured outputs stay unchanged.

## Visual and code-heavy ownership delivery

Init/adopt/upgrade and compact global routing must deliver the visual/code workload distinction while preserving custom guidance and configuration. Native model selection remains provider-neutral; policy delivery does not demonstrate model compliance or effectiveness. The portal benchmark separately measures backend/frontend contracts, visuals, correction evidence and whole-tree usage.

## Client portal pilot

The portal folder adds offline native-counter, recursive-tree, partition/Decimal cost, immutable-evidence, runner/isolation and QA-history controls, plus bounded preview tests. Full/release profiles run these dependency-free checks. Local backend and Playwright/Chromium controls run separately with loopback/process-group permissions. Historical 12 backend and 11 frontend group denominators stay fixed; original frontend failures and symmetric navigation correction are retained. Independent browser/input diagnosis, blind visual review and source provenance distinguish sampled passes from remaining defects. No CI command launches a paid model.

## Completion follow-up

The second portal instrument includes matched actual-studio references, exact-session repairs and fresh critical-risk reviewers inside one condition budget. Seventy-two frozen offline controls cover accounting, phase/audit validation, immutable snapshots and owned cleanup; six preview protocol contracts remain dependency-free. Publication provenance checks preserve 61 instrument and 25 blank-fixture hashes, with separately hashed portable brand capture and post-trial Darwin zero-grace cleanup correction; runner-native.py preserves exact measured bytes. Live or unknown process-group permission denial remains a failure. Process-cleanup tests require host process inspection; browser/loopback controls remain separate. Caps, transport failures, clock discrepancies, incomplete usage and late-recorded recovery instrumentation errors must remain visible, with no automatic pass or zero-cost inference. No CI command invokes a paid model.

## ServiceFlow matched MVP benchmark

`benchmarks/serviceflow-mvp-2026-10/` retains the common task, exact blank fixture, native-versus-portable provenance and uncapped builder/repair/fresh-audit controller. Full and release profiles run its offline instrumentation, source-projection and publication integrity checks plus preview contracts. Native model work and authenticated app acceptance are recorded experimental evidence, not invoked by these offline profiles. Runtime secrets are excluded by name before reading snapshot bytes. Final screenshots and independent app audits are distinct from static-gallery publication checks.

## Cost-aware routing policy delivery

Init/adopt/upgrade preserve project-specific guidance while delivering bounded implementation candidate comparison, separate product-risk and task-difficulty reasoning, and requested/observed model reporting. Installer fallback carries the bundle-decomposition rule without duplicating the full policy. Delivery tests do not establish model compliance or savings. Future trial design and the recorded same-model decision are explained in `docs/DELEGATION_ROUTING.md`; historical benchmark artifacts remain immutable.

## Modular standards and visual gate delivery

Module tests cover init/adopt/upgrade selection, configuration preservation, malformed input and visual packet declarations without code-risk inflation. Installer tests verify selected global defaults, no optional-policy leakage, preserved custom guidance and invalid selection refusal. Deterministic instruction ZIP tests check manifests, one foundation, selected-only content, collision safety and reproducibility. Repository checks reject canonical-template and published-archive drift. Inspect the public module/download presentation at desktop and mobile sizes. The policy requires fresh independent visual review for new/substantial frontend scope, blockers fixed and re-reviewed; delivery tests do not prove agent compliance or certify legal/accessibility completeness. Historical benchmark artifacts and scores remain unchanged.

## Scoped timing-test quarantine

On 2026-10-14, a concurrent full verification failed `test_completion_runner.CompletionTests.test_native_phase_global_timeout_is_observable`: its 0.2-second deadline could terminate the synthetic Python process before it emitted `thread.started`, then parsing failed with `Expected exactly one explicit native CLI root`. Other full runs passed; those passes do not erase the observed instability.

Owner: AethDesign toolkit maintainers. Expiry: 2026-11-14. `scripts/check_serviceflow_regressions.py` quarantines only this exact historical test, validates that exactly one matching test exists, reports the exclusion and fails after expiry. Full/release profiles run that wrapper in place of direct ServiceFlow discovery. Every other ServiceFlow test remains active. Frozen benchmark source, results and provenance are unchanged.

Replacement coverage uses the actual `execute_phase`, event parser, fixture session data and persisted metadata with a controlled process emitting the explicit root before raising `TimeoutExpired`. It verifies observable `timed_out`, absent completion usage and cleanup invocation without relying on scheduler startup speed. Existing real-process deadline/cleanup tests remain in the suite. This controlled test does not prove real host scheduling latency. The follow-up is to stabilize the historical startup assumption in a separately versioned maintenance projection, retain the failure record and remove the quarantine before expiry.

## ServiceFlow visual baseline publication

The full and release profiles run `python3 -B benchmarks/serviceflow-visual-baseline-2026-10/check_publication.py` and its `test_*.py` discovery for local-link, capture-byte, source-reconstruction, privacy-pattern, observed-effort, accounting-subset and current-gate consistency controls. These added commands run offline without paid native sessions, app servers or browser services. They can also be run directly for focused verification. The high-risk benchmark route requires the repository full profile. Static checks do not replace parent-operated desktop/mobile gallery interaction checks or fresh independent publication/visual review. Before completion, require current accepted source, supplemental re-review, final captures and reconciled whole-tree totals; earlier broad PASS artifacts remain intermediate. Originals and first handoffs are immutable. Published source excludes private native sessions and runtime harness. Final status and totals remain unset while evidence is pending.

## Full-remake policy follow-up

The canonical visual module and visual audit reference require a short product-grounded design basis, reconsidered hierarchy, before/after desktop/mobile comparison and explicit review of cumulative patterns. Existing composition, installer and deterministic-pack checks verify delivery without optional-module leakage; they do not establish design quality or runtime compliance. Independent scenario review must distinguish a cosmetic-only remake from justified retained structure, preserve focused cleanup lanes and avoid mandatory novelty, feature expansion or fabricated claims. The frozen ServiceFlow comparison retains its original verdicts and evidence; subsequent owner feedback and diagnosis live in `docs/VISUAL_REMAKE_REVIEW.md`. No new app benchmark or measured improvement is claimed by this policy update.
