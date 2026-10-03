#!/usr/bin/env python3
"""Install the quality-code master for Codex and Claude Code."""

from __future__ import annotations

import argparse
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


def merge_block(existing: str) -> str:
    if GLOBAL_START in existing or GLOBAL_END in existing:
        if GLOBAL_START not in existing or GLOBAL_END not in existing:
            raise InstallError("global instruction file has an incomplete quality-code marker block")
        start = existing.index(GLOBAL_START)
        end = existing.index(GLOBAL_END, start) + len(GLOBAL_END)
        parts = [
            part
            for part in (
                existing[:start].strip(),
                GLOBAL_BLOCK.strip(),
                existing[end:].strip(),
            )
            if part
        ]
        return "\n\n".join(parts) + "\n"
    if existing.strip():
        return existing.rstrip() + "\n\n" + GLOBAL_BLOCK
    return GLOBAL_BLOCK


def write_global(path: Path) -> None:
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(merge_block(existing).rstrip() + "\n", encoding="utf-8")


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
    return parser


def main() -> int:
    args = build_parser().parse_args()
    master = Path(__file__).resolve().parent.parent
    bin_dir = args.bin_dir or args.home / ".local" / "bin"
    try:
        write_global(args.home / ".codex" / "AGENTS.md")
        write_global(args.home / ".claude" / "CLAUDE.md")
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
    except (InstallError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
