export const PRODUCTS = Object.freeze([
  { id: 'arc', name: 'ARC', type: 'pendant', title: 'A study in suspension', priceCents: 24900, price: 'EUR 249.00', dimensions: 'L 96 × D 12 × H 18 cm', material: 'Patinated bronze, opal glass', finish: 'Burnished bronze', light: 'Warm, diffused downward light', note: 'A single drawn curve holds a quiet pool of light above a table.' },
  { id: 'line', name: 'LINE', type: 'wall', title: 'Light along the plane', priceCents: 18900, price: 'EUR 189.00', dimensions: 'W 8 × H 62 × D 11 cm', material: 'Brushed bronze, opal glass', finish: 'Satin bronze', light: 'Vertical, wall-washing light', note: 'A slender opal column softens the threshold between corridor and room.' },
  { id: 'orbit', name: 'ORBIT', type: 'table', title: 'A small field of light', priceCents: 32900, price: 'EUR 329.00', dimensions: 'Ø 24 × H 36 cm', material: 'Cast bronze, opal glass', finish: 'Dark bronze', light: 'Low, ambient table light', note: 'A weighted base and floating globe make a measured companion at dusk.' }
]);
export const STORAGE_KEY = 'aurel.plan.v1';
const productIds = new Set(PRODUCTS.map((product) => product.id));
let sessionPlan;
export function fixtureClass(product) { return `fixture ${product.type}`; }
export function validQuantity(value) { return Number.isInteger(value) && value >= 1 && value <= 10; }
export function normalizePlan(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {};
  const source = value.items && typeof value.items === 'object' && !Array.isArray(value.items) ? value.items : value;
  return Object.fromEntries(PRODUCTS.flatMap(({ id }) => validQuantity(source[id]) ? [[id, source[id]]] : []));
}
export function parsePlan(raw) {
  try { return normalizePlan(JSON.parse(raw ?? '{}')); } catch { return {}; }
}
export function planCount(plan) { return Object.values(normalizePlan(plan)).reduce((sum, qty) => sum + qty, 0); }
export function planTotalCents(plan) { return Object.entries(normalizePlan(plan)).reduce((sum, [id, qty]) => sum + PRODUCTS.find((p) => p.id === id).priceCents * qty, 0); }
export function formatEUR(cents) { return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(cents / 100); }

function readPlan() {
  if (sessionPlan) return sessionPlan;
  try { sessionPlan = parsePlan(localStorage.getItem(STORAGE_KEY)); } catch { sessionPlan = {}; }
  return sessionPlan;
}
function savePlan(plan) {
  const safe = normalizePlan(plan);
  sessionPlan = safe;
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(safe)); } catch { /* Storage can be disabled; the page still works in memory. */ }
  return safe;
}
function renderCount(plan) {
  document.querySelectorAll('[data-testid="plan-count"]').forEach((el) => { el.textContent = String(planCount(plan)); });
}
function activateSharedNavigation(plan) {
  renderCount(plan);
  document.querySelectorAll('[data-testid="plan-count"]').forEach((el) => { el.setAttribute('aria-label', `${planCount(plan)} items in specification`); });
}
function setupCollection() {
  const filter = document.querySelector('[data-testid="type-filter"]');
  if (!filter) return;
  const cards = [...document.querySelectorAll('[data-testid="product-card"]')];
  const applyFilter = () => cards.forEach((card) => { card.hidden = filter.value !== 'all' && card.dataset.type !== filter.value; });
  filter.addEventListener('change', applyFilter);
  applyFilter();
  const dialog = document.querySelector('[data-testid="product-dialog"]');
  let returnFocus = null;
  const closeDialog = () => { if (dialog.open) dialog.close(); };
  document.querySelectorAll('[data-testid="open-product"]').forEach((button) => button.addEventListener('click', () => {
    const product = PRODUCTS.find((item) => item.id === button.dataset.productId);
    if (!product) return;
    returnFocus = button;
    dialog.querySelector('[data-dialog-name]').textContent = product.name;
    dialog.querySelector('[data-dialog-title]').textContent = product.title;
    dialog.querySelector('[data-dialog-note]').textContent = product.note;
    dialog.querySelector('[data-dialog-spec]').textContent = `${product.dimensions} · ${product.material} · ${product.finish}`;
    dialog.querySelector('[data-dialog-price]').textContent = product.price;
    dialog.querySelector('[data-testid="add-product"]').dataset.productId = product.id;
    dialog.querySelector('[data-dialog-fixture]').className = fixtureClass(product);
    dialog.showModal();
  }));
  document.querySelector('[data-testid="close-product"]').addEventListener('click', closeDialog);
  dialog.addEventListener('click', (event) => { if (event.target === dialog) closeDialog(); });
  dialog.addEventListener('close', () => returnFocus?.focus());
}
function setupAdds() {
  document.querySelectorAll('[data-testid="add-product"]').forEach((button) => button.addEventListener('click', () => {
    const id = button.dataset.productId;
    if (!productIds.has(id)) return;
    const plan = readPlan();
    plan[id] = Math.min(10, (plan[id] || 0) + 1);
    activateSharedNavigation(savePlan(plan));
    const status = document.querySelector('[data-add-status]');
    if (status) status.textContent = `${PRODUCTS.find((p) => p.id === id).name} added to the local specification.`;
  }));
}
function setupPlanner() {
  const form = document.querySelector('[data-testid="project-form"]');
  if (!form) return;
  const status = document.querySelector('[data-testid="project-status"]');
  let plan = readPlan();
  const update = () => {
    plan = normalizePlan(plan);
    document.querySelectorAll('[data-plan-row]').forEach((row) => {
      const id = row.dataset.planRow;
      row.hidden = !plan[id];
      const input = row.querySelector(`[data-testid="quantity-${id}"]`);
      if (document.activeElement !== input) input.value = String(plan[id] || 1);
      row.querySelector(`[data-line-total="${id}"]`).textContent = plan[id] ? formatEUR(PRODUCTS.find((product) => product.id === id).priceCents * plan[id]) : '';
    });
    const total = planTotalCents(plan);
    const totalEl = document.querySelector('[data-testid="plan-total"]');
    totalEl.dataset.totalCents = String(total);
    totalEl.textContent = formatEUR(total);
    renderCount(plan);
    document.querySelector('[data-empty-plan]').hidden = planCount(plan) > 0;
    form.hidden = planCount(plan) === 0;
  };
  document.querySelectorAll('[data-plan-row]').forEach((row) => {
    const id = row.dataset.planRow;
    const input = row.querySelector(`[data-testid="quantity-${id}"]`);
    input.addEventListener('change', () => {
      const value = input.valueAsNumber;
      if (!validQuantity(value)) { input.value = String(plan[id] || 1); status.textContent = 'Choose a whole quantity from 1 to 10. Your previous estimate is unchanged.'; return; }
      plan[id] = value; status.textContent = ''; plan = savePlan(plan); update();
    });
    input.addEventListener('input', () => { input.setCustomValidity(''); });
  });
  document.querySelectorAll('[data-testid="remove-product"]').forEach((button) => button.addEventListener('click', () => {
    delete plan[button.dataset.productId]; plan = savePlan(plan); status.textContent = 'Item removed from the local specification.'; update();
  }));
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const name = form.elements.namedItem('name').value.trim();
    status.textContent = `A local specification for ${name} is prepared on this device. No enquiry was sent.`;
    form.reset();
  });
  update();
}

if (typeof document !== 'undefined') {
  const initialPlan = readPlan();
  activateSharedNavigation(initialPlan);
  setupCollection();
  setupAdds();
  setupPlanner();
}
