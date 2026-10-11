const estimateForm = document.querySelector('[data-testid="estimate-form"]');
const estimateStatus = document.querySelector('[data-testid="estimate-status"]');

estimateForm.addEventListener('submit', (event) => {
  event.preventDefault();
  if (!estimateForm.reportValidity()) return;
  const nameField = estimateForm.elements.namedItem('name');
  const name = nameField.value.trim();
  if (!name) {
    estimateStatus.textContent = 'Please enter your name using more than spaces before trying the enquiry demo.';
    nameField.focus();
    return;
  }
  const email = estimateForm.elements.namedItem('email').value.trim();
  estimateStatus.textContent = `Thank you, ${name}. Your landscape project enquiry is ready for ${email}. This is a local demo: nothing has been sent or stored.`;
});
