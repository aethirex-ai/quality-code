const reservationForm = document.querySelector('[data-testid="reservation-form"]');
const reservationStatus = document.querySelector('[data-testid="reservation-status"]');
reservationForm.addEventListener('submit', (event) => {
  event.preventDefault();
  if (!reservationForm.reportValidity()) return;
  const fields = reservationForm.elements;
  const name = fields.namedItem('name').value.trim();
  if (!name) {
    reservationStatus.textContent = 'Please enter your name to preview your stay.';
    fields.namedItem('name').focus();
    return;
  }
  const guests = fields.namedItem('guests').value;
  const date = fields.namedItem('date').value;
  reservationStatus.textContent = `Thank you, ${name}. Your demo stay for ${guests} ${guests === '1' ? 'guest' : 'guests'} arriving ${date} is ready to imagine. This is a local preview: nothing was sent and no room is booked.`;
});
