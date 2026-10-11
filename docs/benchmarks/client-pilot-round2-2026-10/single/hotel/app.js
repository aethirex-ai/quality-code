const form = document.querySelector('[data-testid="reservation-form"]');
const status = document.querySelector('[data-testid="reservation-status"]');
form.addEventListener('submit', (event) => {
  event.preventDefault();
  if (!form.reportValidity()) return;
  const values = new FormData(form);
  const name = String(values.get('name')).trim();
  if (!name) { status.textContent = 'Please enter your name to preview a stay.'; return; }
  const guests = String(values.get('guests'));
  status.textContent = `Demo stay preview for ${name}: arrival ${values.get('date')}, ${guests} ${guests === '1' ? 'guest' : 'guests'}. No room has been booked and no details have been sent. All rates are illustrative.`;
});
