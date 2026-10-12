import { TRIPS, STORAGE_KEY, readTrip, totalCents, money, validTravelers, hasTrip } from './trips.js';

const byId = id => document.querySelector(id);
const imageMarkup = trip => trip.image
  ? `<img src="${trip.image}" alt="${trip.name} journey landscape in ${trip.region}">`
  : '<div class="art-desert" role="img" aria-label="Abstract route illustration in sandstone, tracing the Desert itinerary"></div>';
function cardMarkup(trip, index, detailed = false) {
  const facts = `<div class="journey-facts"><span><strong>${String(index + 1).padStart(2, '0')}</strong> / ${trip.terrain}</span><span>${trip.days} days</span><span>${money(trip.priceCents)} <strong>/ traveler</strong></span></div>`;
  const action = detailed
    ? `<button class="trip-link" type="button" data-testid="select-journey" data-journey-id="${trip.id}"><span>Build this field note</span><b aria-hidden="true">↗</b></button>`
    : `<a class="trip-link" href="journeys.html"><span>Read the field note</span><b aria-hidden="true">↗</b></a>`;
  return `<article class="${detailed ? 'journey-card' : 'trip-card'}" data-testid="journey-card" data-journey-id="${trip.id}">
    <div class="trip-photo">${imageMarkup(trip)}<span class="hero-note meta">${String(index + 1).padStart(2, '0')} / ${trip.region}</span></div>
    <div class="trip-body"><div class="card-meta"><span class="eyebrow">${trip.terrain} · ${trip.days} days</span><span class="meta">${money(trip.priceCents)} / person</span></div><h3>${trip.name}</h3><p>${trip.intro}</p>${detailed ? facts : ''}${action}</div>
  </article>`;
}
function renderHome() {
  const container = byId('[data-home-trips]');
  if (container) container.innerHTML = Object.values(TRIPS).map((trip, index) => cardMarkup(trip, index)).join('');
}
function renderJourneys() {
  const list = byId('[data-journey-list]');
  if (!list) return;
  const filter = byId('[data-testid="terrain-filter"]');
  const paint = () => {
    const trips = Object.values(TRIPS).filter(trip => filter.value === 'all' || trip.terrain === filter.value);
    list.innerHTML = trips.map(cardMarkup).join('');
    byId('[data-results-count]').textContent = `${trips.length} ${trips.length === 1 ? 'journey' : 'journeys'}`;
  };
  list.addEventListener('click', event => {
    const button = event.target.closest('button[data-testid="select-journey"]');
    if (!button || !hasTrip(button.dataset.journeyId)) return;
    const prior = readSaved();
    saveTrip({ ...prior, id: button.dataset.journeyId });
    location.href = `builder.html?trip=${button.dataset.journeyId}`;
  });
  filter.addEventListener('change', paint);
  paint();
}
function readSaved() {
  try { return readTrip(localStorage.getItem(STORAGE_KEY)); }
  catch { return readTrip(null); }
}
function saveTrip(trip) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(trip)); } catch { /* private browsing may disable storage */ }
}
function renderBuilder() {
  const choice = byId('[data-testid="journey-select"]');
  if (!choice) return;
  choice.innerHTML = Object.values(TRIPS).map(t => `<option value="${t.id}">${t.name} · ${t.region} · ${t.days} days</option>`).join('');
  const saved = readSaved();
  const requested = new URLSearchParams(location.search).get('trip');
  let state = { ...saved, id: hasTrip(requested) ? requested : saved.id };
  const travelers = byId('[data-testid="travelers"]');
  const guide = byId('[data-testid="add-guide"]');
  choice.value = state.id;
  travelers.value = String(state.travelers);
  guide.checked = state.guide;
  if (hasTrip(requested)) saveTrip(state);
  const paint = () => {
    const trip = TRIPS[state.id];
    byId('[data-trip-name]').textContent = `${trip.name} / ${trip.terrain}`;
    const travelerLabel = `${state.travelers} traveler${state.travelers === 1 ? '' : 's'}`;
    byId('[data-trip-summary]').textContent = `${trip.place} · ${trip.days} days · ${travelerLabel} · ${state.guide ? 'private guide included' : 'no private guide'} · ${trip.intro}`;
    byId('[data-duration]').textContent = `${trip.days} days · ${trip.days - 1} nights`;
    const cents = totalCents(state);
    const total = byId('[data-testid="trip-total"]');
    total.dataset.totalCents = String(cents);
    total.textContent = money(cents);
    byId('[data-itinerary]').innerHTML = trip.itinerary.map(([number, title, description], index) => `<details class="day" ${index === 0 ? 'open' : ''}><summary><span class="day-num">DAY ${number}</span><span>${title}</span></summary><p>${description}</p></details>`).join('');
    byId('[data-inclusions]').innerHTML = trip.inclusions.map(item => `<li>${item}</li>`).join('');
  };
  const commit = () => { saveTrip(state); paint(); };
  choice.addEventListener('change', () => { state.id = hasTrip(choice.value) ? choice.value : 'ridge'; commit(); });
  travelers.addEventListener('change', () => {
    state.travelers = validTravelers(travelers.value, state.travelers);
    travelers.value = String(state.travelers);
    commit();
  });
  guide.addEventListener('change', () => { state.guide = guide.checked; commit(); });
  const form = byId('[data-testid="trip-form"]');
  form.addEventListener('submit', event => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const name = form.elements.name.value.trim();
    byId('[data-testid="trip-status"]').textContent = `A local demo note for ${name} is ready: ${TRIPS[state.id].name}, ${state.travelers} traveler${state.travelers === 1 ? '' : 's'}, ${money(totalCents(state))}. No information was sent.`;
  });
  paint();
}
renderHome();
renderJourneys();
renderBuilder();
