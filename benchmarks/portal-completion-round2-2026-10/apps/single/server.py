#!/usr/bin/env python3
"""AethDesign's synthetic local workspace. Python stdlib + SQLite only."""
import argparse
import hashlib
import hmac
import json
import secrets
import sqlite3
import sys
import time
from datetime import datetime, timezone
from http.cookies import SimpleCookie, CookieError
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
COOKIE = 'atelier_session'  # Fixed exercise wire contract, not studio branding.
MAX_BODY = 16384
PASSWORD_ROUNDS = 180000


class APIError(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message


def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def text(value, name, maximum, minimum=1, trim=True):
    if not isinstance(value, str) or any(0xD800 <= ord(c) <= 0xDFFF for c in value):
        raise APIError(400, 'invalid_input', f'{name} must be valid text.')
    value = value.strip() if trim else value
    if not minimum <= len(value) <= maximum:
        raise APIError(400, 'invalid_input', f'{name} must contain {minimum}–{maximum} characters.')
    return value


def integer(value, name):
    if type(value) is not int or value < 1 or value > 2147483647:
        raise APIError(400, 'invalid_input', f'{name} must be a positive integer.')
    return value


def validate_unicode(value, depth=0):
    if depth > 20:
        raise APIError(400, 'invalid_input', 'JSON is nested too deeply.')
    if isinstance(value, str):
        text(value, 'Text', MAX_BODY, 0, False)
    elif isinstance(value, dict):
        for key, item in value.items():
            validate_unicode(key, depth + 1)
            validate_unicode(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            validate_unicode(item, depth + 1)


def password_hash(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), PASSWORD_ROUNDS).hex()


def connect(path):
    db = sqlite3.connect(path, timeout=10, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA busy_timeout=10000')
    return db


def initialize(path):
    db = connect(path)
    try:
        db.execute('PRAGMA journal_mode=WAL')
        db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('client','staff')), salt TEXT NOT NULL, verifier TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), expires REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, client_id TEXT NOT NULL REFERENCES users(id),
            client_name TEXT NOT NULL, budget_cents INTEGER NOT NULL, progress INTEGER NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('awaiting_review','approved','changes_requested')),
            current_revision INTEGER NOT NULL, next_milestone TEXT NOT NULL,
            brief TEXT NOT NULL, deliverables TEXT NOT NULL, timeline TEXT NOT NULL,
            category TEXT NOT NULL, description TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS revisions (
            project_id TEXT NOT NULL REFERENCES projects(id), number INTEGER NOT NULL,
            title TEXT NOT NULL, summary TEXT NOT NULL, published_at TEXT NOT NULL,
            PRIMARY KEY(project_id, number)
        );
        CREATE TABLE IF NOT EXISTS decisions (
            project_id TEXT NOT NULL, revision INTEGER NOT NULL, decision TEXT NOT NULL,
            note TEXT NOT NULL, author_id TEXT NOT NULL REFERENCES users(id), created_at TEXT NOT NULL,
            PRIMARY KEY(project_id, revision),
            FOREIGN KEY(project_id,revision) REFERENCES revisions(project_id,number)
        );
        CREATE TABLE IF NOT EXISTS comments (
            id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
            body TEXT NOT NULL, author_id TEXT NOT NULL REFERENCES users(id), created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS events (
            seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL,
            project_id TEXT NOT NULL REFERENCES projects(id), type TEXT NOT NULL,
            actor_id TEXT NOT NULL REFERENCES users(id), revision INTEGER NOT NULL,
            created_at TEXT NOT NULL, detail TEXT NOT NULL
        );
        ''')
        db.execute('BEGIN IMMEDIATE')
        if not db.execute('SELECT 1 FROM users LIMIT 1').fetchone():
            for uid, email, name, role, password in [
                ('s1', 'studio@aethdesign.test', 'AethDesign Studio', 'staff', 'StudioDemo!42'),
                ('c1', 'alex@harbor.test', 'Alex Morgan', 'client', 'HarborDemo!42'),
                ('c2', 'sam@northline.test', 'Sam Ellis', 'client', 'NorthDemo!42'),
            ]:
                salt = secrets.token_hex(16)
                db.execute('INSERT INTO users VALUES (?,?,?,?,?,?)', (uid, email, name, role, salt, password_hash(password, salt)))
            projects = [
                ('p1', 'Harbor Commerce Platform', 'c1', 'Harbor House', 420000, 65, 'awaiting_review', 1,
                 'Commerce UX review',
                 'A considered shopping experience for a fictional homeware business. Help customers discover the right products, compare dimensions and complete a calm, accessible checkout. The build connects a responsive storefront with a structured product catalogue, inventory API and reliable order state.',
                 ['Responsive storefront & product discovery', 'Accessible product detail and checkout flows', 'Catalogue, inventory & order API', 'Reusable interface system and implementation notes'],
                 [{'title': 'Discovery & catalogue mapping', 'status': 'complete'}, {'title': 'Interface system & storefront', 'status': 'complete'}, {'title': 'Commerce UX review', 'status': 'current'}, {'title': 'API integration & launch checks', 'status': 'upcoming'}],
                 'Commerce · Web application', 'Product discovery, a thoughtful checkout, and the systems behind them.'),
                ('p2', 'Harbor Merchant Console', 'c1', 'Harbor House', 780000, 90, 'approved', 2,
                 'Handoff preparation',
                 'An operational workspace for the same fictional merchant. Bring orders, inventory and fulfilment into one clear daily workflow. A role-aware console pairs a reusable UI system with validated APIs, searchable records and traceable order transitions.',
                 ['Order management & fulfilment workspace', 'Inventory controls and low-stock states', 'Role-aware API and validated data contracts', 'Keyboard workflows, QA & handoff documentation'],
                 [{'title': 'Operations workflow mapping', 'status': 'complete'}, {'title': 'Console implementation', 'status': 'complete'}, {'title': 'Client review & approval', 'status': 'complete'}, {'title': 'Handoff preparation', 'status': 'current'}],
                 'Operations · Full-stack', 'A clear daily workspace for orders, stock and fulfilment.'),
                ('p3', 'Northline SaaS Workspace', 'c2', 'Northline', 360000, 40, 'awaiting_review', 1,
                 'SaaS workflow review',
                 'A collaborative SaaS workspace for a fictional product team. Turn scattered initiatives into clear priorities, owned tasks and visible delivery milestones. Design the core planning flows and build a responsive application with workspace-scoped data and predictable API behaviour.',
                 ['Workspace navigation & planning flows', 'Project board and task detail interfaces', 'Workspace-scoped backend and API contracts', 'Responsive component library & accessibility notes'],
                 [{'title': 'Product strategy & workflow map', 'status': 'complete'}, {'title': 'Core interface direction', 'status': 'complete'}, {'title': 'SaaS workflow review', 'status': 'current'}, {'title': 'Application build & validation', 'status': 'upcoming'}],
                 'SaaS · Product design', 'From shared priorities to clear, owned next steps.'),
            ]
            for p in projects:
                values = list(p)
                values[10], values[11] = json.dumps(values[10]), json.dumps(values[11])
                db.execute('INSERT INTO projects VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', values)
            revisions = [
                ('p1', 1, 'Commerce experience direction', 'Review the storefront hierarchy, product information and three-step checkout. The interface uses warm neutral surfaces and clear stock and delivery information. Please confirm product discovery and checkout direction before API integration.', '2026-10-09T09:00:00Z'),
                ('p2', 1, 'Merchant workflow foundation', 'Initial order queue, inventory table and fulfilment detail. The review focused on reducing context switching during daily operations.', '2026-10-02T09:00:00Z'),
                ('p2', 2, 'Operations ready for handoff', 'Refined order filters, explicit fulfilment state transitions and clearer stock warnings. Keyboard navigation and API validation are included in the handoff scope.', '2026-10-08T11:00:00Z'),
                ('p3', 1, 'SaaS workspace direction', 'Review workspace navigation, initiative cards and task ownership. The proposal keeps project context visible while moving between planning and delivery, with explicit empty and permission states.', '2026-10-10T10:00:00Z'),
            ]
            db.executemany('INSERT INTO revisions VALUES (?,?,?,?,?)', revisions)
            db.execute('INSERT INTO decisions VALUES (?,?,?,?,?,?)', ('p2', 2, 'approve', 'Order states and stock warnings are clear. Ready for handoff.', 'c1', '2026-10-09T14:00:00Z'))
            for pid, body in [
                ('p1', 'The first commerce direction is ready. Please review the product discovery and checkout flow; a decision here will guide the next build.'),
                ('p2', 'The approved console is moving into handoff preparation. We are documenting order states and the inventory API.'),
                ('p3', 'The core workspace direction is ready for review. Let us know whether initiative ownership is clear enough for your team.'),
            ]:
                db.execute('INSERT INTO comments VALUES (?,?,?,?,?)', ('seed-' + pid, pid, body, 's1', '2026-10-11T09:00:00Z'))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def public_user(row):
    return {key: row[key] for key in ('id', 'name', 'email', 'role')}


def project_dict(row, detailed=False):
    p = {key: row[key] for key in ('id', 'title', 'progress', 'status', 'category', 'description')}
    for key, source in [('clientId', 'client_id'), ('clientName', 'client_name'), ('budgetCents', 'budget_cents'), ('currentRevision', 'current_revision'), ('nextMilestone', 'next_milestone')]:
        p[key] = row[source]
    if detailed:
        p.update(brief=row['brief'], deliverables=json.loads(row['deliverables']), timeline=json.loads(row['timeline']))
    return p


def actor(db, uid):
    row = db.execute('SELECT id,name,role FROM users WHERE id=?', (uid,)).fetchone()
    return dict(row)


def revision_dict(db, row):
    result = {'number': row['number'], 'title': row['title'], 'summary': row['summary'], 'publishedAt': row['published_at']}
    decision = db.execute('SELECT * FROM decisions WHERE project_id=? AND revision=?', (row['project_id'], row['number'])).fetchone()
    if decision:
        result['decision'] = {'decision': decision['decision'], 'note': decision['note'], 'author': actor(db, decision['author_id']), 'createdAt': decision['created_at']}
    return result


def comment_dict(db, row):
    return {'id': row['id'], 'body': row['body'], 'author': actor(db, row['author_id']), 'createdAt': row['created_at']}


def event(db, pid, kind, uid, revision, stamp, **detail):
    db.execute('INSERT INTO events (id,project_id,type,actor_id,revision,created_at,detail) VALUES (?,?,?,?,?,?,?)', (secrets.token_hex(12), pid, kind, uid, revision, stamp, json.dumps(detail)))


class Handler(BaseHTTPRequestHandler):
    server_version = 'AethDesignLocal/1'

    def log_message(self, fmt, *args):
        # Request paths are not logged (they could contain submitted private text).
        sys.stderr.write(f'{self.command} local request\n')

    def respond(self, status, payload, cookie=None):
        body = json.dumps(payload, ensure_ascii=True).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        if cookie is not None:
            self.send_header('Set-Cookie', cookie)
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        if self.headers.get('Content-Type', '').split(';')[0].strip().lower() != 'application/json':
            raise APIError(415, 'json_required', 'Send this request as application/json.')
        if self.headers.get('Transfer-Encoding'):
            raise APIError(400, 'invalid_input', 'Chunked requests are not supported.')
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            raise APIError(400, 'invalid_input', 'Invalid request length.')
        if not 0 < length <= MAX_BODY:
            raise APIError(400, 'invalid_input', 'Request body must be 1–16384 bytes.')
        try:
            data = json.loads(self.rfile.read(length).decode('utf-8'), parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        except (ValueError, UnicodeError, RecursionError):
            raise APIError(400, 'invalid_json', 'Request must contain a valid JSON object.')
        if not isinstance(data, dict):
            raise APIError(400, 'invalid_input', 'Request must contain a JSON object.')
        validate_unicode(data)
        return data

    def check_origin(self):
        origin = self.headers.get('Origin')
        host = self.headers.get('Host', '')
        allowed_hosts = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
        if host not in allowed_hosts:
            raise APIError(403, 'origin_denied', 'This workspace accepts local requests only.')
        if origin is not None and origin != 'http://' + host:
            raise APIError(403, 'origin_denied', 'Cross-origin writes are not allowed.')
        if self.headers.get('Sec-Fetch-Site') == 'cross-site':
            raise APIError(403, 'origin_denied', 'Cross-site writes are not allowed.')

    def session_token(self):
        try:
            c = SimpleCookie()
            c.load(self.headers.get('Cookie', ''))
            token = c[COOKIE].value if COOKIE in c else ''
        except CookieError:
            token = ''
        if not re.fullmatch(r'[A-Za-z0-9_-]{43}', token):
            return None
        return hashlib.sha256(token.encode('ascii')).hexdigest()

    def user(self, db):
        row = db.execute('SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires>?', (self.session_token(), time.time())).fetchone()
        if not row:
            raise APIError(401, 'authentication_required', 'Please sign in to continue.')
        return row

    def project(self, db, pid, user):
        row = db.execute('SELECT * FROM projects WHERE id=?', (pid,)).fetchone()
        if not row or (user['role'] != 'staff' and row['client_id'] != user['id']):
            raise APIError(404, 'not_found', 'Project not found in this workspace.')
        return row

    def api(self, db, path, body):
        if path == '/api/login' and self.command == 'POST':
            email = text(body.get('email'), 'Email', 254).lower()
            password = text(body.get('password'), 'Password', 256, trim=False)
            user = db.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
            # Always compute one verifier, including for unknown accounts.
            verifier = password_hash(password, user['salt'] if user else '00' * 16)
            if not user or not hmac.compare_digest(verifier, user['verifier']):
                raise APIError(401, 'invalid_credentials', 'Email or password is incorrect.')
            token = secrets.token_urlsafe(32)
            db.execute('INSERT INTO sessions VALUES (?,?,?)', (hashlib.sha256(token.encode('ascii')).hexdigest(), user['id'], time.time() + 7 * 86400))
            return 200, {'user': public_user(user)}, f'{COOKIE}={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=604800'
        if path == '/api/logout' and self.command == 'POST':
            db.execute('DELETE FROM sessions WHERE token_hash=?', (self.session_token(),))
            return 200, {'ok': True}, f'{COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0'
        user = self.user(db)
        if path == '/api/me' and self.command == 'GET':
            return 200, {'user': public_user(user)}, None
        if path == '/api/projects' and self.command == 'GET':
            rows = db.execute('SELECT * FROM projects WHERE ?=\'staff\' OR client_id=? ORDER BY id', (user['role'], user['id'])).fetchall()
            return 200, {'projects': [project_dict(p) for p in rows]}, None
        match = re.fullmatch(r'/api/projects/([A-Za-z0-9_-]{1,80})(?:/(revisions|decision|comments|activity))?', path)
        if not match:
            raise APIError(404, 'not_found', 'Endpoint not found.')
        pid, part = match.groups()
        # Lock before reading state: validation + mutations/events form one atomic unit.
        if self.command == 'POST':
            db.execute('BEGIN IMMEDIATE')
        p = self.project(db, pid, user)
        if self.command == 'GET':
            if part is None:
                payload = {'project': project_dict(p, True)}
            elif part == 'revisions':
                payload = {'revisions': [revision_dict(db, r) for r in db.execute('SELECT * FROM revisions WHERE project_id=? ORDER BY number', (pid,))]}
            elif part == 'comments':
                payload = {'comments': [comment_dict(db, c) for c in db.execute('SELECT * FROM comments WHERE project_id=? ORDER BY created_at,rowid', (pid,))]}
            elif part == 'activity':
                payload = {'events': [dict(id=e['id'], type=e['type'], actor=actor(db, e['actor_id']), revision=e['revision'], createdAt=e['created_at'], **json.loads(e['detail'])) for e in db.execute('SELECT * FROM events WHERE project_id=? ORDER BY seq', (pid,))]}
            else:
                raise APIError(404, 'not_found', 'Endpoint not found.')
            return 200, payload, None
        stamp = now()
        if part == 'revisions':
            if user['role'] != 'staff':
                raise APIError(403, 'role_denied', 'Only the studio can publish revisions.')
            expected = integer(body.get('expectedRevision'), 'Expected revision')
            title = text(body.get('title'), 'Title', 120)
            summary = text(body.get('summary'), 'Summary', 2000)
            if expected != p['current_revision']:
                raise APIError(409, 'revision_conflict', 'A newer revision exists. Review it before publishing.')
            number = expected + 1
            db.execute('INSERT INTO revisions VALUES (?,?,?,?,?)', (pid, number, title, summary, stamp))
            db.execute("UPDATE projects SET current_revision=?,status='awaiting_review' WHERE id=?", (number, pid))
            event(db, pid, 'revision_published', user['id'], number, stamp)
            r = db.execute('SELECT * FROM revisions WHERE project_id=? AND number=?', (pid, number)).fetchone()
            payload, code = {'revision': revision_dict(db, r), 'project': project_dict(self.project(db, pid, user), True)}, 201
        elif part == 'decision':
            if user['role'] != 'client' or user['id'] != p['client_id']:
                raise APIError(403, 'role_denied', 'Only the project client can submit a review decision.')
            number = integer(body.get('revision'), 'Revision')
            decision = text(body.get('decision'), 'Decision', 30)
            if decision not in ('approve', 'request_changes'):
                raise APIError(400, 'invalid_input', 'Choose approve or request_changes.')
            note = text(body.get('note'), 'Review note', 2000, 1 if decision == 'request_changes' else 0)
            if number != p['current_revision'] or p['status'] != 'awaiting_review':
                raise APIError(409, 'revision_conflict', 'This review has changed. Refresh and review the current revision.')
            status = 'approved' if decision == 'approve' else 'changes_requested'
            db.execute('INSERT INTO decisions VALUES (?,?,?,?,?,?)', (pid, number, decision, note, user['id'], stamp))
            db.execute('UPDATE projects SET status=? WHERE id=?', (status, pid))
            event(db, pid, 'decision_submitted', user['id'], number, stamp, decision=decision)
            payload, code = {'project': project_dict(self.project(db, pid, user), True)}, 200
        elif part == 'comments':
            value = text(body.get('body'), 'Comment', 2000)
            cid = secrets.token_hex(12)
            db.execute('INSERT INTO comments VALUES (?,?,?,?,?)', (cid, pid, value, user['id'], stamp))
            event(db, pid, 'comment_added', user['id'], p['current_revision'], stamp, commentId=cid)
            payload, code = {'comment': comment_dict(db, db.execute('SELECT * FROM comments WHERE id=?', (cid,)).fetchone())}, 201
        else:
            raise APIError(404, 'not_found', 'Endpoint not found.')
        db.commit()
        return code, payload, None

    def dispatch(self):
        db = None
        try:
            path = urlsplit(self.path).path
            if path.startswith('/api/'):
                if self.command == 'POST':
                    self.check_origin()
                    body = self.read_json()
                else:
                    body = None
                db = connect(self.server.db_path)
                status, payload, cookie = self.api(db, path, body)
                self.respond(status, payload, cookie)
            elif self.command == 'GET' and path in ('/', '/index.html', '/app.js', '/workspace.js', '/styles.css'):
                name = 'index.html' if path == '/' else path[1:]
                data = (ROOT / 'public' / name).read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', {'html': 'text/html; charset=utf-8', 'js': 'text/javascript; charset=utf-8', 'css': 'text/css; charset=utf-8'}[name.rsplit('.', 1)[1]])
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Cache-Control', 'no-cache')
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.send_header('Referrer-Policy', 'no-referrer')
                self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; connect-src 'self'; font-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'")
                self.end_headers()
                self.wfile.write(data)
            else:
                raise APIError(404, 'not_found', 'Page not found.')
        except APIError as e:
            if db and db.in_transaction:
                db.rollback()
            self.respond(e.status, {'error': {'code': e.code, 'message': e.message}})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            if db and db.in_transaction:
                db.rollback()
            sys.stderr.write(f'Local request failed: {type(e).__name__}\n')
            self.respond(500, {'error': {'code': 'internal_error', 'message': 'The workspace could not complete this request. Please try again.'}})
        finally:
            if db:
                db.close()

    do_GET = dispatch
    do_POST = dispatch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='127.0.0.1', choices=['127.0.0.1', 'localhost'])
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--db', type=Path, default=Path('demo.sqlite3'))
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error('Port must be 0–65535.')
    args.db.parent.mkdir(parents=True, exist_ok=True)
    initialize(str(args.db))
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.db_path = str(args.db)
    print(json.dumps({'ready': True, 'port': server.server_port}), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
