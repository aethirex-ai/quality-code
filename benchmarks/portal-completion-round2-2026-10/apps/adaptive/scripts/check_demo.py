"""Confirm actual browser mutations through the assigned loopback API and SQLite."""
import http.client
import json
import os
import sqlite3
from pathlib import Path

def main():
    port=int(os.environ['PORTAL_PORT']); cookie=''
    def api(method,path,body=None):
        nonlocal cookie
        conn=http.client.HTTPConnection('127.0.0.1',port,timeout=10)
        headers={'Content-Type':'application/json'}
        if cookie:headers['Cookie']=cookie
        conn.request(method,path,json.dumps(body) if body is not None else None,headers)
        response=conn.getresponse();data=json.loads(response.read());next_cookie=response.getheader('Set-Cookie')
        if next_cookie:cookie=next_cookie.split(';')[0]
        conn.close();assert response.status in (200,201),(response.status,data);return data
    api('POST','/api/login',{'email':'studio@aethdesign.test','password':'StudioDemo!42'})
    projects=api('GET','/api/projects')['projects'];assert [p['id'] for p in projects]==['p1','p2','p3']
    p=api('GET','/api/projects/p1')['project'];assert (p['currentRevision'],p['status'],p['budgetCents'])==(2,'approved',420000)
    revisions=api('GET','/api/projects/p1/revisions')['revisions'];assert [r['number'] for r in revisions]==[1,2]
    comments=api('GET','/api/projects/p1/comments')['comments'];assert any('<img src=x onerror=alert(1)>' in c['body'] and c['author']['id']=='c1' for c in comments)
    events=api('GET','/api/projects/p1/activity')['events'];assert [e['decision'] for e in events if e['type']=='decision_submitted']==['request_changes','approve']
    assert len([e for e in events if e['type']=='revision_published'])==1
    assert len([e for e in events if e['type']=='comment_added'])==len(comments)
    with sqlite3.connect(Path('demo.sqlite3')) as conn:
        decisions=conn.execute('SELECT revision,decision FROM decisions WHERE project_id=? ORDER BY revision',('p1',)).fetchall()
        assert decisions==[(1,'request_changes'),(2,'approve')],decisions
    api('POST','/api/logout',{})
    print(json.dumps({'project':'p1','revision':2,'status':'approved','moneyCents':420000,'storedDecisions':decisions,'comments':len(comments),'events':len(events),'exactlyOneEventPerWrite':True}))
if __name__=='__main__':main()
