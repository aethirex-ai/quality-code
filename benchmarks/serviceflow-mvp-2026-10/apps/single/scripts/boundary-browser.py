"""Real-browser regression for server-accepted maximum-length request/service text.
Requires the running local seeded app and supplied browser bridge. Synthetic only.
The added service is deactivated afterwards; its referenced snapshot/history is preserved.
"""
import datetime
import http.cookiejar
import json
import os
import subprocess
import time
import urllib.request
import uuid
from pathlib import Path

port = int(os.environ.get('PORTAL_PORT') or os.environ.get('PORT') or '3000')
origin = f'http://127.0.0.1:{port}'
client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

def api(path, method='GET', body=None):
    headers = {'Origin': origin, 'Content-Type': 'application/json', 'Idempotency-Key': str(uuid.uuid4())}
    request = urllib.request.Request(origin + '/api' + path, data=None if body is None else json.dumps(body).encode(), headers=headers, method=method)
    with client.open(request, timeout=15) as response:
        return json.load(response)

def login_actions():
    return [{'op': 'fill', 'selector': '#email', 'value': 'alex@demo.local'},
            {'op': 'fill', 'selector': '#password', 'value': 'ServiceFlow2026!'},
            {'op': 'click', 'selector': '.login-panel .button'}]

def journey(name, actions, viewport, expected):
    time.sleep(11)  # Respect the enabled production sign-in rate window.
    path = Path('evidence/actions/' + name + '.json')
    path.write_text(json.dumps(actions))
    command = ['python3', 'scripts/preview-check.py', '--id', name, '--page', '/login', '--viewport', str(viewport), '--actions-file', str(path)]
    for text in expected:
        command += ['--expect', text]
    if subprocess.call(command):
        raise SystemExit(1)

api('/auth/sign-in/email', 'POST', {'email': 'admin@demo.local', 'password': 'ServiceFlow2026!'})
service_input = {'name': 'S' * 80, 'description': 'D' * 600, 'price': 'P' * 80, 'category': 'repair', 'active': True}
service = api('/services', 'POST', service_input)
marker = 'AUD-004 boundary ' + uuid.uuid4().hex + ': '
description = marker + 'W' * (2000 - len(marker))
fields = {'description': description, 'location': 'L' * 160, 'preferredFrom': (datetime.date.today() + datetime.timedelta(days=14)).isoformat(), 'contactName': 'N' * 100, 'contactEmail': 'e' * 50 + '@' + 'd' * 50 + '.' + 'f' * 52 + '.local', 'contactPhone': '7' * 30}
try:
    actions = login_actions() + [{'op': 'click', 'selector': '.page-intro a.button'}, {'op': 'select', 'selector': '#serviceId', 'value': service['id']}]
    actions += [{'op': 'fill', 'selector': '#' + name, 'value': value} for name, value in fields.items()]
    actions += [{'op': 'click', 'selector': '.form-submit .button'}, {'op': 'click', 'selector': '.detail-heading'}, {'op': 'click', 'selector': '.detail-heading > .status-new'}]
    journey('supplemental-boundary-max-mobile', actions, 375, ['Request received.', service_input['name'], fields['contactName'], 'New'])
    matches = [request for request in api('/requests') if request['serviceId'] == service['id'] and request['description'] == description]
    assert len(matches) == 1, 'Boundary journey must create exactly one request.'
    request = api('/requests/' + matches[0]['id'])
    assert len(request['history']) == 1
    fixture = {'requestId': request['id'], 'serviceId': service['id'], 'status': request['status'], 'historyEntries': len(request['history']), 'acceptedLengths': {name: len(value) for name, value in fields.items()}, 'serviceLengths': {name: len(service_input[name]) for name in ['name', 'description', 'price']}}
    Path('evidence/browser/supplemental-boundary-fixture.json').write_text(json.dumps(fixture, indent=2) + '\n')
    detail = login_actions() + [{'op': 'click', 'selector': 'a.customer-request[href="/requests/' + request['id'] + '"]'}, {'op': 'click', 'selector': '.detail-heading'}, {'op': 'click', 'selector': '.detail-heading > .status-new'}]
    journey('supplemental-boundary-max-desktop', detail, 1440, [service_input['name'], fields['contactName'], 'New'])
    overview = login_actions() + [{'op': 'click', 'selector': '.customer-stats'}]
    journey('supplemental-boundary-customer-overview', overview, 375, ['Hello, Alex.', service_input['name']])
    staff = [{'op': 'fill', 'selector': '#email', 'value': 'provider@demo.local'},
             {'op': 'fill', 'selector': '#password', 'value': 'ServiceFlow2026!'},
             {'op': 'click', 'selector': '.login-panel .button'},
             {'op': 'click', 'selector': '.stat-grid'},
             {'op': 'select', 'selector': '#status-filter', 'value': ''},
             {'op': 'click', 'selector': '#requests'}]
    journey('supplemental-boundary-staff-overview', staff, 1440, ['Provider workspace', service_input['name']])
    print(json.dumps({'boundary': 'passed', **fixture}))
finally:
    api('/services/' + service['id'], 'PATCH', {**service_input, 'active': False, 'version': service['version']})
