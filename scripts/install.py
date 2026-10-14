#!/usr/bin/env python3
"""Install the quality-code master for Codex and Claude Code."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys


GLOBAL_START = "<!-- quality-code-global:start -->"
GLOBAL_END = "<!-- quality-code-global:end -->"
GLOBAL_BLOCK = f"""{GLOBAL_START}
## Quality-code project bootstrap

- When creating a software project, run `~/.local/bin/quality-code init .` before implementation.
- In an existing software project without `.quality/quality.toml`, run `~/.local/bin/quality-code adopt .` before implementation.
- Preserve existing project content and resolve any reported collision instead of overwriting it.
{GLOBAL_END}
"""


class InstallError(RuntimeError):
    pass


DELEGATION_START = "<!-- quality-code-delegation:start -->"
DELEGATION_END = "<!-- quality-code-delegation:end -->"


def merge_managed(existing: str, block: str, start_marker: str, end_marker: str) -> str:
    starts, ends = existing.count(start_marker), existing.count(end_marker)
    if starts or ends:
        if starts != 1 or ends != 1 or existing.index(end_marker) < existing.index(start_marker):
            raise InstallError("global instruction file has malformed or duplicate quality-code markers")
        start = existing.index(start_marker)
        end = existing.index(end_marker, start) + len(end_marker)
        parts = [part.strip() for part in (existing[:start], block, existing[end:]) if part.strip()]
        return "\n\n".join(parts) + "\n"
    return existing.rstrip() + "\n\n" + block if existing.strip() else block


def merge_block(existing: str, modules: list[str] | None = None) -> str:
    block = GLOBAL_BLOCK
    if modules is not None and modules != ["code", "visuals", "swarms"]:
        suffix = " --modules " + ",".join(modules)
        block = block.replace(" init .`", " init ." + suffix + "`").replace(" adopt .`", " adopt ." + suffix + "`")
    return merge_managed(existing, block, GLOBAL_START, GLOBAL_END)


def module_api(master: Path):
    spec = importlib.util.spec_from_file_location("quality_install_engine", master / "scripts" / "quality_code.py")
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    return engine


def delegation_block(master: Path, modules: list[str] | None = None) -> str:
    template = master / "assets/project/AGENTS.md"
    content = template.read_text(encoding="utf-8")
    engine = module_api(master)
    selected = engine.configured_modules({"quality_modules": modules}) if modules is not None else list(engine.MODULE_NAMES)
    if content.strip() != engine.compose_instructions(master, list(engine.MODULE_NAMES)).strip():
        raise InstallError("canonical full template differs from module sources; regenerate it first")
    required = ("<!-- quality-code:start -->", "## Quality-code workflow",
                "## Efficient delegation and model selection",
                "## Bounded swarms and scoped context",
                "## Quality at delegation boundaries", "<!-- quality-code:end -->")
    positions = [content.find(section) for section in required]
    if any(content.count(section) != 1 for section in required) or positions != sorted(positions):
        raise InstallError("canonical project policy template is missing required structure")
    # Global defaults route to the project policy instead of duplicating its full
    # body in every runtime context. The fallback applies before bootstrap too.
    text = (DELEGATION_START + "\n## Quality-code delegation defaults\n\n"
            "For working software projects, before implementation check that the managed AGENTS.md block "
            "matches the installed composition for the project's quality_modules selection (legacy default: all), not unselected module content. If it is outdated, run "
            "`~/.local/bin/quality-code upgrade --dry-run .`, then `~/.local/bin/quality-code upgrade .`; "
            "preserve project-specific instructions and configuration and resolve collisions.\n\n"
            "The project's managed AGENTS.md owns the complete selected AethDesign standards policy. "
            "Use it when already supplied by the runtime; do not load a second full copy. "
            "For missing policy details, read only relevant sections of the installed template at "
            + str(template) + ". Bootstrap/init/adopt delivers that policy before software implementation.\n\n"
            "Fallback while project policy is unavailable: preserve risk lanes, safety, permissions, skill requirements "
            "and required independent verification. Delegate only ready worthwhile independent outcomes; use coherent "
            "direct owners, useful primary work and the smallest useful team. Discover available models, supported effort, "
            "tools/context/capacity through native evidence; choose the least costly fit likely to satisfy criteria, "
            "escalating when uncertainty or failures justify it. Never invent or hardcode model identifiers, rankings, "
            "prices or settings; inherit supported defaults when discovery is unavailable.\n\n"
            "Before assigning a large bundle to the default model, identify worthwhile bounded implementation outcomes "
            "and compare cheaper qualified candidates. Whole-project risk alone does not justify rejecting them. "
            "Preserve contracts/review/gates, use supported scoped model selection and distinguish requested from observed settings.\n\n"
            "Use one shared budget across the entire tree including every descendant, context transfer, retries and final "
            "verification; branch shares do not reset it. Permit hierarchy only for substantial independent work. "
            "Pass the smallest sufficient task brief in fresh scoped context, including contracts, ownership, constraints, "
            "budget and evidence; bound retrieval/tool output and return paths, checks and unresolved issues. "
            "Do not print media base64 or duplicate investigations/checks unnecessarily. "
            "Distinguish supplied context from model context capacity; use only supported controls. "
            "Keep visually coupled work with one persistent design owner and a small useful helper team; "
            "reserve bounded swarms for ready independent code-heavy outcomes, preserving API/state contracts and gates. "
            "Primary owns integration and observable product/visual/defect validation. A builder/director cannot "
            "provide its independent audit verdict. If a required independent gate is unavailable, report it blocked. "
            "Parallelism and cheaper API models do not prove lower subscription usage.\n\n"
            + DELEGATION_END + "\n")
    prefix = text[:text.index("Fallback while project policy is unavailable:")]
    prefix += "Installed defaults: " + ", ".join(selected) + ". Existing project selections are preserved on upgrade.\n\n"
    fallback = "Fallback while project policy is unavailable: preserve risk lanes, safety, permissions and required independent verification. Do not claim unavailable evidence passed.\n\n"
    if "swarms" in selected:
        fallback = text[text.index("Fallback while project policy is unavailable:"):text.index(DELEGATION_END)]
    if "visuals" in selected:
        fallback += ("Quality Visuals: use specific useful content and intentional composition; remove unjustified slogan eyebrows, arrows, numbering and empty containers. "
                     "For new or substantially redesigned frontends, require desktop/mobile evidence and fresh independent visual review; fix blocking baseline findings before completion. "
                     "Isolated low-risk copy/static-style work keeps its focused builder lane.\n\n")
    return prefix + fallback + DELEGATION_END + "\n"


def merged_global(path: Path, delegation: str, modules: list[str] | None = None) -> str:
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    # Validate delegation markers in the ORIGINAL text before bootstrap replacement
    # can erase malformed nested markers. Neither validation call writes a file.
    merge_managed(existing, delegation, DELEGATION_START, DELEGATION_END)
    # Reject overlapping blocks before merging either, preserving surrounding instructions.
    if GLOBAL_START in existing and DELEGATION_START in existing:
        g0, g1 = existing.index(GLOBAL_START), existing.find(GLOBAL_END)
        d0, d1 = existing.index(DELEGATION_START), existing.find(DELEGATION_END)
        if g1 >= 0 and d1 >= 0 and not (g1 < d0 or d1 < g0):
            raise InstallError("global quality-code marker blocks overlap")
    return merge_managed(merge_block(existing, modules), delegation, DELEGATION_START, DELEGATION_END).rstrip() + "\n"


def install_skill(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    # Only ship the audited runtime distribution, never checkout history or local state.
    for name in ("LICENSE", "SKILL.md", "agents", "assets", "references", "scripts"):
        item = source / name
        target = destination / name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
        else:
            shutil.copy2(item, target)


def update_claude_settings(path: Path) -> None:
    if path.is_file():
        try:
            settings = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise InstallError(f"cannot parse {path}: {exc}") from exc
    else:
        settings = {}
    if not isinstance(settings, dict):
        raise InstallError(f"{path} must contain a JSON object")
    overrides = settings.setdefault("skillOverrides", {})
    if not isinstance(overrides, dict):
        raise InstallError(f"skillOverrides in {path} must be a JSON object")
    overrides["audit-code-change"] = "name-only"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def install_launcher(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink():
        if destination.resolve() == source.resolve():
            return
        raise InstallError(f"{destination} is already a symlink to another target")
    if destination.exists():
        raise InstallError(f"{destination} already exists; refusing to replace it")
    destination.symlink_to(source.resolve())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--bin-dir", type=Path)
    parser.add_argument("--modules", default="all", help="all or comma-separated code, visuals, swarms defaults for new projects")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    master = Path(__file__).resolve().parent.parent
    bin_dir = args.bin_dir or args.home / ".local" / "bin"
    try:
        selected = module_api(master).parse_modules(args.modules)
        delegation = delegation_block(master, selected)
        globals_to_write = [(path, merged_global(path, delegation, selected)) for path in
                            (args.home / ".codex/AGENTS.md", args.home / ".claude/CLAUDE.md")]
        # Preflight both global files before either is written.
        for path, content in globals_to_write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        install_skill(master, args.home / ".codex" / "skills" / "audit-code-change")
        install_skill(master, args.home / ".claude" / "skills" / "audit-code-change")
        update_claude_settings(args.home / ".claude" / "settings.json")
        launcher = master / "scripts" / "quality_code.py"
        launcher.chmod(0o755)
        install_launcher(launcher, bin_dir / "quality-code")
        print(f"PASS: installed quality-code from {master}")
        print(f"PASS: Codex global instructions: {args.home / '.codex' / 'AGENTS.md'}")
        print(f"PASS: Claude global instructions: {args.home / '.claude' / 'CLAUDE.md'}")
        print(f"PASS: launcher: {bin_dir / 'quality-code'}")
        return 0
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
