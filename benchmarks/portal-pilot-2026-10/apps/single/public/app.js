'use strict';

const app = document.querySelector('#app');
const state = { user: null, projects: [], detail: null, revisions: [], comments: [], events: [], filter: 'all', epoch: 0 };
const labels = { awaiting_review: 'Awaiting review', approved: 'Approved', changes_requested: 'Changes requested' };
const icons = {
  grid: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  review: '<path d="M9 5H5v16h14V5h-4M9 3h6v4H9zM8 13l3 3 5-6"/>',
  arrow: '<path d="M5 12h14M13 6l6 6-6 6"/>',
  back: '<path d="M19 12H5m6-6-6 6 6 6"/>',
  logout: '<path d="M9 5H4v14h5m5-14 5 7-5 7m-5-7h10"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  chat: '<path d="M4 4h16v12H8l-4 4z"/>',
  plus: '<path d="M12 4v16M4 12h16"/>',
};
const icon = name => `<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">${icons[name] || icons.arrow}</svg>`;
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money = cents => new Intl.NumberFormat('en-IE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 2, minimumFractionDigits: cents % 100 ? 2 : 0 }).format(cents / 100);
const date = stamp => new Date(stamp).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });
const shortDate = stamp => new Date(stamp).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' });
const badge = status => `<span class="badge ${esc(status)}"><span class="status-dot"></span>${esc(labels[status] || status)}</span>`;
const brand = () => '<span class="brand">AethDesign<span class="brand-star" aria-hidden="true">✳</span></span><span class="brand-sub">ATELIER</span>';
const footer = () => '<footer class="page-footer"><span>Fictional local demo by AethDesign</span><span>Considered design. Shared progress.</span></footer>';

function artwork(id, extra = '') {
  if (id === 'p2') return `<div class="art art-digital ${extra}" role="img" aria-label="Harbor House digital design concept, an editorial website in terracotta and olive"><div class="mini-browser"><div class="browser-bar"><i></i><i></i><i></i><span>HARBOR HOUSE</span></div><div class="browser-content"><span class="mini-label">A PLACE TO EXHALE</span><div class="digital-title">A slower<br><em>kind of stay.</em></div><div class="digital-door"><span></span></div><div class="mini-rule"></div><span class="mini-label">COASTAL LIVING, CONSIDERED.</span></div></div><span class="art-caption">DIGITAL EXPERIENCE / 2026</span></div>`;
  if (id === 'p3') return `<div class="art art-editorial ${extra}" role="img" aria-label="Northline editorial cover concept with large ivory typography on forest green"><div class="editorial-top">FIELD NOTES & OTHER DISCOVERIES <span>VOL. 01</span></div><div class="editorial-name">NORTH<br><em>LINE.</em></div><div class="editorial-bottom"><span>A different<br>point of view.</span><span>44° N<br>09° E</span></div></div>`;
  return `<div class="art art-identity ${extra}" role="img" aria-label="Harbor House identity concept, an architectural monogram and serif wordmark on warm paper"><div class="identity-frame"><span class="mini-label">A QUIETER KIND OF HOSPITALITY</span><svg class="monogram" viewBox="0 0 140 120" aria-hidden="true"><path d="M25 108V35C25 4 69 4 69 35v73M71 108V35c0-31 44-31 44 0v73M15 108h65m-20 0h65M25 66h90M35 108V35c0-17 24-17 24 0v73M81 108V35c0-17 24-17 24 0v73" fill="none" stroke="currentColor" stroke-width="1.4"/></svg><span class="identity-name">Harbor House</span><span class="mini-label">STAY A LITTLE LONGER.</span></div></div>`;
}

class RequestError extends Error {
  constructor(message, status) { super(message); this.status = status; }
}
async function api(path, body) {
  let response;
  try {
    response = await fetch(path, { credentials: 'same-origin', headers: body === undefined ? {} : { 'Content-Type': 'application/json' }, method: body === undefined ? 'GET' : 'POST', body: body === undefined ? undefined : JSON.stringify(body) });
  } catch (_) { throw new RequestError('The local server is unavailable. Please reconnect and try again.', 0); }
  const result = await response.json().catch(() => ({}));
  if (!response.ok) throw new RequestError(result.error?.message || 'This request could not be completed. Please try again.', response.status);
  return result;
}
function notice(testid, text, error = false) {
  const node = document.querySelector(`[data-testid="${testid}"]`);
  if (node) { node.textContent = text; node.classList.toggle('error', error); node.classList.toggle('success', !error && !!text); }
}
function route() {
  const match = location.pathname.match(/^\/projects\/([A-Za-z0-9_-]+)$/);
  return { id: match?.[1], tab: new URLSearchParams(location.search).get('tab') || 'brief' };
}
function navigate(path) {
  history.pushState({}, '', path);
  renderRoute();
  window.scrollTo({ top: 0, behavior: 'instant' });
}
window.addEventListener('popstate', () => renderRoute());
document.addEventListener('click', e => {
  const link = e.target.closest('a[data-nav]');
  if (link && !e.ctrlKey && !e.metaKey && !e.shiftKey && e.button === 0) { e.preventDefault(); navigate(link.getAttribute('href')); }
});

function loginScreen(message = '') {
  document.title = 'Sign in — AethDesign Atelier';
  app.innerHTML = `<div class="login-layout"><section class="login-story"><div class="login-brand">${brand()}</div><div class="story-kicker">THE CLIENT WORKSPACE</div><h2>Good work.<br><em>Made together.</em></h2><p>A little closer to your project.<br>A little more space for the process.</p><div class="login-art">${artwork('p1')}<span class="sample-label">FROM THE ATELIER &nbsp; / &nbsp; HARBOR HOUSE</span></div><div class="story-bottom"><span>Independent minds. Thoughtful design.</span><span>Est. for this demo ↗</span></div></section><main id="main" class="login-main"><div class="login-mobile-brand">${brand()}</div><div class="login-form-wrap"><span class="eyebrow">WELCOME TO THE ATELIER</span><h1>Your project,<br><em>in good company.</em></h1><p class="muted">Sign in to see what’s taking shape.</p><form data-testid="login-form" id="login-form"><label for="email">Email address</label><input id="email" name="email" type="email" autocomplete="username" placeholder="you@your-studio.test" data-testid="login-email" required maxlength="254"><label for="password">Password</label><input id="password" name="password" type="password" autocomplete="current-password" placeholder="Your password" data-testid="login-password" required maxlength="256"><p class="feedback error" data-testid="login-error" role="alert">${esc(message)}</p><button class="button primary login-submit" type="submit" data-testid="login-submit">Enter your workspace ${icon('arrow')}</button></form><div class="demo-accounts"><div class="demo-heading"><span class="tiny-tag">LOCAL DEMO</span><span>Take a look around</span></div><p>Choose a fictional account to fill the sign-in form.</p><div class="account-options"><button type="button" data-account="harbor">Harbor client ${icon('arrow')}</button><button type="button" data-account="northline">Northline client ${icon('arrow')}</button><button type="button" data-account="studio">Studio staff ${icon('arrow')}</button></div><p class="demo-footnote">Synthetic data only. No real message is sent.</p></div></div><div class="login-footer">Fictional local demo by AethDesign<span>PRIVATE BY DESIGN. LOCAL BY DEFAULT.</span></div></main></div>`;
  const accounts = { harbor: ['alex@harbor.test', 'HarborDemo!42'], northline: ['sam@northline.test', 'NorthDemo!42'], studio: ['studio@aethdesign.test', 'StudioDemo!42'] };
  app.querySelectorAll('[data-account]').forEach(button => button.addEventListener('click', () => {
    const values = accounts[button.dataset.account];
    document.querySelector('#email').value = values[0];
    document.querySelector('#password').value = values[1];
    document.querySelector('[data-testid="login-submit"]').focus();
  }));
  document.querySelector('#login-form').addEventListener('submit', async e => {
    e.preventDefault();
    const button = e.target.querySelector('button[type="submit"]');
    button.disabled = true;
    notice('login-error', 'Signing in…');
    try {
      const { user } = await api('/api/login', { email: e.target.email.value, password: e.target.password.value });
      state.user = user;
      state.filter = 'all';
      const dest = route().id ? location.pathname + location.search : '/projects';
      history.replaceState({}, '', dest);
      await renderRoute();
    } catch (err) { notice('login-error', err.message, true); button.disabled = false; }
  });
}

function shell(content, section = 'Overview') {
  const staff = state.user.role === 'staff';
  const waiting = state.projects.filter(p => p.status === 'awaiting_review' || (staff && p.status === 'changes_requested')).length;
  app.innerHTML = `<div class="workspace"><aside class="sidebar"><a class="sidebar-brand" href="/projects" data-nav aria-label="AethDesign Atelier overview">${brand()}</a><span class="sidebar-label">${staff ? 'STUDIO WORKSPACE' : 'CLIENT WORKSPACE'}</span><nav aria-label="Main navigation"><a href="/projects" data-nav class="nav-link ${!route().id && state.filter === 'all' ? 'active' : ''}">${icon('grid')}<span>Overview</span></a><button class="nav-link ${!route().id && state.filter === 'review' ? 'active' : ''}" id="review-nav">${icon('review')}<span>${staff ? 'Review queue' : 'Needs your review'}</span><span class="nav-count">${waiting}</span></button></nav><div class="sidebar-note"><span class="note-star" aria-hidden="true">✳</span><h3>Room for<br><em>the process.</em></h3><p>Your ideas, our craft.<br>One shared place.</p><span class="tiny-tag">${staff ? 'STUDIO ACCESS' : 'YOUR PRIVATE ATELIER'}</span></div><div class="sidebar-user"><div class="avatar ${staff ? 'studio-avatar' : ''}">${staff ? 'AD' : esc(state.user.name.split(' ').map(s => s[0]).join(''))}</div><div><span data-testid="user-name">${esc(state.user.name)}</span><small>${staff ? 'Studio staff' : 'Client'}</small></div><button class="icon-button" data-testid="logout" aria-label="Sign out">${icon('logout')}</button></div></aside><div class="workspace-body"><header class="topbar"><div><span>Atelier</span><span class="breadcrumb-slash">/</span><span>${esc(section)}</span></div><span class="local-indicator"><span></span>Local workspace</span></header><main id="main" class="main-content">${content}</main>${footer()}</div></div>`;
  document.querySelector('[data-testid="logout"]').addEventListener('click', async e => {
    e.currentTarget.disabled = true;
    try {
      await api('/api/logout', {});
      state.epoch++;
      state.user = null; state.projects = []; state.detail = null; state.revisions = []; state.comments = []; state.events = []; state.filter = 'all';
      history.replaceState({}, '', '/login');
      loginScreen();
    } catch (err) {
      e.currentTarget.disabled = false;
      const region = document.querySelector('#global-status');
      region.textContent = err.message;
      region.classList.add('error');
    }
  });
  document.querySelector('#review-nav').addEventListener('click', () => { state.filter = 'review'; navigate('/projects'); });
  const overview = document.querySelector('.nav-link[data-nav]');
  overview.addEventListener('click', () => { state.filter = 'all'; });
}

function dashboard() {
  const staff = state.user.role === 'staff';
  const waiting = state.projects.filter(p => p.status === 'awaiting_review');
  const changes = state.projects.filter(p => p.status === 'changes_requested');
  const firstName = state.user.name.split(' ')[0];
  const projects = state.filter === 'review' ? state.projects.filter(p => p.status === 'awaiting_review' || (staff && p.status === 'changes_requested')) : state.projects;
  const average = state.projects.length ? Math.round(state.projects.reduce((sum, p) => sum + p.progress, 0) / state.projects.length) : 0;
  document.title = `${staff ? 'Studio overview' : 'Your projects'} — AethDesign Atelier`;
  const content = `<div id="global-status" class="feedback" role="alert"></div><section class="page-heading"><div><span class="eyebrow">${staff ? 'BEHIND THE GOOD WORK' : 'YOUR CREATIVE WORKSPACE'}</span><h1>${staff ? 'The studio, at a glance.' : `Welcome back, ${esc(firstName)}.`}</h1><p>${staff ? 'A clear view of what’s ready, what’s next, and what needs a little care.' : 'A shared place for ideas, feedback, and everything taking shape.'}</p></div><span class="heading-mark" aria-hidden="true">✳</span></section><section class="summary-strip" aria-label="Workspace summary"><div><span class="summary-number">${state.projects.length.toString().padStart(2, '0')}</span><span>Projects in your atelier</span></div><div><span class="summary-number">${waiting.length.toString().padStart(2, '0')}<i class="summary-dot"></i></span><span>${staff ? 'Awaiting client review' : 'Ready for your review'}</span></div><div><span class="summary-number">${staff ? changes.length.toString().padStart(2, '0') : average + '<small>%</small>'}</span><span>${staff ? 'Changes to take forward' : 'Overall project progress'}</span></div></section>${waiting.length ? `<section class="review-banner"><div class="banner-icon">${icon('review')}</div><div><span class="eyebrow">${staff ? 'READY FOR A CONVERSATION' : 'A FRESH PERSPECTIVE'}</span><h2>${staff ? 'Good work is ready for review.' : 'Your next chapter is ready.'}</h2><p>${esc(waiting[0].title)} · Revision ${waiting[0].currentRevision}</p></div><a class="button light" data-nav href="/projects/${esc(waiting[0].id)}?tab=revisions">${staff ? 'View review' : 'Take a look'} ${icon('arrow')}</a></section>` : `<section class="review-banner"><div class="banner-icon">${icon('check')}</div><div><span class="eyebrow">ALL CAUGHT UP</span><h2>A little space for what’s next.</h2><p>No revisions are awaiting review. Your project history is always here.</p></div></section>`}<section class="projects-section"><div class="section-heading"><h2>${state.filter === 'review' ? 'The review queue' : 'Your projects'} <span class="count-label">${projects.length}</span></h2><div class="filter-group" role="group" aria-label="Filter projects"><button data-filter="all" aria-pressed="${state.filter === 'all'}">All projects</button><button data-filter="review" aria-pressed="${state.filter === 'review'}">${staff ? 'Needs attention' : 'For review'}</button></div></div><div class="project-grid" data-testid="project-list">${projects.length ? projects.map(p => `<article class="project-card" data-testid="project-card" data-project-id="${esc(p.id)}"><a class="project-art-link" href="/projects/${esc(p.id)}" data-nav aria-label="Open ${esc(p.title)}">${artwork(p.id)}</a><div class="project-card-content"><div class="card-kicker"><span>${esc(p.clientName)}</span><span>0${esc(p.currentRevision)} / REV</span></div><h3><a href="/projects/${esc(p.id)}" data-nav>${esc(p.title)}</a></h3><div class="card-status-row">${badge(p.status)}<span>${p.progress}%</span></div><div class="progress-track"><div class="progress-fill" data-progress="${p.progress}"></div></div><div class="card-next"><span>NEXT MILESTONE</span><strong>${esc(p.nextMilestone)}</strong></div><div class="card-bottom"><span>${money(p.budgetCents)}<small>Project investment</small></span><a href="/projects/${esc(p.id)}" data-nav data-testid="open-project" data-project-id="${esc(p.id)}">Open project ${icon('arrow')}</a></div></div></article>`).join('') : '<div class="empty-state"><span>✳</span><h3>All caught up.</h3><p>There are no projects in this view. You can return to all projects at any time.</p><button class="button secondary" data-filter="all">Show all projects</button></div>'}</div></section><aside class="workspace-note"><span>THE WAY WE WORK</span><p>Good design grows through conversation.<br>Leave a note, ask a question, make it yours.</p><span aria-hidden="true">↗</span></aside>`;
  shell(content);
  app.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => { state.filter = button.dataset.filter; dashboard(); }));
  app.querySelectorAll('[data-progress]').forEach(node => node.style.width = `${node.dataset.progress}%`);
}

function detailView(tab, feedback = {}) {
  const p = state.detail;
  if (!['brief', 'revisions', 'discussion', 'activity'].includes(tab)) tab = 'brief';
  const staff = state.user.role === 'staff';
  document.title = `${p.title} — AethDesign Atelier`;
  const content = `<div id="global-status" class="feedback" role="alert"></div><a class="back-link" href="/projects" data-nav data-testid="back-projects">${icon('back')}Back to overview</a><section data-testid="project-detail" data-project-id="${esc(p.id)}"><header class="detail-heading"><div><span class="eyebrow">${esc(p.clientName)} <span class="eyebrow-divider">/</span> PROJECT 0${esc(p.id.slice(1))}</span><h1 data-testid="project-title">${esc(p.title)}</h1><p>${p.id === 'p1' ? 'A thoughtful identity. A lasting first impression.' : p.id === 'p2' ? 'An inviting digital home, from first click to final detail.' : 'A distinctive voice for stories worth telling.'}</p></div><span data-testid="project-status">${badge(p.status)}</span></header><div class="detail-metrics"><div><span>PROJECT INVESTMENT</span><strong data-testid="project-budget" data-total-cents="${p.budgetCents}">${money(p.budgetCents)}</strong></div><div><span>THE JOURNEY</span><strong>${p.progress}% complete</strong></div><div><span>CURRENT REVISION</span><strong>Revision <span data-testid="current-revision">${p.currentRevision}</span></strong></div><div><span>UP NEXT</span><strong>${esc(p.nextMilestone)}</strong></div></div><nav class="detail-tabs" aria-label="Project sections">${[['brief','Project brief'],['revisions','Revisions & review'],['discussion','Discussion'],['activity','Activity']].map(([key,label]) => `<a data-nav href="/projects/${esc(p.id)}?tab=${key}" data-testid="tab-${key}" ${key === tab ? 'aria-current="page"' : ''}>${label}${key === 'discussion' ? `<span>${state.comments.length}</span>` : ''}</a>`).join('')}</nav><div class="detail-panel" id="detail-panel">${tab === 'brief' ? briefPanel(p) : tab === 'revisions' ? revisionsPanel(p,staff) : tab === 'discussion' ? discussionPanel() : activityPanel()}</div></section>`;
  shell(content, p.clientName);
  for (const [testid, value] of Object.entries(feedback)) notice(testid, value.message, value.error);
  bindDetail();
}

function briefPanel(p) {
  return `<div class="brief-layout"><div class="brief-content"><span class="eyebrow">THE STARTING POINT</span><h2>A clear direction.<br><em>Room to explore.</em></h2><p class="project-brief" data-testid="project-brief">${esc(p.brief)}</p><div class="deliverables-block"><h3>What we’re making <span class="count-label">${p.deliverables.length}</span></h3><ul class="deliverable-list" data-testid="project-deliverables">${p.deliverables.map((d,i) => `<li><span class="list-number">0${i + 1}</span><span>${esc(d)}</span>${icon('check')}</li>`).join('')}</ul></div></div><div class="brief-side">${artwork(p.id, 'detail-art')}<div class="timeline-block"><span class="eyebrow">FROM IDEA TO REALITY</span><h3>The project journey</h3><ol class="timeline" data-testid="project-timeline">${p.timeline.map(t => `<li class="${esc(t.status)}"><span class="timeline-marker">${t.status === 'complete' ? icon('check') : ''}</span><div><strong>${esc(t.title)}</strong><span>${t.status === 'complete' ? 'Complete' : t.status === 'current' ? 'Current milestone' : 'Coming up'}</span></div></li>`).join('')}</ol></div></div></div>`;
}

function revisionsPanel(p,staff) {
  const current = state.revisions.find(r => r.number === p.currentRevision);
  const finalized = current?.decision;
  return `<div class="review-layout"><div class="revision-history"><div class="panel-heading"><div><span class="eyebrow">THE WORK, AS IT EVOLVES</span><h2>Every step forward.</h2></div><span class="count-label">${state.revisions.length} revision${state.revisions.length === 1 ? '' : 's'}</span></div>${[...state.revisions].reverse().map(r => `<article class="revision-card ${r.number === p.currentRevision ? 'latest' : ''}" data-testid="revision-card" data-revision-number="${r.number}"><div class="revision-top"><span class="revision-number">R${String(r.number).padStart(2, '0')}</span><span class="tiny-tag">${r.number === p.currentRevision ? 'CURRENT DIRECTION' : 'PREVIOUS DIRECTION'}</span><time datetime="${esc(r.publishedAt)}">${date(r.publishedAt)}</time></div><h3>${esc(r.title)}</h3><p>${esc(r.summary)}</p>${r.number === p.currentRevision ? artwork(p.id,'revision-art') : ''}${r.decision ? `<div class="revision-decision">${icon(r.decision.decision === 'approve' ? 'check' : 'chat')}<div><strong>${r.decision.decision === 'approve' ? 'Approved' : 'Changes requested'} by ${esc(r.decision.author.name)}</strong><small>${date(r.decision.createdAt)}</small>${r.decision.note ? `<p>${esc(r.decision.note)}</p>` : ''}</div></div>` : ''}</article>`).join('')}</div><aside class="review-side">${staff ? `<form id="revision-form" class="action-panel"><span class="eyebrow">STUDIO OPERATIONS</span><h3>A new chapter.</h3><p>Publish a new revision to open a fresh client review. Earlier decisions stay in the history.</p><span class="form-context">Publishing after revision ${p.currentRevision}</span><label for="revision-title">Revision title</label><input id="revision-title" data-testid="revision-title" name="title" required maxlength="120" placeholder="e.g. Refined identity direction"><label for="revision-summary">What’s changed?</label><textarea id="revision-summary" data-testid="revision-summary" name="summary" required maxlength="2000" rows="5" placeholder="Give the client a clear sense of what to review."></textarea><p class="feedback" data-testid="revision-status" role="status" aria-live="polite"></p><button type="submit" class="button primary full-width" data-testid="publish-revision">Publish revision ${icon('plus')}</button><small class="form-footnote">Visible to this project’s client in this local demo.</small></form>` : `<div class="action-panel"><span class="eyebrow">YOUR PERSPECTIVE MATTERS</span><h3>${p.status === 'awaiting_review' ? 'Make it yours.' : 'A decision, recorded.'}</h3><p>${p.status === 'awaiting_review' ? 'Take a moment with the current direction. Approve it to move forward, or tell us what you’d like to refine.' : 'Your feedback is part of the process. A new studio revision will open the next review.'}</p>${p.status === 'awaiting_review' ? `<form id="decision-form"><span class="form-context">You’re reviewing revision ${p.currentRevision}</span><label for="decision-note">Your review note</label><textarea id="decision-note" data-testid="decision-note" name="note" maxlength="2000" rows="5" placeholder="What feels right? What could feel better?"></textarea><small class="input-hint">A note is required when requesting changes.</small><p class="feedback" data-testid="decision-status" role="status" aria-live="polite"></p><button type="submit" name="decision" value="approve" class="button primary full-width" data-testid="approve-revision">Approve this revision ${icon('check')}</button><button type="submit" name="decision" value="request_changes" class="button secondary full-width" data-testid="request-changes">Request changes ${icon('chat')}</button></form>` : `${badge(p.status)}${finalized ? `<div class="final-note"><span>YOUR REVIEW NOTE</span><p>${esc(finalized.note || 'Approved without an additional note.')}</p></div>` : ''}<p class="feedback" data-testid="decision-status" role="status" aria-live="polite">This revision’s review is complete.</p>`}</div>`}<div class="quiet-note">${icon('chat')}<p>Have a smaller thought?<br><a href="/projects/${esc(p.id)}?tab=discussion" data-nav>Start a conversation</a> in the discussion.</p></div></aside></div>`;
}

function discussionPanel() {
  return `<div class="discussion-layout"><div><div class="panel-heading"><div><span class="eyebrow">THE CONVERSATION</span><h2>Good ideas start here.</h2></div><span class="count-label">${state.comments.length} note${state.comments.length === 1 ? '' : 's'}</span></div><div class="comment-list">${state.comments.length ? state.comments.map(c => `<article class="comment" data-testid="comment-item"><div class="avatar ${c.author.role === 'staff' ? 'studio-avatar' : ''}">${c.author.role === 'staff' ? 'AD' : esc(c.author.name.split(' ').map(s => s[0]).join(''))}</div><div class="comment-content"><header><strong>${esc(c.author.name)}</strong><span class="tiny-tag">${c.author.role === 'staff' ? 'STUDIO' : 'CLIENT'}</span><time datetime="${esc(c.createdAt)}">${date(c.createdAt)}</time></header><p data-testid="comment-text">${esc(c.body)}</p></div></article>`).join('') : '<div class="empty-state"><h3>The first word is yours.</h3><p>Start the conversation with a thought or question.</p></div>'}</div></div><aside><form id="comment-form" class="action-panel"><span class="eyebrow">LEAVE A LITTLE THOUGHT</span><h3>Keep it flowing.</h3><p>Feedback, questions, or a small spark of inspiration. Your studio and this project’s client can see these notes.</p><label for="comment-body">Your note</label><textarea id="comment-body" name="body" rows="6" required maxlength="2000" data-testid="comment-body" placeholder="Share what’s on your mind…"></textarea><p class="feedback" data-testid="comment-status" role="status" aria-live="polite"></p><button class="button primary full-width" type="submit" data-testid="comment-submit">Add to the conversation ${icon('arrow')}</button><small class="form-footnote">Saved locally to this project. No real message is sent.</small></form></aside></div>`;
}

function activityPanel() {
  return `<div class="activity-layout"><div><span class="eyebrow">A RECORD OF THE PROCESS</span><h2>The story so far.</h2><p class="muted">Revisions, decisions, and conversations — all in one place.</p><ol class="activity-list">${[...state.events].reverse().map(event => `<li data-testid="activity-item" data-event-type="${esc(event.type)}"><div class="activity-icon">${icon(event.type === 'revision_published' ? 'plus' : event.type === 'comment_added' ? 'chat' : 'check')}</div><div><p><strong>${esc(event.actor.name)}</strong> ${event.type === 'revision_published' ? `published revision ${event.revision}` : event.type === 'comment_added' ? 'added a discussion note' : `${event.decision === 'approve' ? 'approved' : 'requested changes to'} revision ${event.revision}`}</p>${event.title ? `<span>${esc(event.title)}</span>` : ''}<time datetime="${esc(event.createdAt)}">${date(event.createdAt)} · ${event.actor.role === 'staff' ? 'Studio' : 'Client'}</time></div></li>`).join('') || '<li class="empty-state">No project activity yet.</li>'}</ol></div><aside class="activity-note"><span class="note-star" aria-hidden="true">✳</span><h3>Nothing lost.<br><em>Everything considered.</em></h3><p>Each successful change leaves a trace. Earlier revisions and decisions stay here as the project moves forward.</p></aside></div>`;
}

async function loadDetail(id) {
  const [detail,revisions,comments,activity] = await Promise.all([api(`/api/projects/${id}`),api(`/api/projects/${id}/revisions`),api(`/api/projects/${id}/comments`),api(`/api/projects/${id}/activity`)]);
  return { detail: detail.project, revisions: revisions.revisions, comments: comments.comments, events: activity.events };
}

function bindDetail() {
  const p = state.detail;
  const decisionForm = document.querySelector('#decision-form');
  decisionForm?.addEventListener('submit', async e => {
    e.preventDefault();
    const decision = e.submitter?.value || 'approve';
    const note = decisionForm.note.value.trim();
    if (decision === 'request_changes' && !note) { notice('decision-status', 'Please add a note so the studio knows what to refine.', true); decisionForm.note.focus(); return; }
    await mutation(decisionForm, 'decision-status', 'decision', { revision: p.currentRevision, decision, note }, decision === 'approve' ? 'Revision approved. Thank you — the studio can move forward.' : 'Changes requested. Your review note is saved.', 'revisions');
  });
  const commentForm = document.querySelector('#comment-form');
  commentForm?.addEventListener('submit', async e => {
    e.preventDefault();
    const body = commentForm.body.value.trim();
    if (!body) { notice('comment-status', 'Please write a note before adding it.', true); return; }
    await mutation(commentForm, 'comment-status', 'comments', { body }, 'Your note is saved to the conversation.', 'discussion');
  });
  const revisionForm = document.querySelector('#revision-form');
  revisionForm?.addEventListener('submit', async e => {
    e.preventDefault();
    const title = revisionForm.title.value.trim();
    const summary = revisionForm.summary.value.trim();
    if (!title || !summary) { notice('revision-status', 'Add a title and a summary before publishing.', true); return; }
    await mutation(revisionForm, 'revision-status', 'revisions', { expectedRevision: p.currentRevision, title, summary }, `Revision ${p.currentRevision + 1} is published and ready for client review.`, 'revisions');
  });
}

async function mutation(form, feedbackId, action, payload, success, tab) {
  const id = state.detail.id;
  const epoch = state.epoch;
  const controls = [...form.querySelectorAll('button, input, textarea')];
  const draft = [...form.querySelectorAll('input, textarea')].filter(node => node.name).map(node => ({ name: node.name, value: node.value }));
  let saved = false;
  controls.forEach(node => node.disabled = true);
  notice(feedbackId, 'Saving to your project…');
  try {
    await api(`/api/projects/${id}/${action}`, payload);
    saved = true;
    const updated = await loadDetail(id);
    if (epoch !== state.epoch || route().id !== id) return;
    Object.assign(state, updated);
    state.projects = state.projects.map(p => p.id === id ? state.detail : p);
    detailView(tab, { [feedbackId]: { message: success } });
    document.querySelector(`[data-testid="${feedbackId}"]`)?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  } catch (err) {
    if (epoch !== state.epoch || route().id !== id) return;
    if (err.status === 401) { state.user = null; state.projects = []; state.detail = null; state.comments = []; state.revisions = []; state.events = []; loginScreen('Your session has ended. Please sign in again.'); return; }
    if (saved) {
      notice(feedbackId, 'Your change was saved, but the latest project could not be loaded. Refresh the page before continuing.', true);
      return;
    }
    if (err.status === 409) {
      try {
        Object.assign(state, await loadDetail(id));
        state.projects = state.projects.map(p => p.id === id ? state.detail : p);
        detailView(tab, { [feedbackId]: { message: err.message + ' No change was submitted. Please review the latest state.', error: true } });
        const currentForm = form.id && document.getElementById(form.id);
        if (currentForm) draft.forEach(field => { if (currentForm.elements[field.name]) currentForm.elements[field.name].value = field.value; });
      } catch (refreshError) { controls.forEach(node => node.disabled = false); notice(feedbackId, refreshError.message, true); }
    } else {
      controls.forEach(node => node.disabled = false);
      notice(feedbackId, err.message, true);
    }
  }
}

async function renderRoute() {
  const epoch = ++state.epoch;
  if (!state.user) { loginScreen(); return; }
  const { id, tab } = route();
  shell('<div id="global-status" class="feedback" role="alert"></div><div class="loading-state" role="status"><span class="note-star">✳</span><p>Gathering the latest from your Atelier…</p></div>', id ? 'Project' : 'Overview');
  try {
    const { projects } = await api('/api/projects');
    if (epoch !== state.epoch) return;
    state.projects = projects;
    if (id) {
      const loaded = await loadDetail(id);
      if (epoch !== state.epoch) return;
      Object.assign(state, loaded);
      detailView(tab);
    } else dashboard();
  } catch (err) {
    if (epoch !== state.epoch) return;
    if (err.status === 401) { state.user = null; state.projects = []; state.detail = null; state.comments = []; state.revisions = []; state.events = []; loginScreen('Please sign in to continue.'); return; }
    document.title = `${err.status === 404 ? 'Project unavailable' : 'Workspace unavailable'} — AethDesign Atelier`;
    shell(`<div id="global-status" class="feedback" role="alert"></div><div class="empty-state error-state"><span>✳</span><h1>${err.status === 404 ? 'This project isn’t in your atelier.' : 'A brief pause in the process.'}</h1><p role="alert">${esc(err.message)}</p><a href="/projects" data-nav data-testid="back-projects" class="button primary">Back to overview ${icon('arrow')}</a><button class="button secondary" id="retry">Try again</button></div>`);
    document.querySelector('#retry').addEventListener('click',renderRoute);
  }
}

async function boot() {
  try { state.user = (await api('/api/me')).user; await renderRoute(); }
  catch (err) { loginScreen(err.status === 401 ? '' : err.message); }
}
boot();
