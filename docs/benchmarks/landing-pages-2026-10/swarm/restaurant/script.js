const reservationForm = document.querySelector('[data-testid="reservation-form"]');
const reservationStatus = document.querySelector('[data-testid="reservation-status"]');

if (reservationForm && reservationStatus) {
  reservationForm.addEventListener('submit', (event) => {
    event.preventDefault();

    if (!reservationForm.checkValidity()) {
      reservationForm.reportValidity();
      return;
    }

    const formData = new FormData(reservationForm);
    const name = String(formData.get('name') ?? '').trim();
    const dateValue = String(formData.get('date') ?? '');
    const guests = String(formData.get('guests') ?? '').trim();
    const [year, month, day] = dateValue.split('-').map(Number);
    const date = new Date(year, month - 1, day);
    const dateLabel = Number.isNaN(date.getTime())
      ? dateValue
      : new Intl.DateTimeFormat('en-GB', {
          weekday: 'long',
          day: 'numeric',
          month: 'long',
          year: 'numeric',
        }).format(date);

    reservationStatus.textContent = `Thanks, ${name}. Your demo request for ${guests} ${guests === '1' ? 'guest' : 'guests'} on ${dateLabel} is ready. This is a local demonstration; no reservation has been made.`;
  });
}
