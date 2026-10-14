#!/usr/bin/env python3
"""Check public distribution parity, standard-pack freshness, and local Markdown links."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import tempfile
from urllib.parse import unquote


root = Path(__file__).resolve().parents[1]


def load_pack_builder():
    path = root / "scripts" / "build_standard_packs.py"
    spec = importlib.util.spec_from_file_location("quality_standard_pack_builder", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load standard pack builder at {path}")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    return builder


def load_engine():
    spec = importlib.util.spec_from_file_location("quality_repository_engine", root / "scripts" / "quality_code.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load quality-code engine")
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    return engine


def instruction_template_errors(repository_root: Path) -> list[str]:
    engine = load_engine()
    expected = engine.compose_instructions(repository_root, list(engine.MODULE_NAMES))
    template = repository_root / "assets" / "project" / "AGENTS.md"
    if not template.is_file() or template.read_text(encoding="utf-8") != expected:
        return ["assets/project/AGENTS.md does not match canonical full module composition"]
    return []


def public_pack_freshness_errors(repository_root: Path) -> list[str]:
    builder = load_pack_builder()
    download_dir = repository_root / "docs" / "downloads"
    if download_dir.is_symlink():
        return ["docs/downloads must be a real directory, not a symlink"]
    expected_names = set(builder.PACK_NAMES.values())
    with tempfile.TemporaryDirectory(prefix="quality-pack-freshness-") as temporary:
        generated = {path.name: path.read_bytes() for path in builder.build(Path(temporary))}
    errors: list[str] = []
    present = {path.name for path in download_dir.glob("*.zip")} if download_dir.is_dir() else set()
    if present != expected_names:
        missing = sorted(expected_names - present)
        extra = sorted(present - expected_names)
        if missing:
            errors.append(f"missing public standard pack(s): {', '.join(missing)}")
        if extra:
            errors.append(f"unexpected ZIP archive(s) in docs/downloads: {', '.join(extra)}")
    for name in sorted(expected_names & present):
        artifact = download_dir / name
        if artifact.is_symlink() or not artifact.is_file():
            errors.append(f"public standard pack is not a regular file: docs/downloads/{name}")
        elif artifact.read_bytes() != generated[name]:
            errors.append(f"stale public standard pack: docs/downloads/{name}")
    return errors


def repository_errors(repository_root: Path = root) -> list[str]:
    errors = []
    for source, copy in (("scripts/quality_code.py", ".quality/quality.py"),
                         ("LICENSE", ".quality/LICENSE"),
                         ("assets/project/.quality/audit-result.schema.json", ".quality/audit-result.schema.json")):
        if (repository_root / source).read_bytes() != (repository_root / copy).read_bytes():
            errors.append(f"distribution drift: {source} != {copy}")
    errors.extend(instruction_template_errors(repository_root))
    errors.extend(public_pack_freshness_errors(repository_root))
    for document in repository_root.rglob("*.md"):
        if ".git" in document.parts:
            continue
        for target in re.findall(r"\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
            if ":" in target or target.startswith("#"):
                continue
            local = unquote(target.split("#", 1)[0])
            if local and not (document.parent / local).exists():
                errors.append(f"broken reference in {document.relative_to(repository_root)}: {target}")
    return errors


def main() -> int:
    errors = repository_errors()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: distribution parity, instruction composition, public pack freshness, and local Markdown references")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
