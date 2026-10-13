"""Real HTTP regressions for the local portal's auth and transactional state."""
import concurrent.futures
import http.client
import json
import os
import select
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCOUNTS = {
    "staff":("studio@aethdesign.test","StudioDemo!42"),
    "c1":("alex@harbor.test","HarborDemo!42"),
    "c2":("sam@northline.test","NorthDemo!42"),
}


class BackendContract(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.db = str(Path(self.folder.name)/"portal.sqlite3")
        self.process = None
        self.start()

    def start(self):
        self.process = subprocess.Popen([sys.executable,str(ROOT/"server.py"),"--host","127.0.0.1","--port","0","--db",self.db],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
        ready, _, _ = select.select([self.process.stdout],[],[],10)
        self.assertTrue(ready,"Server did not produce readiness within ten seconds")
        line = self.process.stdout.readline()
        self.assertTrue(line,"Server exited before readiness")
        data = json.loads(line)
        self.assertEqual(data["ready"],True)
        self.port = data["port"]
        self.assertGreater(self.port,0)

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            self.process.stdout.close()
            self.process = None

    def tearDown(self):
        self.stop()
        self.folder.cleanup()

    def request(self, method, path, body=None, cookie=None, headers=None, raw=None):
        connection = http.client.HTTPConnection("127.0.0.1",self.port,timeout=10)
        request_headers = {"Content-Type":"application/json"} if method=="POST" else {}
        if cookie:
            request_headers["Cookie"] = cookie
        request_headers.update(headers or {})
        payload = raw if raw is not None else json.dumps(body) if body is not None else None
        connection.request(method,path,payload,request_headers)
        response = connection.getresponse()
        content = response.read()
        status, response_headers = response.status, dict(response.getheaders())
        connection.close()
        data = json.loads(content) if response_headers.get("Content-Type","").startswith("application/json") else content
        if status>=400:
            self.assertIsInstance(data,dict)
            self.assertIsInstance(data.get("error",{}).get("code"),str)
            self.assertIsInstance(data["error"].get("message"),str)
            self.assertNotIn("Traceback",data["error"]["message"])
        return status,data,response_headers

    def login(self, name):
        email,password = ACCOUNTS[name]
        status,data,headers = self.request("POST","/api/login",{"email":email,"password":password})
        self.assertEqual(status,200)
        self.assertEqual(data["user"]["role"],"staff" if name=="staff" else "client")
        cookie = headers["Set-Cookie"]
        for required in ("Path=/","HttpOnly","SameSite=Lax"):
            self.assertIn(required,cookie)
        return cookie.split(";",1)[0]

    def get(self,path,cookie):
        status,data,_ = self.request("GET",path,cookie=cookie)
        self.assertEqual(status,200)
        return data

    def events(self,cookie,project="p1"):
        return self.get(f"/api/projects/{project}/activity",cookie)["events"]

    def publish(self,cookie,expected=1,project="p1"):
        return self.request("POST",f"/api/projects/{project}/revisions",{"expectedRevision":expected,"title":"  Refined direction  ","summary":"  Refined typography and responsive layouts.  "},cookie)

    def test_seed_auth_permissions_and_secure_verifiers(self):
        self.assertEqual(self.request("GET","/api/projects")[0],401)
        self.assertEqual(self.request("GET","/api/me",cookie="atelier_session=staff")[0],401)
        self.assertEqual(self.request("POST","/api/login",{"email":ACCOUNTS["c1"][0],"password":"wrong"})[0],401)
        staff,c1,c2 = self.login("staff"),self.login("c1"),self.login("c2")
        self.assertEqual(self.get("/api/me",c1)["user"]["id"],"c1")
        for cookie,expected in [(staff,["p1","p2","p3"]),(c1,["p1","p2"]),(c2,["p3"])]:
            projects = self.get("/api/projects",cookie)["projects"]
            self.assertEqual([p["id"] for p in projects],expected)
            self.assertNotIn("password",json.dumps(projects))
        expected = {"p1":("awaiting_review",1,420000,65),"p2":("approved",2,780000,90),"p3":("awaiting_review",1,360000,40)}
        for ident,values in expected.items():
            project = self.get("/api/projects/"+ident,staff)["project"]
            self.assertEqual(tuple(project[k] for k in ("status","currentRevision","budgetCents","progress")),values)
            self.assertGreaterEqual(len(project["deliverables"]),3)
            self.assertGreaterEqual(len(project["timeline"]),3)
            self.assertTrue(project["brief"])
            self.assertEqual(len(self.get(f"/api/projects/{ident}/comments",staff)["comments"]),1)
            revisions = self.get(f"/api/projects/{ident}/revisions",staff)["revisions"]
            self.assertEqual([r["number"] for r in revisions],list(range(1,values[1]+1)))
        for suffix in ("","/revisions","/comments","/activity"):
            self.assertEqual(self.request("GET","/api/projects/p3"+suffix,cookie=c1)[0],404)
        self.assertEqual(self.request("GET","/api/projects/unknown",cookie=staff)[0],404)
        self.assertEqual(self.publish(c1)[0],403)
        self.assertEqual(self.request("POST","/api/projects/p1/decision",{"revision":1,"decision":"approve","note":""},staff)[0],403)
        self.assertEqual(self.request("POST","/api/projects/p3/comments",{"body":"intrusion"},c1)[0],404)
        with sqlite3.connect(self.db) as db:
            rows = db.execute("SELECT salt,password_hash FROM accounts").fetchall()
            self.assertEqual(len({row[0] for row in rows}),3)
            self.assertTrue(all(len(salt)==32 and len(verifier)==64 for salt,verifier in rows))
            self.assertEqual(db.execute("SELECT count(*) FROM events").fetchone()[0],0)

    def test_json_origin_and_input_validation_no_partial_writes(self):
        staff,c1 = self.login("staff"),self.login("c1")
        path = "/api/projects/p1/comments"
        for raw in ("{", "[]", "null",'{"body":NaN}', '{"body":"x"' ,'{"body":true}'):
            self.assertEqual(self.request("POST",path,cookie=c1,raw=raw)[0],400)
        for body in ({},{"body":None},{"body":23},{"body":" "},{"body":"x"*2001}):
            self.assertEqual(self.request("POST",path,body,c1)[0],400)
        self.assertEqual(self.request("POST",path,{"body":"x"},c1,{"Content-Type":"text/plain"})[0],415)
        for origin in ("https://evil.test","null","http://[","http://localhost:9"):
            self.assertEqual(self.request("POST",path,{"body":"x"},c1,{"Origin":origin})[0],403)
        self.assertEqual(self.request("POST",path,cookie=c1,raw='{"body":"'+'x'*16400+'"}')[0],400)
        for value in (True,"1",0,-1,None,1.5):
            self.assertEqual(self.request("POST","/api/projects/p1/revisions",{"expectedRevision":value,"title":"Title","summary":"Summary"},staff)[0],400)
            self.assertEqual(self.request("POST","/api/projects/p1/decision",{"revision":value,"decision":"approve","note":""},c1)[0],400)
        invalid_publications = [{"expectedRevision":1,"title":" ","summary":"Summary"},{"expectedRevision":1,"title":"x"*121,"summary":"Summary"},{"expectedRevision":1,"title":"Title","summary":"x"*2001},{"expectedRevision":1,"title":"Title","summary":[]}]
        for body in invalid_publications:
            self.assertEqual(self.request("POST","/api/projects/p1/revisions",body,staff)[0],400)
        for body in ({"revision":1,"decision":"request_changes","note":" "},{"revision":1,"decision":[],"note":""},{"revision":1,"decision":"approve","note":None},{"revision":1,"decision":"approve","note":"x"*2001}):
            self.assertEqual(self.request("POST","/api/projects/p1/decision",body,c1)[0],400)
        self.assertEqual(self.events(staff),[])
        self.assertEqual(len(self.get(path,c1)["comments"]),1)
        self.assertEqual(self.get("/api/projects/p1",c1)["project"]["currentRevision"],1)
        status,_,_ = self.request("POST",path,{"body":"Same-origin comment"},c1,{"Origin":f"http://127.0.0.1:{self.port}","Content-Type":"application/json; charset=utf-8"})
        self.assertEqual(status,201)

    def test_atomic_concurrent_publication_and_stale_rejection(self):
        staff = self.login("staff")
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _:self.publish(staff),range(2)))
        self.assertEqual(sorted(result[0] for result in results),[201,409])
        revisions = self.get("/api/projects/p1/revisions",staff)["revisions"]
        self.assertEqual([r["number"] for r in revisions],[1,2])
        self.assertEqual(revisions[1]["title"],"Refined direction")
        self.assertEqual(len(self.events(staff)),1)
        self.assertEqual(self.events(staff)[0]["type"],"revision_published")
        self.assertEqual(self.publish(staff)[0],409)
        self.assertEqual(len(self.events(staff)),1)

    def test_invalid_unicode_scalar_is_bounded_input_error(self):
        staff,c1 = self.login("staff"),self.login("c1")
        invalid = "\ud800"
        cases = [
            ("/api/projects/p1/comments",{"body":invalid},c1),
            ("/api/projects/p1/revisions",{"expectedRevision":1,"title":invalid,"summary":"Summary"},staff),
            ("/api/projects/p1/revisions",{"expectedRevision":1,"title":"Title","summary":invalid},staff),
            ("/api/projects/p1/decision",{"revision":1,"decision":"approve","note":invalid},c1),
            ("/api/login",{"email":invalid,"password":"password"},None),
            ("/api/login",{"email":ACCOUNTS["c1"][0],"password":invalid},None),
        ]
        for path,body,cookie in cases:
            with self.subTest(path=path,field=next(key for key,value in body.items() if value==invalid)):
                self.assertEqual(self.request("POST",path,body,cookie)[0],400)
        self.assertEqual(self.events(staff),[])
        self.assertEqual(self.get("/api/projects/p1",c1)["project"]["currentRevision"],1)

    def test_decision_immutable_reopens_review_and_events(self):
        staff,c1 = self.login("staff"),self.login("c1")
        body = {"revision":1,"decision":"request_changes","note":"  Please increase the wordmark spacing.  "}
        status,data,_ = self.request("POST","/api/projects/p1/decision",body,c1)
        self.assertEqual(status,200)
        self.assertEqual(data["project"]["status"],"changes_requested")
        self.assertEqual(data["project"]["budgetCents"],420000)
        self.assertEqual(data["project"]["currentRevision"],1)
        for decision in ("approve","request_changes"):
            self.assertEqual(self.request("POST","/api/projects/p1/decision",{**body,"decision":decision},c1)[0],409)
        self.assertEqual(len(self.events(staff)),1)
        self.assertEqual(self.publish(staff)[0],201)
        self.assertEqual(self.request("POST","/api/projects/p1/decision",body,c1)[0],409)
        status,data,_ = self.request("POST","/api/projects/p1/decision",{"revision":2,"decision":"approve","note":""},c1)
        self.assertEqual(status,200)
        self.assertEqual(data["project"]["status"],"approved")
        decisions = self.get("/api/projects/p1",c1)["project"]["decisions"]
        self.assertEqual([d["decision"] for d in decisions],["request_changes","approve"])
        self.assertEqual(decisions[0]["note"],"Please increase the wordmark spacing.")
        events = self.events(staff)
        self.assertEqual([event["type"] for event in events],["decision_submitted","revision_published","decision_submitted"])
        self.assertEqual(events[-1]["decision"],"approve")
        self.assertEqual(self.publish(staff,expected=2)[0],201)
        self.assertEqual(self.get("/api/projects/p1",c1)["project"]["status"],"awaiting_review")
        self.assertEqual(self.publish(staff,expected=2,project="p2")[0],201)
        self.assertEqual(self.get("/api/projects/p2",c1)["project"]["decisions"][0]["decision"],"approve")

    def test_competing_decisions_produce_one_event(self):
        c1 = self.login("c1")
        def submit(decision):
            return self.request("POST","/api/projects/p1/decision",{"revision":1,"decision":decision,"note":"A review note."},c1)[0]
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(submit,["approve","request_changes"]))
        self.assertEqual(sorted(statuses),[200,409])
        self.assertEqual(len(self.events(c1)),1)
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM decisions WHERE project_id='p1'").fetchone()[0],1)

    def test_literal_comments_authorship_session_restart_and_logout(self):
        c1 = self.login("c1")
        literal = '<img src=x onerror="alert(1)"> & <script>test</script>'
        status,data,_ = self.request("POST","/api/projects/p1/comments",{"body":"  "+literal+"  ","author":{"id":"s1","role":"staff"},"role":"staff"},c1)
        self.assertEqual(status,201)
        self.assertEqual(data["comment"]["body"],literal)
        self.assertEqual(data["comment"]["author"],{"id":"c1","name":"Alex Morgan","role":"client"})
        self.assertEqual(self.events(c1)[0]["commentId"],data["comment"]["id"])
        self.assertEqual(self.request("POST","/api/projects/p1/decision",{"revision":1,"decision":"approve","note":""},c1)[0],200)
        self.stop()
        self.start()
        self.assertEqual(self.get("/api/me",c1)["user"]["id"],"c1")
        self.assertEqual(self.get("/api/projects/p1/comments",c1)["comments"][-1]["body"],literal)
        self.assertEqual(self.get("/api/projects/p1",c1)["project"]["status"],"approved")
        self.assertEqual(len(self.events(c1)),2)
        status,_,headers = self.request("POST","/api/logout",{},c1)
        self.assertEqual(status,200)
        self.assertIn("Max-Age=0",headers["Set-Cookie"])
        self.assertEqual(self.request("GET","/api/me",cookie=c1)[0],401)
        self.assertEqual(self.request("POST","/api/projects/p1/comments",{"body":"after logout"},c1)[0],401)
        self.stop()
        self.start()
        self.assertEqual(self.request("GET","/api/me",cookie=c1)[0],401)
        c2 = self.login("c2")
        self.assertEqual(self.request("GET","/api/projects/p1",cookie=c2)[0],404)

    def test_static_boundary_and_nonloopback_cli(self):
        for path in ("/server.py","/demo.sqlite3","/../server.py","/%2e%2e/server.py","/%00","/.quality/quality.toml"):
            self.assertEqual(self.request("GET",path)[0],404)
        result = subprocess.run([sys.executable,str(ROOT/"server.py"),"--host","0.0.0.0","--port","0","--db",self.db],cwd=ROOT,capture_output=True,text=True,timeout=5)
        self.assertNotEqual(result.returncode,0)
        self.assertNotIn('"ready": true',result.stdout)


if __name__ == "__main__":
    unittest.main()
