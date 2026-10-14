from __future__ import annotations

import hashlib
import importlib.util
import json
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("standard_pack_builder", ROOT / "scripts" / "build_standard_packs.py")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)
CHECK_SPEC = importlib.util.spec_from_file_location("repository_checks", ROOT / "scripts" / "check_repository.py")
repository_checks = importlib.util.module_from_spec(CHECK_SPEC)
CHECK_SPEC.loader.exec_module(repository_checks)


class FakeEngine:
    MODULE_NAMES = ("code", "visuals", "swarms")

    def __init__(self, root: Path):
        self.root = root

    def find_master_root(self):
        return self.root

    def parse_modules(self, value: str) -> list[str]:
        if value == "all":
            return list(self.MODULE_NAMES)
        requested = value.split(",")
        if any(not part.strip() for part in requested):
            raise ValueError("empty module")
        unknown = set(requested) - set(self.MODULE_NAMES)
        if unknown:
            raise ValueError("unknown module")
        return [name for name in self.MODULE_NAMES if name in requested]

    def compose_instructions(self, _master: Path, modules: list[str]) -> str:
        return "FOUNDATION ONCE\n" + "".join(f"MODULE:{name}\n" for name in modules)


class StandardPackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="standard-packs-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "source"
        (self.root / "assets" / "project").mkdir(parents=True)
        (self.root / "assets" / "project" / "AGENTS.md").write_text("source master\n")
        (self.root / "LICENSE").write_text("test license\n")
        self.output = Path(self.temp.name) / "out"
        self.engine = FakeEngine(self.root)
        self.old_loader = builder.load_engine
        builder.load_engine = lambda: self.engine
        self.addCleanup(setattr, builder, "load_engine", self.old_loader)

    def test_default_archives_have_selected_content_and_expected_paths(self):
        paths = builder.build(self.output)
        self.assertEqual([path.name for path in paths], [
            "quality-code-by-aethdesign.zip", "quality-visuals-by-aethdesign.zip",
            "quality-swarms-by-aethdesign.zip", "quality-standards-by-aethdesign.zip",
        ])
        for path, expected in zip(paths, ("code", "visuals", "swarms", "code visuals swarms")):
            with zipfile.ZipFile(path) as archive:
                self.assertEqual(set(archive.namelist()), set(builder.ENTRY_NAMES))
                agents = archive.read("AGENTS.md").decode()
                self.assertEqual(agents.count("FOUNDATION ONCE"), 1)
                for module in self.engine.MODULE_NAMES:
                    self.assertEqual(f"MODULE:{module}" in agents, module in expected.split())
                self.assertEqual(archive.read("LICENSE"), b"test license\n")
                manifest = json.loads(archive.read("manifest.json"))
                self.assertEqual(manifest["schema"], 1)
                self.assertEqual(manifest["foundation"], "once")
                self.assertEqual(manifest["AGENTSsha256"], hashlib.sha256(archive.read("AGENTS.md")).hexdigest())

    def test_custom_pack_uses_engine_union_and_is_byte_deterministic(self):
        path, = builder.build(self.output, "swarms,code,swarms")
        with zipfile.ZipFile(path) as archive:
            self.assertEqual(json.loads(archive.read("manifest.json"))["modules"], ["code", "swarms"])
            agents = archive.read("AGENTS.md").decode()
            self.assertEqual(agents.count("FOUNDATION ONCE"), 1)
            self.assertNotIn("MODULE:visuals", agents)
        first = path.read_bytes()
        builder.build(self.output, "swarms,code,swarms")
        self.assertEqual(path.read_bytes(), first)

    def test_readme_branding_matches_the_selected_module(self):
        expected = {
            "code": "# Quality Code by AethDesign",
            "visuals": "# Quality Visuals by AethDesign",
            "swarms": "# Quality Swarms by AethDesign",
        }
        for module, heading in expected.items():
            readme = builder._readme([module])
            self.assertIn(heading, readme)
            self.assertIn("instruction-only download", readme)
            self.assertIn("does not include the executable toolkit", readme)
            self.assertIn("scripts/quality_code.py upgrade", readme)
        self.assertIn("# Quality Standards by AethDesign", builder._readme(["code", "visuals", "swarms"]))

    def test_invalid_selection_fails_before_creating_output(self):
        with self.assertRaises(ValueError):
            builder.build(self.output, "code,unknown")
        self.assertFalse(self.output.exists())

    def test_unrelated_existing_destination_is_preserved(self):
        self.output.mkdir()
        collision = self.output / "quality-code-by-aethdesign.zip"
        collision.write_bytes(b"user file")
        with self.assertRaises(builder.PackError):
            builder.build(self.output)
        self.assertEqual(collision.read_bytes(), b"user file")
        self.assertFalse((self.output / "quality-visuals-by-aethdesign.zip").exists())

    def test_symlink_output_directory_and_destination_are_refused(self):
        elsewhere = Path(self.temp.name) / "elsewhere"
        elsewhere.mkdir()
        out_link = Path(self.temp.name) / "out-link"
        out_link.symlink_to(elsewhere, target_is_directory=True)
        with self.assertRaises(builder.PackError):
            builder.build(out_link)
        self.output.mkdir()
        destination = self.output / "quality-code-by-aethdesign.zip"
        destination.symlink_to(elsewhere / "target.zip")
        with self.assertRaises(builder.PackError):
            builder.build(self.output)
        self.assertFalse((elsewhere / "target.zip").exists())


class CanonicalEnginePackTests(unittest.TestCase):
    def test_real_engine_builds_four_archives_with_exact_composition(self):
        engine = builder.load_engine()
        root = engine.find_master_root()
        with tempfile.TemporaryDirectory(prefix="canonical-packs-") as directory:
            output = Path(directory)
            paths = builder.build(output)
            self.assertEqual([path.name for path in paths], [
                "quality-code-by-aethdesign.zip", "quality-visuals-by-aethdesign.zip",
                "quality-swarms-by-aethdesign.zip", "quality-standards-by-aethdesign.zip",
            ])
            selections = (["code"], ["visuals"], ["swarms"], list(engine.MODULE_NAMES))
            first_build = [path.read_bytes() for path in paths]
            for path, modules in zip(paths, selections):
                with zipfile.ZipFile(path) as archive:
                    self.assertEqual(archive.namelist(), list(builder.ENTRY_NAMES))
                    agents = archive.read("AGENTS.md").decode("utf-8")
                    self.assertEqual(agents, engine.compose_instructions(root, modules))
                    self.assertEqual(agents.count("## Shared quality foundation"), 1)
                    for module in engine.MODULE_NAMES:
                        heading = {
                            "code": "## Quality Code by AethDesign",
                            "visuals": "## Quality Visuals by AethDesign",
                            "swarms": "## Quality Swarms by AethDesign",
                        }[module]
                        self.assertEqual(heading in agents, module in modules)
                    manifest = json.loads(archive.read("manifest.json"))
                    self.assertEqual(manifest["modules"], modules)
                    self.assertEqual(manifest["AGENTSsha256"], hashlib.sha256(archive.read("AGENTS.md")).hexdigest())
            builder.build(output)
            self.assertEqual([path.read_bytes() for path in paths], first_build)

    def test_real_engine_rejects_unknown_selection_without_creating_output(self):
        with tempfile.TemporaryDirectory(prefix="invalid-packs-") as directory:
            output = Path(directory) / "new-output"
            with self.assertRaisesRegex(RuntimeError, "unknown quality module"):
                builder.build(output, "code,unknown")
            self.assertFalse(output.exists())

    def test_real_engine_preserves_unrelated_archive_collision_without_partial_packs(self):
        with tempfile.TemporaryDirectory(prefix="collision-packs-") as directory:
            output = Path(directory)
            collision = output / "quality-visuals-by-aethdesign.zip"
            collision.write_bytes(b"unrelated archive")
            with self.assertRaises(builder.PackError):
                builder.build(output)
            self.assertEqual(collision.read_bytes(), b"unrelated archive")
            self.assertFalse((output / "quality-code-by-aethdesign.zip").exists())


class RepositoryPackChecksTests(unittest.TestCase):
    def test_full_agents_template_matches_canonical_engine_composition(self):
        self.assertEqual(repository_checks.instruction_template_errors(ROOT), [])

    def test_public_zip_freshness_check_detects_missing_stale_and_extra_archives(self):
        with tempfile.TemporaryDirectory(prefix="repository-download-check-") as directory:
            repository_root = Path(directory)
            download_dir = repository_root / "docs" / "downloads"
            download_dir.mkdir(parents=True)
            self.assertTrue(repository_checks.public_pack_freshness_errors(repository_root))
            with tempfile.TemporaryDirectory(prefix="fresh-public-packs-") as generated_dir:
                generated = builder.build(Path(generated_dir))
                for archive in generated:
                    shutil.copyfile(archive, download_dir / archive.name)
            self.assertEqual(repository_checks.public_pack_freshness_errors(repository_root), [])
            (download_dir / "quality-code-by-aethdesign.zip").write_bytes(b"stale")
            (download_dir / "extra.zip").write_bytes(b"unexpected")
            failures = repository_checks.public_pack_freshness_errors(repository_root)
            self.assertTrue(any("stale public standard pack" in failure for failure in failures))
            self.assertTrue(any("unexpected ZIP archive" in failure for failure in failures))

    def test_public_pack_freshness_rejects_symlink_artifacts(self):
        with tempfile.TemporaryDirectory(prefix="repository-download-link-") as directory:
            repository_root = Path(directory)
            download_dir = repository_root / "docs" / "downloads"
            download_dir.mkdir(parents=True)
            with tempfile.TemporaryDirectory(prefix="one-generated-pack-") as generated_dir:
                generated = builder.build(Path(generated_dir))
                for archive in generated:
                    (download_dir / archive.name).symlink_to(archive)
            failures = repository_checks.public_pack_freshness_errors(repository_root)
            self.assertTrue(any("not a regular file" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
