#!/usr/bin/env python3
"""Offline checks for the public ServiceFlow visual-trial projection."""
import hashlib
import json
import math
import pathlib
import re
import shutil
import subprocess
import tempfile
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

CASE = pathlib.Path(__file__).resolve().parent
ROOT = CASE.parents[1]
DOCS = ROOT / 'docs/benchmarks' / CASE.name


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def within(base, relative):
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()):
        raise ValueError('Path escapes declared artifact boundary')
    return path


def validate_results(data):
    assert data['prompt_sha256'] == hashlib.sha256(data['prompt'].encode()).hexdigest(), 'Prompt hash mismatch'
    assert {a['id'] for a in data['apps']} == {'single', 'adaptive'}, 'Both conditions required'
    for app in data['apps']:
        assert app['initial_seconds'] > 0
        for key in ['initial_usage', 'total_usage']:
            usage = app.get(key)
            if usage is not None:
                assert 0 <= usage['cached_input_tokens'] <= usage['input_tokens'], 'Cached input is a subset'
                assert 0 <= usage.get('reasoning_output_tokens', 0) <= usage['output_tokens'], 'Reasoning is a subset'
                assert usage['input_tokens'] + usage['output_tokens'] == usage['total_tokens'], 'Total tokens mismatch'
        identities = set()
        for shot in app['captures']:
            identity = (shot['stage'], shot['screen'], shot['css_viewport_width'])
            assert identity not in identities, 'Duplicate capture state'
            identities.add(identity)
            assert shot['condition'] == app['id'], 'Capture condition mismatch'
            assert 0 < shot.get('display_canvas_ratio', 1) <= 1, 'Invalid display clipping ratio'
        if data['complete']:
            assert app['final_verdict'] == 'PASS', 'Complete requires final PASS'
            assert app.get('final_capture_status') == 'PASS', 'Complete requires accepted final captures'
            assert all(shot.get('gate_status') == 'PASS' for shot in app['captures'] if shot['stage'] == 'accepted'), 'Accepted captures require final review'
            assert app['acceptance_wall_seconds'] > 0 and app['total_usage'] is not None
            assert app['total_text_proxy_usd'] is not None
            assert app.get('broad_gate_verdict') == 'PASS' and app.get('supplemental_review_verdict') == 'PASS', 'Both review layers must pass'
            if app['id'] == 'single':
                assert app.get('publication_followup_verdict') == 'PASS' and app.get('publication_followup_result_sha256'), 'Late Single correction requires focused acceptance'
            phases = app.get('phase_breakdown')
            assert phases, 'Complete requires phase accounting'
            for phase in phases:
                assert {x['model'] for x in phase['model_settings']} == set(phase['models']), 'Missing observed model settings'
                assert all(x['reasoning_effort'] == ('high' if x['model'] == 'gpt-6.1-sol' else 'medium') for x in phase['model_settings']), 'Observed effort mismatch'
            for counter in ['input_tokens', 'cached_input_tokens', 'output_tokens', 'reasoning_output_tokens', 'total_tokens']:
                assert sum(phase['usage'][counter] for phase in phases) == app['total_usage'][counter], 'Phase counters do not reconcile'
            assert math.isclose(sum(phase['text_proxy_usd'] for phase in phases), app['total_text_proxy_usd'], abs_tol=1e-7), 'Phase prices do not reconcile'
            assert math.isclose(sum(phase['native_seconds'] for phase in phases), app['native_phase_seconds'], abs_tol=1e-5), 'Phase duration mismatch'
            assert math.isclose(app['native_phase_seconds'] + app['parent_interphase_gap_seconds'], app['acceptance_wall_seconds'], abs_tol=1e-5), 'Wall interval does not reconcile'
            required = {(stage, screen['id'], width) for stage in ['before', 'initial', 'accepted'] for screen in data['screens'] for width in [1440, 375]}
            assert required <= identities, 'Complete requires desktop/mobile captures at every stage'
        else:
            assert app['total_usage'] is None and app['acceptance_wall_seconds'] is None and app['total_text_proxy_usd'] is None, 'Pending final totals must be unset'
            assert app['final_verdict'] != 'PASS', 'Pending must not claim final PASS'
            assert all(s.get('gate_status') == 'pending-independent-review' for s in app['captures'] if s['stage'] == 'accepted'), 'Pending final-slot captures need explicit pending status'


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
        self.ids = set()
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            assert attrs['id'] not in self.ids, 'Duplicate HTML ID'
            self.ids.add(attrs['id'])
        for attr in ['href', 'src']:
            if attr in attrs:
                self.urls.append(attrs[attr])


def validate_links():
    parser = Links()
    parser.feed((DOCS / 'index.html').read_text())
    for url in parser.urls:
        part = urlsplit(url)
        if part.scheme or part.netloc:
            continue
        if not part.path:
            assert not part.fragment or part.fragment in parser.ids, 'Broken same-page anchor'
            continue
        target = (DOCS / unquote(part.path)).resolve()
        assert target.is_relative_to(ROOT) and target.exists(), 'Missing local link: ' + url


def validate_sources(complete=False):
    manifests = sorted((CASE / 'source').glob('*/*/manifest.json'))
    assert manifests, 'Missing source projections'
    inventory = json.loads((CASE / 'source-inventory.json').read_text())['stages']
    for item in inventory:
        if item['stage'] == 'accepted':
            assert item.get('gate_status') == ('PASS' if complete else 'pending-independent-review'), 'Inventory status must match trial acceptance'
    stages = {(item['condition'], item['stage']): {x['path']: x['sha256'] for x in item['files']} for item in inventory}
    for condition in ['single', 'adaptive']:
        original = ROOT / 'benchmarks/serviceflow-mvp-2026-10/apps' / condition
        for relative, expected in stages[(condition, 'before')].items():
            assert digest(within(original, relative)) == expected, 'Original inventory mismatch'
    for path in manifests:
        manifest = json.loads(path.read_text())
        if path.parent.name == 'accepted':
            assert manifest.get('gate_status') == ('PASS' if complete else 'pending-independent-review'), 'Final source status must match trial acceptance'
        patch = within(path.parent, manifest['patch'])
        assert digest(patch) == manifest['patch_sha256'], 'Patch byte mismatch'
        condition = path.parent.parent.name
        original = ROOT / 'benchmarks/serviceflow-mvp-2026-10/apps' / condition
        reconstructed = dict(stages[(condition, 'before')])
        for entry in manifest['source_changes'] + manifest['assets']:
            if entry['after_sha256'] is None:
                reconstructed.pop(entry['path'], None)
            else:
                reconstructed[entry['path']] = entry['after_sha256']
        assert reconstructed == stages[(condition, path.parent.name)], 'Complete UI inventory differs from projection'
        with tempfile.TemporaryDirectory(prefix='serviceflow-public-replay-') as temporary:
            stage = pathlib.Path(temporary)
            for entry in manifest['source_changes']:
                relative = entry['path']
                assert relative == 'index.html' or relative.startswith(('src/client/', 'public/')), 'Unexpected source path'
                source = within(original, relative)
                if entry['before_sha256'] is not None:
                    assert digest(source) == entry['before_sha256'], 'Original source changed'
                    target = within(stage, relative)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, target)
            subprocess.run(['git', 'apply', '--check', str(patch)], cwd=stage, check=True, capture_output=True)
            subprocess.run(['git', 'apply', str(patch)], cwd=stage, check=True, capture_output=True)
            for entry in manifest['source_changes']:
                output = within(stage, entry['path'])
                assert (digest(output) if output.exists() else None) == entry['after_sha256'], 'Source reconstruction mismatch'
        for asset in manifest['assets']:
            base = CASE if manifest.get('asset_paths_relative_to') == 'case directory' else path.parent
            assert digest(within(base, asset['asset'])) == asset['after_sha256'], 'Asset mismatch'


def validate_publication():
    data = json.loads((DOCS / 'results.json').read_text())
    validate_results(data)
    inventory = json.loads((DOCS / 'capture-provenance.json').read_text())
    referenced = [s for a in data['apps'] for s in a['captures']]
    assert sorted(inventory, key=lambda s: s['url']) == sorted(referenced, key=lambda s: s['url']), 'Capture inventory differs from gallery data'
    assert len({s['url'] for s in inventory}) == len(inventory), 'Capture URL reused'
    supplemental = json.loads((DOCS / 'supplemental-capture-provenance.json').read_text())
    assert {(x['screen'], x['css_viewport_width']) for x in supplemental} == {('privacy', 1440), ('privacy', 375)}, 'Missing supplemental privacy renders'
    for shot in inventory + supplemental:
        assert digest(within(DOCS, shot['url'])) == shot['sha256'], 'Capture byte mismatch'
    assert not (DOCS / 'single-data.json').exists(), 'Obsolete result payload exposed'
    forbidden = re.compile(r'/Users/|/private/(?:tmp|var)/|(?:sk-proj-|sk-live-|Bearer\s+[A-Za-z0-9._-]{16})|\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b')
    for base in [CASE, DOCS]:
        for path in base.rglob('*'):
            if path.is_file() and path.suffix in {'.json', '.md', '.html', '.js', '.css', '.patch'}:
                assert not forbidden.search(path.read_text()), 'Private pattern in ' + path.relative_to(ROOT).as_posix()
    validate_links()
    validate_sources(data['complete'])
    return len(inventory) + len(supplemental)


if __name__ == '__main__':
    count = validate_publication()
    print(f'PASS: {count} exact capture bytes, source reconstruction, links, privacy patterns and result invariants. Visual/functional/independent gates remain separate.')
