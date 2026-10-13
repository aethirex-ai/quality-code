#!/usr/bin/env python3
"""AethDesign's fictional, loopback-only client portal (Python stdlib)."""
import argparse
import hashlib
import hmac
import ipaddress
import json
import mimetypes
import secrets
import sqlite3
import sys
import time
from contextlib import closing
from datetime import datetime, timezone
from http.cookies import SimpleCookie, CookieError
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

PUBLIC = Path(__file__).resolve().parent / "public"
COOKIE = "atelier_session"
MAX_BODY = 16384
PASSWORD_ROUNDS = 240000


class APIError(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message


def now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def password_hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), PASSWORD_ROUNDS).hex()


def connect(path):
    db = sqlite3.connect(path, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA busy_timeout=15000")
    return db


def initialize(path):
    with closing(connect(path)) as db, db:
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript("""
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('staff','client')),
                salt TEXT NOT NULL, password_hash TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, client_id TEXT NOT NULL REFERENCES accounts(id),
                client_name TEXT NOT NULL, budget_cents INTEGER NOT NULL, progress INTEGER NOT NULL,
                status TEXT NOT NULL, current_revision INTEGER NOT NULL, next_milestone TEXT NOT NULL,
                brief TEXT NOT NULL, deliverables TEXT NOT NULL, timeline TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS revisions (
                project_id TEXT NOT NULL REFERENCES projects(id), number INTEGER NOT NULL,
                title TEXT NOT NULL, summary TEXT NOT NULL, published_at TEXT NOT NULL,
                PRIMARY KEY(project_id,number));
            CREATE TABLE IF NOT EXISTS decisions (
                project_id TEXT NOT NULL, revision INTEGER NOT NULL,
                decision TEXT NOT NULL, note TEXT NOT NULL, author_id TEXT NOT NULL REFERENCES accounts(id),
                created_at TEXT NOT NULL, PRIMARY KEY(project_id,revision),
                FOREIGN KEY(project_id,revision) REFERENCES revisions(project_id,number));
            CREATE TABLE IF NOT EXISTS comments (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL,
                project_id TEXT NOT NULL REFERENCES projects(id), body TEXT NOT NULL,
                author_id TEXT NOT NULL REFERENCES accounts(id), created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL,
                project_id TEXT NOT NULL REFERENCES projects(id), type TEXT NOT NULL,
                actor_id TEXT NOT NULL REFERENCES accounts(id), revision INTEGER NOT NULL,
                created_at TEXT NOT NULL, details TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES accounts(id),
                expires_at REAL NOT NULL);
        """)
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT 1 FROM accounts LIMIT 1").fetchone():
            return
        for ident, email, name, role, password in [
            ("s1", "studio@aethdesign.test", "AethDesign Studio", "staff", "StudioDemo!42"),
            ("c1", "alex@harbor.test", "Alex Morgan", "client", "HarborDemo!42"),
            ("c2", "sam@northline.test", "Sam Ellis", "client", "NorthDemo!42"),
        ]:
            salt = secrets.token_hex(16)
            db.execute("INSERT INTO accounts VALUES (?,?,?,?,?,?)", (ident,email,name,role,salt,password_hash(password,salt)))
        seeds = [
            ("p1", "Harbor House Identity", "c1", "Harbor House", 420000, 65, "awaiting_review", 1, "Identity review",
             "A welcoming identity for a coastal house of considered objects. Balance a confident wordmark with tactile details, a warm palette and the ease of life by the water.",
             ["Primary and secondary wordmarks", "Coastal colour and typography system", "Stationery and packaging concepts", "Identity guidelines"],
             [{"title":"Discovery & positioning","status":"complete"},{"title":"Identity exploration","status":"complete"},{"title":"Identity review","status":"current"},{"title":"Guidelines & handoff","status":"upcoming"}]),
            ("p2", "Harbor Digital Experience", "c1", "Harbor House", 780000, 90, "approved", 2, "Handoff preparation",
             "Bring the Harbor House collection online through quiet storytelling, clear product discovery and an accessible shopping journey. This demo represents design review, with no live checkout.",
             ["Responsive homepage and collection layouts", "Product detail and discovery flows", "Accessible component library", "Developer handoff notes"],
             [{"title":"Experience mapping","status":"complete"},{"title":"Digital direction","status":"complete"},{"title":"Responsive review","status":"complete"},{"title":"Handoff preparation","status":"current"}]),
            ("p3", "Northline Editorial", "c2", "Northline", 360000, 40, "awaiting_review", 1, "Editorial review",
             "An editorial system for independent perspectives on place and culture. Establish a distinctive reading rhythm with expressive headlines, generous margins and a flexible grid for photography.",
             ["Editorial grid and type hierarchy", "Cover and feature spread concepts", "Photography treatment guide", "Reusable issue templates"],
             [{"title":"Editorial workshop","status":"complete"},{"title":"System exploration","status":"complete"},{"title":"Editorial review","status":"current"},{"title":"Issue templates","status":"upcoming"}]),
        ]
        for item in seeds:
            db.execute("INSERT INTO projects VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (*item[:10],json.dumps(item[10]),json.dumps(item[11])))
        for project, number, title, summary, date in [
            ("p1",1,"Identity direction","A grounded serif wordmark, sea-glass accents and a modular monogram introduce a warm, confident coastal identity.","2026-09-18T10:00:00Z"),
            ("p2",1,"Digital direction","A story-led homepage and considered collection navigation translate the brand into a calm digital experience.","2026-09-10T10:00:00Z"),
            ("p2",2,"Responsive refinement","Refined mobile navigation, accessible contrast and final product-page layouts incorporate your first-round feedback.","2026-09-22T10:00:00Z"),
            ("p3",1,"Editorial system","A strong typographic masthead and flexible six-column grid create room for long-form stories and unexpected image pairings.","2026-09-24T10:00:00Z"),
        ]:
            db.execute("INSERT INTO revisions VALUES (?,?,?,?,?)", (project,number,title,summary,date))
        db.execute("INSERT INTO decisions VALUES (?,?,?,?,?,?)", ("p2",2,"approve","The responsive refinement is approved. Please prepare the handoff.","c1","2026-09-23T09:00:00Z"))
        for project, body in [("p1","The first identity direction is ready for your review. We would love your thoughts on the wordmark and palette."),("p2","The responsive refinements are approved; we are assembling your handoff notes."),("p3","The editorial system explores a flexible rhythm for stories and photography. Let us know how it feels for the next issue.")]:
            db.execute("INSERT INTO comments (id,project_id,body,author_id,created_at) VALUES (?,?,?,?,?)", ("seed-"+project,project,body,"s1","2026-09-25T12:00:00Z"))


def user_data(row):
    return {"id":row["id"],"name":row["name"],"email":row["email"],"role":row["role"]}


def actor_data(row):
    return {"id":row["author_id"],"name":row["author_name"],"role":row["author_role"]}


def project_data(row):
    return {"id":row["id"],"title":row["title"],"clientId":row["client_id"],"clientName":row["client_name"],
            "budgetCents":row["budget_cents"],"progress":row["progress"],"status":row["status"],
            "currentRevision":row["current_revision"],"nextMilestone":row["next_milestone"],
            "brief":row["brief"],"deliverables":json.loads(row["deliverables"]),"timeline":json.loads(row["timeline"])}


def revision_data(row):
    return {"number":row["number"],"title":row["title"],"summary":row["summary"],"publishedAt":row["published_at"]}


def comment_data(row):
    return {"id":row["id"],"body":row["body"],"author":actor_data(row),"createdAt":row["created_at"]}


def text_field(body, key, maximum, empty=False):
    value = body.get(key)
    if not isinstance(value, str):
        raise APIError(400,"invalid_input",f"{key} must be text.")
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise APIError(400,"invalid_input",f"{key} must contain valid Unicode text.")
    value = value.strip()
    if len(value) > maximum or (not value and not empty):
        raise APIError(400,"invalid_input",f"{key} must contain {'0' if empty else '1'}–{maximum} characters.")
    return value


def revision_field(body, key):
    value = body.get(key)
    if type(value) is not int or value < 1 or value > 2147483647:
        raise APIError(400,"invalid_input",f"{key} must be a positive integer.")
    return value


class PortalServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, address, db_path):
        self.db_path = db_path
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    server_version = "Atelier"
    sys_version = ""

    def log_message(self, format, *args):
        # Do not include credentials, cookies, bodies or query strings in logs.
        sys.stderr.write(f"{self.client_address[0]} {self.command} {self.path.split('?')[0]}\n")

    def send_json(self, status, data, cookie=None):
        encoded = json.dumps(data,ensure_ascii=True,separators=(",",":")).encode()
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(encoded)))
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff")
        if cookie:
            self.send_header("Set-Cookie",cookie)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(encoded)

    def token(self):
        try:
            cookies = SimpleCookie()
            cookies.load(self.headers.get("Cookie", ""))
            value = cookies[COOKIE].value if COOKIE in cookies else ""
            return value if len(value) == 64 else ""
        except CookieError:
            return ""

    def authenticated(self, db):
        token = self.token()
        row = db.execute("SELECT a.* FROM sessions s JOIN accounts a ON a.id=s.user_id WHERE token_hash=? AND expires_at>?", (hashlib.sha256(token.encode()).hexdigest(),time.time())).fetchone() if token else None
        if not row:
            raise APIError(401,"unauthorized","Please sign in to continue.")
        return row

    def authorized_project(self, db, ident, user):
        row = db.execute("SELECT * FROM projects WHERE id=?", (ident,)).fetchone()
        if not row or (user["role"] != "staff" and row["client_id"] != user["id"]):
            raise APIError(404,"not_found","Project not found.")
        return row

    def read_body(self):
        origin = self.headers.get("Origin")
        host = self.headers.get("Host", "")
        if origin is not None and origin != "http://" + host:
            raise APIError(403,"cross_origin","Cross-origin writes are not allowed.")
        if origin is not None:
            try:
                parsed = urlsplit(origin)
                valid_host = parsed.hostname in ("127.0.0.1","localhost","::1") and parsed.port == self.server.server_port
            except ValueError:
                valid_host = False
            if not valid_host:
                raise APIError(403,"cross_origin","Cross-origin writes are not allowed.")
        if self.headers.get("Content-Type", "").split(";",1)[0].strip().lower() != "application/json":
            raise APIError(415,"unsupported_media_type","Send mutation requests as application/json.")
        if self.headers.get("Transfer-Encoding"):
            raise APIError(400,"invalid_input","Unsupported request encoding.")
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise APIError(400,"invalid_input","Invalid request length.")
        if length < 1 or length > MAX_BODY:
            raise APIError(400,"invalid_input","JSON request must contain 1–16384 bytes.")
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"),parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        except (ValueError,UnicodeError,RecursionError):
            raise APIError(400,"invalid_input","Request must contain valid JSON.")
        if not isinstance(body,dict):
            raise APIError(400,"invalid_input","Request body must be a JSON object.")
        return body

    def add_event(self, db, project, kind, user, revision, timestamp, **details):
        db.execute("INSERT INTO events (id,project_id,type,actor_id,revision,created_at,details) VALUES (?,?,?,?,?,?,?)", (secrets.token_hex(12),project,kind,user["id"],revision,timestamp,json.dumps(details)))

    def api(self):
        path = urlsplit(self.path).path
        method = self.command
        with closing(connect(self.server.db_path)) as db, db:
            if path == "/api/login" and method == "POST":
                body = self.read_body()
                email = text_field(body,"email",254).lower()
                password = body.get("password")
                if not isinstance(password,str) or not password.strip() or len(password)>256:
                    raise APIError(400,"invalid_input","password must contain 1–256 characters.")
                if any(0xD800 <= ord(char) <= 0xDFFF for char in password):
                    raise APIError(400,"invalid_input","password must contain valid Unicode text.")
                user = db.execute("SELECT * FROM accounts WHERE email=?", (email,)).fetchone()
                # Run a verifier even when the email is unknown.
                verifier = password_hash(password,user["salt"] if user else "00"*16)
                if not user or not hmac.compare_digest(verifier,user["password_hash"]):
                    raise APIError(401,"invalid_credentials","Email or password is incorrect.")
                token = secrets.token_hex(32)
                db.execute("INSERT INTO sessions VALUES (?,?,?)", (hashlib.sha256(token.encode()).hexdigest(),user["id"],time.time()+30*86400))
                db.commit()
                self.send_json(200,{"user":user_data(user)},f"{COOKIE}={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=2592000")
                return
            if method == "POST":
                db.execute("BEGIN IMMEDIATE")
            user = self.authenticated(db)
            if path == "/api/me" and method == "GET":
                self.send_json(200,{"user":user_data(user)})
                return
            if path == "/api/logout" and method == "POST":
                self.read_body()
                db.execute("DELETE FROM sessions WHERE token_hash=?", (hashlib.sha256(self.token().encode()).hexdigest(),))
                db.commit()
                self.send_json(200,{"ok":True},f"{COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0")
                return
            if path == "/api/projects" and method == "GET":
                rows = db.execute("SELECT * FROM projects ORDER BY id").fetchall() if user["role"]=="staff" else db.execute("SELECT * FROM projects WHERE client_id=? ORDER BY id",(user["id"],)).fetchall()
                self.send_json(200,{"projects":[project_data(row) for row in rows]})
                return
            parts = path.strip("/").split("/")
            if len(parts) not in (3,4) or parts[:2] != ["api","projects"]:
                raise APIError(404,"not_found","API route not found.")
            project = self.authorized_project(db,parts[2],user)
            endpoint = parts[3] if len(parts)==4 else ""
            if method == "GET":
                if not endpoint:
                    data = project_data(project)
                    decisions = db.execute("SELECT d.*,a.name author_name,a.role author_role FROM decisions d JOIN accounts a ON a.id=d.author_id WHERE d.project_id=? ORDER BY revision",(project["id"],)).fetchall()
                    data["decisions"] = [{"revision":r["revision"],"decision":r["decision"],"note":r["note"],"author":actor_data(r),"createdAt":r["created_at"]} for r in decisions]
                    self.send_json(200,{"project":data})
                elif endpoint == "revisions":
                    rows = db.execute("SELECT * FROM revisions WHERE project_id=? ORDER BY number",(project["id"],)).fetchall()
                    self.send_json(200,{"revisions":[revision_data(r) for r in rows]})
                elif endpoint == "comments":
                    rows = db.execute("SELECT c.*,a.name author_name,a.role author_role FROM comments c JOIN accounts a ON a.id=c.author_id WHERE c.project_id=? ORDER BY c.sequence",(project["id"],)).fetchall()
                    self.send_json(200,{"comments":[comment_data(r) for r in rows]})
                elif endpoint == "activity":
                    rows = db.execute("SELECT e.*,a.name author_name,a.role author_role,e.actor_id author_id FROM events e JOIN accounts a ON a.id=e.actor_id WHERE e.project_id=? ORDER BY e.sequence",(project["id"],)).fetchall()
                    self.send_json(200,{"events":[{"id":r["id"],"type":r["type"],"actor":actor_data(r),"revision":r["revision"],"createdAt":r["created_at"],**json.loads(r["details"])} for r in rows]})
                else:
                    raise APIError(404,"not_found","API route not found.")
                return
            if method != "POST":
                raise APIError(405,"method_not_allowed","This API method is not supported.")
            body = self.read_body()
            timestamp = now()
            if endpoint == "revisions":
                if user["role"] != "staff":
                    raise APIError(403,"forbidden","Only studio staff can publish revisions.")
                expected = revision_field(body,"expectedRevision")
                title, summary = text_field(body,"title",120), text_field(body,"summary",2000)
                if expected != project["current_revision"]:
                    raise APIError(409,"revision_conflict","A newer revision is available. Refresh before publishing.")
                number = expected+1
                db.execute("INSERT INTO revisions VALUES (?,?,?,?,?)",(project["id"],number,title,summary,timestamp))
                db.execute("UPDATE projects SET current_revision=?,status='awaiting_review' WHERE id=?",(number,project["id"]))
                self.add_event(db,project["id"],"revision_published",user,number,timestamp)
                updated = db.execute("SELECT * FROM projects WHERE id=?",(project["id"],)).fetchone()
                db.commit()
                self.send_json(201,{"revision":{"number":number,"title":title,"summary":summary,"publishedAt":timestamp},"project":project_data(updated)})
            elif endpoint == "decision":
                if user["role"] != "client":
                    raise APIError(403,"forbidden","Only the project client can submit a review decision.")
                revision = revision_field(body,"revision")
                decision = body.get("decision")
                if not isinstance(decision,str) or decision not in ("approve","request_changes"):
                    raise APIError(400,"invalid_input","decision must be approve or request_changes.")
                note = text_field(body,"note",2000,empty=decision=="approve")
                if revision != project["current_revision"] or project["status"] != "awaiting_review":
                    raise APIError(409,"decision_conflict","This review has changed or already been finalized. Refresh to review the current state.")
                status = "approved" if decision=="approve" else "changes_requested"
                db.execute("INSERT INTO decisions VALUES (?,?,?,?,?,?)",(project["id"],revision,decision,note,user["id"],timestamp))
                db.execute("UPDATE projects SET status=? WHERE id=?",(status,project["id"]))
                self.add_event(db,project["id"],"decision_submitted",user,revision,timestamp,decision=decision,note=note)
                updated = db.execute("SELECT * FROM projects WHERE id=?",(project["id"],)).fetchone()
                db.commit()
                self.send_json(200,{"project":project_data(updated)})
            elif endpoint == "comments":
                body_text = text_field(body,"body",2000)
                ident = secrets.token_hex(12)
                db.execute("INSERT INTO comments (id,project_id,body,author_id,created_at) VALUES (?,?,?,?,?)",(ident,project["id"],body_text,user["id"],timestamp))
                self.add_event(db,project["id"],"comment_added",user,project["current_revision"],timestamp,commentId=ident)
                db.commit()
                self.send_json(201,{"comment":{"id":ident,"body":body_text,"author":{"id":user["id"],"name":user["name"],"role":user["role"]},"createdAt":timestamp}})
            else:
                raise APIError(404,"not_found","API route not found.")

    def static(self):
        if self.command not in ("GET","HEAD"):
            raise APIError(405,"method_not_allowed","Use GET for public assets.")
        path = unquote(urlsplit(self.path).path)
        if "\x00" in path or "\\" in path or any(part == ".." for part in path.split("/")):
            raise APIError(404,"not_found","Asset not found.")
        target = (PUBLIC / ("index.html" if path=="/" else path.lstrip("/"))).resolve()
        if not target.is_relative_to(PUBLIC.resolve()) or not target.is_file():
            raise APIError(404,"not_found","Asset not found.")
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type",mimetypes.guess_type(target.name)[0] or "application/octet-stream")
        self.send_header("Content-Length",str(len(data)))
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Cache-Control","no-cache")
        self.send_header("Referrer-Policy","same-origin")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def handle_portal(self):
        self.connection.settimeout(15)
        try:
            if urlsplit(self.path).path.startswith("/api/"):
                self.api()
            else:
                self.static()
        except APIError as error:
            self.send_json(error.status,{"error":{"code":error.code,"message":error.message}})
        except (BrokenPipeError,ConnectionResetError,TimeoutError):
            return
        except Exception as error:
            sys.stderr.write(f"Request failed: {type(error).__name__}\n")
            self.send_json(500,{"error":{"code":"internal_error","message":"The request could not be completed. Please try again."}})

    do_GET = handle_portal
    do_POST = handle_portal
    do_HEAD = handle_portal
    do_PUT = handle_portal
    do_PATCH = handle_portal
    do_DELETE = handle_portal
    do_OPTIONS = handle_portal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host",default="127.0.0.1")
    parser.add_argument("--port",type=int,default=8000)
    parser.add_argument("--db",default="demo.sqlite3")
    args = parser.parse_args()
    if args.host == "localhost":
        args.host = "127.0.0.1"
    try:
        loopback = ipaddress.ip_address(args.host).is_loopback
    except ValueError:
        loopback = False
    if not loopback or ":" in args.host or not 0 <= args.port <= 65535:
        parser.error("Use an IPv4 loopback host and a port from 0 to 65535.")
    initialize(args.db)
    server = PortalServer((args.host,args.port),args.db)
    print(json.dumps({"ready":True,"port":server.server_port}),flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
