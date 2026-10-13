#!/usr/bin/env python3
"""AethDesign fictional local workspace: stdlib HTTP and transactional SQLite."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import hmac
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import sqlite3
import sys
import time
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
MAX_BODY = 32768
STATIC = {'/': ('index.html', 'text/html; charset=utf-8'), '/index.html': ('index.html', 'text/html; charset=utf-8'), '/app.mjs': ('app.mjs', 'application/javascript; charset=utf-8'), '/state.mjs': ('state.mjs', 'application/javascript; charset=utf-8'), '/styles.css': ('styles.css', 'text/css; charset=utf-8'), '/favicon.svg': ('favicon.svg', 'image/svg+xml')}


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def password_verifier(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), 210000).hex()


@contextmanager
def connection(db):
    conn = sqlite3.connect(db, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    try:
        yield conn
    finally:
        conn.close()


def initialize(db):
    Path(db).parent.mkdir(parents=True, exist_ok=True)
    with connection(db) as conn:
        conn.execute('PRAGMA journal_mode = WAL')
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, role TEXT NOT NULL, salt TEXT NOT NULL, verifier TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, title TEXT NOT NULL, client_id TEXT NOT NULL REFERENCES users(id), client_name TEXT NOT NULL, budget_cents INTEGER NOT NULL, progress INTEGER NOT NULL, status TEXT NOT NULL, current_revision INTEGER NOT NULL, next_milestone TEXT NOT NULL, brief TEXT NOT NULL, deliverables TEXT NOT NULL, timeline TEXT NOT NULL, category TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS revisions (project_id TEXT NOT NULL REFERENCES projects(id), number INTEGER NOT NULL, title TEXT NOT NULL, summary TEXT NOT NULL, published_at TEXT NOT NULL, PRIMARY KEY(project_id, number));
        CREATE TABLE IF NOT EXISTS decisions (project_id TEXT NOT NULL, revision INTEGER NOT NULL, decision TEXT NOT NULL, note TEXT NOT NULL, author_id TEXT NOT NULL REFERENCES users(id), created_at TEXT NOT NULL, PRIMARY KEY(project_id, revision), FOREIGN KEY(project_id,revision) REFERENCES revisions(project_id,number));
        CREATE TABLE IF NOT EXISTS comments (id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), body TEXT NOT NULL, author_id TEXT NOT NULL REFERENCES users(id), created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT NOT NULL REFERENCES projects(id), type TEXT NOT NULL, actor_id TEXT NOT NULL REFERENCES users(id), revision INTEGER NOT NULL, created_at TEXT NOT NULL, decision TEXT, comment_id TEXT);
        ''')
        conn.execute('BEGIN IMMEDIATE')
        if conn.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0:
            for uid, name, email, role, password in [
                ('s1', 'AethDesign Studio', 'studio@aethdesign.test', 'staff', 'StudioDemo!42'),
                ('c1', 'Alex Morgan', 'alex@harbor.test', 'client', 'HarborDemo!42'),
                ('c2', 'Sam Ellis', 'sam@northline.test', 'client', 'NorthDemo!42')]:
                salt = secrets.token_hex(16)
                conn.execute('INSERT INTO users VALUES (?,?,?,?,?,?)', (uid, name, email, role, salt, password_verifier(password, salt)))
            fixtures = [
                ('p1', 'Harbor Commerce Platform', 'c1', 'Harbor House', 420000, 65, 'awaiting_review', 1, 'Commerce UX review', 'Build a confident shopping experience for Harbor House. The product brings clear product discovery, thoughtful cart recovery and an accessible checkout into one responsive commerce platform. This review focuses on the purchase journey before implementation.', ['Responsive storefront and product discovery', 'Cart and checkout interaction specification', 'Accessible component library and implementation handoff'], [{'title':'Discovery and commerce strategy','status':'complete'}, {'title':'Commerce experience direction','status':'current'}, {'title':'Implementation and checkout validation','status':'upcoming'}], 'Commerce platform'),
                ('p2', 'Harbor Merchant Console', 'c1', 'Harbor House', 780000, 90, 'approved', 2, 'Handoff preparation', 'Give the Harbor operations team a single workspace for order triage, inventory health and fulfillment. The approved direction balances dense operational information with clear action paths and reusable interface components for the engineering team.', ['Order management dashboard and exception states', 'Inventory health views and bulk actions', 'Developer-ready interface components and handoff notes'], [{'title':'Merchant workflow discovery','status':'complete'}, {'title':'Console refinement and approval','status':'complete'}, {'title':'Engineering handoff preparation','status':'current'}], 'Merchant software'),
                ('p3', 'Northline SaaS Workspace', 'c2', 'Northline', 360000, 40, 'awaiting_review', 1, 'SaaS workflow review', 'Design a focused SaaS workspace that helps Northline teams coordinate projects without losing context. The current direction connects team onboarding, shared priorities and a clear work queue, with responsive layouts and accessible interaction patterns.', ['Workspace overview and task coordination', 'Team onboarding and invitation flow specification', 'Responsive SaaS component system and prototypes'], [{'title':'Product discovery and user journeys','status':'complete'}, {'title':'SaaS workspace direction','status':'current'}, {'title':'Usability validation and build planning','status':'upcoming'}], 'SaaS workspace')]
            for values in fixtures:
                v = list(values); v[10] = json.dumps(v[10]); v[11] = json.dumps(v[11])
                conn.execute('INSERT INTO projects VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', v)
            for project, number, title, summary, stamp in [
                ('p1',1,'Commerce experience direction','A focused storefront with editorial product discovery, a persistent cart and a clear three-step checkout. Review the hierarchy, product detail flow and mobile purchase experience.','2026-10-08T10:00:00Z'),
                ('p2',1,'Merchant workflow foundation','Initial operational dashboard connects order status, inventory signals and fulfillment actions in a consistent navigation structure.','2026-10-03T10:00:00Z'),
                ('p2',2,'Merchant console refinement','Refined exception handling, bulk inventory controls and compact order details. Accessibility and implementation annotations are ready for handoff.','2026-10-09T10:00:00Z'),
                ('p3',1,'SaaS workspace direction','A shared overview, prioritized work queue and guided onboarding help teams understand what needs attention and move work forward.','2026-10-07T10:00:00Z')]:
                conn.execute('INSERT INTO revisions VALUES (?,?,?,?,?)',(project,number,title,summary,stamp))
            conn.execute('INSERT INTO decisions VALUES (?,?,?,?,?,?)', ('p2',2,'approve','Approved for engineering handoff.','c1','2026-10-10T09:00:00Z'))
            for pid, author, body in [('p1','c1','The new product discovery flow feels clear. Let’s check the mobile checkout before approval.'),('p2','s1','Revision 2 is approved. We are preparing implementation notes and the component handoff.'),('p3','c2','The shared work queue is promising. Please keep the onboarding path simple for new teams.')]:
                cid = 'seed-' + pid
                conn.execute('INSERT INTO comments VALUES (?,?,?,?,?)',(cid,pid,body,author,'2026-10-11T09:00:00Z'))
                conn.execute('INSERT INTO events (project_id,type,actor_id,revision,created_at,comment_id) VALUES (?,?,?,?,?,?)',(pid,'comment_added',author,2 if pid=='p2' else 1,'2026-10-11T09:00:00Z',cid))
        conn.commit()


class ApiError(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message


def validate_unicode(value):
    if isinstance(value, str):
        if any(0xD800 <= ord(c) <= 0xDFFF for c in value):
            raise ApiError(400, 'invalid_text', 'Text must contain valid Unicode characters.')
    elif isinstance(value, dict):
        for key, item in value.items():
            validate_unicode(key); validate_unicode(item)
    elif isinstance(value, list):
        for item in value:
            validate_unicode(item)


def field_text(data, key, maximum, allow_empty=False, trim=True):
    value = data.get(key)
    if not isinstance(value, str):
        raise ApiError(400, 'invalid_field', key + ' must be text.')
    validate_unicode(value)
    value = value.strip() if trim else value
    if len(value) > maximum or (not allow_empty and not value.strip()):
        raise ApiError(400, 'invalid_field', key + ' has an invalid length.')
    return value


def field_number(data, key):
    value = data.get(key)
    if type(value) is not int or not 1 <= value <= 2147483647:
        raise ApiError(400, 'invalid_field', key + ' must be a positive integer.')
    return value


def user_json(row):
    return {k: row[k] for k in ('id', 'name', 'email', 'role')}


def actor_json(row):
    return {k: row[k] for k in ('id', 'name', 'role')}


def project_json(row, detail=True):
    output = {'id':row['id'], 'title':row['title'], 'clientId':row['client_id'], 'clientName':row['client_name'], 'budgetCents':row['budget_cents'], 'progress':row['progress'], 'status':row['status'], 'currentRevision':row['current_revision'], 'nextMilestone':row['next_milestone'], 'category':row['category']}
    if detail:
        output.update(brief=row['brief'], deliverables=json.loads(row['deliverables']), timeline=json.loads(row['timeline']))
    return output


class Handler(BaseHTTPRequestHandler):
    server_version = 'AethWorkspace'

    def log_message(self, fmt, *args):
        print('%s %s' % (self.address_string(), fmt % args), file=sys.stderr)

    def respond(self, status, value, cookie=None):
        raw = json.dumps(value, ensure_ascii=True).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        if cookie: self.send_header('Set-Cookie', cookie)
        self.end_headers(); self.wfile.write(raw)

    def do_GET(self):
        self.handle_request(False)

    def do_POST(self):
        self.handle_request(True)

    def do_PUT(self):
        self.respond(405, {'error': {'code':'method_not_allowed', 'message':'Use a supported request method.'}})

    do_DELETE = do_PATCH = do_OPTIONS = do_PUT

    def handle_request(self, write):
        try:
            if len(self.path) > 2048: raise ApiError(400, 'invalid_path', 'Request path is too long.')
            path = urlsplit(self.path).path
            if not path.startswith('/api/'):
                if write: raise ApiError(405, 'method_not_allowed', 'This resource is read-only.')
                return self.serve_static(path)
            data = self.read_json() if write else None
            with connection(self.server.db) as conn:
                self.route(conn, path, data, write)
        except ApiError as error:
            self.respond(error.status, {'error':{'code':error.code,'message':error.message}})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            print('Request failed safely', file=sys.stderr)
            self.respond(500, {'error':{'code':'internal_error','message':'The request could not be completed. Please try again.'}})

    def serve_static(self, path):
        item = STATIC.get(path)
        if not item: raise ApiError(404, 'not_found', 'Resource not found.')
        target = ROOT / 'public' / item[0]
        if target.is_symlink() or not target.is_file(): raise ApiError(404, 'not_found', 'Resource not found.')
        raw = target.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', item[1]); self.send_header('Content-Length',str(len(raw)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.end_headers(); self.wfile.write(raw)

    def read_json(self):
        origin = self.headers.get('Origin')
        if origin:
            try:
                parsed = urlsplit(origin)
                request_origin = urlsplit('http://' + self.headers.get('Host', ''))
                same = parsed.scheme == 'http' and parsed.hostname in ('127.0.0.1','localhost') and parsed.hostname == request_origin.hostname and (parsed.port or 80) == (request_origin.port or 80) == self.server.server_port and not parsed.username and not parsed.password and not parsed.path and not parsed.query and not parsed.fragment
            except ValueError: same = False
            if not same: raise ApiError(403, 'cross_origin', 'Cross-origin writes are not allowed.')
        if self.headers.get_content_type() != 'application/json':
            raise ApiError(415, 'json_required', 'Write requests must use application/json.')
        if self.headers.get('Transfer-Encoding'):
            raise ApiError(400, 'invalid_body', 'A fixed-length JSON body is required.')
        try: size = int(self.headers.get('Content-Length', '0'))
        except ValueError: raise ApiError(400, 'invalid_body', 'Invalid body length.')
        if not 1 <= size <= MAX_BODY: raise ApiError(400, 'invalid_body', 'JSON body must be between 1 and 32768 bytes.')
        try:
            data = json.loads(self.rfile.read(size).decode('utf-8'), parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
            if not isinstance(data, dict): raise ValueError()
            validate_unicode(data)
        except (ValueError, RecursionError): raise ApiError(400, 'invalid_json', 'Provide a valid JSON object with valid Unicode text.')
        return data

    def token(self):
        try:
            jar = cookies.SimpleCookie(); jar.load(self.headers.get('Cookie', ''))
            item = jar.get('atelier_session')
            return item.value if item and len(item.value) <= 128 else None
        except cookies.CookieError: return None

    def current_user(self, conn):
        row = conn.execute('SELECT u.* FROM users u JOIN sessions s ON s.user_id=u.id WHERE s.token=? AND s.expires>?', (self.token(),time.time())).fetchone()
        if not row: raise ApiError(401, 'authentication_required', 'Please sign in to continue.')
        return row

    def project(self, conn, pid, user):
        row = conn.execute('SELECT * FROM projects WHERE id=?',(pid,)).fetchone()
        if not row or (user['role'] != 'staff' and row['client_id'] != user['id']):
            raise ApiError(404, 'project_not_found', 'Project not found.')
        return row

    def route(self, conn, path, data, write):
        if path == '/api/login' and write:
            email = field_text(data, 'email', 254).lower()
            password = field_text(data, 'password', 128, trim=False)
            user = conn.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
            # A dummy hash keeps unknown-email credentials on the same expensive path.
            verifier = password_verifier(password, user['salt'] if user else '00'*16)
            if not user or not hmac.compare_digest(verifier, user['verifier']):
                raise ApiError(401, 'invalid_credentials', 'Email or password is incorrect.')
            token = secrets.token_urlsafe(32)
            conn.execute('INSERT INTO sessions VALUES (?,?,?)',(token,user['id'],time.time()+7*86400)); conn.commit()
            return self.respond(200, {'user':user_json(user)}, 'atelier_session='+token+'; Path=/; HttpOnly; SameSite=Lax')
        if path == '/api/logout' and write:
            conn.execute('DELETE FROM sessions WHERE token=?',(self.token(),)); conn.commit()
            return self.respond(200, {'ok':True}, 'atelier_session=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0')
        user = self.current_user(conn)
        if path == '/api/me' and not write: return self.respond(200, {'user':user_json(user)})
        if path == '/api/projects' and not write:
            rows = conn.execute('SELECT * FROM projects ORDER BY id' if user['role']=='staff' else 'SELECT * FROM projects WHERE client_id=? ORDER BY id', () if user['role']=='staff' else (user['id'],)).fetchall()
            return self.respond(200, {'projects':[project_json(row,False) for row in rows]})
        parts = path.split('/')
        if len(parts) not in (4,5) or parts[1:3] != ['api','projects'] or not parts[3]:
            raise ApiError(404, 'not_found', 'API resource not found.')
        pid = parts[3]
        # Serialize all project mutations before checking state or authorization.
        if write: conn.execute('BEGIN IMMEDIATE')
        project = self.project(conn,pid,user)
        section = parts[4] if len(parts)==5 else ''
        if not write:
            if not section: return self.respond(200, {'project':project_json(project)})
            if section=='revisions':
                rows=conn.execute('SELECT * FROM revisions WHERE project_id=? ORDER BY number',(pid,)).fetchall()
                return self.respond(200, {'revisions':[{'number':r['number'],'title':r['title'],'summary':r['summary'],'publishedAt':r['published_at']} for r in rows]})
            if section=='comments':
                rows=conn.execute('SELECT c.*,u.name,u.role FROM comments c JOIN users u ON u.id=c.author_id WHERE project_id=? ORDER BY created_at,c.rowid',(pid,)).fetchall()
                return self.respond(200, {'comments':[{'id':r['id'],'body':r['body'],'author':{'id':r['author_id'],'name':r['name'],'role':r['role']},'createdAt':r['created_at']} for r in rows]})
            if section=='activity':
                rows=conn.execute('SELECT e.*,u.name,u.role FROM events e JOIN users u ON u.id=e.actor_id WHERE project_id=? ORDER BY created_at,e.id',(pid,)).fetchall()
                events=[]
                for r in rows:
                    event={'id':str(r['id']),'type':r['type'],'actor':{'id':r['actor_id'],'name':r['name'],'role':r['role']},'revision':r['revision'],'createdAt':r['created_at']}
                    if r['decision']: event['decision']=r['decision']
                    if r['comment_id']: event['commentId']=r['comment_id']
                    events.append(event)
                return self.respond(200, {'events':events})
        stamp = utc_now()
        if write and section=='revisions':
            if user['role']!='staff': raise ApiError(403,'staff_required','Only studio staff can publish revisions.')
            expected=field_number(data,'expectedRevision'); title=field_text(data,'title',120); summary=field_text(data,'summary',2000)
            if expected!=project['current_revision']: raise ApiError(409,'revision_conflict','A newer revision is available. Refresh before publishing.')
            number=expected+1
            conn.execute('INSERT INTO revisions VALUES (?,?,?,?,?)',(pid,number,title,summary,stamp))
            conn.execute("UPDATE projects SET current_revision=?,status='awaiting_review' WHERE id=?",(number,pid))
            event_id = conn.execute('INSERT INTO events (project_id,type,actor_id,revision,created_at) VALUES (?,?,?,?,?)',(pid,'revision_published',user['id'],number,stamp)).lastrowid
            snapshot = project_json(self.project(conn,pid,user))
            event = {'id':str(event_id),'type':'revision_published','actor':actor_json(user),'revision':number,'createdAt':stamp}
            conn.commit()
            return self.respond(201, {'revision':{'number':number,'title':title,'summary':summary,'publishedAt':stamp},'project':snapshot,'event':event})
        if write and section=='decision':
            if user['role']!='client': raise ApiError(403,'client_required','Only the project client can submit a review decision.')
            revision=field_number(data,'revision'); decision=field_text(data,'decision',32); note=field_text(data,'note',2000,allow_empty=decision=='approve')
            if decision not in ('approve','request_changes'): raise ApiError(400,'invalid_decision','Choose approve or request_changes.')
            if revision!=project['current_revision'] or project['status']!='awaiting_review': raise ApiError(409,'decision_conflict','This review changed or already has a decision. Refresh the current revision.')
            status='approved' if decision=='approve' else 'changes_requested'
            conn.execute('INSERT INTO decisions VALUES (?,?,?,?,?,?)',(pid,revision,decision,note,user['id'],stamp))
            conn.execute('UPDATE projects SET status=? WHERE id=?',(status,pid))
            event_id = conn.execute('INSERT INTO events (project_id,type,actor_id,revision,created_at,decision) VALUES (?,?,?,?,?,?)',(pid,'decision_submitted',user['id'],revision,stamp,decision)).lastrowid
            snapshot = project_json(self.project(conn,pid,user))
            event = {'id':str(event_id),'type':'decision_submitted','actor':actor_json(user),'revision':revision,'createdAt':stamp,'decision':decision}
            conn.commit()
            return self.respond(200, {'project':snapshot,'event':event})
        if write and section=='comments':
            body=field_text(data,'body',2000); cid=secrets.token_urlsafe(18)
            conn.execute('INSERT INTO comments VALUES (?,?,?,?,?)',(cid,pid,body,user['id'],stamp))
            event_id = conn.execute('INSERT INTO events (project_id,type,actor_id,revision,created_at,comment_id) VALUES (?,?,?,?,?,?)',(pid,'comment_added',user['id'],project['current_revision'],stamp,cid)).lastrowid
            event = {'id':str(event_id),'type':'comment_added','actor':actor_json(user),'revision':project['current_revision'],'createdAt':stamp,'commentId':cid}
            conn.commit()
            return self.respond(201, {'comment':{'id':cid,'body':body,'author':actor_json(user),'createdAt':stamp},'event':event})
        raise ApiError(404,'not_found','API resource not found.')


class WorkspaceServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, host, port, db):
        if host not in ('127.0.0.1','localhost'): raise ValueError('Only loopback hosts are allowed.')
        self.db = str(Path(db).resolve())
        initialize(self.db)
        super().__init__((host,port),Handler)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',default='127.0.0.1',choices=('127.0.0.1','localhost'))
    parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--db',default='demo.sqlite3')
    args=parser.parse_args()
    with WorkspaceServer(args.host,args.port,args.db) as server:
        print(json.dumps({'ready':True,'port':server.server_port}),flush=True)
        try: server.serve_forever()
        except KeyboardInterrupt: pass


if __name__=='__main__': main()
