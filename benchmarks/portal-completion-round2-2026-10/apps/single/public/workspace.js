/* State owner shared by the browser and dependency-free regression tests. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.Workspace = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  class APIError extends Error {
    constructor(status, message) { super(message); this.status = status; }
  }
  async function http(path, body) {
    let response;
    try {
      response = await fetch(path, {method: body === undefined ? 'GET' : 'POST', credentials: 'same-origin',
        headers: body === undefined ? {} : {'Content-Type': 'application/json'},
        body: body === undefined ? undefined : JSON.stringify(body)});
    } catch (_) { throw new APIError(0, 'Connection interrupted. Please try again.'); }
    let data;
    try { data = await response.json(); } catch (_) { throw new APIError(response.status, 'The workspace returned an unreadable response.'); }
    if (!response.ok) throw new APIError(response.status, String(data.error?.message || 'This request could not be completed.').slice(0, 240));
    return data;
  }
  class Controller {
    constructor(api = http, changed = () => {}) {
      this.api = api; this.changed = changed;
      this.accountEpoch = 0; this.navigationEpoch = 0; this.authQueue = Promise.resolve();
      this.drafts = new Map(); this.pending = new Set(); this.notices = new Map();
      this.state = {user: null, projects: [], detail: null, projectId: null, tab: 'brief', loading: true,
        error: '', loginError: '', authBusy: false, refreshError: '', revisions: [], comments: [], events: []};
    }
    emit() { this.changed(this.state); }
    token() { return {account: this.accountEpoch, navigation: this.navigationEpoch, user: this.state.user?.id}; }
    accountLive(t) { return t.account === this.accountEpoch && t.user === this.state.user?.id; }
    live(t) { return this.accountLive(t) && t.navigation === this.navigationEpoch; }
    key(kind, pid = this.state.projectId) { return `${this.state.user?.id}:${pid}:${kind}`; }
    draft(kind) { return this.drafts.get(this.key(kind)) || ''; }
    setDraft(kind, value) { this.drafts.set(this.key(kind), value); }
    notice(kind) { return this.notices.get(this.key(kind)) || ''; }
    busy(kind) { return this.pending.has(this.key(kind)); }
    async start(selection = {}) {
      const t = this.token();
      try {
        const data = await this.api('/api/me');
        if (!this.live(t)) return;
        this.state.user = data.user;
        await this.overview(false);
        if (this.state.user && selection.projectId && this.state.projects.some(p => p.id === selection.projectId))
          await this.open(selection.projectId, selection.tab || 'brief');
      } catch (e) {
        if (!this.live(t)) return;
        this.state.loading = false;
        this.state.loginError = e.status === 401 ? '' : e.message;
        this.emit();
      }
    }
    reset() {
      this.accountEpoch++; this.navigationEpoch++;
      this.drafts.clear(); this.notices.clear(); this.pending.clear();
      Object.assign(this.state, {user: null, projects: [], detail: null, projectId: null, tab: 'brief', loading: false,
        error: '', loginError: '', refreshError: '', revisions: [], comments: [], events: []});
    }
    async login(email, password) {
      if (this.state.authBusy) return;
      this.reset(); this.state.authBusy = true; this.emit();
      const epoch = this.accountEpoch;
      const operation = async () => {
        try {
          const data = await this.api('/api/login', {email, password});
          if (epoch !== this.accountEpoch) return;
          this.state.user = data.user; this.state.authBusy = false;
          await this.overview();
        } catch (e) {
          if (epoch !== this.accountEpoch) return;
          this.state.loginError = e.message; this.state.authBusy = false; this.emit();
        }
      };
      // Serialize cookie-changing requests even if logout is slow and login is immediate.
      this.authQueue = this.authQueue.then(operation, operation);
      await this.authQueue;
    }
    async logout() {
      this.reset(); this.state.authBusy = true; this.emit();
      const epoch = this.accountEpoch;
      const operation = async () => {
        try { await this.api('/api/logout', {}); }
        catch (e) {
          if (epoch === this.accountEpoch) this.state.loginError = 'Sign-out could not be confirmed. Retry sign-out before using another account.';
          // If logout failed, a subsequent sign-in still replaces the browser cookie;
          // no old-account response is allowed to render.
        }
        if (epoch === this.accountEpoch) { this.state.authBusy = false; this.emit(); }
      };
      this.authQueue = this.authQueue.then(operation, operation);
      await this.authQueue;
    }
    async overview(clear = true) {
      if (!this.state.user) return;
      this.navigationEpoch++;
      const t = this.token();
      this.state.projectId = null; this.state.detail = null; this.state.error = ''; this.state.refreshError = '';
      this.state.loading = true;
      this.state.revisions = []; this.state.comments = []; this.state.events = [];
      if (clear) this.emit();
      try {
        const data = await this.api('/api/projects');
        if (!this.live(t)) return;
        this.state.projects = data.projects; this.state.loading = false; this.emit();
      } catch (e) { this.fail(t, e); }
    }
    async open(pid, tab = 'brief') {
      if (!this.state.user) return;
      this.navigationEpoch++;
      const t = this.token();
      this.state.projectId = pid; this.state.tab = ['brief', 'revisions', 'discussion', 'activity'].includes(tab) ? tab : 'brief';
      this.state.detail = null; this.state.revisions = []; this.state.comments = []; this.state.events = [];
      this.state.loading = true; this.state.error = ''; this.state.refreshError = ''; this.emit();
      try { await this.refresh(t); } catch (e) { this.fail(t, e); }
    }
    tab(name) {
      if (!['brief', 'revisions', 'discussion', 'activity'].includes(name)) return;
      this.state.tab = name; this.emit();
    }
    fail(t, e) {
      if (!this.live(t)) return;
      if (e.status === 401) { this.reset(); this.state.loginError = 'Your session ended. Please sign in again.'; }
      else { this.state.loading = false; this.state.error = e.message; }
      this.emit();
    }
    async refresh(t = this.token()) {
      const pid = this.state.projectId;
      if (!pid || !this.live(t)) return;
      const base = `/api/projects/${encodeURIComponent(pid)}`;
      const [p, r, c, a] = await Promise.all([this.api(base), this.api(base + '/revisions'), this.api(base + '/comments'), this.api(base + '/activity')]);
      if (!this.live(t)) return;
      Object.assign(this.state, {detail: p.project, revisions: r.revisions, comments: c.comments,
        events: a.events, loading: false, error: '', refreshError: ''});
      this.state.projects = this.state.projects.map(item => item.id === pid ? p.project : item);
      this.emit();
    }
    async retryRefresh() {
      const t = this.token();
      try { await this.refresh(t); }
      catch (e) {
        if (!this.live(t)) return;
        if (e.status === 401) return this.fail(t, e);
        this.state.refreshError = 'The latest details are still unavailable. Your saved work is retained. Try refreshing again.'; this.emit();
      }
    }
    async mutate(kind, value) {
      if (!this.state.detail || this.busy(kind)) return;
      const t = this.token(), pid = this.state.projectId, key = this.key(kind);
      const base = `/api/projects/${encodeURIComponent(pid)}`;
      let path, body, drafts;
      if (kind === 'decision') {
        if (this.state.detail.status !== 'awaiting_review') return;
        path = base + '/decision'; drafts = {decision: this.draft('decision')};
        body = {revision: this.state.detail.currentRevision, decision: value, note: drafts.decision};
      } else if (kind === 'comment') {
        path = base + '/comments'; drafts = {comment: this.draft('comment')}; body = {body: drafts.comment};
      } else if (kind === 'revision') {
        path = base + '/revisions'; drafts = {title: this.draft('title'), summary: this.draft('summary')};
        body = {expectedRevision: this.state.detail.currentRevision, title: drafts.title, summary: drafts.summary};
      } else return;
      this.pending.add(key); this.notices.set(key, 'Saving…'); this.emit();
      let committed = false;
      try {
        const data = await this.api(path, body);
        committed = true;
        if (!this.accountLive(t)) return;
        this.notices.set(key, kind === 'comment' ? 'Comment saved.' : kind === 'decision' ? 'Review decision saved.' : 'Revision published.');
        for (const [field, submitted] of Object.entries(drafts)) {
          const dk = `${t.user}:${pid}:${field}`;
          if (this.drafts.get(dk) === submitted) this.drafts.delete(dk);
        }
        if (!this.live(t)) return;
        if (data.project) {
          this.state.detail = data.project;
          this.state.projects = this.state.projects.map(p => p.id === pid ? data.project : p);
        }
        if (data.comment) this.state.comments.push(data.comment);
        if (data.revision) this.state.revisions.push(data.revision);
        this.emit(); // Acknowledge persistence before attempting GET recovery.
        await this.refresh(t);
      } catch (e) {
        if (!this.live(t)) return;
        if (committed) {
          this.state.refreshError = 'Saved successfully. Latest history could not be refreshed. Refresh details to catch up; you do not need to submit again.';
        } else if (e.status === 409) {
          this.notices.set(key, e.message + ' Your draft is retained.');
          try { await this.refresh(t); }
          catch (refreshError) {
            if (!this.live(t)) return;
            if (refreshError.status === 401) return this.fail(t, refreshError);
            this.state.refreshError = 'The review changed, but the latest details could not be loaded. Refresh before trying again.';
          }
        } else if (e.status === 401) { return this.fail(t, e); }
        else this.notices.set(key, e.message);
        if (this.live(t)) this.emit();
      } finally {
        if (this.accountLive(t)) {
          this.pending.delete(key);
          if (this.live(t)) this.emit();
        }
      }
    }
  }
  return {Controller, APIError, http};
});
