const form = document.querySelector('[data-testid="estimate-form"]');
const status = document.querySelector('[data-testid="estimate-status"]');
form.addEventListener('submit', (event) => {
  event.preventDefault();
  if (!form.reportValidity()) return;
  const values = new FormData(form);
  const name = String(values.get('name')).trim();
  if (!name) { status.textContent = 'Please enter your name to preview an enquiry.'; return; }
  status.textContent = `Demo enquiry preview for ${name}: ${values.get('project')}. A real first conversation would explore your site, priorities and scope before any estimate. Nothing has been sent or saved.`;
});
