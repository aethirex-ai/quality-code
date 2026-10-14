"""Real browser/API regression for useful, editable, unsent no-key drafts.
Requires the local seeded app and supplied bridge; synthetic data only.
Configured-provider transport is covered separately with mocks, never live calls.
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

origin = 'http://127.0.0.1:' + (os.environ.get('PORTAL_PORT') or os.environ.get('PORT') or '3000')
client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
folder = Path('evidence/repair-v2-001-audit-03')
folder.mkdir(exist_ok=True)
Path('evidence/actions').mkdir(exist_ok=True)

def api(path, method='GET', body=None):
    request = urllib.request.Request(origin + '/api' + path,
        data=None if body is None else json.dumps(body).encode(),
        headers={'Origin': origin, 'Content-Type': 'application/json'}, method=method)
    with client.open(request, timeout=15) as response:
        return json.load(response)

def login(email):
    return [{'op': 'fill', 'selector': '#email', 'value': email},
        {'op': 'fill', 'selector': '#password', 'value': 'ServiceFlow2026!'},
        {'op': 'click', 'selector': '.login-panel .button'}]

def journey(name, actions, viewport, expected):
    time.sleep(11)  # Preserve the production authentication rate limit.
    path = Path('evidence/actions/' + name + '.json')
    path.write_text(json.dumps(actions))
    command = ['python3', 'scripts/preview-check.py', '--id', name, '--page', '/login',
        '--viewport', str(viewport), '--actions-file', str(path)]
    for text in expected:
        command += ['--expect', text]
    subprocess.run(command, check=True)

api('/auth/sign-in/email', 'POST', {'email': 'provider@demo.local', 'password': 'ServiceFlow2026!'})
description = 'Draft regression ' + uuid.uuid4().hex[:8] + ': The room size is 20 square metres. Parking access is available. All materials are supplied.'
fields = {'description': description, 'location': 'BS3 1AB · Synthetic Bristol',
    'preferredFrom': (datetime.date.today() + datetime.timedelta(days=14)).isoformat(),
    'contactPhone': '07700.900123'}
submit = login('alex@demo.local') + [
    {'op': 'click', 'selector': '.page-intro a.button'},
    {'op': 'select', 'selector': '#serviceId', 'value': 'small-repairs'}]
submit += [{'op': 'fill', 'selector': '#' + name, 'value': value} for name, value in fields.items()]
submit += [{'op': 'click', 'selector': '.form-submit .button'}, {'op': 'click', 'selector': '.timeline'}]
journey('audit03-draft-customer', submit, 375, ['Request received.', description, 'Request submitted'])
matches = [request for request in api('/requests') if request['description'] == description]
assert len(matches) == 1, 'Browser submission must create exactly one request.'
request_id = matches[0]['id']
before = api('/requests/' + request_id)
draft = api('/requests/' + request_id + '/draft', 'POST', {})
assert draft['source'] == 'deterministic', 'This benchmark must run without an AI key.'
assert '?' not in draft['text'], 'Size/access/materials already supplied: no redundant questions.'
assert '07700.900123' not in draft['text']
assert 'Nothing has been sent' in draft['notice']
assert before == api('/requests/' + request_id), 'Drafting must not mutate status/history.'
open_detail = login('provider@demo.local') + [
    {'op': 'click', 'selector': 'a.recent-card[href="/requests/' + request_id + '"]'},
    {'op': 'click', 'selector': '.draft-panel > button'},
    {'op': 'click', 'selector': '#reply-draft'}]
journey('audit03-draft-desktop', open_detail, 1440, [description, draft['notice'], 'Editable reply draft'])
edit = open_detail + [
    {'op': 'fill', 'selector': '#reply-draft', 'value': draft['text'] + '\nReviewed demo wording.'},
    {'op': 'check', 'selector': '.checkbox-label input'},
    {'op': 'click', 'selector': '#reply-draft'}]
journey('audit03-draft-mobile', edit, 375, [description, draft['notice'], 'Editable reply draft'])
after = api('/requests/' + request_id)
assert before == after, 'Generating/editing/reviewing drafts must leave persisted request unchanged.'
result = {'requestId': request_id, 'source': draft['source'], 'questions': draft['text'].count('?'),
    'status': after['status'], 'historyEntries': len(after['history']), 'unchangedAfterDrafting': before == after,
    'browserJourneys': 3, 'liveAIRequests': 0}
(folder / 'draft-browser-result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
