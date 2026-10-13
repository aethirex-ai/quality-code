export class ApiError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}
export async function request(path, options = {}) {
  const response = await fetch(path, {credentials: 'same-origin', headers: {'Content-Type': 'application/json'}, ...options});
  let data;
  try { data = await response.json(); } catch { throw new ApiError(response.status, 'The workspace could not read the response. Please try again.'); }
  if (!response.ok) throw new ApiError(response.status, data.error?.message || 'The request could not be completed.');
  return data;
}
export class Workspace {
  constructor(api = request, notify = () => {}) {
    this.api = api; this.notify = notify; this.accountEpoch = 0; this.viewEpoch = 0; this.refreshSequence = 0;
    this.user = null; this.projects = []; this.detail = null; this.selectedId = null; this.tab = 'brief';
    this.loading = true; this.authBusy = false; this.error = ''; this.drafts = new Map(); this.feedback = new Map(); this.pending = new Map();
  }
  changed() { this.notify(this); }
  scope() { return {account: this.accountEpoch, view: this.viewEpoch, user: this.user?.id, project: this.selectedId}; }
  sameAccount(s) { return s.account === this.accountEpoch && s.user === this.user?.id; }
  current(s) { return this.sameAccount(s) && s.view === this.viewEpoch && s.project === this.selectedId; }
  key(project = this.selectedId) { return `${this.user?.id}:${project}`; }
  draft(field, value, project = this.selectedId) {
    const key = `${this.key(project)}:${field}`;
    if (value !== undefined) this.drafts.set(key, value);
    return this.drafts.get(key) || '';
  }
  message(kind, project = this.selectedId) { return this.feedback.get(`${this.key(project)}:${kind}`); }
  setMessage(kind, message, project = this.selectedId) { this.feedback.set(`${this.key(project)}:${kind}`, message); }
  reset() {
    this.accountEpoch++; this.viewEpoch++; this.refreshSequence++;
    this.user = null; this.projects = []; this.detail = null; this.selectedId = null; this.tab = 'brief';
    this.error = ''; this.drafts.clear(); this.feedback.clear(); this.pending.clear();
  }
  async boot(selection = () => null) {
    const epoch = this.accountEpoch;
    try {
      const {user} = await this.api('/api/me');
      if (epoch !== this.accountEpoch) return;
      this.user = user;
      await this.loadProjects(selection);
    } catch (e) { if (epoch === this.accountEpoch && e.status !== 401) this.error = e.message; }
    finally { if (epoch === this.accountEpoch) { this.loading = false; this.changed(); } }
  }
  async login(email, password, selection = () => null) {
    if (this.authBusy) return;
    this.reset(); this.authBusy = true; this.loading = false; const epoch = this.accountEpoch; this.changed();
    try {
      const {user} = await this.api('/api/login', {method: 'POST', body: JSON.stringify({email, password})});
      if (epoch !== this.accountEpoch) return;
      this.user = user; this.changed(); await this.loadProjects(selection);
    } catch (e) { if (epoch === this.accountEpoch) this.error = e.message; }
    finally { if (epoch === this.accountEpoch) { this.authBusy = false; this.changed(); } }
  }
  async logout() {
    if (this.authBusy) return;
    this.reset(); this.authBusy = true; this.loading = false; const epoch = this.accountEpoch; this.changed();
    try { await this.api('/api/logout', {method:'POST', body:'{}'}); }
    catch (e) { if (epoch === this.accountEpoch) this.error = 'Sign-out could not be confirmed. Retry before switching accounts.'; }
    finally { if (epoch === this.accountEpoch) { this.authBusy = false; this.changed(); } }
  }
  async loadProjects(selection = () => null) {
    const scope = this.scope(); this.loading = true; this.error = ''; this.changed();
    try {
      const {projects} = await this.api('/api/projects');
      if (!this.current(scope)) return;
      this.projects = projects;
      const saved = selection(this.user);
      if (saved && projects.some(p => p.id === saved.project)) { await this.open(saved.project, saved.tab); return; }
    } catch (e) { if (this.current(scope)) this.error = e.message; }
    finally { if (this.current(scope)) { this.loading = false; this.changed(); } }
  }
  async open(id, tab = 'brief') {
    if (!this.projects.some(p => p.id === id)) return;
    this.viewEpoch++; this.selectedId = id; this.tab = ['brief','revisions','discussion','activity'].includes(tab) ? tab : 'brief';
    this.detail = null; this.error = ''; this.loading = true; this.changed();
    await this.refresh();
  }
  overview() { this.viewEpoch++; this.refreshSequence++; this.selectedId = null; this.detail = null; this.loading = false; this.error = ''; this.changed(); }
  setTab(tab) { if (['brief','revisions','discussion','activity'].includes(tab)) { this.tab = tab; this.changed(); } }
  async refresh() {
    if (!this.selectedId || !this.user) return false;
    const scope = this.scope(), sequence = ++this.refreshSequence, path = `/api/projects/${scope.project}`;
    try {
      const results = await Promise.all([this.api(path), this.api(path+'/revisions'), this.api(path+'/comments'), this.api(path+'/activity')]);
      if (!this.current(scope) || sequence !== this.refreshSequence) return false;
      const [p,r,c,a] = results; this.detail = {project:p.project, revisions:r.revisions, comments:c.comments, events:a.events};
      this.projects = this.projects.map(old => old.id === p.project.id ? {...old, ...p.project} : old);
      this.error = '';
      for (const kind of ['comment','decision','revision']) {
        if (this.message(kind)?.recover) {
          const prior=this.message(kind);
          this.setMessage(kind, {state:prior.state,text:prior.state==='success'?{comment:'Comment saved. Project is up to date.',decision:'Review decision saved. Project is up to date.',revision:'New revision published. Project is up to date.'}[kind]:'Project is up to date. Your draft is preserved; review the latest direction before submitting.',recover:false});
        }
      }
      return true;
    } catch (e) {
      if (this.current(scope) && sequence === this.refreshSequence) this.error = e.message;
      return false;
    } finally { if (this.current(scope) && sequence === this.refreshSequence) { this.loading = false; this.changed(); } }
  }
  async mutate(kind, payload, fields = {}) {
    if (!this.user || !this.detail || this.pending.has(this.key())) return;
    const scope = this.scope(), key = this.key(), token = Symbol(kind), path = `/api/projects/${scope.project}`;
    this.pending.set(key, token); this.setMessage(kind, {state:'pending', text:'Saving…'}); this.changed();
    let committed = false;
    try {
      const suffix = {comment:'/comments', decision:'/decision', revision:'/revisions'}[kind];
      const result = await this.api(path+suffix, {method:'POST', body:JSON.stringify(payload)});
      if (!this.sameAccount(scope)) return;
      committed = true;
      for (const [field,value] of Object.entries(fields)) if (this.draft(field, undefined, scope.project) === value) this.draft(field, '', scope.project);
      this.setMessage(kind, {state:'success', text:{comment:'Comment saved.', decision:'Review decision saved.', revision:'New revision published.'}[kind]}, scope.project);
      if (!this.current(scope)) return;
      if (result.project) {
        this.detail.project = {...this.detail.project, ...result.project};
        this.projects = this.projects.map(p => p.id === scope.project ? {...p,...result.project} : p);
      }
      if (result.comment) this.detail.comments.push(result.comment);
      if (result.revision) this.detail.revisions.push(result.revision);
      if (result.event && !this.detail.events.some(event => event.id === result.event.id)) this.detail.events.push(result.event);
      this.changed();
      const refreshed = await this.refresh();
      if (!this.current(scope)) return;
      if (!refreshed) this.setMessage(kind, {state:'success', text:'Saved successfully. The latest activity could not be loaded. Refresh to recover; your submission is already stored.', recover:true});
    } catch (e) {
      if (!this.sameAccount(scope)) return;
      this.setMessage(kind, {state:'error', text:e.status === 409 ? 'This review has changed. Your draft is preserved. Loading the latest revision before you continue…' : e.message}, scope.project);
      if (!this.current(scope)) return;
      if (e.status === 409) {
        const refreshed = await this.refresh();
        if (!this.current(scope)) return;
        this.setMessage(kind, {state:'error', text:refreshed ? 'This review changed in another session. Check the latest revision; your draft is preserved.' : 'This review changed. Your draft is preserved. Refresh the project before submitting again.', recover:!refreshed});
      }
    } finally {
      if (this.sameAccount(scope) && this.pending.get(key) === token) {
        this.pending.delete(key);
        // Render current state only: a returned-to project must unlock its controls.
        this.changed();
      }
    }
    return committed;
  }
}
