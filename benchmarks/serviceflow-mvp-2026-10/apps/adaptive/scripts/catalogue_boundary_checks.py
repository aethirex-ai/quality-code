"""Real browser regression for server-accepted catalogue text boundaries.
Requires the running local demo + supplied bridge; temporary synthetic services
are created as admin and deleted through the authorized API after inspection.
"""
import http.cookiejar
import json
import os
import subprocess
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:' + os.environ.get('PORTAL_PORT', '3000')
ATTEMPT = uuid.uuid4().hex
RESULTS = []


def call(opener, path, method='GET', body=None):
    headers = {'Content-Type': 'application/json', 'Origin': BASE}
    if method != 'GET':
        headers['Idempotency-Key'] = uuid.uuid4().hex
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(BASE + '/api' + path, data=data, headers=headers, method=method)
    with opener.open(request, timeout=15) as response:
        return response.status, json.load(response)


def render(name, viewport, service, admin=False):
    card = f'.service-card:has(h3:text-is("{service["name"]}"))'
    actions = []
    if admin:
        actions = [
            {'op': 'click', 'selector': "button:has-text('Admin')"},
            {'op': 'click', 'selector': "button:has-text('Sign in')"},
            {'op': 'click', 'selector': "a:has-text('Service catalogue')"},
        ]
    actions += [
        {'op': 'click', 'selector': card + ' h3'},
        {'op': 'click', 'selector': card + (' .catalogue-price' if admin else ' .service-bottom > span')},
    ]
    folder = ROOT / 'evidence'
    folder.mkdir(exist_ok=True)
    action_path = folder / f'catalogue-boundary-actions-{name}-{ATTEMPT}.json'
    action_path.write_text(json.dumps(actions, indent=2) + '\n')
    command = ['python3', 'preview_client.py', '--page', '/login' if admin else '/services', '--viewport', str(viewport), '--actions-file', str(action_path.relative_to(ROOT))]
    process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    result = json.loads(process.stdout)
    RESULTS.append({'name': name, 'viewport': viewport, 'serviceId': service['id'], 'nameLength': len(service['name']), 'descriptionLength': len(service['description']), 'priceLength': len(service['price']), 'result': result})
    for path in [folder / 'catalogue-boundary-results.json', folder / f'catalogue-boundary-attempt-{ATTEMPT}.json']:
        path.write_text(json.dumps(RESULTS, indent=2) + '\n')
    print(f'{name}: width={result.get("documentWidth")}, overflow={result.get("horizontalOverflow")}, screenshot={result.get("screenshot")}', flush=True)
    assert process.returncode == 0 and result.get('ok'), result
    assert all(action.get('ok') for action in result.get('actionResults', [])), 'Boundary service must be settled and visible'
    assert not result.get('errors') and not result.get('blockedRequests'), 'Unexpected browser/network error'
    assert not result.get('horizontalOverflow'), 'Accepted catalogue text causes horizontal overflow'
    assert result.get('documentWidth') == viewport, 'Catalogue width must stay within the viewport'


def main():
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    status, _ = call(opener, '/auth/sign-in/email', 'POST', {'email': 'admin@serviceflow.demo', 'password': 'DemoHome2026!'})
    assert status == 200
    cases = [
        ('reported-name', {'name': 'WindowRepairsAndGardenMaintenance' * 3, 'description': 'Synthetic boundary service for window repairs and garden maintenance.', 'price': 'Request a quote', 'active': True}),
        ('all-text-limits', {'name': ('WindowRepairsAndGardenMaintenance' * 3 + 'X')[:100], 'description': 'Maintenance' * 63 + 'CareNow', 'price': 'IndicativePrice' * 6 + 'QuoteLabel', 'active': True}),
    ]
    for label, data in cases:
        status, created = call(opener, '/services', 'POST', data)
        assert status == 201, 'Boundary must pass real server validation'
        service = created['service']
        try:
            assert service['name'] == data['name'] and service['description'] == data['description'] and service['price'] == data['price']
            for width in ([375, 1440] if label == 'reported-name' else [375]):
                render(f'{label}-public-{width}', width, service)
                render(f'{label}-admin-{width}', width, service, admin=True)
        finally:
            status, deleted = call(opener, f'/services/{service["id"]}?version={service["version"]}', 'DELETE', {})
            assert status == 200 and deleted['success'], 'Temporary unreferenced boundary service cleanup must succeed'
    print(f'PASS {len(RESULTS)} settled public/admin catalogue boundary renders; temporary services cleaned up.')


if __name__ == '__main__':
    main()
