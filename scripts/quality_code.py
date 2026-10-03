#!/usr/bin/env python3
"""Bootstrap, validate, route, and audit the shared quality-code standard."""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib
from typing import Any


STANDARD_VERSION = 3
RISK_ORDER = {"low": 0, "normal": 1, "high": 2, "critical": 3}
REQUIRED_PROJECT_FILES = (
    "AGENTS.md",
    "CLAUDE.md",
    "MAP.md",
    "TESTING.md",
    "quality",
    ".quality/quality.py",
    ".quality/audit-result.schema.json",
    ".quality/LICENSE",
)
MANAGED_START = "<!-- quality-code:start -->"
MANAGED_END = "<!-- quality-code:end -->"
CLAUDE_IMPORT = "@AGENTS.md"


class QualityError(RuntimeError):
    pass


def run(command: list[str], cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    except FileNotFoundError as exc:
        raise QualityError(f"command not found: {command[0]}") from exc
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise QualityError(f"{' '.join(command)} failed: {detail}")
    return result


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], root, check=check)


def find_project_root(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / ".quality" / "quality.toml").is_file():
            return candidate
    raise QualityError(f"no .quality/quality.toml found from {start}")


def find_master_root() -> Path:
    root = Path(__file__).resolve().parent.parent
    if (root / "assets" / "project").is_dir() and (root / "SKILL.md").is_file():
        return root
    raise QualityError(
        "master assets are unavailable from this project-local copy; "
        "run init, adopt, or upgrade with the global quality-code command"
    )


def load_config(root: Path) -> dict[str, Any]:
    path = root / ".quality" / "quality.toml"
    try:
        with path.open("rb") as handle:
            config = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise QualityError(f"cannot read {path}: {exc}") from exc
    if config.get("version") != 1:
        raise QualityError("quality.toml version must be 1")
    return config


def headings(markdown: str) -> set[str]:
    result: set[str] = set()
    for line in markdown.splitlines():
        stripped = line.lstrip()
        if not stripped.startswith("#"):
            continue
        title = stripped.lstrip("#").strip().rstrip("#").strip()
        if title:
            result.add(title)
    return result


def command_profiles(config: dict[str, Any]) -> dict[str, list[list[str]]]:
    raw_profiles = config.get("verify")
    if not isinstance(raw_profiles, dict) or not raw_profiles:
        raise QualityError("quality.toml must define [verify] profiles")
    profiles: dict[str, list[list[str]]] = {}
    for name, commands in raw_profiles.items():
        if not isinstance(commands, list) or not commands:
            raise QualityError(f"verify profile {name!r} must contain command arrays")
        normalized: list[list[str]] = []
        for command in commands:
            if not isinstance(command, list) or not command or not all(
                isinstance(part, str) and part for part in command
            ):
                raise QualityError(f"verify profile {name!r} has an invalid command")
            if any("REPLACE_ME" in part for part in command):
                raise QualityError(f"verify profile {name!r} still contains a placeholder")
            normalized.append(command)
        profiles[name] = normalized
    return profiles


def configured_areas(config: dict[str, Any]) -> list[dict[str, Any]]:
    areas = config.get("areas")
    if not isinstance(areas, list) or not areas:
        raise QualityError("quality.toml must define at least one [[areas]] route")
    for area in areas:
        if not isinstance(area, dict):
            raise QualityError("every [[areas]] entry must be a table")
        if area.get("risk") not in RISK_ORDER:
            raise QualityError(f"area {area.get('name')!r} has an invalid risk")
        paths = area.get("paths")
        if not isinstance(paths, list) or not paths or not all(isinstance(item, str) for item in paths):
            raise QualityError(f"area {area.get('name')!r} must define paths")
    if not any(area.get("fallback") is True for area in areas):
        raise QualityError("quality.toml must define a fallback area")
    return areas


def validate(root: Path, config: dict[str, Any]) -> None:
    errors: list[str] = []
    for relative in REQUIRED_PROJECT_FILES:
        if not (root / relative).is_file():
            errors.append(f"missing {relative}")
    if config.get("standard_version") != STANDARD_VERSION:
        errors.append(
            f"standard_version must be {STANDARD_VERSION}; run quality-code upgrade --dry-run {root}"
        )

    try:
        profiles = command_profiles(config)
        areas = configured_areas(config)
    except QualityError as exc:
        errors.append(str(exc))
        profiles = {}
        areas = []

    map_path = root / "MAP.md"
    map_headings: set[str] = set()
    if map_path.is_file():
        map_text = map_path.read_text(encoding="utf-8")
        map_headings = headings(map_text)
        limit = config.get("policy", {}).get("map_word_limit", 900)
        if not isinstance(limit, int) or limit < 100:
            errors.append("policy.map_word_limit must be an integer of at least 100")
        elif len(map_text.split()) > limit:
            errors.append(f"MAP.md exceeds the {limit}-word context budget")

    agents_path = root / "AGENTS.md"
    if agents_path.is_file():
        agents_text = agents_path.read_text(encoding="utf-8")
        if MANAGED_START not in agents_text or MANAGED_END not in agents_text:
            errors.append("AGENTS.md is missing the managed quality-code block")
    claude_path = root / "CLAUDE.md"
    if claude_path.is_file() and CLAUDE_IMPORT not in claude_path.read_text(encoding="utf-8"):
        errors.append("CLAUDE.md must import @AGENTS.md")

    for area in areas:
        for section in area.get("map_sections", []):
            if section not in map_headings:
                errors.append(f"area {area.get('name')!r} references missing MAP.md section {section!r}")
        for profile in area.get("required_profiles", []):
            if profile not in profiles:
                errors.append(f"area {area.get('name')!r} references missing profile {profile!r}")

    risk_profiles = config.get("audit", {}).get("required_profiles_by_risk", {})
    if not isinstance(risk_profiles, dict):
        errors.append("audit.required_profiles_by_risk must be a table")
    else:
        for risk in RISK_ORDER:
            names = risk_profiles.get(risk)
            if not isinstance(names, list) or not names:
                errors.append(f"audit.required_profiles_by_risk.{risk} must be a non-empty array")
                continue
            for name in names:
                if name not in profiles:
                    errors.append(f"risk {risk!r} references missing profile {name!r}")

    audit_threshold = config.get("audit", {}).get("independent_audit_min_risk")
    if audit_threshold not in RISK_ORDER:
        errors.append("audit.independent_audit_min_risk must be low, normal, high, or critical")

    if errors:
        raise QualityError("validation failed:\n- " + "\n- ".join(errors))
    print(f"PASS: {root} quality standard is valid")


def matching_areas(paths: list[str], areas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Resolve fallback per file; one specific match must not hide another file's risk.
    selected: set[int] = set()
    for path in paths:
        specific = [index for index, area in enumerate(areas)
                    if area.get("fallback") is not True
                    and any(fnmatch.fnmatch(path, pattern) for pattern in area["paths"])]
        effective = specific or [index for index, area in enumerate(areas)
                                 if area.get("fallback") is True]
        selected.update(effective)
    return [area for index, area in enumerate(areas) if index in selected]


def highest_risk(areas: list[dict[str, Any]]) -> str:
    if not areas:
        return "critical"
    return max((area["risk"] for area in areas), key=RISK_ORDER.__getitem__)


def unique_commands(values: list[list[str]]) -> list[list[str]]:
    seen: set[tuple[str, ...]] = set()
    result: list[list[str]] = []
    for value in values:
        key = tuple(value)
        if value and key not in seen:
            seen.add(key)
            result.append(value)
    return result


def unique_strings(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def base_exists(root: Path, base: str) -> bool:
    return git(root, "rev-parse", "--verify", "--quiet", base, check=False).returncode == 0


def changed_files(root: Path, base: str) -> tuple[list[str], bool, list[str]]:
    has_base = base_exists(root, base)
    if has_base:
        tracked = git(root, "diff", "--relative", "--name-only", "-z", "--diff-filter=ACMRD",
                      base, "--", ".").stdout.split("\0")
    else:
        tracked = git(root, "ls-files", "--cached", "-z", "--", ".").stdout.split("\0")
    untracked = git(root, "ls-files", "--others", "--exclude-standard", "-z", "--", ".").stdout.split("\0")
    return sorted(set(filter(None, [*tracked, *untracked]))), has_base, sorted(filter(None, untracked))


def select_profiles(config: dict[str, Any], risk: str, areas: list[dict[str, Any]]) -> list[str]:
    configured = config["audit"]["required_profiles_by_risk"][risk]
    additional = [name for area in areas for name in area.get("required_profiles", [])]
    return unique_strings([*configured, *additional])


def audit_threshold(config: dict[str, Any]) -> str:
    threshold = config.get("audit", {}).get("independent_audit_min_risk")
    if threshold not in RISK_ORDER:
        raise QualityError("audit.independent_audit_min_risk must be low, normal, high, or critical")
    return threshold


def independent_audit_required(config: dict[str, Any], risk: str) -> bool:
    return RISK_ORDER[risk] >= RISK_ORDER[audit_threshold(config)]


def packet(root: Path, config: dict[str, Any], base: str, criteria: str, *, force: bool = False) -> dict[str, Any]:
    files, has_base, untracked = changed_files(root, base)
    if not files:
        raise QualityError("no changed files found for the requested audit scope")
    areas = matching_areas(files, configured_areas(config))
    risk = highest_risk(areas)
    required = independent_audit_required(config, risk)
    if not required and not force:
        threshold = audit_threshold(config)
        raise QualityError(
            f"independent audit is not required for {risk} risk (threshold: {threshold}); "
            "do not generate an audit packet unless the user explicitly requested an audit; "
            "use --force only for that explicit request"
        )
    profiles = select_profiles(config, risk, areas)
    commands = command_profiles(config)
    map_sections = unique_strings([section for area in areas for section in area.get("map_sections", [])])
    tests = unique_strings([test for area in areas for test in area.get("tests", [])])
    diff_command = ["git", "diff", "--relative", "--find-renames"]
    if has_base:
        diff_command.append(base)
    diff_command.extend(["--", "."])
    diff_commands = [diff_command]
    if not has_base:
        diff_commands.insert(0, ["git", "diff", "--cached", "--relative", "--find-renames", "--", "."])
    return {
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "project": config.get("project", root.name),
        "root": str(root),
        "base": base,
        "base_exists": has_base,
        "acceptance_criteria": criteria,
        "changed_files": files,
        "risk": risk,
        "independent_audit_required": required,
        "audit_forced": force and not required,
        "matched_areas": [area.get("name", "unnamed") for area in areas],
        "required_profiles": profiles,
        "commands": {name: commands[name] for name in profiles},
        "map": {"path": "MAP.md", "sections": map_sections},
        "project_testing": "TESTING.md",
        "related_tests": tests,
        "diff_commands": diff_commands,
        "untracked_files_to_read": untracked,
        "audit_constraints": [
            "Use a fresh agent and explicitly invoke audit-code-change.",
            "Treat builder conclusions and prior test output as untrusted.",
            "Do not modify the project worktree.",
        ],
    }


def run_profile(root: Path, profile: str, profiles: dict[str, list[list[str]]]) -> None:
    if profile not in profiles:
        raise QualityError(f"unknown verify profile {profile!r}")
    for command in profiles[profile]:
        print(f"RUN: {json.dumps(command)}", flush=True)
        try:
            result = subprocess.run(command, cwd=root, check=False)
        except FileNotFoundError as exc:
            raise QualityError(f"command not found: {command[0]}") from exc
        if result.returncode != 0:
            raise QualityError(f"profile {profile!r} failed with exit code {result.returncode}")
    print(f"PASS: verify profile {profile}")


def read_criteria(args: argparse.Namespace) -> str:
    if args.criteria is not None:
        value = args.criteria.strip()
    else:
        try:
            value = Path(args.criteria_file).read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise QualityError(f"cannot read acceptance criteria: {exc}") from exc
    if not value:
        raise QualityError("acceptance criteria must not be empty")
    return value


def npm_command(root: Path, script: str) -> list[str]:
    if (root / "pnpm-lock.yaml").is_file():
        return ["pnpm", "run", script]
    if (root / "yarn.lock").is_file():
        return ["yarn", script]
    if (root / "bun.lock").is_file() or (root / "bun.lockb").is_file():
        return ["bun", "run", script]
    return ["npm", "run", script]


def detect_profiles(root: Path) -> tuple[dict[str, list[list[str]]], list[str], list[str]]:
    tests: list[list[str]] = []
    static: list[list[str]] = []
    builds: list[list[str]] = []
    notes: list[str] = []

    package_json = root / "package.json"
    if package_json.is_file():
        try:
            scripts = json.loads(package_json.read_text(encoding="utf-8")).get("scripts", {})
        except (OSError, json.JSONDecodeError) as exc:
            raise QualityError(f"cannot inspect package.json: {exc}") from exc
        if isinstance(scripts, dict):
            for name in ("test:unit", "test"):
                if isinstance(scripts.get(name), str):
                    tests.append(npm_command(root, name))
                    break
            for name in ("lint", "typecheck", "check"):
                if isinstance(scripts.get(name), str):
                    static.append(npm_command(root, name))
            if isinstance(scripts.get("build"), str):
                builds.append(npm_command(root, "build"))
        notes.append("JavaScript/TypeScript commands were detected from package.json scripts.")

    pyproject = root / "pyproject.toml"
    python_tests = any((root / name).exists() for name in ("tests", "pytest.ini", "tox.ini"))
    if pyproject.is_file():
        try:
            pyconfig = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise QualityError(f"cannot inspect pyproject.toml: {exc}") from exc
        tools = pyconfig.get("tool", {})
        if isinstance(tools, dict) and "pytest" in tools:
            python_tests = True
        if isinstance(tools, dict) and "ruff" in tools:
            static.append(["python3", "-m", "ruff", "check", "."])
        if isinstance(tools, dict) and "mypy" in tools:
            static.append(["python3", "-m", "mypy", "."])
        notes.append("Python commands were detected from pyproject.toml and test layout.")
    if python_tests:
        tests.append(["python3", "-m", "pytest"])

    if (root / "Package.swift").is_file():
        tests.append(["swift", "test"])
        builds.append(["swift", "build", "-c", "release"])
        notes.append("Swift Package Manager verification was detected.")
    if (root / "Cargo.toml").is_file():
        tests.append(["cargo", "test"])
        static.append(["cargo", "check", "--all-targets"])
        builds.append(["cargo", "build", "--release"])
        notes.append("Cargo verification was detected.")
    if (root / "go.mod").is_file():
        tests.append(["go", "test", "./..."])
        static.append(["go", "vet", "./..."])
        notes.append("Go verification was detected.")

    makefile = root / "Makefile"
    if makefile.is_file() and not (tests or static or builds):
        make_text = makefile.read_text(encoding="utf-8", errors="replace")
        targets = set(re.findall(r"^([A-Za-z0-9_.-]+)\s*:(?![=])", make_text, re.MULTILINE))
        if "test" in targets:
            tests.append(["make", "test"])
        if "lint" in targets:
            static.append(["make", "lint"])
        if "build" in targets:
            builds.append(["make", "build"])
        notes.append("Make targets were inspected for verification commands.")

    baseline = [["git", "diff", "--check"]]
    tests = unique_commands(tests)
    static = unique_commands(static)
    builds = unique_commands(builds)
    fast = tests[:1] or static[:1] or baseline
    changed = unique_commands([*tests, *static]) or baseline
    full = unique_commands([*tests, *static, *builds]) or baseline
    release = unique_commands([*full, *builds]) or baseline
    if not tests:
        notes.append("No automated product test command was detected; add one before behavioral work can pass audit.")
    return (
        {"fast": fast, "changed": changed, "full": full, "release": release},
        [" ".join(command) for command in tests],
        notes,
    )


def detected_paths(root: Path, candidates: tuple[str, ...]) -> list[str]:
    return [name for name in candidates if (root / name).exists()]


def render_template(path: Path, replacements: dict[str, str]) -> str:
    text = path.read_text(encoding="utf-8")
    for key in sorted(replacements, key=len, reverse=True):
        text = text.replace(key, replacements[key])
    return text


def render_project(master: Path, root: Path) -> dict[str, str]:
    profiles, test_commands, notes = detect_profiles(root)
    source_paths = detected_paths(root, ("src", "app", "lib", "Sources", "packages", "webapp"))
    test_paths = detected_paths(root, ("tests", "test", "Tests", "spec", "__tests__"))
    entry_points = detected_paths(
        root,
        ("package.json", "pyproject.toml", "Package.swift", "Cargo.toml", "go.mod", "main.py", "server.js", "index.html"),
    )
    generated = detected_paths(root, ("dist", "build", "coverage", ".next", "target"))
    project_name = root.name
    canonical = ", ".join(f"`{path}/`" for path in source_paths) or "Not established; update before implementation."
    entries = ", ".join(f"`{path}`" for path in entry_points) or "Not established; update before implementation."
    test_locations = ", ".join(f"`{path}/`" for path in test_paths) or "No test directory detected."
    generated_paths = ", ".join(f"`{path}/`" for path in generated) or "None detected."
    replacements = {
        "PROJECT_NAME": project_name,
        "YYYY-MM-DD": dt.date.today().isoformat(),
        "USER_OUTCOME": "Define the primary user outcome before implementation.",
        "CANONICAL_PATHS": canonical,
        "ENTRY_POINTS": entries,
        "LEGACY_PATHS": "None identified; record legacy or archived paths when discovered.",
        "GENERATED_PATHS": generated_paths,
        "INPUT -> COMPONENT -> STATE_OR_SERVICE -> OUTPUT": "Input -> project entry point -> domain logic -> observable output",
        "AREA | `PATH` | RESPONSIBILITY": f"Application | {canonical} | Canonical product implementation",
        "API_IPC_CLI_SCHEMA_CONTRACTS": "Document public interfaces and schemas before changing them.",
        "DATABASE_FILES_SETTINGS_CACHES": "Document persisted state and migration requirements before changing them.",
        "PROVIDERS_SERVICES_PLATFORM_APIS": "Document external systems when introduced.",
        "VERSIONS_MIGRATIONS_ALIASES": "Preserve documented compatibility; record exceptions explicitly.",
        "INPUT_AUTHORIZATION_BOUNDARIES": "Treat external input and privilege transitions as untrusted boundaries.",
        "DATA_CLASSIFICATION_AND_STORAGE": "Do not store secrets or personal data without an explicit design and test basis.",
        "PRIVILEGED_OPERATIONS_OR_NONE": "None identified; update before adding privileged or destructive behavior.",
        "FAILURE_INVARIANTS": "Fail safely without corrupting state or exposing sensitive data.",
        "INVARIANT_ONE": "Acceptance criteria must describe observable behavior before implementation.",
        "INVARIANT_TWO": "Behavioral fixes require proportionate regression evidence; high-risk changes require an independent audit.",
        "CO_CHANGE_RULES": "Update MAP.md, TESTING.md, and quality routing when boundaries or risks change.",
        "MANUAL_EVIDENCE": "Record project-specific manual evidence in TESTING.md.",
        "HIGH_RISK_AREA_AND_REASON": "Security, persistence, release, and destructive paths require explicit risk routing.",
        "MIGRATION_OR_COMPATIBILITY_BOUNDARY": "Public contracts and persisted state require compatibility evidence.",
        "RELEASE_OR_SECURITY_BOUNDARY": "Release and security changes require the release verification profile.",
        "PRIMARY_USER_OUTCOME": "The primary user outcome recorded in MAP.md.",
        "MOST_IMPORTANT_FAILURE_TO_PREVENT": "Incorrect behavior, unsafe state changes, or silent data loss.",
        "PUBLIC_OR_PERSISTED_CONTRACT_TO_PRESERVE": "Documented interfaces, schemas, files, and migration promises.",
        "RISK | critical/high/normal/low | TESTS_OR_MANUAL_EVIDENCE": "Undocumented behavioral change | high | Focused regression test plus full verification",
        "`PATH` | PURE_OR_CONTAINED_LOGIC": f"{test_locations} | Pure or contained logic",
        "`PATH` | BOUNDARIES_AND_COMPATIBILITY": f"{test_locations} | Boundaries and compatibility",
        "`PATH_OR_MANUAL` | USER_OUTCOMES": f"{test_locations} or recorded manual evidence | User outcomes",
        "YES_OR_EXCEPTIONS": "Yes; document any exception before relying on a live dependency.",
        "PATHS": test_locations,
        "METHOD": "Use fixtures and dependency boundaries; document remaining nondeterminism.",
        "REQUIREMENTS": "No special requirements detected; update when platforms or credentials are needed.",
        "LIST": "Production services, real customer data, destructive environments, and unapproved credentials.",
        "COVERAGE_OR_GAP": "Not yet characterized; update when the product boundary is defined.",
        "SCENARIO | STEPS | LOCATION_OR_REPORT": "Primary user workflow | Define before release | Retain concise result with the audit evidence",
        "GAP_OWNER_EXPIRY_AND_MITIGATION": "; ".join(notes),
    }
    assets = master / "assets" / "project"
    profile_toml = "\n".join(
        f"{name} = {json.dumps(commands, ensure_ascii=False)}" for name, commands in profiles.items()
    )
    quality_toml = (assets / ".quality" / "quality.toml").read_text(encoding="utf-8")
    quality_toml = quality_toml.replace('project = "PROJECT_NAME"', f"project = {json.dumps(project_name)}")
    quality_toml = quality_toml.replace("VERIFY_PROFILES", profile_toml)
    return {
        "AGENTS.md": (assets / "AGENTS.md").read_text(encoding="utf-8"),
        "CLAUDE.md": (assets / "CLAUDE.md").read_text(encoding="utf-8"),
        "MAP.md": render_template(assets / "MAP.md", replacements),
        "TESTING.md": render_template(assets / "TESTING.md", replacements),
        ".quality/quality.toml": quality_toml,
        "quality": (assets / "quality").read_text(encoding="utf-8"),
        ".quality/LICENSE": (master / "LICENSE").read_text(encoding="utf-8"),
    }


def write_text(path: Path, text: str, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    if executable:
        path.chmod(path.stat().st_mode | 0o111)


def managed_merge(existing: str, managed: str) -> str:
    if MANAGED_START not in managed or MANAGED_END not in managed:
        raise QualityError("managed AGENTS template is malformed")
    if MANAGED_START in existing or MANAGED_END in existing:
        if MANAGED_START not in existing or MANAGED_END not in existing:
            raise QualityError("existing AGENTS.md has an incomplete quality-code marker block")
        start = existing.index(MANAGED_START)
        end = existing.index(MANAGED_END, start) + len(MANAGED_END)
        return existing[:start].rstrip() + "\n\n" + managed.strip() + "\n" + existing[end:].lstrip()
    if existing.strip():
        return existing.rstrip() + "\n\n" + managed.strip() + "\n"
    return managed.rstrip() + "\n"


def level_two_sections(markdown: str) -> list[tuple[str, str]]:
    lines = markdown.splitlines(keepends=True)
    starts: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            starts.append((index, match.group(1).strip()))
    result: list[tuple[str, str]] = []
    for position, (index, name) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        result.append((name, "".join(lines[index:end]).rstrip()))
    return result


def merge_missing_sections(existing: str, template: str) -> str:
    known = headings(existing)
    additions = [section for name, section in level_two_sections(template) if name not in known]
    if not additions:
        return existing.rstrip() + "\n"
    return existing.rstrip() + "\n\n" + "\n\n".join(additions) + "\n"


def ensure_claude_import(existing: str) -> str:
    if CLAUDE_IMPORT in existing:
        return existing.rstrip() + "\n"
    if existing.strip():
        return f"{CLAUDE_IMPORT}\n\n{existing.lstrip()}".rstrip() + "\n"
    return f"{CLAUDE_IMPORT}\n"


def containing_git_root(root: Path) -> Path | None:
    result = git(root, "rev-parse", "--show-toplevel", check=False)
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip()).resolve()


def ensure_git(root: Path) -> tuple[Path, bool]:
    existing = containing_git_root(root)
    if existing is not None:
        return existing, False
    git(root, "init", "--quiet")
    return root, True


def preflight_wrapper(root: Path, wrapper: str) -> None:
    path = root / "quality"
    if not path.exists():
        return
    existing = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    if "quality-code managed wrapper" not in existing and existing != wrapper:
        raise QualityError(f"{path} already exists and is not managed by quality-code; rename it before adoption")


def bootstrap(root_arg: str, mode: str) -> None:
    root = Path(root_arg).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    master = find_master_root()
    config_path = root / ".quality" / "quality.toml"
    if config_path.exists():
        if mode == "init":
            raise QualityError(f"{root} is already initialized; run quality-code upgrade or validate")
        validate(root, load_config(root))
        print(f"PASS: {root} was already adopted")
        return

    rendered = render_project(master, root)
    preflight_wrapper(root, rendered["quality"])
    # A project with no quality.toml has no established managed runtime boundary.
    # Refuse collisions before Git initialization or any project file writes.
    for relative in (".quality/quality.py", ".quality/audit-result.schema.json", ".quality/LICENSE"):
        destination = root / relative
        if destination.exists() or destination.is_symlink():
            raise QualityError(f"{destination} already exists; resolve this collision before adoption")
    git_root, created_git = ensure_git(root)

    agents_path = root / "AGENTS.md"
    existing_agents = agents_path.read_text(encoding="utf-8") if agents_path.is_file() else ""
    write_text(agents_path, managed_merge(existing_agents, rendered["AGENTS.md"]))
    claude_path = root / "CLAUDE.md"
    existing_claude = claude_path.read_text(encoding="utf-8") if claude_path.is_file() else ""
    write_text(claude_path, ensure_claude_import(existing_claude))

    for name in ("MAP.md", "TESTING.md"):
        path = root / name
        if path.is_file():
            write_text(path, merge_missing_sections(path.read_text(encoding="utf-8"), rendered[name]))
        else:
            write_text(path, rendered[name])

    write_text(config_path, rendered[".quality/quality.toml"])
    write_text(root / ".quality/LICENSE", rendered[".quality/LICENSE"])
    shutil.copy2(master / "scripts" / "quality_code.py", root / ".quality" / "quality.py")
    (root / ".quality" / "quality.py").chmod(0o755)
    shutil.copy2(
        master / "assets" / "project" / ".quality" / "audit-result.schema.json",
        root / ".quality" / "audit-result.schema.json",
    )
    write_text(root / "quality", rendered["quality"], executable=True)

    validate(root, load_config(root))
    if created_git:
        print(f"PASS: initialized Git at {root}")
    elif git_root != root:
        print(f"PASS: reused parent Git repository {git_root}; no nested repository was created")
    else:
        print(f"PASS: reused existing Git repository {git_root}")
    print(f"PASS: {mode} completed for {root}")


def update_standard_version(text: str) -> str:
    # Preserve formatting, but verify the complete parsed configuration rather
    # than assuming that a textual match belongs to the root version setting.
    try:
        original = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise QualityError(f"cannot parse quality.toml before migration: {exc}") from exc
    expected = {**original, "standard_version": STANDARD_VERSION}
    if "standard_version" not in original:
        return f"standard_version = {STANDARD_VERSION}\n" + text
    if type(original["standard_version"]) is not int:
        raise QualityError("standard_version must be a TOML integer before migration")
    pattern = (
        r"^([ \t]*(?:standard_version|\"standard_version\"|'standard_version')[ \t]*=[ \t]*)"
        r"[+-]?(?:0[xX][0-9A-Fa-f_]+|0[oO][0-7_]+|0[bB][01_]+|[0-9][0-9_]*)"
        r"([ \t]*(?:#[^\r\n]*)?\r?)$"
    )
    for match in re.finditer(pattern, text, re.MULTILINE):
        candidate = (text[:match.start()] + match.group(1) + str(STANDARD_VERSION)
                     + match.group(2) + text[match.end():])
        try:
            if tomllib.loads(candidate) == expected:
                return candidate
        except tomllib.TOMLDecodeError:
            continue
    raise QualityError("cannot safely migrate standard_version formatting; normalize its root assignment before upgrade")


def ensure_audit_threshold(text: str) -> str:
    if re.search(r"^independent_audit_min_risk\s*=", text, re.MULTILINE):
        return text
    updated, count = re.subn(
        r"^(\[audit\][ \t]*)$",
        rf'\1\nindependent_audit_min_risk = "high"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise QualityError("quality.toml is missing the [audit] table")
    return updated


def migrate_project_policy(name: str, text: str) -> str:
    if name == "MAP.md":
        return text.replace(
            "Behavioral fixes require regression evidence and an independent audit.",
            "Behavioral fixes require proportionate regression evidence; high-risk changes require an independent audit.",
        )
    if name == "TESTING.md":
        return text.replace(
            "Builder self-validation is mandatory but never replaces the fresh-agent audit.",
            "Builder self-validation is mandatory for every change. When the independent gate applies, it cannot be replaced by builder self-review.",
        )
    return text


def upgrade(root_arg: str, dry_run: bool) -> None:
    master = find_master_root()
    root = find_project_root(Path(root_arg).expanduser())
    rendered = render_project(master, root)
    config_path = root / ".quality" / "quality.toml"
    # Preflight migration before dry-run output or any managed-file writes.
    config_text = ensure_audit_threshold(update_standard_version(config_path.read_text(encoding="utf-8")))
    actions = [
        "refresh managed AGENTS.md block",
        "ensure CLAUDE.md imports AGENTS.md",
        "add missing MAP.md and TESTING.md standard sections without replacing project content",
        "refresh project-local quality engine, schema, and wrapper",
        f"set standard_version to {STANDARD_VERSION}",
        "set the independent audit threshold to high when missing",
    ]
    if dry_run:
        print(json.dumps({"project": str(root), "dry_run": True, "actions": actions}, indent=2))
        return

    license_path = root / ".quality/LICENSE"
    if license_path.exists() and license_path.read_text(encoding="utf-8").strip() != rendered[".quality/LICENSE"].strip():
        raise QualityError(f"{license_path} contains an unrelated notice; resolve this collision before upgrade")
    preflight_wrapper(root, rendered["quality"])
    write_text(license_path, rendered[".quality/LICENSE"])
    agents_path = root / "AGENTS.md"
    write_text(
        agents_path,
        managed_merge(agents_path.read_text(encoding="utf-8") if agents_path.is_file() else "", rendered["AGENTS.md"]),
    )
    claude_path = root / "CLAUDE.md"
    write_text(
        claude_path,
        ensure_claude_import(claude_path.read_text(encoding="utf-8") if claude_path.is_file() else ""),
    )
    for name in ("MAP.md", "TESTING.md"):
        path = root / name
        existing = path.read_text(encoding="utf-8") if path.is_file() else ""
        existing = migrate_project_policy(name, existing)
        write_text(path, merge_missing_sections(existing, rendered[name]) if existing else rendered[name])

    write_text(config_path, config_text)
    shutil.copy2(master / "scripts" / "quality_code.py", root / ".quality" / "quality.py")
    (root / ".quality" / "quality.py").chmod(0o755)
    shutil.copy2(
        master / "assets" / "project" / ".quality" / "audit-result.schema.json",
        root / ".quality" / "audit-result.schema.json",
    )
    preflight_wrapper(root, rendered["quality"])
    write_text(root / "quality", rendered["quality"], executable=True)
    validate(root, load_config(root))
    print(f"PASS: upgraded {root} to quality-code standard {STANDARD_VERSION}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=".", help="project path or any path beneath it")
    subparsers = parser.add_subparsers(dest="command", required=True)
    initialize = subparsers.add_parser("init", help="initialize a new project and its Git boundary")
    initialize.add_argument("path", nargs="?", default=".")
    adopt = subparsers.add_parser("adopt", help="adopt an existing project without replacing its content")
    adopt.add_argument("path", nargs="?", default=".")
    upgrade_parser = subparsers.add_parser("upgrade", help="upgrade managed standard files")
    upgrade_parser.add_argument("path", nargs="?", default=".")
    upgrade_parser.add_argument("--dry-run", action="store_true")
    subparsers.add_parser("validate", help="validate project quality files")
    verify = subparsers.add_parser("verify", help="run a configured verification profile")
    verify.add_argument("profile")
    context = subparsers.add_parser("context", help="print risk routing for named paths")
    context.add_argument("paths", nargs="+")
    audit_packet = subparsers.add_parser("audit-packet", help="generate a compact audit handoff")
    audit_packet.add_argument("--base", help="Git base; defaults to quality.toml")
    audit_packet.add_argument(
        "--force",
        action="store_true",
        help="allow a low- or normal-risk packet only when the user explicitly requested an audit",
    )
    criteria_group = audit_packet.add_mutually_exclusive_group(required=True)
    criteria_group.add_argument("--criteria")
    criteria_group.add_argument("--criteria-file")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command in {"init", "adopt"}:
            bootstrap(args.path, args.command)
            return 0
        if args.command == "upgrade":
            upgrade(args.path, args.dry_run)
            return 0

        root = find_project_root(Path(args.project))
        config = load_config(root)
        if args.command == "validate":
            validate(root, config)
        elif args.command == "verify":
            run_profile(root, args.profile, command_profiles(config))
        elif args.command == "context":
            areas = matching_areas(args.paths, configured_areas(config))
            risk = highest_risk(areas)
            print(
                json.dumps(
                    {
                        "paths": args.paths,
                        "risk": risk,
                        "independent_audit_min_risk": audit_threshold(config),
                        "independent_audit_required": independent_audit_required(config, risk),
                        "areas": [area.get("name", "unnamed") for area in areas],
                        "map_sections": unique_strings(
                            [section for area in areas for section in area.get("map_sections", [])]
                        ),
                        "tests": unique_strings([test for area in areas for test in area.get("tests", [])]),
                    },
                    indent=2,
                )
            )
        elif args.command == "audit-packet":
            base = args.base or config.get("audit", {}).get("default_base", "HEAD")
            print(json.dumps(packet(root, config, base, read_criteria(args), force=args.force), indent=2))
        return 0
    except QualityError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
