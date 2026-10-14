#!/usr/bin/env python3
"""Build deterministic, instruction-only Quality Code download packs."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import zipfile


ENGINE_PATH = Path(__file__).resolve().with_name("quality_code.py")
PACK_NAMES = {
    "code": "quality-code-by-aethdesign.zip",
    "visuals": "quality-visuals-by-aethdesign.zip",
    "swarms": "quality-swarms-by-aethdesign.zip",
    "all": "quality-standards-by-aethdesign.zip",
}
PACK_MARKER = "quality-code-standard-pack"
ENTRY_NAMES = ("AGENTS.md", "LICENSE", "README.md", "manifest.json")
MODULE_BRANDS = {
    "code": "Quality Code by AethDesign",
    "visuals": "Quality Visuals by AethDesign",
    "swarms": "Quality Swarms by AethDesign",
}


class PackError(ValueError):
    """An unsafe or invalid pack request."""


def load_engine():
    spec = importlib.util.spec_from_file_location("quality_code_pack_engine", ENGINE_PATH)
    if spec is None or spec.loader is None:
        raise PackError(f"cannot load quality-code engine at {ENGINE_PATH}")
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    return engine


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _readme(modules: list[str]) -> str:
    selection = ",".join(modules)
    title = (
        "Quality Standards by AethDesign"
        if modules == ["code", "visuals", "swarms"]
        else MODULE_BRANDS[modules[0]]
        if len(modules) == 1
        else "Quality " + " and ".join(module.title() for module in modules) + " by AethDesign"
    )
    module_names = ", ".join(module.title() for module in modules)
    return (
        f"# {title}\n\n"
        f"This download contains the {module_names} agent instruction module"
        f"{'s' if len(modules) != 1 else ''}, with the shared quality foundation included once.\n\n"
        "This is an instruction-only download. It does not include the executable toolkit, "
        "project templates, or bootstrap command.\n\n"
        "Source and toolkit: https://github.com/aethirex-ai/quality-code . "
        "Setup: https://github.com/aethirex-ai/quality-code/blob/main/docs/GETTING_STARTED.md . "
        "The Code module expects MAP.md, TESTING.md and the local quality CLI; "
        "initialize/adopt the project with the toolkit and the same module selection before implementation. "
        "Visuals and Swarms can use existing project tools and requirements.\n\n"
        "Do not stack multiple downloaded AGENTS.md packs. Choose one combined selection. "
        "For a project that needs the executable toolkit, use the root repository CLI to "
        "initialize or adopt it, or to change an existing selection. For example: "
        f"`python3 scripts/quality_code.py upgrade /path/to/project --modules {selection}`. "
        "The CLI manages the AGENTS.md block while preserving user content.\n"
    )


def _manifest(modules: list[str], files: dict[str, bytes]) -> bytes:
    payload = {
        "schema": 1,
        "product": PACK_MARKER,
        "modules": modules,
        "foundation": "once",
        "AGENTSsha256": _digest(files["AGENTS.md"]),
        "files": {name: _digest(files[name]) for name in ENTRY_NAMES if name != "manifest.json"},
    }
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _is_owned_pack(path: Path, valid_modules: tuple[str, ...], expected_modules: list[str] | None = None) -> bool:
    try:
        with zipfile.ZipFile(path) as archive:
            if sorted(archive.namelist()) != sorted(ENTRY_NAMES):
                return False
            manifest = json.loads(archive.read("manifest.json"))
            if (manifest.get("schema") != 1 or manifest.get("product") != PACK_MARKER
                    or manifest.get("foundation") != "once"):
                return False
            modules = manifest.get("modules")
            if not isinstance(modules, list) or not modules or not all(
                isinstance(module, str) and module in valid_modules for module in modules
            ) or len(set(modules)) != len(modules):
                return False
            if expected_modules is not None and modules != expected_modules:
                return False
            hashes = manifest.get("files")
            if not isinstance(hashes, dict) or set(hashes) != set(ENTRY_NAMES) - {"manifest.json"}:
                return False
            if manifest.get("AGENTSsha256") != hashes.get("AGENTS.md"):
                return False
            return all(_digest(archive.read(name)) == hashes[name] for name in hashes)
    except (OSError, zipfile.BadZipFile, KeyError, json.JSONDecodeError, AttributeError):
        return False


def _write_deterministic_zip(destination: Path, files: dict[str, bytes]) -> None:
    # Stage beside destination so replacement is atomic and never leaves a partial ZIP.
    fd, temporary_name = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent)
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name in ENTRY_NAMES:
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                info.flag_bits = 0
                archive.writestr(info, files[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def build(output_dir: Path, modules: str | None = None) -> list[Path]:
    if output_dir.is_symlink():
        raise PackError(f"refusing symlink output directory: {output_dir}")
    engine = load_engine()
    module_names = engine.MODULE_NAMES
    if modules is None:
        selections = [(name, [name]) for name in module_names]
        selections.append(("all", list(module_names)))
    else:
        selected = engine.parse_modules(modules)
        selections = [("custom", selected)]

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise PackError(f"cannot create output directory {output_dir}: {exc}") from exc
    if not output_dir.is_dir():
        raise PackError(f"output path is not a directory: {output_dir}")

    root = Path(engine.find_master_root())
    license_path = root / "LICENSE"
    destinations = [(key, output_dir / ("quality-custom-by-aethdesign.zip" if key == "custom" else PACK_NAMES[key]), selected)
                    for key, selected in selections]
    # Validate every destination before writing any pack.
    for key, destination, selected in destinations:
        if destination.is_symlink():
            raise PackError(f"refusing symlink destination: {destination}")
        expected_modules = None if key == "custom" else selected
        if destination.exists() and not _is_owned_pack(destination, module_names, expected_modules):
            raise PackError(f"refusing to overwrite unrelated file: {destination}")

    output_paths = []
    for _, destination, selected in destinations:
        files = {
            "AGENTS.md": engine.compose_instructions(root, selected).encode("utf-8"),
            "LICENSE": license_path.read_bytes(),
            "README.md": _readme(selected).encode("utf-8"),
        }
        files["manifest.json"] = _manifest(selected, files)
        _write_deterministic_zip(destination, files)
        output_paths.append(destination)
    return output_paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path, help="directory for generated ZIP archives")
    parser.add_argument("--modules", help="build one custom pack for a comma-separated module selection")
    args = parser.parse_args(argv)
    try:
        outputs = build(args.output_dir, args.modules)
    except Exception as exc:
        if hasattr(exc, "message"):
            detail = exc.message
        else:
            detail = str(exc)
        print(f"error: {detail}", file=sys.stderr)
        return 2
    for path in outputs:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
