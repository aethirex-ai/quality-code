# Choose your standards

| Module key | Published name | Scope |
| --- | --- | --- |
| `code` | Quality Code by AethDesign | Project mapping, risk lanes, tests and code audit gates |
| `visuals` | Quality Visuals by AethDesign | Frontend content/composition/completeness and visual completion gate |
| `swarms` | Quality Swarms by AethDesign | Task/model routing, coherent ownership, shared budgets and scoped context |

A small shared foundation is always composed once. It preserves existing requirements, acceptance criteria, truthful evidence and independent-review integrity. Selecting one module does not silently enable the others. Removing a module cannot waive a stricter existing project or user requirement.

## Instruction-only downloads

[Code](downloads/quality-code-by-aethdesign.zip), [Visuals](downloads/quality-visuals-by-aethdesign.zip), [Swarms](downloads/quality-swarms-by-aethdesign.zip), or [all three](downloads/quality-standards-by-aethdesign.zip).

Each contains AGENTS.md, README.md, LICENSE and a SHA-256 manifest. Merge the one managed block into your project's instructions while preserving local rules. Do not concatenate multiple packs: use the all pack or CLI composition instead. Instruction packs contain no executable toolkit and do not launch reviewers or enforce model compliance. Agents still need native review/render tools; unavailable required evidence stays BLOCKED.

## Toolkit composition

Clone the repository as described in [Getting started](GETTING_STARTED.md). New init/adopt defaults to all modules:

```sh
python3 scripts/quality_code.py init /path/to/new-project --modules code,visuals
python3 scripts/quality_code.py adopt /path/to/existing-project --modules visuals
python3 scripts/quality_code.py upgrade --dry-run /path/to/project --modules all
python3 scripts/quality_code.py upgrade /path/to/project --modules all
```

An explicit `--modules` replaces the project's selection. Upgrade without the flag preserves it. Legacy configurations without a selection retain their original bytes and use all three; new or explicitly selected configurations record `quality_modules` in `.quality/quality.toml`. Invalid or empty selections fail before writes. Changing an existing adopted selection uses upgrade, not adopt.

One managed AGENTS.md block contains one foundation and only selected modules. CLAUDE.md imports it. Toolkit files/configuration remain available even for a single instruction module; unselected policy is not injected. The CLI routes risk and prepares packets, while the agent follows instructions through its native capabilities.

Global defaults for new projects can be chosen with `python3 scripts/install.py --modules code,visuals`. Existing project selections survive upgrade. Global guidance routes to the selected project policy instead of repeating it in full. Reinstall refreshes the audit skill; the installer writes home configuration and is not transactional.

## Custom instruction pack

```sh
python3 scripts/build_standard_packs.py --output-dir /tmp/my-standards --modules code,visuals
```

The builder emits a deterministic composed instruction archive. Published source fragments live in [assets/modules](../assets/modules/); the full [project template](../assets/project/AGENTS.md) and four public archives are checked for drift. Shared rules are stored once in a composed output, not repeated along module boundaries.
