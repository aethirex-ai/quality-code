/* A single visual owner: templates, navigation and accessible form adapters. */
'use strict';
const root = document.getElementById('app');
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
const money = cents => new Intl.NumberFormat('en-IE', {style:'currency', currency:'EUR'}).format(cents / 100);
const date = value => new Intl.DateTimeFormat('en-GB', {day:'numeric', month:'short', year:'numeric', timeZone:'UTC'}).format(new Date(value));
const statuses = {awaiting_review:'Awaiting review', approved:'Approved', changes_requested:'Changes requested'};
const badge = status => `<span class="badge ${esc(status)}"><span class="status-dot"></span>${esc(statuses[status] || status)}</span>`;
const arrow = '<span aria-hidden="true">↗</span>';
const brand = `<span class="monogram" aria-hidden="true">AÐ</span><span class="wordmark">AETHDESIGN</span>`;
const attribution = 'Fictional local demo by AethDesign';
const demoAccounts = {
  harbor: {email:'alex@harbor.test', password:'HarborDemo!42'},
  northline: {email:'sam@northline.test', password:'NorthDemo!42'},
  studio: {email:'studio@aethdesign.test', password:'StudioDemo!42'}
};
const loginDraft = {email:'', password:''}; // Memory only, cleared on successful sign-in.
let previousUser = null;

function productPreview(pid, compact = false) {
  if (pid === 'p1') return `<div class="product-preview commerce ${compact ? 'compact' : ''}" aria-label="Fictional Harbor storefront interface preview">
    <div class="preview-browser"><span class="browser-dots">● ● ●</span><span>harbor / storefront</span><span>↗</span></div>
    <div class="store-nav"><b>HARBOR HOUSE</b><span>Living &nbsp; Lighting &nbsp; Objects</span><span>Bag (0)</span></div>
    <div class="store-main"><div><span class="mini-label">ROOM FOR THE EVERYDAY</span><h3>A little more<br>space to live.</h3><p>Considered essentials for the places we call home.</p><span class="store-cta">Explore the collection &nbsp; →</span></div>
    <div class="product-still"><div class="vase"></div><div class="stem stem-one"></div><div class="stem stem-two"></div><div class="pedestal"></div><span>THE EVERYDAY COLLECTION</span></div></div>
    <div class="store-bottom"><span>01 / Product discovery</span><span>Designed for desktop & mobile</span></div></div>`;
  if (pid === 'p2') return `<div class="product-preview console ${compact ? 'compact' : ''}" aria-label="Fictional merchant console interface preview">
    <div class="preview-browser"><span class="browser-dots">● ● ●</span><span>harbor / merchant</span><span>↗</span></div>
    <div class="console-layout"><div class="mini-sidebar"><b>H.</b><span class="selected">Overview</span><span>Orders</span><span>Inventory</span><span>Settings</span></div>
    <div class="console-content"><div class="mini-heading"><b>Operations overview</b><span>This week ⌄</span></div><div class="mini-stats"><div>Orders to fulfil<strong>24</strong></div><div>Stock alerts<strong>03</strong></div></div>
    <div class="mini-table"><div><span>Recent orders</span><span>Status</span></div><div><span>#HH-1048 · Home collection</span><i>Ready</i></div><div><span>#HH-1047 · Everyday objects</span><i>In progress</i></div><div><span>#HH-1046 · Living essentials</span><i>Dispatched</i></div></div></div></div></div>`;
  return `<div class="product-preview saas ${compact ? 'compact' : ''}" aria-label="Fictional Northline SaaS planning interface preview">
    <div class="preview-browser"><span class="browser-dots">● ● ●</span><span>northline / workspace</span><span>↗</span></div>
    <div class="saas-nav"><b>n / northline</b><span>Workspace &nbsp; / &nbsp; Product</span><span class="mini-avatar">SE</span></div>
    <div class="board"><div class="board-heading"><b>Ideas into motion.</b><span>Q4 initiatives</span></div><div class="board-columns"><div><span>Planned <i>2</i></span><article><small>PRODUCT</small><b>Workspace onboarding</b><p>A clearer first five minutes.</p><span>SE &nbsp; · &nbsp; 3 tasks</span></article><article><b>Search & discovery</b><span>4 tasks</span></article></div><div><span>In progress <i>1</i></span><article><small>DESIGN</small><b>Planning experience</b><p>One place for the next step.</p><span>SE &nbsp; · &nbsp; 5 tasks</span></article></div><div><span>Ready for review <i>1</i></span><article><small>ENGINEERING</small><b>Workspace permissions</b><p>Clear roles. Useful control.</p><span>2 tasks</span></article></div></div></div></div>`;
}

function footer() { return `<footer><span>${attribution}</span><span>Product design. Full-stack development.</span></footer>`; }
function loginPage(state) {
  return `<div class="login-page"><header class="topbar"><a class="brand" href="/" aria-label="AethDesign workspace">${brand}</a><span class="top-meta">CLIENT WORKSPACE <span class="tiny-line"></span> LOCAL DEMO</span></header>
    <main id="main" class="login-main"><section class="login-intro"><span class="eyebrow">WEB & APP DESIGN STUDIO</span><h1>Your product.<br><em>Our shared workspace.</em></h1><p>From the first interface to the systems behind it. Review direction, share feedback and follow your product into delivery.</p>
    <div class="login-preview">${productPreview('p1', true)}<div class="preview-caption"><span class="status-dot"></span> DIGITAL PRODUCTS, BUILT END TO END.</div></div></section>
    <section class="login-panel"><div class="panel-heading"><span class="eyebrow">LET’S MOVE THINGS FORWARD</span><h2>Welcome back.</h2><p>Sign in to your project workspace.</p></div>
    <form data-testid="login-form" id="login-form"><label for="login-email">Email address</label><input id="login-email" data-testid="login-email" type="email" name="email" autocomplete="username" maxlength="254" placeholder="you@company.com" value="${esc(loginDraft.email)}" required>
    <label for="login-password">Password</label><input id="login-password" data-testid="login-password" type="password" name="password" autocomplete="current-password" maxlength="256" placeholder="Your password" value="${esc(loginDraft.password)}" required>
    ${state.loginError ? `<p class="feedback error" role="alert" data-testid="login-error">${esc(state.loginError)}</p>` : ''}
    <button class="button primary full" data-testid="login-submit" type="submit" ${state.authBusy ? 'disabled' : ''}>${state.authBusy ? 'Signing in…' : `Enter workspace ${arrow}`}</button></form>
    <div class="demo-picker"><span class="eyebrow">EXPLORE THE FICTIONAL DEMO</span><p>Choose a role to fill its local demo credentials.</p><div class="demo-buttons"><button data-demo="harbor">Harbor client</button><button data-demo="northline">Northline client</button><button data-demo="studio">Studio</button></div><span class="demo-note">Synthetic accounts · Stored on this device’s local server</span></div>
    <div class="login-end"><span class="mini-symbol">↗</span><p>One studio. The whole product.<br><span>UI/UX, frontend, backend and delivery.</span></p></div></section></main>${footer()}</div>`;
}
function shell(state, content) {
  const needs = state.projects.filter(p => p.status === 'awaiting_review').length;
  const staff = state.user.role === 'staff';
  return `<div class="workspace-shell"><header class="topbar"><a class="brand" href="/" data-nav="overview" aria-label="AethDesign project overview">${brand}</a><span class="top-meta">${staff ? 'STUDIO' : 'CLIENT'} WORKSPACE <span class="tiny-line"></span> LOCAL DEMO</span><div class="account"><span class="avatar">${staff ? 'AÐ' : esc(state.user.name.split(' ').map(s=>s[0]).join(''))}</span><span class="account-label"><b data-testid="user-name">${esc(state.user.name)}</b><small>${staff ? 'Studio team' : 'Client account'}</small></span><button class="logout" data-testid="logout" aria-label="Sign out">Sign out <span aria-hidden="true">↗</span></button></div></header>
    <div class="workspace-body"><aside class="sidebar"><div class="side-label">YOUR WORKSPACE</div><button class="side-nav ${!state.projectId ? 'active' : ''}" data-nav="overview"><span aria-hidden="true">▦</span> Project overview <span class="count">${state.projects.length}</span></button>
    <div class="side-projects"><span class="side-label">PROJECTS</span>${state.projects.map(p => `<button data-open="${esc(p.id)}" class="side-project ${state.projectId === p.id ? 'active' : ''}"><span class="status-dot ${esc(p.status)}"></span><span>${esc(p.title.replace('Harbor ', '').replace('Northline ', ''))}</span></button>`).join('')}</div>
    <div class="side-review"><span class="eyebrow">NEXT IN DELIVERY</span><strong>${needs ? `${needs} ${needs === 1 ? 'review' : 'reviews'} waiting` : 'Reviews up to date'}</strong><p>${staff ? 'Keep direction and delivery connected.' : 'Your feedback shapes what comes next.'}</p></div>
    <div class="side-bottom"><span class="side-label">AETHDESIGN</span><p>Independent studio.<br>End-to-end thinking.</p><span class="local-indicator"><i></i> LOCAL WORKSPACE</span></div></aside>
    <div class="content-wrap"><main id="main" tabindex="-1">${content}</main>${footer()}</div></div></div>`;
}
function projectCard(p, index, staff) {
  return `<article class="project-card" data-testid="project-card" data-project-id="${esc(p.id)}"><div class="card-preview"><span class="preview-tag">${p.id === 'p1' ? 'STOREFRONT' : p.id === 'p2' ? 'MERCHANT CONSOLE' : 'SAAS WORKSPACE'} / INTERFACE DIRECTION</span>${productPreview(p.id, true)}</div>
    <div class="card-body"><div class="card-meta"><span>${esc(staff ? p.clientName : p.category)}</span>${badge(p.status)}</div><h2>${esc(p.title)}</h2><p>${esc(p.description)}</p><div class="progress-row"><span>Delivery progress</span><span>${p.progress}%</span></div><div class="progress"><div class="progress-fill progress-${p.progress}"></div></div>
    <div class="card-bottom"><div><small>NEXT MILESTONE</small><span>${esc(p.nextMilestone)}</span></div><button class="button card-open" data-testid="open-project" data-project-id="${esc(p.id)}" data-open="${esc(p.id)}">Open project ${arrow}</button></div></div></article>`;
}
function overview(state) {
  const staff = state.user.role === 'staff', count = state.projects.length;
  const review = state.projects.filter(p=>p.status==='awaiting_review').length;
  const approved = state.projects.filter(p=>p.status==='approved').length;
  return `<div class="page-heading"><div><span class="eyebrow">${staff ? 'STUDIO / DELIVERY OVERVIEW' : 'CLIENT / PROJECT OVERVIEW'}</span><h1>${staff ? 'The whole picture.' : `Good to see you, ${esc(state.user.name.split(' ')[0])}.`}</h1><p>${staff ? 'Product direction, client decisions and the next build. All in one place.' : 'Your projects, the latest direction, and a clear next step.'}</p></div><span class="heading-date">WORKSPACE SNAPSHOT<br><b>13 October 2026</b></span></div>
    <div class="summary-strip"><div><span>ACTIVE PROJECTS</span><strong>${count.toString().padStart(2,'0')}<small>${staff ? 'Across the studio' : 'In your workspace'}</small></strong></div><div><span>AWAITING REVIEW</span><strong>${review.toString().padStart(2,'0')}<small>${review ? 'Ready for a decision' : 'Nothing waiting'}</small></strong></div><div><span>${staff ? 'APPROVED DIRECTIONS' : 'PROJECT INVESTMENT'}</span><strong class="summary-money">${staff ? approved.toString().padStart(2,'0') : money(state.projects.reduce((s,p)=>s+p.budgetCents,0))}<small>${staff ? 'Moving toward handoff' : 'Total agreed scope · EUR'}</small></strong></div></div>
    <div class="section-heading"><h2>Your projects <span class="muted">/ ${count.toString().padStart(2,'0')}</span></h2><span class="section-note">DESIGN → DEVELOPMENT → DELIVERY</span></div>
    <div class="project-grid" data-testid="project-list">${state.projects.length ? state.projects.map((p,i)=>projectCard(p,i,staff)).join('') : `<div class="empty"><h2>No projects yet.</h2><p>Your assigned projects will appear here.</p></div>`}</div>
    <div class="workspace-note"><span class="note-icon" aria-hidden="true">↗</span><div><b>One conversation. A connected product.</b><p>Project direction, implementation notes and your feedback stay together in each workspace.</p></div></div>`;
}
function draftField(kind, testid, label, max, rows = 4, hint = '') {
  return `<label for="${testid}">${label}</label>${hint ? `<p class="field-hint" id="${testid}-hint">${hint}</p>` : ''}<textarea id="${testid}" data-testid="${testid}" data-draft="${kind}" rows="${rows}" maxlength="${max}" ${hint ? `aria-describedby="${testid}-hint"` : ''}>${esc(controller.draft(kind))}</textarea>`;
}
function feedback(kind, id) {
  const notice = controller.notice(kind);
  return `<p class="feedback ${notice.includes('saved') || notice.includes('published') ? 'success' : ''}" data-testid="${id}" role="status" aria-live="polite">${esc(notice)}</p>`;
}
function reviewForm(state) {
  const p = state.detail;
  if (state.user.role === 'staff') return `<aside class="action-panel"><span class="eyebrow">STUDIO / NEXT ITERATION</span><h2>Publish a revision.</h2><p>Share what changed and give the client a clear review focus. Publishing opens a new review.</p><form id="revision-form"><label for="revision-title">Revision title</label><input id="revision-title" data-testid="revision-title" data-draft="title" maxlength="120" required placeholder="What’s new in this direction?" value="${esc(controller.draft('title'))}">${draftField('summary','revision-summary','Summary & review focus',2000,5)}<button class="button primary full" type="submit" data-testid="publish-revision" ${controller.busy('revision') ? 'disabled' : ''}>${controller.busy('revision') ? 'Publishing…' : `Publish revision ${p.currentRevision+1} ${arrow}`}</button>${feedback('revision','revision-status')}</form><span class="panel-footnote">Based on revision ${p.currentRevision} · Previous reviews are retained.</span></aside>`;
  if (p.status !== 'awaiting_review') return `<aside class="action-panel resolved"><span class="eyebrow">CLIENT / REVIEW DECISION</span><span class="resolved-icon" aria-hidden="true">${p.status === 'approved' ? '✓' : '↗'}</span><h2>${p.status === 'approved' ? 'Direction approved.' : 'Feedback received.'}</h2><p>${p.status === 'approved' ? 'This revision is approved. The studio can move forward with the agreed direction.' : 'Your requested changes are recorded. The studio can address them in the next revision.'}</p>${feedback('decision','decision-status')}<span class="panel-footnote">Revision ${p.currentRevision} · Decision retained in history</span></aside>`;
  return `<aside class="action-panel"><span class="eyebrow">CLIENT / YOUR NEXT STEP</span><h2>Review the direction.</h2><p>Approve this revision to move forward, or describe what needs to change.</p><form id="decision-form">${draftField('decision','decision-note','Your review note',2000,5,'Required when requesting changes. Optional for approval.')}<button class="button primary full" type="submit" data-testid="approve-revision" ${controller.busy('decision') ? 'disabled' : ''}>Approve revision ${arrow}</button><button class="button secondary full" type="button" data-testid="request-changes" ${controller.busy('decision') ? 'disabled' : ''}>Request changes</button>${feedback('decision','decision-status')}</form><span class="panel-footnote">You are reviewing revision ${p.currentRevision}.</span></aside>`;
}
function brief(state) {
  const p = state.detail;
  return `<div class="detail-grid"><div class="detail-primary"><section class="brief-panel"><span class="eyebrow">01 / THE PRODUCT</span><h2>A clear brief.<br><em>A connected build.</em></h2><p data-testid="project-brief">${esc(p.brief)}</p><div class="scope-tags"><span>UI/UX direction</span><span>Responsive frontend</span><span>Backend & APIs</span></div></section><section class="content-panel"><div class="section-heading"><h2>Agreed deliverables</h2><span class="muted">${p.deliverables.length.toString().padStart(2,'0')}</span></div><ul class="deliverables" data-testid="project-deliverables">${p.deliverables.map((d,i)=>`<li><span>${(i+1).toString().padStart(2,'0')}</span>${esc(d)}<i aria-hidden="true">↗</i></li>`).join('')}</ul></section><section class="content-panel"><div class="section-heading"><h2>Delivery milestones</h2><span class="muted">${p.progress}% complete</span></div><ol class="timeline" data-testid="project-timeline">${p.timeline.map(t=>`<li class="${esc(t.status)}"><span class="timeline-marker" aria-hidden="true">${t.status==='complete'?'✓':t.status==='current'?'•':''}</span><div><b>${esc(t.title)}</b><small>${t.status==='complete'?'Complete':t.status==='current'?'Current focus':'Up next'}</small></div></li>`).join('')}</ol></section></div><aside class="context-panel"><span class="eyebrow">CURRENT DIRECTION / R${p.currentRevision}</span>${productPreview(p.id,true)}<p class="context-caption">Fictional ${p.id==='p1'?'commerce':p.id==='p2'?'operations':'SaaS'} interface preview. See Revisions for the review focus.</p><div class="context-bottom"><span class="eyebrow">NEXT MILESTONE</span><h3>${esc(p.nextMilestone)}</h3><p>${p.status==='awaiting_review'?'The current direction is ready for your review.':p.status==='approved'?'The approved direction is moving toward delivery.':'The studio will use your feedback for the next iteration.'}</p><button class="button secondary full" data-tab="revisions">${state.user.role==='staff'?'Manage revisions':'View revision & review'} ${arrow}</button></div></aside></div>`;
}
function revisions(state) {
  const current = state.revisions.find(r=>r.number===state.detail.currentRevision);
  return `<div class="detail-grid"><section class="detail-primary revision-section"><div class="section-heading"><h2>Revision history</h2><span class="muted">${state.revisions.length} ${state.revisions.length===1?'direction':'directions'}</span></div>${[...state.revisions].reverse().map(r=>`<article class="revision-card ${r.number===state.detail.currentRevision?'current':''}" data-testid="revision-card" data-revision-number="${r.number}"><div class="revision-meta"><span class="revision-number">R${String(r.number).padStart(2,'0')}</span><span>${r.number===state.detail.currentRevision?'CURRENT REVISION':'PREVIOUS DIRECTION'}</span><time>${date(r.publishedAt)}</time></div><h2>${esc(r.title)}</h2><p>${esc(r.summary)}</p>${r.number===state.detail.currentRevision?`<div class="revision-preview">${productPreview(state.projectId,true)}</div>`:''}${r.decision?`<div class="decision-record"><b>${r.decision.decision==='approve'?'Approved':'Changes requested'} · ${esc(r.decision.author.name)}</b>${r.decision.note?`<p>${esc(r.decision.note)}</p>`:''}<time>${date(r.decision.createdAt)}</time></div>`:''}</article>`).join('')}${!current?'<p class="empty">Revision details are unavailable. Refresh the latest details.</p>':''}</section>${reviewForm(state)}</div>`;
}
function discussion(state) {
  return `<div class="detail-grid discussion-grid"><section class="detail-primary"><div class="section-heading"><h2>The conversation</h2><span class="muted">${state.comments.length} ${state.comments.length===1?'comment':'comments'}</span></div><div class="comments">${state.comments.length ? state.comments.map(c=>`<article class="comment" data-testid="comment-item"><div class="comment-avatar">${c.author.role==='staff'?'AÐ':esc(c.author.name.split(' ').map(n=>n[0]).join(''))}</div><div class="comment-content"><div class="comment-heading"><b>${esc(c.author.name)}</b><span class="role-label">${c.author.role==='staff'?'STUDIO':'CLIENT'}</span><time>${date(c.createdAt)}</time></div><p data-testid="comment-text">${esc(c.body)}</p></div></article>`).join('') : '<div class="empty"><h2>Start the conversation.</h2><p>Questions and implementation notes belong here.</p></div>'}</div><section class="comment-compose"><h2>Add to the discussion.</h2><form id="comment-form">${draftField('comment','comment-body','Your comment',2000,4,'Visible to this project’s client and the studio.')}<div class="compose-bottom"><span>Keep the product context together.</span><button class="button primary" type="submit" data-testid="comment-submit" ${controller.busy('comment') ? 'disabled' : ''}>${controller.busy('comment')?'Saving…':`Post comment ${arrow}`}</button></div>${feedback('comment','comment-status')}</form></section></section><aside class="discussion-note"><span class="eyebrow">A SHARED POINT OF REFERENCE</span><h2>Good feedback<br><em>moves things forward.</em></h2><p>Tell us what works, what feels unclear, and what the product needs to do. Specific context helps us connect the interface to the implementation.</p><div><span class="eyebrow">LOOKING FOR A DECISION?</span><p>Use the revision review to approve a direction or request changes.</p><button class="text-button" data-tab="revisions">Go to revisions ${arrow}</button></div></aside></div>`;
}
function activity(state) {
  const labels = {revision_published:'Published a new revision', decision_submitted:'Submitted a review decision', comment_added:'Added a comment'};
  return `<section class="activity-panel"><div class="section-heading"><h2>Project activity</h2><span class="muted">A record of shared progress</span></div>${state.events.length ? `<ol class="activity-list">${[...state.events].reverse().map(e=>`<li data-testid="activity-item" data-event-type="${esc(e.type)}"><span class="activity-icon" aria-hidden="true">${e.type==='decision_submitted'?'✓':e.type==='comment_added'?'↳':'↗'}</span><div><b>${esc(labels[e.type] || e.type)}</b><p>${esc(e.actor.name)} · Revision ${e.revision}${e.decision?` · ${e.decision==='approve'?'Approved':'Changes requested'}`:''}</p></div><time>${date(e.createdAt)}</time></li>`).join('')}</ol>` : '<div class="empty"><span class="empty-symbol" aria-hidden="true">↗</span><h2>The next step starts here.</h2><p>New revisions, review decisions and discussion comments will appear in this project’s activity.</p></div>'}</section>`;
}
function detail(state) {
  const p = state.detail;
  return `<section data-testid="project-detail" data-project-id="${esc(p.id)}"><button class="back-button" data-testid="back-projects" data-nav="overview"><span aria-hidden="true">←</span> All projects</button><div class="detail-heading"><div><span class="eyebrow">${esc(p.clientName)} / ${esc(p.category)}</span><h1 data-testid="project-title">${esc(p.title)}</h1><p>${esc(p.description)}</p></div><div data-testid="project-status">${badge(p.status)}</div></div><div class="project-stats"><div><span>PROJECT INVESTMENT</span><b data-testid="project-budget" data-total-cents="${p.budgetCents}">${money(p.budgetCents)}</b></div><div><span>DELIVERY PROGRESS</span><b>${p.progress}% <span class="stat-small">of agreed scope</span></b></div><div><span>CURRENT REVISION</span><b data-testid="current-revision">${String(p.currentRevision).padStart(2,'0')} <span class="stat-small">${p.status==='awaiting_review'?'Ready to review':'Decision recorded'}</span></b></div><div><span>NEXT MILESTONE</span><b class="stat-milestone">${esc(p.nextMilestone)}</b></div></div>
    <nav class="tabs" aria-label="Project sections">${[['brief','Project brief',''],['revisions','Revisions',state.revisions.length],['discussion','Discussion',state.comments.length],['activity','Activity','']].map(([name,label,num])=>`<button data-testid="tab-${name}" data-tab="${name}" class="${state.tab===name?'active':''}" aria-current="${state.tab===name?'page':'false'}">${label}${num!==''?` <span>${num}</span>`:''}</button>`).join('')}</nav>
    ${state.refreshError?`<div class="recovery" role="status"><span>${esc(state.refreshError)}</span><button class="button secondary" data-retry="refresh">Refresh details</button></div>`:''}
    ${state.tab==='brief'?brief(state):state.tab==='revisions'?revisions(state):state.tab==='discussion'?discussion(state):activity(state)}</section>`;
}
function render(state) {
  const focused = document.activeElement;
  const focusId = focused?.id, start = focused?.selectionStart, end = focused?.selectionEnd;
  if (state.user && previousUser !== state.user.id) { loginDraft.email=''; loginDraft.password=''; }
  if (!state.user && previousUser) history.replaceState({}, '', '/');
  previousUser = state.user?.id || null;
  if (state.loading && !state.user) root.innerHTML = `<main id="main" class="initial">${brand}<p role="status">Opening your workspace…</p></main>`;
  else if (!state.user) root.innerHTML = loginPage(state);
  else {
    let content;
    if (state.loading) content = `<div class="loading-panel" role="status"><span class="eyebrow">YOUR WORKSPACE</span><h1>Bringing it together.</h1><p>Loading the latest project details…</p></div>`;
    else if (state.error) content = `<div class="error-panel" role="alert"><span class="eyebrow">WORKSPACE UPDATE</span><h1>Let’s try that again.</h1><p>${esc(state.error)}</p><button class="button primary" data-retry="load">Try again</button><button class="text-button" data-testid="back-projects" data-nav="overview">Back to projects</button></div>`;
    else content = state.detail ? detail(state) : overview(state);
    root.innerHTML = shell(state,content);
  }
  if (focusId) {
    const el = document.getElementById(focusId);
    if (el) { el.focus({preventScroll:true}); if (typeof start === 'number' && el.setSelectionRange && el.type !== 'email') el.setSelectionRange(start,end); }
  }
}
const controller = new Workspace.Controller(Workspace.http, render);
function route(pid, tab = 'brief', push = true) {
  const url = pid ? `/?project=${encodeURIComponent(pid)}&tab=${encodeURIComponent(tab)}` : '/';
  if (push) history.pushState({}, '', url);
  if (!pid) controller.overview(); else controller.open(pid,tab);
}
root.addEventListener('input', event => {
  const el = event.target;
  if (el.id==='login-email') loginDraft.email=el.value;
  else if (el.id==='login-password') loginDraft.password=el.value;
  else if (el.dataset.draft) controller.setDraft(el.dataset.draft,el.value);
});
root.addEventListener('submit', event => {
  event.preventDefault();
  const form = event.target;
  if (form.id==='login-form') {
    const email = document.getElementById('login-email').value, password = document.getElementById('login-password').value;
    history.replaceState({}, '', '/'); controller.login(email,password);
  } else if (form.id==='comment-form') controller.mutate('comment');
  else if (form.id==='revision-form') controller.mutate('revision');
  else if (form.id==='decision-form') controller.mutate('decision','approve');
});
root.addEventListener('click', event => {
  const el = event.target.closest('button, a');
  if (!el) return;
  if (el.dataset.demo) {
    const account=demoAccounts[el.dataset.demo]; loginDraft.email=account.email; loginDraft.password=account.password;
    render(controller.state); document.getElementById('login-submit')?.focus();
  } else if (el.dataset.testid==='logout') controller.logout();
  else if (el.dataset.nav==='overview') { event.preventDefault(); route(null); }
  else if (el.dataset.open) { route(el.dataset.open); window.scrollTo(0,0); }
  else if (el.dataset.tab) {
    history.pushState({}, '', `/?project=${encodeURIComponent(controller.state.projectId)}&tab=${el.dataset.tab}`);
    controller.tab(el.dataset.tab);
  } else if (el.dataset.testid==='request-changes') {
    const note=document.getElementById('decision-note');
    if (!note.value.trim()) { note.setCustomValidity('Describe the changes you need before submitting.'); note.reportValidity(); note.addEventListener('input',()=>note.setCustomValidity(''),{once:true}); return; }
    controller.mutate('decision','request_changes');
  } else if (el.dataset.retry==='refresh') controller.retryRefresh();
  else if (el.dataset.retry==='load') controller.state.projectId ? controller.open(controller.state.projectId,controller.state.tab) : controller.overview();
});
window.addEventListener('popstate',()=>{
  const q=new URLSearchParams(location.search), pid=q.get('project');
  if (!controller.state.user) return;
  if (pid && controller.state.projects.some(p=>p.id===pid)) controller.open(pid,q.get('tab')||'brief'); else controller.overview();
});
const query = new URLSearchParams(location.search);
controller.start({projectId:query.get('project'),tab:query.get('tab')});
