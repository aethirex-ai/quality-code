'use strict';

const form = document.querySelector('[data-testid="estimate-form"]');
const status = document.querySelector('[data-testid="estimate-status"]');
const submitButton = form.querySelector('button[type="submit"]');
submitButton.disabled = false;

form.addEventListener('submit', (event) => {
  event.preventDefault();
  if (!form.reportValidity()) return;

  const nameInput = form.elements.namedItem('name');
  const name = nameInput.value.trim();
  if (!name) {
    nameInput.setCustomValidity('Please enter your name.');
    nameInput.reportValidity();
    return;
  }

  const project = form.elements.namedItem('project').value;
  status.textContent = `Thank you, ${name}. Your ${project} estimate enquiry is ready in this local demo. No message was sent and your details are not saved.`;
  status.classList.add('is-success');
});

form.elements.namedItem('name').addEventListener('input', (event) => {
  event.target.setCustomValidity('');
});
