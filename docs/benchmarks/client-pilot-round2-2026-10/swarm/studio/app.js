'use strict';
const count = document.querySelector('[data-testid="class-count"]');
const status = document.querySelector('[data-testid="shortlist-status"]');
let classCount = 0;
for (const button of document.querySelectorAll('button[data-class]')) {
  button.addEventListener('click', () => {
    classCount += 1;
    count.textContent = String(classCount);
    status.textContent = `${button.dataset.class} added. ${classCount} ${classCount === 1 ? 'class' : 'classes'} in your local demo shortlist. Nothing is booked.`;
  });
}
