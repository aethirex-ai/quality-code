from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "quality_code.py"


def load_engine():
    spec = importlib.util.spec_from_file_location("quality_modules_engine", SCRIPT)
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    return engine


engine = load_engine()


class ModuleCompositionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="quality-modules-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        self.root.mkdir()

    def cli(self, *args, expected=0):
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), *args],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def config(self):
        return engine.load_config(self.root)

    def snapshot(self):
        return {path.relative_to(self.root): path.read_bytes()
                for path in self.root.rglob("*") if path.is_file() and ".git" not in path.parts}

    def budget_map(self, *, omit=()):
        sections = [
            "# UI Annotate architecture map",
            "## Product boundary\nExisting UI product boundary and architecture detail.",
            "## Runtime flow\nExisting runtime flow detail.",
            "## Contracts and state\nExisting state and contract detail.",
            "## Security, privacy, and safety\nExisting security detail.",
            "## Change invariants\nExisting invariants detail.",
            "## Verification\nExisting verification detail.",
            "## Quality-code standards\nRetain this local section exactly.",
            "## Generated inventory\nRetain the local generated inventory guidance.",
            "## Ownership and context routing\nRetain this combined local section.",
        ]
        sections = [section for section in sections
                    if not any(section.startswith(f"## {name}\n") for name in omit)]
        text = "\n\n".join(sections) + "\n\n"
        padding_count = 1300 - len(text.split())
        self.assertGreater(padding_count, 0)
        text += " ".join(f"existingdetail{i}" for i in range(padding_count)) + "\n"
        self.assertEqual(len(text.split()), 1300)
        return text

    def test_parse_modules_canonicalizes_and_rejects_invalid_values(self):
        self.assertEqual(engine.parse_modules("swarms,code,code"), ["code", "swarms"])
        self.assertEqual(engine.parse_modules("all"), ["code", "visuals", "swarms"])
        for value in ("", ",code", "code,", "all,code", "unknown"):
            with self.subTest(value=value), self.assertRaises(engine.QualityError):
                engine.parse_modules(value)

    def test_compose_single_pair_and_all_in_canonical_order(self):
        module_dir = ROOT / "assets" / "modules"
        foundation = (module_dir / "foundation.md").read_text().strip()
        for selected in (["code"], ["visuals", "swarms"], ["code", "visuals", "swarms"]):
            with self.subTest(selected=selected):
                result = engine.compose_instructions(ROOT, selected)
                self.assertEqual(result.count(engine.MANAGED_START), 1)
                self.assertEqual(result.count(engine.MANAGED_END), 1)
                self.assertEqual(result.count(foundation), 1)
                last_position = -1
                for name in engine.MODULE_NAMES:
                    fragment = (module_dir / f"{name}.md").read_text().strip()
                    if name in selected:
                        position = result.index(fragment)
                        self.assertGreater(position, last_position)
                        last_position = position
                    else:
                        self.assertNotIn(fragment, result)

    def test_composer_rejects_malformed_selected_fragments(self):
        with self.assertRaises(engine.QualityError):
            engine.compose_instructions(ROOT, [])
        assets = self.root / "assets/modules"
        assets.mkdir(parents=True)
        (assets / "foundation.md").write_text("## Shared quality foundation\nRules.\n")
        (assets / "code.md").write_text("## Quality Code by AethDesign\nRules.\n<!-- quality-code:start -->")
        with self.assertRaises(engine.QualityError):
            engine.compose_instructions(self.root, ["code"])

    def test_init_persists_canonical_selection_and_generated_copy(self):
        self.cli("init", str(self.root), "--modules", "swarms,code,code")
        self.assertEqual(self.config()["quality_modules"], ["code", "swarms"])
        agents = (self.root / "AGENTS.md").read_text()
        module_dir = ROOT / "assets" / "modules"
        self.assertIn((module_dir / "foundation.md").read_text().strip(), agents)
        self.assertIn((module_dir / "code.md").read_text().strip(), agents)
        self.assertIn((module_dir / "swarms.md").read_text().strip(), agents)
        self.assertNotIn((module_dir / "visuals.md").read_text().strip(), agents)
        self.assertEqual((self.root / ".quality/quality.py").read_bytes(), SCRIPT.read_bytes())

    def test_invalid_selection_fails_before_creating_project_files(self):
        self.root.rmdir()
        self.cli("init", str(self.root), "--modules", "code,unknown", expected=2)
        self.assertFalse(self.root.exists())

    def test_adopt_explicit_change_requires_upgrade_and_no_flag_keeps_selection(self):
        self.cli("init", str(self.root), "--modules", "code")
        before = self.snapshot()
        self.cli("adopt", str(self.root), "--modules", "visuals", expected=2)
        self.assertEqual(before, self.snapshot())
        self.cli("adopt", str(self.root))
        self.assertEqual(self.config()["quality_modules"], ["code"])

    def test_upgrade_replaces_selection_and_preserves_custom_toml(self):
        self.cli("init", str(self.root), "--modules", "code")
        config_path = self.root / ".quality/quality.toml"
        config_path.write_text(config_path.read_text() + "\n# local comment\n[custom]\nkeep = true\n")
        self.cli("upgrade", str(self.root), "--modules", "swarms,visuals")
        self.assertEqual(self.config()["quality_modules"], ["visuals", "swarms"])
        config_text = config_path.read_text()
        self.assertIn("# local comment", config_text)
        self.assertIn("[custom]\nkeep = true", config_text)
        agents = (self.root / "AGENTS.md").read_text()
        self.assertNotIn((ROOT / "assets/modules/code.md").read_text().strip(), agents)
        self.assertIn((ROOT / "assets/modules/visuals.md").read_text().strip(), agents)
        self.assertIn((ROOT / "assets/modules/swarms.md").read_text().strip(), agents)

    def test_legacy_upgrade_defaults_to_all_without_config_rewrite(self):
        self.cli("init", str(self.root), "--modules", "code")
        config_path = self.root / ".quality/quality.toml"
        config_path.write_text("\n".join(line for line in config_path.read_text().splitlines()
                                             if not line.startswith("quality_modules =")) + "\n")
        before_config = config_path.read_bytes()
        self.cli("upgrade", str(self.root))
        self.assertNotIn("quality_modules", self.config())
        self.assertEqual(config_path.read_bytes(), before_config)
        self.assertIn((ROOT / "assets/modules/visuals.md").read_text().strip(),
                      (self.root / "AGENTS.md").read_text())

    def test_upgrade_preserves_1300_word_map_when_optional_sections_would_exceed_budget(self):
        self.cli("init", str(self.root), "--modules", "code")
        map_path = self.root / "MAP.md"
        text = self.budget_map()
        map_path.write_text(text)
        config_path = self.root / ".quality/quality.toml"
        config_path.write_text(config_path.read_text().replace("map_word_limit = 900", "map_word_limit = 1300"))
        testing_path = self.root / "TESTING.md"
        testing_before = testing_path.read_bytes()
        self.cli("upgrade", "--dry-run", str(self.root), "--modules", "visuals")
        self.assertEqual(map_path.read_text(), text)
        self.cli("upgrade", str(self.root), "--modules", "visuals")
        self.assertEqual(map_path.read_text(), text)
        self.assertEqual(len(map_path.read_text().split()), 1300)
        self.assertEqual(testing_path.read_bytes(), testing_before)
        self.assertEqual(self.config()["quality_modules"], ["visuals"])
        self.cli("--project", str(self.root), "validate")

    def test_upgrade_refuses_to_drop_route_section_when_budget_cannot_fit_it(self):
        self.cli("init", str(self.root), "--modules", "code")
        map_path = self.root / "MAP.md"
        map_path.write_text(self.budget_map(omit=("Contracts and state",)))
        config_path = self.root / ".quality/quality.toml"
        config_path.write_text(config_path.read_text().replace("map_word_limit = 900", "map_word_limit = 1300"))
        before = self.snapshot()
        self.cli("upgrade", str(self.root), "--modules", "visuals", expected=2)
        self.assertEqual(self.snapshot(), before)

    def test_blank_or_missing_map_budget_fails_in_dry_run_and_before_writes(self):
        for state in ("blank", "missing"):
            with self.subTest(state=state):
                project = Path(self.temp.name) / state
                project.mkdir()
                self.cli("init", str(project), "--modules", "code")
                map_path = project / "MAP.md"
                if state == "blank":
                    map_path.write_text("")
                else:
                    map_path.unlink()
                config_path = project / ".quality/quality.toml"
                config_path.write_text(config_path.read_text().replace(
                    "map_word_limit = 900", "map_word_limit = 100"))

                def snapshot():
                    return {path.relative_to(project): path.read_bytes()
                            for path in project.rglob("*")
                            if path.is_file() and ".git" not in path.parts}

                before = snapshot()
                dry_run = self.cli("upgrade", "--dry-run", str(project), "--modules", "visuals", expected=2)
                self.assertIn("cannot safely add required MAP.md", dry_run.stderr)
                self.assertEqual(snapshot(), before)
                actual = self.cli("upgrade", str(project), "--modules", "visuals", expected=2)
                self.assertIn("cannot safely add required MAP.md", actual.stderr)
                self.assertEqual(snapshot(), before)

    def test_dry_run_is_unchanged_and_invalid_config_fails_before_writes(self):
        self.cli("init", str(self.root), "--modules", "code")
        before = self.snapshot()
        self.cli("upgrade", "--dry-run", str(self.root), "--modules", "all")
        self.assertEqual(before, self.snapshot())
        config = self.root / ".quality/quality.toml"
        original = config.read_text()
        for bad_value in ('[]', '["not-a-module"]', '["code", "code"]', '"code"', '["code", 1]'):
            with self.subTest(bad_value=bad_value):
                config.write_text(original.replace('quality_modules = ["code"]',
                                                   f'quality_modules = {bad_value}'))
                before = self.snapshot()
                with self.assertRaises(engine.QualityError):
                    engine.load_config(self.root)
                self.cli("upgrade", str(self.root), expected=2)
                self.assertEqual(before, self.snapshot())
        config.write_text(original)

    def test_audit_packet_reports_selection_and_visual_policy(self):
        self.cli("init", str(self.root), "--modules", "visuals")
        (self.root / "src").mkdir()
        (self.root / "src/view.css").write_text("/* scoped change */\n")
        result = json.loads(subprocess.run(
            [sys.executable, "-B", str(self.root / ".quality/quality.py"), "--project", str(self.root),
             "audit-packet", "--force", "--criteria", "Report selected policy"],
            text=True, capture_output=True, check=True).stdout)
        self.assertEqual(result["quality_modules"]["selected"], ["visuals"])
        policy = result["quality_modules"]["visual_policy"]
        self.assertTrue(policy["available"])
        self.assertIn("Content and composition", policy["requirements"])
        self.assertIn("CSS filename alone does not establish that scope", policy["applicability"])

    def test_visual_scope_requests_independent_gate_without_changing_risk(self):
        self.cli("init", str(self.root), "--modules", "visuals")
        (self.root / "src").mkdir()
        (self.root / "src/view.css").write_text("/* substantial new UI */\n")
        result = json.loads(self.cli("--project", str(self.root), "audit-packet", "--visual",
                                     "--criteria", "Review the new user interface").stdout)
        self.assertEqual(result["risk"], "normal")
        self.assertTrue(result["independent_audit_required"])
        self.assertTrue(result["visual_review_required"])

    def test_visual_gate_rejects_projects_without_visual_module(self):
        self.cli("init", str(self.root), "--modules", "code")
        (self.root / "src").mkdir()
        (self.root / "src/view.css").write_text("/* change */\n")
        self.cli("--project", str(self.root), "audit-packet", "--visual",
                 "--criteria", "Review the new user interface", expected=2)


if __name__ == "__main__":
    unittest.main()
