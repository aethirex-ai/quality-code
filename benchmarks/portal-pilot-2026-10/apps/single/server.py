#!/usr/bin/env python3
"""A synthetic loopback studio portal. Python stdlib + durable SQLite only."""
import argparse
import hashlib
import hmac
import json
import logging
import secrets
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from http.cookies import SimpleCookie, CookieError
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
SESSION_SECONDS = 7 * 24 * 3600


def now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def connect(path):
    db = sqlite3.connect(path, timeout=15, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db


@contextmanager
def transaction(db):
    db.execute("BEGIN IMMEDIATE")
    try:
        yield
        db.execute("COMMIT")
    except BaseException:
        db.execute("ROLLBACK")
        raise


def password_hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 240000).hex()


def initialize(path):
    db = connect(path)
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, name TEXT NOT NULL,
          email TEXT UNIQUE NOT NULL, role TEXT NOT NULL CHECK(role IN ('client','staff')),
          salt TEXT NOT NULL, verifier TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,
          user_id TEXT NOT NULL REFERENCES users(id), expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, client_id TEXT NOT NULL REFERENCES users(id),
          title TEXT NOT NULL, client_name TEXT NOT NULL, budget_cents INTEGER NOT NULL,
          progress INTEGER NOT NULL, status TEXT NOT NULL, current_revision INTEGER NOT NULL,
          next_milestone TEXT NOT NULL, brief TEXT NOT NULL, deliverables TEXT NOT NULL, timeline TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS revisions(project_id TEXT NOT NULL REFERENCES projects(id),
          number INTEGER NOT NULL, title TEXT NOT NULL, summary TEXT NOT NULL, published_at TEXT NOT NULL,
          PRIMARY KEY(project_id,number));
        CREATE TABLE IF NOT EXISTS decisions(project_id TEXT NOT NULL, revision INTEGER NOT NULL,
          decision TEXT NOT NULL, note TEXT NOT NULL, author_id TEXT NOT NULL REFERENCES users(id),
          created_at TEXT NOT NULL, PRIMARY KEY(project_id,revision),
          FOREIGN KEY(project_id,revision) REFERENCES revisions(project_id,number));
        CREATE TABLE IF NOT EXISTS comments(seq INTEGER PRIMARY KEY AUTOINCREMENT,
          id TEXT UNIQUE NOT NULL, project_id TEXT NOT NULL REFERENCES projects(id),
          body TEXT NOT NULL, author_id TEXT NOT NULL REFERENCES users(id), created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,
          id TEXT UNIQUE NOT NULL, project_id TEXT NOT NULL REFERENCES projects(id),
          type TEXT NOT NULL, actor_id TEXT NOT NULL REFERENCES users(id), revision INTEGER NOT NULL,
          created_at TEXT NOT NULL, details TEXT NOT NULL);
    """)
    with transaction(db):
        if not db.execute("SELECT 1 FROM meta WHERE key='seeded'").fetchone():
            for ident, name, email, role, password in [
                ("s1", "AethDesign Studio", "studio@aethdesign.test", "staff", "StudioDemo!42"),
                ("c1", "Alex Morgan", "alex@harbor.test", "client", "HarborDemo!42"),
                ("c2", "Sam Ellis", "sam@northline.test", "client", "NorthDemo!42"),
            ]:
                salt = secrets.token_hex(16)
                db.execute("INSERT INTO users VALUES (?,?,?,?,?,?)", (ident,name,email,role,salt,password_hash(password,salt)))
            seeds = [
                ("p1", "c1", "Harbor House Identity", "Harbor House", 420000, 65, "awaiting_review", 1, "Identity review",
                 "An identity for a quieter kind of hospitality. Harbor House brings the warmth of a coastal home to a considered guest experience. Our direction pairs an architectural monogram with expressive serif typography and a palette drawn from stone, salt and olive groves.",
                 ["Primary wordmark & architectural monogram", "Warm-neutral colour & typography system", "Stationery, room keys & guest welcome kit", "Identity guidelines & application templates"],
                 [{"title":"Discovery & positioning","status":"complete"},{"title":"Identity exploration","status":"complete"},{"title":"Identity review","status":"current"},{"title":"Guidelines & handoff","status":"upcoming"}]),
                ("p2", "c1", "Harbor Digital Experience", "Harbor House", 780000, 90, "approved", 2, "Handoff preparation",
                 "A digital arrival that feels as thoughtful as the stay itself. The approved experience balances atmospheric editorial storytelling with a clear path through rooms, local experiences and practical guest information. The final system is ready for your development team.",
                 ["Responsive website design system", "Room & experience page layouts", "Accessible navigation & booking entry design", "Developer specifications & component library"],
                 [{"title":"Experience mapping","status":"complete"},{"title":"Digital design direction","status":"complete"},{"title":"Final design approval","status":"complete"},{"title":"Handoff preparation","status":"current"}]),
                ("p3", "c2", "Northline Editorial", "Northline", 360000, 40, "awaiting_review", 1, "Editorial review",
                 "A journal for the curious and the outdoors-inclined. Northline's editorial system uses a confident grid, generous margins and a distinctive typographic voice to bring field notes, long-form essays and photography into a single, flexible publication.",
                 ["Journal masthead & typographic hierarchy", "Modular editorial grid & feature layouts", "Issue one cover & contents system", "Print-ready template specifications"],
                 [{"title":"Editorial strategy","status":"complete"},{"title":"Grid & type exploration","status":"complete"},{"title":"Editorial review","status":"current"},{"title":"Issue one production","status":"upcoming"}]),
            ]
            for p in seeds:
                db.execute("INSERT INTO projects VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (*p[:10], json.dumps(p[10]), json.dumps(p[11])))
            revisions = [
                ("p1",1,"Identity direction","A sculptural H monogram, a warm olive palette and a welcoming serif wordmark. Review the direction for character, legibility and its fit with the Harbor House guest experience.","2026-10-08T09:00:00Z"),
                ("p2",1,"Digital foundations","An editorial homepage and clear room discovery flow, with a reusable component library for the guest experience.","2026-10-02T10:00:00Z"),
                ("p2",2,"Refined digital experience","A calmer navigation, improved room comparison and fully responsive page layouts. Your feedback from the first review is incorporated throughout.","2026-10-09T10:00:00Z"),
                ("p3",1,"Editorial system","A flexible twelve-column grid, a bold masthead and three feature layouts designed to balance field photography with long-form reading.","2026-10-10T09:00:00Z"),
            ]
            db.executemany("INSERT INTO revisions VALUES (?,?,?,?,?)", revisions)
            db.execute("INSERT INTO decisions VALUES (?,?,?,?,?,?)", ("p2",2,"approve","The refined navigation feels right. Ready for handoff.","c1","2026-10-10T14:00:00Z"))
            for ident, text in [("p1","The first identity direction is ready. We would love your thoughts on the monogram and the warmth of the palette."), ("p2","The final digital layouts are approved. We are preparing the component notes for handoff."), ("p3","The editorial system is ready for a first look. The feature layouts show how the grid adapts to different story lengths.")]:
                db.execute("INSERT INTO comments(id,project_id,body,author_id,created_at) VALUES (?,?,?,?,?)", ("seed-"+ident,ident,text,"s1","2026-10-11T10:00:00Z"))
            for ident, num, title, summary, stamp in revisions:
                add_event(db,ident,"revision_published","s1",num,stamp,{"title":title})
            add_event(db,"p2","decision_submitted","c1",2,"2026-10-10T14:00:00Z",{"decision":"approve"})
            db.execute("INSERT INTO meta VALUES ('seeded','1')")
    db.close()


def public_user(row):
    return {key: row[key] for key in ("id", "name", "email", "role")}


def actor(db, ident):
    row = db.execute("SELECT id,name,role FROM users WHERE id=?", (ident,)).fetchone()
    return dict(row)


def project_json(row, detail=False):
    result = {"id":row["id"],"title":row["title"],"clientId":row["client_id"],"clientName":row["client_name"],
              "budgetCents":row["budget_cents"],"progress":row["progress"],"status":row["status"],
              "currentRevision":row["current_revision"],"nextMilestone":row["next_milestone"]}
    if detail:
        result.update(brief=row["brief"],deliverables=json.loads(row["deliverables"]),timeline=json.loads(row["timeline"]))
    return result


def add_event(db, project, kind, user, revision, stamp, details):
    db.execute("INSERT INTO events(id,project_id,type,actor_id,revision,created_at,details) VALUES (?,?,?,?,?,?,?)",
               (secrets.token_hex(12),project,kind,user,revision,stamp,json.dumps(details)))


class APIError(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message


def text_field(body, key, maximum, empty=False, trim=True):
    value = body.get(key)
    if not isinstance(value,str):
        raise APIError(400,"invalid_field",f"{key} must be text.")
    value = value.strip() if trim else value
    if len(value)>maximum or (not empty and not value.strip()):
        raise APIError(400,"invalid_field",f"{key} must contain {'0' if empty else '1'}–{maximum} characters.")
    return value


def revision_field(body, key):
    value = body.get(key)
    if type(value) is not int or value < 1 or value > 2147483647:
        raise APIError(400,"invalid_revision",f"{key} must be a positive integer.")
    return value


def allowed_host(host, port):
    hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
    if port == 80:
        hosts.update(("127.0.0.1", "localhost"))
    return host in hosts


class Handler(BaseHTTPRequestHandler):
    server_version = "AtelierLocal"
    sys_version = ""

    def setup(self):
        super().setup()
        self.connection.settimeout(15)

    def send_json(self, status, data, cookie=None):
        raw = json.dumps(data,ensure_ascii=True).encode()
        self.send_response(status)
        self.common_headers()
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(raw)))
        if cookie:
            self.send_header("Set-Cookie",cookie)
        self.end_headers()
        self.wfile.write(raw)

    def common_headers(self):
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Referrer-Policy","same-origin")
        self.send_header("X-Frame-Options","DENY")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; font-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")

    def do_GET(self):
        self.dispatch(False)

    def do_POST(self):
        self.dispatch(True)

    def do_PUT(self):
        self.send_json(405,{"error":{"code":"method_not_allowed","message":"Use the documented API method."}})

    do_DELETE = do_PUT
    do_PATCH = do_PUT
    do_OPTIONS = do_PUT

    def dispatch(self, write):
        db = None
        try:
            port = self.server.server_port
            host = self.headers.get("Host","")
            if not allowed_host(host, port):
                raise APIError(403,"invalid_host","This demo accepts loopback requests only.")
            if write:
                origin = self.headers.get("Origin")
                if origin is not None and origin != "http://"+host:
                    raise APIError(403,"cross_origin","Cross-origin changes are not allowed.")
                if self.headers.get("Content-Type","").split(";",1)[0].strip().lower() != "application/json":
                    raise APIError(415,"json_required","Send changes as application/json.")
            path = urlsplit(self.path).path
            if not path.startswith("/api/"):
                if write:
                    raise APIError(404,"not_found","This page does not accept changes.")
                return self.static(path)
            db = connect(self.server.db_path)
            if path == "/api/login" and write:
                return self.login(db,self.read_body())
            user = self.authenticate(db)
            if path == "/api/me" and not write:
                return self.send_json(200,{"user":public_user(user)})
            if path == "/api/logout" and write:
                self.read_body()
                db.execute("DELETE FROM sessions WHERE token_hash=?", (self.session_hash(),))
                return self.send_json(200,{"ok":True},"atelier_session=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0")
            if path == "/api/projects" and not write:
                rows = db.execute("SELECT * FROM projects WHERE ?='staff' OR client_id=? ORDER BY id", (user["role"],user["id"])).fetchall()
                return self.send_json(200,{"projects":[project_json(r) for r in rows]})
            match = re.fullmatch(r"/api/projects/([A-Za-z0-9_-]{1,80})(?:/(revisions|decision|comments|activity))?",path)
            if not match:
                raise APIError(404,"not_found","The requested resource was not found.")
            ident, action = match.groups()
            if write:
                body = self.read_body()
                with transaction(db):
                    project = self.authorize(db,ident,user)
                    status, result = self.mutate(db,project,user,action,body)
                return self.send_json(status,result)
            project = self.authorize(db,ident,user)
            if action is None:
                return self.send_json(200,{"project":project_json(project,True)})
            if action == "revisions":
                rows = db.execute("SELECT * FROM revisions WHERE project_id=? ORDER BY number",(ident,)).fetchall()
                result=[]
                for row in rows:
                    item={"number":row["number"],"title":row["title"],"summary":row["summary"],"publishedAt":row["published_at"]}
                    d=db.execute("SELECT * FROM decisions WHERE project_id=? AND revision=?",(ident,row["number"])).fetchone()
                    if d:
                        item["decision"]={"decision":d["decision"],"note":d["note"],"author":actor(db,d["author_id"]),"createdAt":d["created_at"]}
                    result.append(item)
                return self.send_json(200,{"revisions":result})
            if action == "comments":
                return self.send_json(200,{"comments":[self.comment_json(db,r) for r in db.execute("SELECT * FROM comments WHERE project_id=? ORDER BY created_at,seq",(ident,))]})
            if action == "activity":
                events=[]
                for row in db.execute("SELECT * FROM events WHERE project_id=? ORDER BY created_at,seq",(ident,)):
                    events.append({"id":row["id"],"type":row["type"],"actor":actor(db,row["actor_id"]),"revision":row["revision"],"createdAt":row["created_at"],**json.loads(row["details"])})
                return self.send_json(200,{"events":events})
            raise APIError(405,"method_not_allowed","Use the documented API method.")
        except APIError as exc:
            self.send_json(exc.status,{"error":{"code":exc.code,"message":exc.message}})
        except (BrokenPipeError,ConnectionResetError,TimeoutError):
            pass
        except Exception:
            logging.exception("Local request failed")
            self.send_json(500,{"error":{"code":"server_error","message":"The local server could not complete this request. Please try again."}})
        finally:
            if db is not None:
                db.close()

    def read_body(self):
        try:
            length=int(self.headers.get("Content-Length","0"))
            if self.headers.get("Transfer-Encoding") or not 0 < length <= 16384:
                raise ValueError()
            raw=self.rfile.read(length)
            if len(raw) != length:
                raise ValueError()
            def reject_constant(value):
                raise ValueError(value)
            result=json.loads(raw,parse_constant=reject_constant)
            if not isinstance(result,dict):
                raise ValueError()
            return result
        except (ValueError,UnicodeError,RecursionError):
            raise APIError(400,"invalid_json","Send a JSON object of at most 16 KiB with valid field values.") from None

    def session_hash(self):
        try:
            cookie=SimpleCookie()
            cookie.load(self.headers.get("Cookie",""))
            value=cookie["atelier_session"].value if "atelier_session" in cookie else ""
        except CookieError:
            value=""
        return hashlib.sha256(value.encode()).hexdigest()

    def authenticate(self,db):
        user=db.execute("SELECT u.* FROM users u JOIN sessions s ON s.user_id=u.id WHERE s.token_hash=? AND s.expires>?",(self.session_hash(),time.time())).fetchone()
        if user is None:
            raise APIError(401,"unauthenticated","Please sign in to your Atelier workspace.")
        return user

    def login(self,db,body):
        email=text_field(body,"email",254).lower()
        password=text_field(body,"password",256,trim=False)
        row=db.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
        salt=row["salt"] if row else "0"*32
        verifier=password_hash(password,salt)
        if not row or not hmac.compare_digest(verifier,row["verifier"]):
            raise APIError(401,"invalid_credentials","The email or password is incorrect. Please try again.")
        token=secrets.token_urlsafe(32)
        with transaction(db):
            db.execute("DELETE FROM sessions WHERE expires<=? OR token_hash=?",(time.time(),self.session_hash()))
            db.execute("INSERT INTO sessions VALUES (?,?,?)",(hashlib.sha256(token.encode()).hexdigest(),row["id"],time.time()+SESSION_SECONDS))
        self.send_json(200,{"user":public_user(row)},f"atelier_session={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age={SESSION_SECONDS}")

    def authorize(self,db,ident,user):
        row=db.execute("SELECT * FROM projects WHERE id=?",(ident,)).fetchone()
        if row is None or (user["role"]!="staff" and row["client_id"]!=user["id"]):
            raise APIError(404,"not_found","This project was not found in your workspace.")
        return row

    def comment_json(self,db,row):
        return {"id":row["id"],"body":row["body"],"author":actor(db,row["author_id"]),"createdAt":row["created_at"]}

    def mutate(self,db,p,user,action,body):
        ident, stamp=p["id"],now()
        if action == "revisions":
            if user["role"]!="staff":
                raise APIError(403,"staff_only","Only studio staff can publish a revision.")
            expected=revision_field(body,"expectedRevision")
            title=text_field(body,"title",120)
            summary=text_field(body,"summary",2000)
            if expected!=p["current_revision"]:
                raise APIError(409,"revision_conflict","A newer revision is available. Refresh and review it before publishing.")
            number=expected+1
            db.execute("INSERT INTO revisions VALUES (?,?,?,?,?)",(ident,number,title,summary,stamp))
            db.execute("UPDATE projects SET current_revision=?,status='awaiting_review' WHERE id=?",(number,ident))
            add_event(db,ident,"revision_published",user["id"],number,stamp,{"title":title})
            updated=db.execute("SELECT * FROM projects WHERE id=?",(ident,)).fetchone()
            return 201,{"revision":{"number":number,"title":title,"summary":summary,"publishedAt":stamp},"project":project_json(updated,True)}
        if action == "decision":
            if user["role"]!="client":
                raise APIError(403,"client_only","Only the project client can submit a review decision.")
            revision=revision_field(body,"revision")
            decision=body.get("decision")
            if decision not in ("approve","request_changes"):
                raise APIError(400,"invalid_decision","Choose approve or request_changes.")
            note=text_field(body,"note",2000,empty=decision=="approve")
            if revision!=p["current_revision"] or p["status"]!="awaiting_review":
                raise APIError(409,"review_conflict","This review has changed or is already complete. The latest project state has been loaded; review it before deciding.")
            status="approved" if decision=="approve" else "changes_requested"
            db.execute("INSERT INTO decisions VALUES (?,?,?,?,?,?)",(ident,revision,decision,note,user["id"],stamp))
            db.execute("UPDATE projects SET status=? WHERE id=?",(status,ident))
            add_event(db,ident,"decision_submitted",user["id"],revision,stamp,{"decision":decision})
            return 200,{"project":project_json(db.execute("SELECT * FROM projects WHERE id=?",(ident,)).fetchone(),True)}
        if action == "comments":
            body_text=text_field(body,"body",2000)
            comment_id=secrets.token_hex(12)
            db.execute("INSERT INTO comments(id,project_id,body,author_id,created_at) VALUES (?,?,?,?,?)",(comment_id,ident,body_text,user["id"],stamp))
            add_event(db,ident,"comment_added",user["id"],p["current_revision"],stamp,{"commentId":comment_id})
            row=db.execute("SELECT * FROM comments WHERE id=?",(comment_id,)).fetchone()
            return 201,{"comment":self.comment_json(db,row)}
        raise APIError(405,"method_not_allowed","This resource does not accept that change.")

    def static(self,path):
        assets={"/app.js":("app.js","text/javascript"),"/style.css":("style.css","text/css"),"/favicon.svg":("favicon.svg","image/svg+xml")}
        if path in assets:
            name,mime=assets[path]
        elif path in ("/","/login","/projects","/studio") or re.fullmatch(r"/projects/[A-Za-z0-9_-]{1,80}",path):
            name,mime="index.html","text/html"
        else:
            raise APIError(404,"not_found","This page was not found.")
        raw=(ROOT/"public"/name).read_bytes()
        self.send_response(200)
        self.common_headers()
        self.send_header("Content-Type",mime+"; charset=utf-8")
        self.send_header("Cache-Control","no-cache")
        self.send_header("Content-Length",str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host",choices=("127.0.0.1","localhost"),default="127.0.0.1")
    parser.add_argument("--port",type=int,default=8000)
    parser.add_argument("--db",type=Path,default=Path("demo.sqlite3"))
    args=parser.parse_args()
    if not 0<=args.port<=65535:
        parser.error("port must be 0–65535")
    args.db=args.db.resolve()
    args.db.parent.mkdir(parents=True,exist_ok=True)
    initialize(args.db)
    server=ThreadingHTTPServer((args.host,args.port),Handler)
    server.daemon_threads=True
    server.db_path=args.db
    print(json.dumps({"ready":True,"port":server.server_port}),flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
