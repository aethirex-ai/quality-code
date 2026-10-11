let count = 0;
const counter = document.querySelector('[data-testid="class-count"]');
const status = document.querySelector('[data-testid="class-status"]');
document.querySelectorAll('[data-testid="add-class"]').forEach((button) => {
  button.addEventListener('click', () => {
    count += 1;
    counter.textContent = String(count);
    status.textContent = `${button.dataset.class} added. Your local shortlist contains ${count} ${count === 1 ? 'session' : 'sessions'}. No class has been booked.`;
  });
});
