# Provider-neutral delegation

Quality Code standard v3 uses the coding agent's native runtime to discover available models and select a suitable model and supported effort settings. There are no hardcoded model names, providers, rankings, concurrency numbers, or effort labels in the policy.

## Decision process

1. **Decide whether to delegate.** Identify an independent, bounded task with a useful deliverable. Estimate briefing and integration overhead. Small or tightly coupled work usually stays with the primary agent. Existing low-risk restrictions still apply.
2. **Discover native capabilities.** Use exposed native model-listing and capability tools and runtime metadata to determine actual account access, supported tools, context limits, effort controls, and concurrency. Reuse relevant discovery within the task; refresh when requirements or access change.
3. **Select from evidence.** Match complexity, uncertainty, product risk, skill requirements, and context/tool needs against accessible candidates. Respect user selections and higher-priority runtime restrictions. Use supported defaults where explicit effort controls do not exist.
4. **Budget the whole task.** Include helper context, generated and reasoning tokens when reported, coordination, validation, retries, and integration. Lower elapsed time alone does not establish lower token use or cost. Use native usage evidence when available; otherwise state the basis for estimates without inventing prices or capabilities.
5. **Brief and coordinate.** Assign outcomes, file ownership or read-only boundaries, relevant skills, dependencies, evidence requirements, and concise reporting. Parallelize independent tasks; serialize dependent tasks. Reuse helpers where context helps, and keep recursive delegation within the same constraints.
6. **Integrate and verify.** The primary agent validates results. Escalate model capability or supported effort when evidence shows the first choice is insufficient. A helper's confident answer cannot substitute for verification.

“Best fit” means the best supported choice from currently available evidence, not a guarantee of universal model optimality. A model catalog may list identifiers without exposing capability, cost, or comparative performance; do not infer those attributes from names or run speculative model benchmarks to fill the gaps.

## Capability fallbacks

| Native runtime capability | Action |
| --- | --- |
| Discovery and explicit model/effort selection available | Choose among accessible candidates using supported controls and current evidence |
| Model catalog lacks capability or usage data | Use known native metadata or prior relevant evidence; state material uncertainty |
| Discovery unavailable | Inherit the current model and supported defaults; do not guess identifiers |
| Explicit model or effort selection unavailable | Use inherited settings; do not simulate unsupported routing |
| Subagents unavailable | Complete permitted builder work locally; a required independent audit remains blocked until independence is available |

## Practical examples

**A bounded repository investigation:** A helper traces a specific state transition and reports file references and unresolved questions. Native capability evidence supports selecting an efficient candidate that has the required code tools and context capacity. The primary agent continues a separate implementation task.

**A difficult integration defect:** Begin with the smallest useful team. One helper can reproduce the user flow while the primary agent traces the relevant service contract. Give each distinct ownership and evidence requirements. Increase capability or supported effort only if ambiguity or failed verification justifies it.

**A security-sensitive change:** Product risk still requires the configured full and release checks and a fresh independent auditor. Implementation helpers may accelerate the build, but none can issue the independent verdict for work they implemented or materially directed.

## Skills and independence

A skill's workload is a selection input, not a fixed model tier. Read the relevant skill and match its actual requirements. Applicable skill instructions cannot override explicit user selections or higher-priority runtime restrictions. Send only necessary skill context and permitted data to helpers.

Audit independence concerns the agent's participation and evidence, not a model brand. Keep auditors fresh and read-only, supply raw scope and acceptance criteria, and omit builder conclusions. Follow [the audit protocol](../references/AUDIT_PROTOCOL.md).

## Delivery and limitations

The managed instruction block lives in [the project template](../assets/project/AGENTS.md) and is delivered through init, adopt, and upgrade. The toolkit's Python engine does not call provider model APIs or orchestrate agents. Native capability discovery and enforcement depend on the host runtime; this standard introduces no additional provider integrations or credentials.

No speed or token savings are claimed without measurements. Compare similar tasks and product risks using actual completion time, total reported usage, retries, validation outcomes, and defects where that evidence is available.
