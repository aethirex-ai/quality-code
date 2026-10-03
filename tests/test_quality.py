from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


engine = module('quality_engine', 'quality_code.py')
installer = module('quality_installer', 'install.py')


class QualityIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='quality-code-test-')
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / 'project'
        self.project.mkdir()

    def cli(self, *args, expected=0):
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/quality_code.py'), *args],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def init(self):
        self.cli('init', str(self.project))

    def local(self, *args, expected=0):
        return self.cli('--project', str(self.project), *args, expected=expected)

    def test_init_creates_valid_local_project(self):
        self.init()
        self.local('validate')
        self.assertTrue((self.project / '.git').is_dir())
        self.assertEqual((self.project / '.quality/quality.py').read_bytes(),
                         (ROOT / 'scripts/quality_code.py').read_bytes())
        self.assertIn('No automated product test', (self.project / 'TESTING.md').read_text())

    def test_adopt_preserves_custom_sections_and_instructions(self):
        fixtures = {'AGENTS.md': '# Local rules\nKeep my code.\n',
                    'MAP.md': '# Map\n\n## Product boundary\nMy original boundary.\n',
                    'CLAUDE.md': 'Keep Claude guidance.\n',
                    'TESTING.md': '# Tests\n\n## Known gaps and residual risk\nMy gap.\n'}
        for name, text in fixtures.items():
            (self.project / name).write_text(text)
        self.cli('adopt', str(self.project))
        for name, text in (('AGENTS.md', 'Keep my code.'), ('MAP.md', 'My original boundary.'),
                           ('CLAUDE.md', 'Keep Claude guidance.'), ('TESTING.md', 'My gap.')):
            self.assertIn(text, (self.project / name).read_text())
        self.assertEqual((self.project / 'MAP.md').read_text().count('## Product boundary'), 1)
        before = {f: f.read_bytes() for f in self.project.rglob('*') if f.is_file() and '.git' not in f.parts}
        self.cli('adopt', str(self.project))
        self.assertEqual(before, {f: f.read_bytes() for f in before})

    def test_collision_refuses_unmanaged_wrapper_without_writes(self):
        (self.project / 'quality').write_text('my executable')
        self.cli('adopt', str(self.project), expected=2)
        self.assertEqual((self.project / 'quality').read_text(), 'my executable')
        self.assertFalse((self.project / 'AGENTS.md').exists())

    def test_reuses_parent_git_boundary(self):
        subprocess.run(['git', 'init', '--quiet', self.temp.name], check=True)
        self.init()
        self.assertFalse((self.project / '.git').exists())

    def test_security_route_requires_independent_audit(self):
        self.init()
        result = json.loads(self.local('context', 'src/auth/session.py').stdout)
        self.assertEqual(result['risk'], 'critical')
        self.assertTrue(result['independent_audit_required'])
        self.assertIn('Contracts and state', result['map_sections'])

    def test_normal_route_does_not_require_independent_audit(self):
        self.init()
        result = json.loads(self.local('context', 'src/view.py').stdout)
        self.assertEqual(result['risk'], 'normal')
        self.assertFalse(result['independent_audit_required'])

    def test_highest_specific_risk_wins(self):
        areas = [{'name': 'fallback', 'paths': ['**'], 'risk': 'critical', 'fallback': True},
                 {'name': 'high', 'paths': ['src/**'], 'risk': 'high'},
                 {'name': 'critical', 'paths': ['src/auth/**'], 'risk': 'critical'}]
        for path, expected in [('src/auth/a.py', 'critical'), ('src/view.py', 'high'), ('other.py', 'critical')]:
            self.assertEqual(engine.highest_risk(engine.matching_areas([path], areas)), expected)

    def test_mixed_paths_retain_unmatched_fallback_risk(self):
        areas = [{"name": "fallback", "paths": ["**"], "risk": "critical", "fallback": True,
                  "required_profiles": ["release"]},
                 {"name": "view", "paths": ["src/**"], "risk": "normal", "required_profiles": []}]
        matched = engine.matching_areas(["src/view.py", "unrouted-payment.py"], areas)
        self.assertEqual(engine.highest_risk(matched), "critical")
        self.assertEqual({a["name"] for a in matched}, {"fallback", "view"})
        config = {"audit": {"required_profiles_by_risk": {"critical": ["full"]}}}
        self.assertEqual(engine.select_profiles(config, "critical", matched), ["full", "release"])

    def test_parent_git_packet_is_project_relative_and_scoped(self):
        parent = Path(self.temp.name)
        subprocess.run(["git", "init", "--quiet", str(parent)], check=True)
        self.init()
        (self.project / "src/auth").mkdir(parents=True)
        auth = self.project / "src/auth/session.py"
        auth.write_text("# before\n")
        sibling = parent / "sibling.txt"
        sibling.write_text("before\n")
        subprocess.run(["git", "add", "."], cwd=parent, check=True)
        subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                        "commit", "--quiet", "-m", "Fixture baseline"], cwd=parent, check=True)
        auth.write_text("# after\n")
        sibling.write_text("after\n")
        result = json.loads(self.local("audit-packet", "--criteria", "Reject expired sessions").stdout)
        self.assertEqual(result["changed_files"], ["src/auth/session.py"])
        self.assertEqual(result["risk"], "critical")
        self.assertEqual(set(result["required_profiles"]), {"full", "release"})
        diff = subprocess.run(result["diff_commands"][0], cwd=self.project,
                              text=True, capture_output=True, check=True).stdout
        self.assertIn("src/auth/session.py", diff)
        self.assertNotIn("sibling.txt", diff)
        (self.project / "new.txt").write_text("new\n")
        (parent / "unrelated.txt").write_text("unrelated\n")
        result = json.loads(self.local("audit-packet", "--criteria", "Reject expired sessions").stdout)
        self.assertEqual(result["untracked_files_to_read"], ["new.txt"])

    def test_runtime_and_license_collisions_preserve_every_file(self):
        for relative in (".quality/quality.py", ".quality/audit-result.schema.json", ".quality/LICENSE"):
            with self.subTest(relative=relative):
                collision = self.project / relative
                collision.parent.mkdir(exist_ok=True)
                collision.write_text("Original unrelated content\n")
                before = {f: f.read_bytes() for f in self.project.rglob("*") if f.is_file()}
                self.cli("adopt", str(self.project), expected=2)
                self.assertEqual(before, {f: f.read_bytes() for f in self.project.rglob("*") if f.is_file()})
                self.assertFalse((self.project / ".git").exists())
                collision.unlink()

    def test_generated_project_retains_license_notice(self):
        self.init()
        self.assertEqual((self.project / ".quality/LICENSE").read_bytes(), (ROOT / "LICENSE").read_bytes())
        (self.project / ".quality/LICENSE").unlink()
        self.cli("upgrade", str(self.project))
        self.assertEqual((self.project / ".quality/LICENSE").read_bytes(), (ROOT / "LICENSE").read_bytes())


    def test_packet_includes_untracked_files_and_criteria(self):
        self.init()
        (self.project / 'src/auth').mkdir(parents=True)
        (self.project / 'src/auth/session.py').write_text('# synthetic fixture\n')
        result = json.loads(self.local('audit-packet', '--criteria', 'Reject expired sessions').stdout)
        self.assertEqual(result['risk'], 'critical')
        self.assertEqual(result['acceptance_criteria'], 'Reject expired sessions')
        self.assertIn('src/auth/session.py', result['untracked_files_to_read'])
        self.assertEqual(set(result['required_profiles']), {'full', 'release'})

    def test_normal_packet_requires_explicit_force(self):
        self.init()
        self.local('audit-packet', '--criteria', 'A visible change', expected=2)
        result = json.loads(self.local('audit-packet', '--force', '--criteria', 'A visible change').stdout)
        self.assertTrue(result['audit_forced'])

    def test_empty_criteria_rejected(self):
        self.init()
        self.local('audit-packet', '--force', '--criteria', ' ', expected=2)

    def test_verification_failure_stops_later_commands(self):
        marker = self.project / 'should-not-exist'
        profiles = {'full': [[sys.executable, '-c', 'raise SystemExit(9)'],
                             [sys.executable, '-c', "from pathlib import Path; Path('should-not-exist').touch()"]]}
        with self.assertRaises(engine.QualityError):
            engine.run_profile(self.project, 'full', profiles)
        self.assertFalse(marker.exists())

    def test_unknown_profile_is_not_a_pass(self):
        self.init()
        self.local('verify', 'missing', expected=2)

    def test_upgrade_preserves_custom_config_and_map(self):
        self.init()
        config = self.project / '.quality/quality.toml'
        config.write_text(config.read_text().replace('map_word_limit = 900', 'map_word_limit = 1200'))
        map_file = self.project / 'MAP.md'
        map_file.write_text(map_file.read_text() + '\n## Custom boundary\nKeep this.\n')
        before = {f: f.read_bytes() for f in self.project.rglob('*') if f.is_file() and '.git' not in f.parts}
        self.cli('upgrade', '--dry-run', str(self.project))
        self.assertEqual(before, {f: f.read_bytes() for f in before})
        self.cli('upgrade', str(self.project))
        self.assertIn('map_word_limit = 1200', config.read_text())
        self.assertIn('Keep this.', map_file.read_text())
        self.local('validate')

    def test_installer_isolated_home_and_distribution(self):
        home = Path(self.temp.name) / 'home'
        (home / '.codex').mkdir(parents=True)
        (home / '.codex/AGENTS.md').write_text('Keep global rules.\n')
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/install.py'), '--home', str(home)],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Keep global rules.', (home / '.codex/AGENTS.md').read_text())
        for agent in ('.codex', '.claude'):
            skill = home / agent / 'skills/audit-code-change'
            self.assertEqual({f.name for f in skill.iterdir()}, {'LICENSE', 'SKILL.md', 'agents', 'assets', 'references', 'scripts'})
            self.assertFalse((skill / '.git').exists())
            self.assertEqual((skill / 'LICENSE').read_bytes(), (ROOT / 'LICENSE').read_bytes())
            self.assertEqual((skill / 'assets/project/AGENTS.md').read_bytes(),
                             (ROOT / 'assets/project/AGENTS.md').read_bytes())
        self.assertTrue((home / '.local/bin/quality-code').is_symlink())
        settings = json.loads((home / '.claude/settings.json').read_text())
        self.assertEqual(settings['skillOverrides']['audit-code-change'], 'name-only')

    def test_delegation_policy_delivered_by_init_and_adopt(self):
        template = (ROOT / 'assets/project/AGENTS.md').read_text()
        for command in ('init', 'adopt'):
            with self.subTest(command=command):
                project = Path(self.temp.name) / command
                project.mkdir()
                (project / 'AGENTS.md').write_text('# Local rules\nPreserve local instruction.\n')
                self.cli(command, str(project))
                delivered = (project / 'AGENTS.md').read_text()
                self.assertIn(template.strip(), delivered)
                self.assertIn('Preserve local instruction.', delivered)

    def test_v2_upgrade_delivers_policy_and_preserves_custom_context(self):
        self.init()
        agents = self.project / 'AGENTS.md'
        old = (ROOT / 'assets/project/AGENTS.md').read_text()
        start = old.index('## Efficient delegation and model selection')
        end = old.index('For review, diagnosis, or planning', start)
        old = old[:start] + old[end:]
        agents.write_text('Before managed block.\n\n' + old + '\nAfter managed block.\n')
        config = self.project / '.quality/quality.toml'
        config.write_text(config.read_text().replace('standard_version = 3', 'standard_version = 2'))
        before_config = engine.load_config(self.project)
        self.local('validate', expected=2)
        before_agents = agents.read_bytes()
        self.cli('upgrade', '--dry-run', str(self.project))
        self.assertEqual(agents.read_bytes(), before_agents)
        self.cli('upgrade', str(self.project))
        after = agents.read_text()
        self.assertIn((ROOT / 'assets/project/AGENTS.md').read_text().strip(), after)
        self.assertIn('Before managed block.', after)
        self.assertIn('After managed block.', after)
        after_config = engine.load_config(self.project)
        self.assertEqual(after_config['standard_version'], 3)
        self.assertEqual(before_config['verify'], after_config['verify'])
        self.assertEqual((self.project / '.quality/quality.py').read_bytes(),
                         (ROOT / 'scripts/quality_code.py').read_bytes())
        self.local('validate')


    def v2_project_from_public_baseline(self):
        # Frozen source from the published v2 commit works offline, including
        # shallow CI checkouts with no historical Git objects.
        baseline = ROOT / 'tests/fixtures/v2'
        subprocess.run([sys.executable, '-B', str(baseline / 'scripts/quality_code.py'),
                        'init', str(self.project)], capture_output=True, check=True)
        return baseline

    def test_real_v2_upgrade_preserves_commented_configuration(self):
        self.v2_project_from_public_baseline()
        config = self.project / '.quality/quality.toml'
        config.write_text(config.read_text().replace('standard_version = 2',
                                                    'standard_version = 2 # custom installation'))
        original = engine.load_config(self.project)
        self.cli('upgrade', str(self.project))
        self.assertIn('standard_version = 3 # custom installation', config.read_text())
        expected = {**original, 'standard_version': 3}
        self.assertEqual(engine.load_config(self.project), expected)
        result = subprocess.run([sys.executable, '-B', str(self.project / '.quality/quality.py'),
                                 '--project', str(self.project), 'validate'], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_upgrade_rejects_unsupported_assignment_before_writes(self):
        self.v2_project_from_public_baseline()
        config = self.project / '.quality/quality.toml'
        # A valid escaped TOML key has the same parsed meaning, but cannot be
        # safely located by this migration's supported textual assignment forms.
        config.write_text(config.read_text().replace('standard_version = 2',
                                                    r'"standard_\u0076ersion" = 2'))
        self.assertEqual(engine.load_config(self.project)['standard_version'], 2)
        before = {f: f.read_bytes() for f in self.project.rglob('*') if f.is_file() and '.git' not in f.parts}
        self.cli('upgrade', str(self.project), expected=2)
        self.assertEqual(before, {f: f.read_bytes() for f in before})

    def test_version_migration_preserves_valid_assignment_formats(self):
        for assignment in ('  standard_version = +2 # retain', '"standard_version" = 0x2 # retain',
                           "'standard_version' = 0b10 # retain"):
            with self.subTest(assignment=assignment):
                original = 'version = 1\n' + assignment + '\n[verify]\nfast = [["true"]]\n'
                updated = engine.update_standard_version(original)
                self.assertEqual(engine.tomllib.loads(updated),
                                 {**engine.tomllib.loads(original), 'standard_version': 3})
                self.assertIn('# retain', updated)


    def test_global_merge_is_idempotent_and_retains_surrounding_text(self):
        first = installer.merge_block('My policy.\n')
        self.assertEqual(installer.merge_block(first), first)
        self.assertIn('My policy.', first)
        with self.assertRaises(installer.InstallError):
            installer.merge_block(installer.GLOBAL_START)


if __name__ == '__main__':
    unittest.main()
