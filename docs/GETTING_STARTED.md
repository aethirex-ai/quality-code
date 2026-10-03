# Getting started

## Try the toolkit without changing your agent configuration

From this repository, run `python3 scripts/quality_code.py init /path/to/new-project` or `python3 scripts/quality_code.py adopt /path/to/existing-project`. Adoption preserves existing documentation sections; tailor them to the product before behavioral work.

Use `./quality validate` for structure, `./quality context <paths...>` for routing, and `./quality verify <profile>` to run the configured commands. Verification profiles are `fast`, `changed`, `full`, and `release`. Detected commands are conservative starting points, not a complete test strategy.

## Install the global agent bootstrap

Review `scripts/install.py` first. Then, from the repository:

```sh
python3 scripts/install.py
```

The installer:

- merges a marked bootstrap block into `~/.codex/AGENTS.md` and `~/.claude/CLAUDE.md`;
- copies LICENSE and the toolkit’s distribution files into each agent’s `skills/audit-code-change` directory;
- sets Claude’s `skillOverrides.audit-code-change` to `name-only`;
- creates `~/.local/bin/quality-code` as a symlink to this checkout’s CLI.

Keep the checkout at a stable location. Moving or deleting it breaks the launcher. Existing instruction text outside the managed block is retained. Skill copies are refreshed on reinstall; do not use them for local edits. The installer is not transactional: a later collision can leave earlier changes applied. Back up your existing agent configuration before installation.

You can inspect installation in an isolated directory first:

```sh
python3 scripts/install.py --home /tmp/quality-code-demo-home
```

The generated global block instructs agents to run `quality-code init .` for new projects and `quality-code adopt .` for projects missing `.quality/quality.toml`.

## Invoke the audit skill

After required builder checks pass, generate a packet with a clear base:

```sh
./quality audit-packet --base HEAD --criteria "Observable acceptance criteria" > /tmp/quality-audit-packet.json
```

Use a fresh agent and explicitly invoke `$audit-code-change` in Codex or `/audit-code-change` in Claude Code. Give it the packet, repository root, and raw diff scope. The CLI does not start the agent. Low and normal work requires `--force` only when the user explicitly requested an independent audit.

## Upgrade an adopted project

```sh
python3 /path/to/quality-code/scripts/quality_code.py upgrade --dry-run /path/to/project
python3 /path/to/quality-code/scripts/quality_code.py upgrade /path/to/project
```

The dry run preflights version migration and reports intended actions. Supported TOML assignment formatting, including inline comments, is retained; unsupported formatting is rejected before managed files are written. Upgrade refreshes managed instructions, the local engine, wrapper, schema, and accompanying license; it retains configured commands and custom map/testing sections. Review the diff afterward.

## Adopt standard v3 delegation guidance

Upgrade from this checkout to refresh the managed `AGENTS.md` block, project-local engine, and standard version. Your configured verification commands and custom documentation remain in place. The Python CLI distributes the instructions; it does not discover models, choose effort, or spawn helpers itself. The coding agent uses its own runtime's native capabilities when following the policy.

Read [the delegation policy](DELEGATION.md). No provider account, API key, or model-routing dependency is added by this update. Existing global installations need an updated toolkit checkout or refreshed skill distribution before they can distribute v3 to projects.

## Custom routing

See [the example route](../examples/risk-route.toml). Add project-specific paths, meaningful test references, and valid map section names. The catch-all route is a fallback; more specific routes determine matched risk. When several specific routes match, the highest risk wins.

## Platform support

The toolkit requires Python 3.11+ (`tomllib`) and Git. The wrapper targets POSIX shells; CI covers Ubuntu and macOS. Direct Python invocation is possible on other systems, but Windows integration and global agent paths are not validated here.
